"""
Git Agent - Centralized Git Operations Manager

Responsibilities:
- Listen to events from other agents
- Decide when to commit
- Generate semantic commit messages
- Manage branches (git-flow)
- Handle rollbacks

Event-driven architecture: Reacts to changes, doesn't make them directly.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from app.git_context_manager import Git_Context_Manager
from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics
from app.agents.diff_generator import apply_patch, read_file_safe
from app.repositories.proposal_repository import get_proposal_repository
from app.models.proposal import ChangeProposal
from enum import Enum
from pathlib import Path
import json
import os
import httpx
import asyncio

logger = logging.getLogger(__name__)


class CommitType(Enum):
    """Conventional commit types"""

    FEAT = "feat"  # New feature
    FIX = "fix"  # Bug fix
    DOCS = "docs"  # Documentation
    REFACTOR = "refactor"  # Code refactoring
    TEST = "test"  # Tests
    CHORE = "chore"  # Maintenance
    AGENT = "agent"  # Agent-generated change


class EventType(Enum):
    """Event types that trigger git operations"""

    CONTEXT_UPDATED = "context.updated"
    SPEC_CREATED = "spec.created"
    SPEC_UPDATED = "spec.updated"
    CODE_CHANGED = "code.changed"
    MILESTONE_COMPLETED = "milestone.completed"
    PROPOSAL_APPROVED = "proposal.approved"
    TEST_PASSED = "test.passed"


class GitAgent(BaseAgent):
    """
    Git Agent - Handles all git operations intelligently

    Design principles:
    - Event-driven: reacts to events, doesn't poll
    - Smart commits: decides when changes are worth committing
    - Semantic messages: follows conventional commits
    - Idempotent: safe to retry operations
    """

    def __init__(self, workspace_id: str = "default", project_id: Optional[str] = None):
        # Initialize base agent
        super().__init__(
            workspace_id=workspace_id, agent_id="git", project_id=project_id
        )

        # Git-specific manager
        self.git_manager = Git_Context_Manager(workspace_id=workspace_id)

        # Subscribe to events
        self.subscribe_to_event(EventTypes.PROPOSAL_APPROVED)
        self.subscribe_to_event(EventTypes.MILESTONE_COMPLETE)

        # Configuration for LLM-enhanced commits
        self.use_llm_commits = os.getenv("USE_LLM_COMMITS", "false").lower() == "true"
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Environment detection (always check)
        self.is_cloud_run = self._is_cloud_run_mode()
        logger.info(f"[GitAgent] Initialized for workspace: {workspace_id} (mode: {'Cloud Run' if self.is_cloud_run else 'local'})")

    def _is_cloud_run_mode(self) -> bool:
        """
        Determine if running in Cloud Run (production) mode.
        
        Returns:
            True if in Cloud Run mode, False if local mode
        """
        environment = os.getenv("ENVIRONMENT", "local")
        use_pubsub = os.getenv("USE_PUBSUB", "false").lower() == "true"
        is_production = environment == "production"
        return is_production or use_pubsub

    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events (BaseAgent interface).

        Args:
            event_type: Type of event
            data: Event data payload
        """
        logger.info(f"[GitAgent] Received event: {event_type} with data keys: {list(data.keys()) if data else 'empty'}")

        try:
            if event_type == EventTypes.PROPOSAL_APPROVED or event_type == "proposal.approved.v1":
                logger.info(f"[GitAgent] Processing PROPOSAL_APPROVED event for proposal: {data.get('proposal_id')}")
                await self._handle_proposal_approved_v2(data)
            elif event_type == EventTypes.MILESTONE_COMPLETE:
                await self._handle_milestone_v2(data)

            # Update metrics
            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(f"[GitAgent] Error handling {event_type}: {e}")
            self.increment_metric("errors")

    async def handle_event_legacy(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Main event handler - routes events to appropriate handlers

        Args:
            event: Event dict with 'type', 'data', 'source', etc.

        Returns:
            commit_hash if committed, None otherwise
        """
        event_type = event.get("type")
        logger.info(f"[GitAgent] Handling event: {event_type}")

        # Route to specific handler
        handlers = {
            EventType.CONTEXT_UPDATED.value: self._handle_context_update,
            EventType.SPEC_CREATED.value: self._handle_spec_change,
            EventType.SPEC_UPDATED.value: self._handle_spec_change,
            EventType.CODE_CHANGED.value: self._handle_code_change,
            EventType.MILESTONE_COMPLETED.value: self._handle_milestone,
            EventType.PROPOSAL_APPROVED.value: self._handle_proposal,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(event)
        else:
            logger.warning(f"[GitAgent] No handler for event type: {event_type}")
            return None

    async def _handle_context_update(self, event: Dict[str, Any]) -> Optional[str]:
        """Handle context update events"""
        data = event.get("data", {})
        changes = data.get("changes", [])

        # Check if changes are significant
        if not self._should_commit(changes):
            logger.info("[GitAgent] Changes not significant enough for commit")
            return None

        # Generate commit message
        message = self._generate_commit_message(
            commit_type=CommitType.CHORE,
            scope="context",
            subject="Update project context",
            body=self._format_changes(changes),
            agent_name=event.get("source", "git-agent"),
        )

        # Commit
        return self._commit(message, agent="git-agent")

    async def _handle_spec_change(self, event: Dict[str, Any]) -> Optional[str]:
        """Handle spec creation/update events"""
        data = event.get("data", {})
        file_name = data.get("file_name", "document")
        action = "Add" if event["type"] == EventType.SPEC_CREATED.value else "Update"

        message = self._generate_commit_message(
            commit_type=CommitType.DOCS,
            scope="spec",
            subject=f"{action} {file_name}",
            body=data.get("description", ""),
            agent_name=event.get("source", "spec-agent"),
        )

        return self._commit(message, agent="git-agent")

    async def _handle_code_change(self, event: Dict[str, Any]) -> Optional[str]:
        """Handle code change events"""
        data = event.get("data", {})
        files = data.get("files", [])

        # Determine if it's a feature, fix, or refactor
        commit_type = self._infer_commit_type(data)

        message = self._generate_commit_message(
            commit_type=commit_type,
            scope=data.get("scope", "core"),
            subject=data.get("summary", "Code changes"),
            body=f"Modified files:\n" + "\n".join(f"- {f}" for f in files),
            agent_name=event.get("source", "strategy-agent"),
        )

        return self._commit(message, agent="git-agent")

    async def _handle_proposal_approved_v2(self, data: Dict) -> None:
        """Handle proposal.approved.v1 event (new event bus format)"""
        proposal_id = data.get("proposal_id")
        workspace_id = data.get("workspace_id", self.workspace_id)

        logger.info(f"[GitAgent] Proposal {proposal_id} approved in workspace {workspace_id}, applying changes...")
        
        if not proposal_id:
            logger.error("[GitAgent] No proposal_id in event data - cannot process")
            return

        # 1. Load proposal to get diff/changes
        proposal_dict = self._load_proposal(proposal_id)
        if not proposal_dict:
            logger.error(f"[GitAgent] Proposal {proposal_id} not found")
            return

        # Convert to ChangeProposal model for type safety
        try:
            proposal = ChangeProposal(**proposal_dict)
        except Exception as e:
            logger.error(f"[GitAgent] Failed to parse proposal {proposal_id}: {e}")
            # Fallback: create a minimal ChangeProposal-like object from dict
            class ProposalObj:
                def __init__(self, d: Dict):
                    self.id = d.get("id", proposal_id)
                    self.workspace_id = d.get("workspace_id", workspace_id)
                    self.agent_id = d.get("agent_id")
                    self.title = d.get("title", proposal_id)
                    self.description = d.get("description", "")
                    self.proposed_changes = d.get("proposed_changes", [])
            proposal = ProposalObj(proposal_dict)

        # 2. Always check environment mode (local vs Cloud Run)
        # This is critical: behavior differs based on environment
        mode_str = "Cloud Run" if self.is_cloud_run else "local"
        logger.info(f"[GitAgent] Processing proposal in {mode_str} mode")

        # 3. Apply changes based on environment mode
        files_changed = []
        commit_hash = None
        
        if self.is_cloud_run:
            # Cloud Run mode: No git local available
            # Trigger GitHub Action workflow to apply changes remotely
            logger.info(
                f"[GitAgent] Cloud Run mode: Triggering GitHub Action workflow to apply changes"
            )
            github_action_result = await self._trigger_github_action(proposal)
            if github_action_result:
                status = github_action_result.get("status")
                logger.info(
                    f"[GitAgent] GitHub Action trigger result: {status}"
                )
                if status == "error":
                    error_msg = github_action_result.get("message", "Unknown error")
                    logger.warning(f"[GitAgent] GitHub Action trigger failed: {error_msg}")
        else:
            # Local mode: Git is available locally
            # Apply changes locally, commit, and push if needed
            # NO need to trigger GitHub Action (we have git access)
            logger.info(f"[GitAgent] Local mode: Applying changes locally with git...")
            files_changed = await self._apply_proposal_changes(proposal_dict)
            logger.info(f"[GitAgent] Applied changes to {len(files_changed)} files")

            # Generate commit message
            proposal_title = getattr(proposal, "title", None) or proposal_dict.get("title", proposal_id)
            proposal_description = getattr(proposal, "description", None) or proposal_dict.get("description", "")
            message = self._generate_commit_message(
                commit_type=CommitType.AGENT,
                scope="proposal",
                subject=f"Apply proposal: {proposal_title}",
                body=f"{proposal_description}\n\nProposal-ID: {proposal_id}",
                agent_name="git-agent",
            )

            # Commit locally
            commit_hash = self._commit(message, agent="git-agent")

            if commit_hash:
                # Publish git.commit event
                await self.publish_event(
                    topic=Topics.GIT_EVENTS,
                    event_type=EventTypes.GIT_COMMIT,
                    data={
                        "commit_hash": commit_hash,
                        "workspace_id": workspace_id,
                        "proposal_id": proposal_id,
                        "files_changed": files_changed,
                    },
                )
                logger.info(
                    f"[GitAgent] Committed locally: {commit_hash} for proposal {proposal_id}"
                )

    async def _handle_milestone_v2(self, data: Dict) -> None:
        """Handle milestone.complete.v1 event (new event bus format)"""
        milestone_id = data.get("milestone_id")
        milestone_name = data.get("name", "Unknown")

        logger.info(f"[GitAgent] Milestone {milestone_name} completed, creating tag...")

        message = self._generate_commit_message(
            commit_type=CommitType.CHORE,
            scope="milestone",
            subject=f"Complete milestone: {milestone_name}",
            body=f"Milestone ID: {milestone_id}",
            agent_name="milestone-agent",
        )

        commit_hash = self._commit(message, agent="git-agent")

        if commit_hash:
            # Could create Git tag here
            logger.info(
                f"[GitAgent] Milestone {milestone_name} committed: {commit_hash}"
            )

    async def _handle_milestone(self, event: Dict[str, Any]) -> Optional[str]:
        """Handle milestone completion - creates commit + tag"""
        data = event.get("data", {})
        milestone_name = data.get("name", "Milestone")

        message = self._generate_commit_message(
            commit_type=CommitType.FEAT,
            scope="milestone",
            subject=f"Complete {milestone_name}",
            body=data.get("summary", ""),
            agent_name="milestone-agent",
        )

        commit_hash = self._commit(message, agent="git-agent")

        # TODO: Create git tag
        # self._create_tag(milestone_name, commit_hash)

        return commit_hash

    async def _handle_proposal(self, event: Dict[str, Any]) -> Optional[str]:
        """Handle approved proposal - merges branch if exists"""
        data = event.get("data", {})
        proposal_id = data.get("proposal_id")

        message = self._generate_commit_message(
            commit_type=CommitType.AGENT,
            scope="proposal",
            subject=f"Apply proposal {proposal_id}",
            body=data.get("changes_summary", ""),
            agent_name=event.get("source", "unknown-agent"),
        )

        # TODO: Check if branch exists and merge
        # branch_name = f"agent/proposal-{proposal_id}"
        # if self._branch_exists(branch_name):
        #     self._merge_branch(branch_name)

        return self._commit(message, agent="git-agent")

    def _should_commit(self, changes: List[str]) -> bool:
        """
        Decide if changes are significant enough for a commit

        Rules:
        - At least 1 significant change
        - Not just whitespace
        - Not just comments (unless docs)
        """
        if not changes:
            return False

        # For MVP, commit everything
        # TODO: Add more sophisticated logic
        return len(changes) > 0

    def _infer_commit_type(self, data: Dict[str, Any]) -> CommitType:
        """Infer commit type from change data"""
        description = data.get("description", "").lower()

        if "fix" in description or "bug" in description:
            return CommitType.FIX
        elif "test" in description:
            return CommitType.TEST
        elif "refactor" in description:
            return CommitType.REFACTOR
        elif "doc" in description:
            return CommitType.DOCS
        else:
            return CommitType.FEAT

    async def _generate_commit_message_async(
        self,
        commit_type: CommitType,
        scope: str,
        subject: str,
        body: str = "",
        agent_name: str = "git-agent",
    ) -> str:
        """
        Generate semantic commit message, optionally using LLM

        Format:
        <type>(<scope>): <subject>

        <body>

        Generated-by: <agent_name>
        """
        # Try LLM first if enabled
        if self.use_llm_commits:
            changes_context = f"{subject}\n{body}" if body else subject
            llm_message = await self._generate_llm_commit_message(
                commit_type, scope, changes_context
            )
            if llm_message:
                # Add metadata footer
                return f"{llm_message}\n\nGenerated-by: {agent_name} (LLM-enhanced)"

        # Fallback to template
        return self._generate_commit_message(
            commit_type, scope, subject, body, agent_name
        )

    def _generate_commit_message(
        self,
        commit_type: CommitType,
        scope: str,
        subject: str,
        body: str = "",
        agent_name: str = "git-agent",
    ) -> str:
        """
        Generate semantic commit message following conventional commits (template)

        Format:
        <type>(<scope>): <subject>

        <body>

        Generated-by: <agent_name>
        """
        header = f"{commit_type.value}({scope}): {subject}"

        parts = [header]

        if body:
            parts.append("")  # Empty line
            parts.append(body)

        parts.append("")  # Empty line
        parts.append(f"Generated-by: {agent_name}")

        return "\n".join(parts)

    def _format_changes(self, changes: List[str]) -> str:
        """Format list of changes into commit body"""
        if not changes:
            return "No specific changes listed"

        return "Changes:\n" + "\n".join(f"- {change}" for change in changes)

    def _commit(self, message: str, agent: str = "git-agent", allow_empty: bool = False) -> Optional[str]:
        """
        Execute git commit using Git_Context_Manager.

        Git_Context_Manager already handles:
        - History logging (history.json + task_history.md)
        - Markdown updates (context.md, timeline.md)
        - Reward tracking (via _track_reward_action)

        GitAgent only adds LLM-enhanced commit messages on top.

        Args:
            message: Commit message
            agent: Agent name for tracking
            allow_empty: If True, allow commit even with no changes (for temporal markers)

        Returns:
            Commit hash or None if failed
        """
        try:
            logger.info(f"[GitAgent] Committing with message: {message[:50]}... (allow_empty={allow_empty})")
            # Git_Context_Manager handles everything: commit + history + markdown + rewards
            result = self.git_manager.commit_changes(message=message, agent=agent, allow_empty=allow_empty)
            logger.info(f"[GitAgent] Commit successful: {result}")
            return result
        except Exception as e:
            logger.error(f"[GitAgent] Commit failed: {str(e)}")
            return None
    
    async def force_temporal_commit(self, reason: str = "temporal_marker") -> Optional[str]:
        """
        Force a commit to mark the current date/time.
        
        This is useful for:
        - Marking start/end of day
        - Creating temporal reference points
        - Updating daily checklists
        - Situating agents in time
        
        Args:
            reason: Reason for the temporal commit (e.g., "daily_marker", "checkpoint", "session_start")
            
        Returns:
            Commit hash or None if failed
        """
        if self.is_cloud_run:
            logger.info("[GitAgent] Cloud Run mode - temporal commits are handled via GitHub API")
            return None
        
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S UTC')
        
        message = f"chore(temporal): {reason} - {date_str} {time_str}\n\nTemporal marker to situate agents in time.\nReason: {reason}\nTimestamp: {now.isoformat()}"
        
        logger.info(f"[GitAgent] Forcing temporal commit: {reason} at {date_str} {time_str}")
        return self._commit(message=message, agent="git-agent", allow_empty=True)

    # ===== LLM-Enhanced Commit Messages (GitAgent-specific feature) =====

    async def _generate_llm_commit_message(
        self, commit_type: CommitType, scope: str, changes_context: str
    ) -> Optional[str]:
        """
        Generate commit message using Gemini LLM

        Falls back to template if LLM fails
        """
        if not self.use_llm_commits or not self.gemini_api_key:
            return None

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""Generate a concise git commit message following Conventional Commits format.

Type: {commit_type.value}
Scope: {scope}
Context: {changes_context}

Requirements:
- Format: <type>(<scope>): <subject>
- Subject: imperative mood, lowercase, no period
- Max 50 chars for subject
- Be specific and actionable

Generate ONLY the commit message, nothing else."""

            response = model.generate_content(prompt)
            message = response.text.strip()

            # Validate format
            if ":" in message and len(message.split("\n")[0]) <= 72:
                logger.info(
                    f"[GitAgent] Generated LLM commit message: {message[:50]}..."
                )
                return message

        except Exception as e:
            logger.warning(f"[GitAgent] LLM commit generation failed: {e}")

        return None

    # ===== Proposal Application Methods =====

    def _load_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Load proposal from Firestore (with local fallback)"""

        # Try Firestore first (if enabled)
        if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
            try:
                repo = get_proposal_repository(project_id=self.project_id)
                proposal = repo.get(proposal_id)
                if proposal:
                    logger.info(
                        f"[GitAgent] Loaded proposal from Firestore: {proposal_id}"
                    )
                    return proposal
                else:
                    logger.warning(
                        f"[GitAgent] Proposal not found in Firestore: {proposal_id}"
                    )
            except Exception as e:
                logger.error(f"[GitAgent] Firestore error, falling back to local: {e}")

        # Fallback to local file storage
        proposals_dir = Path(self.workspace_path) / "proposals"
        proposal_file = proposals_dir / f"{proposal_id}.json"

        if not proposal_file.exists():
            logger.warning(f"[GitAgent] Proposal file not found: {proposal_file}")
            return None

        try:
            with open(proposal_file, "r") as f:
                proposal = json.load(f)
            logger.debug(f"[GitAgent] Loaded proposal from local file: {proposal_id}")
            return proposal
        except Exception as e:
            logger.error(f"[GitAgent] Failed to load proposal: {e}")
            return None

    async def _apply_proposal_changes(self, proposal: Dict) -> List[str]:
        """
        Apply changes from proposal to workspace files.

        Args:
            proposal: Proposal dict with proposed_changes

        Returns:
            List of files changed
        """
        files_changed = []
        proposed_changes = proposal.get("proposed_changes", [])

        for change in proposed_changes:
            file_path = change.get("file_path")
            change_type = change.get("change_type")

            if not file_path:
                continue

            full_path = Path(self.workspace_path) / file_path

            try:
                if change_type == "create" or change_type == "update":
                    # Get the new content
                    new_content = change.get("after")

                    if new_content:
                        # Ensure directory exists
                        full_path.parent.mkdir(parents=True, exist_ok=True)

                        # Write new content
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(new_content)

                        logger.info(f"[GitAgent] {change_type.title()}d: {file_path}")
                        files_changed.append(file_path)
                    else:
                        logger.warning(f"[GitAgent] No 'after' content for {file_path}")

                elif change_type == "delete":
                    if full_path.exists():
                        full_path.unlink()
                        logger.info(f"[GitAgent] Deleted: {file_path}")
                        files_changed.append(file_path)

            except Exception as e:
                logger.error(f"[GitAgent] Failed to apply change to {file_path}: {e}")

        return files_changed

    async def _trigger_github_action(self, proposal: Any) -> Optional[Dict[str, Any]]:
        """
        Trigger GitHub Action via repository_dispatch webhook.
        
        This method is called by Git Agent when a proposal is approved.
        Works in both local and Cloud Run modes.

        Args:
            proposal: ChangeProposal object or dict-like object with proposal data

        Returns:
            dict with status and message, or None if not configured
        """
        github_token = os.getenv("GITHUB_TOKEN") or os.getenv("PERSONAL_GITHUB_TOKEN")
        if github_token:
            github_token = github_token.strip()
        if not github_token:
            logger.warning(
                "[GitAgent] GITHUB_TOKEN or PERSONAL_GITHUB_TOKEN not configured - skipping GitHub Action trigger"
            )
            return {
                "status": "error",
                "message": "GITHUB_TOKEN or PERSONAL_GITHUB_TOKEN must be configured to trigger GitHub Actions",
                "reason": "configuration_missing"
            }

        github_repo = os.getenv("GITHUB_REPO") or os.getenv("GITHUB_REPOSITORY")
        if github_repo:
            github_repo = github_repo.strip()
        if not github_repo:
            logger.warning(
                "[GitAgent] GITHUB_REPO not configured - skipping GitHub Action trigger"
            )
            return {
                "status": "error",
                "message": "GITHUB_REPO (owner/repo) must be set to trigger GitHub Actions",
                "reason": "configuration_missing"
            }

        # Extract proposal data (works with both ChangeProposal model and dict)
        proposal_id = getattr(proposal, "id", None) or proposal.get("id") if isinstance(proposal, dict) else None
        proposal_workspace_id = getattr(proposal, "workspace_id", None) or proposal.get("workspace_id") if isinstance(proposal, dict) else self.workspace_id
        proposal_agent_id = getattr(proposal, "agent_id", None) or proposal.get("agent_id") if isinstance(proposal, dict) else None
        proposal_title = getattr(proposal, "title", None) or proposal.get("title", proposal_id) if isinstance(proposal, dict) else proposal_id

        url = f"https://api.github.com/repos/{github_repo}/dispatches"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {
            "event_type": "proposal-approved",
            "client_payload": {
                "proposal_id": proposal_id,
                "workspace_id": proposal_workspace_id or self.workspace_id,
                "agent_id": proposal_agent_id,
                "title": proposal_title,
            },
        }

        logger.info(
            f"[GitAgent] 🚀 Triggering GitHub Action for proposal={proposal_id} (workspace={proposal_workspace_id}, repo={github_repo})"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json=payload, headers=headers, timeout=10.0
                )

                if response.status_code == 204:
                    logger.info(
                        f"[GitAgent] ✅ GitHub Action triggered successfully for proposal: {proposal_id}"
                    )
                    return {
                        "status": "success",
                        "message": f"GitHub Action triggered for proposal {proposal_id}",
                        "repo": github_repo,
                    }
                else:
                    error_text = response.text
                    logger.error(
                        f"[GitAgent] ❌ GitHub Action trigger failed: {response.status_code} - {error_text}"
                    )
                    return {
                        "status": "error",
                        "status_code": response.status_code,
                        "message": f"Failed to trigger GitHub Action: {error_text}",
                        "repo": github_repo,
                    }
        except (httpx.TimeoutException, httpx.ReadTimeout) as e:
            logger.error(f"[GitAgent] ❌ GitHub Action trigger timeout: {e}")
            return {
                "status": "error",
                "message": f"Timeout while triggering GitHub Action: {str(e)}",
                "repo": github_repo,
            }
        except Exception as e:
            logger.error(f"[GitAgent] ❌ Error triggering GitHub Action: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error triggering GitHub Action: {str(e)}",
                "repo": github_repo
            }

    # ===== Future features (branches, tags, rollback) =====

    def _create_branch(self, branch_name: str) -> bool:
        """Create a new git branch"""
        # TODO: Implement
        pass

    def _merge_branch(self, branch_name: str) -> bool:
        """Merge branch into current branch"""
        # TODO: Implement
        pass

    def _create_tag(self, tag_name: str, commit_hash: str) -> bool:
        """Create git tag at specific commit"""
        # TODO: Implement
        pass

    def _rollback(self, commit_hash: str) -> bool:
        """Rollback to specific commit"""
        # TODO: Implement
        pass


# ===== Helper function for easy usage =====


async def commit_via_agent(
    workspace_id: str, event_type: str, data: Dict[str, Any], source: str = "manual"
) -> Optional[str]:
    """
    Convenience function to trigger Git Agent from anywhere

    Usage:
        await commit_via_agent(
            workspace_id="contextpilot",
            event_type="spec.created",
            data={"file_name": "API.md", "description": "Added API docs"},
            source="spec-agent"
        )
    """
    agent = GitAgent(workspace_id=workspace_id)

    # Use new event handler interface
    await agent.handle_event(event_type, data)

    # Return commit hash from last operation
    # For now, check if repo has new commits
    if agent.git_manager.repo.head.is_valid():
        return agent.git_manager.repo.head.commit.hexsha
    return None

    def get_git_context_for_proposal(self, proposal_type: str = "general") -> Dict:
        """
        Get rich git context for proposal generation.

        Args:
            proposal_type: Type of proposal to tailor git context

        Returns:
            Dictionary with git context information
        """
        try:
            import subprocess

            # Get recent commits with more detail
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "-20",
                    "--format=%h|%s|%an|%ad",
                    "--date=short",
                ],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            recent_commits = []
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split("|", 3)
                        if len(parts) >= 4:
                            recent_commits.append(
                                {
                                    "hash": parts[0],
                                    "message": parts[1],
                                    "author": parts[2],
                                    "date": parts[3],
                                }
                            )

            # Get branch information
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            current_branch = (
                branch_result.stdout.strip()
                if branch_result.returncode == 0
                else "unknown"
            )

            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            modified_files = []
            if status_result.returncode == 0:
                modified_files = [
                    line[3:]
                    for line in status_result.stdout.strip().split("\n")
                    if line
                ]

            # Get commit stats
            stats_result = subprocess.run(
                ["git", "log", "--oneline", "--since=1.week.ago"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            weekly_commits = (
                len(stats_result.stdout.strip().split("\n"))
                if stats_result.returncode == 0
                else 0
            )

            return {
                "recent_commits": recent_commits[:10],  # Last 10 commits
                "current_branch": current_branch,
                "modified_files": modified_files,
                "weekly_commit_count": weekly_commits,
                "total_commits": len(recent_commits),
                "context_for": proposal_type,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.warning(f"[Git Agent] Could not get git context: {e}")
            return {
                "recent_commits": [],
                "current_branch": "unknown",
                "modified_files": [],
                "weekly_commit_count": 0,
                "total_commits": 0,
                "context_for": proposal_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
