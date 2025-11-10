import asyncio
import difflib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agents.base_agent import BaseAgent
from app.utils.workspace_manager import get_workspace_path
from app.services.event_bus import EventTypes

logger = logging.getLogger(__name__)


class SpecAgent(BaseAgent):
    """Documentation quality agent.

    This agent inspects required documentation artifacts in the workspace,
    highlights missing or stale files, and produces lightweight proposals
    with suggested content to keep the docs aligned with the project state.
    """

    agent_display_name = "Specification Agent"

    def __init__(
        self,
        workspace_path: Optional[str] = None,
        workspace_id: str = "default",
        project_id: Optional[str] = None,
    ) -> None:
        # Determine workspace path before calling BaseAgent (so ensure_workspace_exists runs)
        resolved_workspace_path = (
            Path(workspace_path).resolve()
            if workspace_path
            else Path(get_workspace_path(workspace_id)).resolve()
        )

        self._explicit_workspace_path = str(resolved_workspace_path)
        super().__init__(workspace_id=workspace_id, agent_id="spec", project_id=project_id)

        # Override workspace_path with explicit value when provided
        self.workspace_path = str(resolved_workspace_path)
        self.workspace_dir = Path(self.workspace_path)
        self.proposals_dir = self.workspace_dir / "proposals"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

        # Define documentation templates
        self.required_documents: Dict[str, str] = {
            "PROJECT.md": (
                "# Project Overview\n\n"
                "## Vision\nDescribe the long-term vision for the project.\n\n"
                "## Goals\n- [ ] Short-term goal\n- [ ] Mid-term goal\n- [ ] Long-term goal\n\n"
                "## Current Focus\nSummarize what the team is working on this week.\n"
            ),
            "STATUS.md": (
                "# Weekly Status\n\n"
                "## Highlights\n- Achievement 1\n- Achievement 2\n\n"
                "## Risks\n- Risk 1\n- Risk 2\n\n"
                "## Next Steps\n- Action 1\n- Action 2\n"
            ),
            ".contextpilot/workspace.yaml": (
                "# ContextPilot Workspace Metadata\n"
                "name: {workspace_id}\n"
                "description: Update this file with workspace metadata.\n"
            ),
        }

        # Subscribe to events that trigger documentation validation/updates
        self.subscribe_to_event(EventTypes.GIT_COMMIT)
        self.subscribe_to_event(EventTypes.PROPOSAL_APPROVED)
        self.subscribe_to_event(EventTypes.PROPOSAL_CREATED)
        
        logger.info("[SpecAgent] Subscribed to events: git.commit.v1, proposal.approved.v1, proposal.created.v1")

    # ------------------------------------------------------------------
    # Documentation analysis
    # ------------------------------------------------------------------
    async def validate_docs(self) -> List[Dict[str, Any]]:
        """Detect missing or stale documentation files."""

        self.increment_metric("events_processed")
        issues = await asyncio.to_thread(self._collect_doc_issues)
        logger.info("[SpecAgent] Found %d documentation issues", len(issues))
        return issues

    def _collect_doc_issues(self) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        for relative_path, template in self.required_documents.items():
            expected_path = self.workspace_dir / relative_path
            context_template = template.format(workspace_id=self.workspace_id)

            if not expected_path.exists():
                issues.append(
                    {
                        "file": relative_path,
                        "type": "missing_file",
                        "severity": "high",
                        "message": f"Required documentation file '{relative_path}' is missing.",
                        "suggested_content": context_template,
                    }
                )
                continue

            try:
                content = expected_path.read_text(encoding="utf-8")
            except Exception as exc:  # pragma: no cover - unlikely but defensive
                issues.append(
                    {
                        "file": relative_path,
                        "type": "read_error",
                        "severity": "high",
                        "message": f"Failed to read '{relative_path}': {exc}",
                        "suggested_content": context_template,
                    }
                )
                continue

            if not content.strip():
                issues.append(
                    {
                        "file": relative_path,
                        "type": "empty_file",
                        "severity": "medium",
                        "message": f"'{relative_path}' is empty. Fill in the template content.",
                        "suggested_content": context_template,
                    }
                )
                continue

            # Simple freshness heuristic: ensure key headings exist
            required_headings = [h for h in ["## Vision", "## Goals", "## Highlights"] if h in context_template]
            missing_headings = [heading for heading in required_headings if heading not in content]
            if missing_headings:
                issues.append(
                    {
                        "file": relative_path,
                        "type": "missing_sections",
                        "severity": "medium",
                        "message": f"'{relative_path}' is missing sections: {', '.join(missing_headings)}.",
                        "suggested_content": context_template,
                    }
                )

        return issues

    # ------------------------------------------------------------------
    # Proposal creation helpers
    # ------------------------------------------------------------------
    async def _create_proposal_for_issue(self, issue: Dict[str, Any]) -> str:
        """Generate a proposal artifact for the provided issue."""

        proposal_id = f"spec-{uuid4().hex[:8]}"
        target_file = issue.get("file", "docs/UNKNOWN.md")
        absolute_path = self.workspace_dir / target_file
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        existing_text = ""
        if absolute_path.exists():
            try:
                existing_text = absolute_path.read_text(encoding="utf-8")
            except Exception as exc:  # pragma: no cover
                logger.warning("[SpecAgent] Could not read %s for diff generation: %s", absolute_path, exc)

        suggested_text = issue.get("suggested_content", existing_text)
        diff = self._generate_diff(target_file, existing_text, suggested_text)

        proposal_payload = {
            "id": proposal_id,
            "agent_id": "spec",
            "title": f"Update {target_file}",
            "status": "pending",
            "issue": issue,
            "proposed_changes": [
                {
                    "file_path": target_file,
                    "change_type": "update" if absolute_path.exists() else "create",
                    "description": issue.get("message", "Documentation improvement"),
                }
            ],
            "diff": {
                "format": "unified",
                "content": diff,
            },
        }

        # Write JSON artifact
        json_path = self.proposals_dir / f"{proposal_id}.json"
        json_path.write_text(json.dumps(proposal_payload, indent=2), encoding="utf-8")

        # Write human-friendly markdown summary
        markdown_path = self.proposals_dir / f"{proposal_id}.md"
        markdown_path.write_text(
            self._format_markdown_summary(proposal_payload, suggested_text),
            encoding="utf-8",
        )

        logger.info("[SpecAgent] Created proposal %s for %s", proposal_id, target_file)
        self.increment_metric("events_published")
        return proposal_id

    def _generate_diff(self, file_path: str, current: str, proposed: str) -> str:
        current_lines = current.splitlines()
        proposed_lines = proposed.splitlines()
        diff_lines = difflib.unified_diff(
            current_lines,
            proposed_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
        return "\n".join(diff_lines)

    def _format_markdown_summary(self, proposal: Dict[str, Any], suggested_text: str) -> str:
        issue = proposal.get("issue", {})
        diff_block = proposal.get("diff", {}).get("content", "")
        return (
            f"# Proposal {proposal['id']}\n\n"
            f"**Agent:** Spec\n\n"
            f"**Target file:** `{issue.get('file', 'unknown')}`\n\n"
            f"**Issue:** {issue.get('message', 'Documentation update')}\n\n"
            f"## Suggested Content\n\n"
            f"```markdown\n{suggested_text}\n```\n\n"
            f"## Diff\n\n"
            f"```diff\n{diff_block}\n```\n"
        )

    # ------------------------------------------------------------------
    # Context generation helpers (used by other agents)
    # ------------------------------------------------------------------

    def generate_context_summary(self, proposal_type: str = "development") -> str:
        """
        Provide a lightweight textual summary of the current documentation state.

        Other agents (e.g. DevelopmentAgent) call this as part of their context
        gathering so they don't fall back to a generic summary.
        """

        sections: List[str] = []

        def _read_file(path: Path, label: str, limit: int = 1200) -> None:
            if not path.exists():
                sections.append(f"## {label}\nStatus: missing\n")
                return

            try:
                content = path.read_text(encoding="utf-8").strip()
                if len(content) > limit:
                    content = content[:limit] + "\n...[truncated]..."
                sections.append(f"## {label}\n{content}\n")
            except Exception as exc:  # pragma: no cover - defensive
                sections.append(f"## {label}\nError reading file: {exc}\n")

        # Core documents
        _read_file(self.workspace_dir / "README.md", "README")
        _read_file(self.workspace_dir / "ARCHITECTURE.md", "Architecture")
        _read_file(self.workspace_dir / "STATUS.md", "Status")
        _read_file(self.workspace_dir / "ROADMAP.md", "Roadmap")

        # Workspace metadata
        _read_file(self.workspace_dir / ".contextpilot" / "workspace.yaml", "Workspace Metadata")

        # Outstanding documentation issues
        try:
            issues = self._collect_doc_issues()
            if issues:
                issue_lines = [
                    f"- [{issue.get('severity','unknown')}] {issue.get('file','?')}: {issue.get('message','')}"
                    for issue in issues[:10]
                ]
                sections.append("## Documentation Issues\n" + "\n".join(issue_lines) + "\n")
        except Exception as exc:  # pragma: no cover
            sections.append(f"## Documentation Issues\nUnable to compute issues: {exc}\n")

        sections.append(
            f"## Context Metadata\nProposal type: {proposal_type}\nWorkspace: {self.workspace_id}\n"
        )

        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _handle_git_commit(self, data: Dict[str, Any]) -> None:
        """Update documentation when code changes are committed."""
        files_changed = data.get("files_changed", [])
        commit_hash = data.get("commit_hash")
        proposal_id = data.get("proposal_id")
        
        logger.info(
            f"[SpecAgent] Git commit detected: {commit_hash}, "
            f"files: {len(files_changed)}, proposal: {proposal_id}"
        )
        
        # Validate docs after code changes
        issues = await self.validate_docs()
        if issues:
            logger.info(f"[SpecAgent] Found {len(issues)} documentation issues after commit")
            # Create proposals for high-severity issues
            for issue in issues:
                if issue.get("severity") == "high":
                    await self._create_proposal_for_issue(issue)
                    logger.info(
                        f"[SpecAgent] Created proposal for high-severity issue: {issue.get('file')}"
                    )
        else:
            logger.debug("[SpecAgent] No documentation issues found after commit")

    async def _handle_proposal_approved(self, data: Dict[str, Any]) -> None:
        """Update documentation when proposals are approved."""
        proposal_id = data.get("proposal_id")
        agent_id = data.get("agent_id")
        workspace_id = data.get("workspace_id")
        
        logger.info(
            f"[SpecAgent] Proposal approved: {proposal_id} by {agent_id} in {workspace_id}"
        )
        
        # Validate docs after proposal approval (in case approved changes affect docs)
        issues = await self.validate_docs()
        if issues:
            logger.debug(f"[SpecAgent] Found {len(issues)} documentation issues after proposal approval")

    async def _handle_proposal_created(self, data: Dict[str, Any]) -> None:
        """Track new proposals and validate documentation consistency."""
        proposal_id = data.get("proposal_id")
        agent_id = data.get("agent_id")
        title = data.get("title", "")
        
        logger.debug(
            f"[SpecAgent] Proposal created: {proposal_id} by {agent_id} - {title[:50]}"
        )
        
        # Store proposal info in memory for context
        self.remember(f"proposal_{proposal_id}", {
            "agent_id": agent_id,
            "title": title,
            "created_at": data.get("timestamp"),
        })

    # ------------------------------------------------------------------
    # BaseAgent abstract method implementations
    # ------------------------------------------------------------------

    async def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle incoming events and trigger documentation validation/updates.
        
        Args:
            event_type: Type of event (e.g., 'git.commit.v1')
            event_data: Event data payload
        """
        try:
            logger.info(f"[SpecAgent] Received event: {event_type}")
            
            if event_type == EventTypes.GIT_COMMIT:
                await self._handle_git_commit(event_data)
            elif event_type == EventTypes.PROPOSAL_APPROVED:
                await self._handle_proposal_approved(event_data)
            elif event_type == EventTypes.PROPOSAL_CREATED:
                await self._handle_proposal_created(event_data)
            else:
                logger.debug(
                    f"[SpecAgent] Unhandled event type: {event_type}"
                )
            
            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(
                f"[SpecAgent] Error handling {event_type}: {e}",
                exc_info=True
            )
            self.increment_metric("errors")

    async def start(self) -> None:
        """No background work needed for SpecAgent."""
        logger.debug("[SpecAgent] start() called - no-op.")

    async def stop(self) -> None:
        """No teardown required for SpecAgent."""
        logger.debug("[SpecAgent] stop() called - no-op.")


__all__ = ["SpecAgent"]