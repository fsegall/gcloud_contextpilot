"""
Spec Agent - Documentation Curator

Manages markdown artifacts, validates consistency, generates docs from code.
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path
import yaml
import json

from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics
from app.agents.diff_generator import generate_unified_diff, read_file_safe
from app.services.llm_service import get_llm_service
from app.repositories.proposal_repository import get_proposal_repository

logger = logging.getLogger(__name__)


class SpecAgent(BaseAgent):
    """
    Spec Agent manages documentation artifacts as versioned code.

    Responsibilities:
    - Generate/update markdown docs
    - Validate docs vs code consistency
    - Manage templates
    - Create Change Proposals for doc updates
    """

    def __init__(
        self,
        workspace_path: str,
        workspace_id: str = "default",
        project_id: Optional[str] = None,
    ):
        """
        Initialize Spec Agent.

        Args:
            workspace_path: Path to workspace directory
            workspace_id: Workspace identifier
            project_id: GCP project ID for Pub/Sub
        """
        # Initialize base agent
        super().__init__(
            workspace_id=workspace_id, agent_id="spec", project_id=project_id
        )

        # Spec-specific paths (ensure Path objects)
        self.workspace_path = Path(self.workspace_path)  # Convert to Path if string
        self.docs_path = self.workspace_path / "docs"
        self.templates_path = Path(__file__).parent.parent / "templates"

        # Initialize LLM service
        try:
            self.llm = get_llm_service()
            logger.info(f"[Spec Agent] LLM service initialized")
        except Exception as e:
            logger.warning(f"[Spec Agent] LLM service not available: {e}")
            self.llm = None

        # Subscribe to events
        self.subscribe_to_event(EventTypes.GIT_COMMIT)
        self.subscribe_to_event(EventTypes.CONTEXT_DELTA)

        logger.info(f"Spec Agent initialized for workspace: {workspace_path}")

    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events.

        Args:
            event_type: Type of event
            data: Event data payload
        """
        logger.info(f"[Spec Agent] Received event: {event_type}")

        try:
            if event_type == EventTypes.GIT_COMMIT:
                await self._handle_git_commit(data)
            elif event_type == EventTypes.CONTEXT_DELTA:
                await self._handle_context_delta(data)

            # Update metrics
            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(f"[Spec Agent] Error handling {event_type}: {e}")
            self.increment_metric("errors")

    async def _handle_git_commit(self, data: Dict) -> None:
        """Handle git.commit.v1 event"""
        commit_hash = data.get("commit_hash")
        workspace_id = data.get("workspace_id")

        logger.info(f"[Spec Agent] Processing commit {commit_hash}")

        # Analyze documentation consistency
        issues = self.validate_documentation()

        if issues:
            logger.warning(f"[Spec Agent] Found {len(issues)} documentation issues")
            # Create proposals for issues
            for issue in issues:
                await self._create_proposal_for_issue(issue)

    async def _handle_context_delta(self, data: Dict) -> None:
        """Handle context.delta.v1 event"""
        delta_type = data.get("type")
        scope = data.get("scope", [])

        logger.info(f"[Spec Agent] Context delta: {delta_type} in {scope}")
        # Could trigger specific doc updates based on scope

    async def handle_context_update(self, event: Dict):
        """
        Handle context.update.v1 event.

        When code changes, check if docs need updating.
        """
        logger.info(f"Spec Agent received context update: {event['event_id']}")

        data = event["data"]
        files_changed = data.get("files_changed", [])

        # Check if API routes changed
        if any("routes" in f or "api" in f for f in files_changed):
            logger.info("API changes detected, checking if API.md needs update")
            await self._check_api_docs(event)

        # Check if architecture changed
        if any("services" in f or "agents" in f for f in files_changed):
            logger.info("Architecture changes detected")
            await self._check_architecture_docs(event)

    async def _check_api_docs(self, event: Dict):
        """Check if API.md needs updating based on code changes."""

        # TODO: Parse FastAPI routes from code
        # TODO: Compare with current API.md
        # TODO: Generate diff
        # TODO: Create Change Proposal

        logger.info("API doc validation not yet implemented")

    async def _check_architecture_docs(self, event: Dict):
        """Check if ARCHITECTURE.md needs updating."""

        logger.info("Architecture doc validation not yet implemented")

    async def generate_daily_checklist(self, user_id: str) -> str:
        """
        Generate daily checklist from template.

        Args:
            user_id: User to generate checklist for

        Returns:
            Path to generated checklist
        """
        logger.info(f"Generating daily checklist for user: {user_id}")

        # Load template
        template_path = self.templates_path / "daily_checklist.md"

        with open(template_path, "r") as f:
            template = f.read()

        # Get today's date
        today = datetime.now(timezone.utc)
        day_of_week = today.strftime("%A")
        date = today.strftime("%Y-%m-%d")

        # Simple substitution (in production, use proper templating)
        content = template.replace("{{day_of_week}}", day_of_week)
        content = content.replace("{{date}}", date)
        content = content.replace("{{generation_time}}", today.isoformat())

        # TODO: Fetch coach nudges and populate
        content = content.replace("{{#if coach_nudges}}", "")
        content = content.replace("{{else}}", "")
        content = content.replace("{{/if}}", "")
        content = content.replace("{{#each coach_nudges}}", "")
        content = content.replace("{{/each}}", "")

        # Save to workspace
        output_path = self.workspace_path / f"daily_checklist_{date}.md"

        with open(output_path, "w") as f:
            f.write(content)

        logger.info(f"✅ Daily checklist generated: {output_path}")

        # Emit event
        if self.event_bus:
            await self.event_bus.publish(
                topic=Topics.SPEC_EVENTS,
                event_type=EventTypes.SPEC_UPDATE,
                source="spec-agent",
                data={
                    "file": str(output_path),
                    "action": "created",
                    "type": "daily_checklist",
                },
            )

        return str(output_path)

    async def validate_docs(self) -> List[Dict]:
        """
        Validate all documentation for consistency.

        Returns:
            List of validation issues
        """
        logger.info("Validating documentation consistency")

        issues = []

        # Check if standard docs exist
        required_docs = ["README.md", "ARCHITECTURE.md"]

        for doc in required_docs:
            doc_path = self.workspace_path / doc
            if not doc_path.exists():
                issues.append(
                    {
                        "type": "missing_doc",
                        "file": doc,
                        "severity": "high",
                        "message": f"{doc} not found",
                    }
                )

        # TODO: Check API endpoints vs API.md
        # TODO: Check architecture diagram vs actual structure
        # TODO: Check for stale docs (>7 days since related code changed)

        if issues:
            logger.warning(f"Found {len(issues)} documentation issues")

            # Emit validation event
            if self.event_bus:
                await self.event_bus.publish(
                    topic=Topics.SPEC_EVENTS,
                    event_type=EventTypes.SPEC_VALIDATION,
                    source="spec-agent",
                    data={
                        "issues": issues,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
        else:
            logger.info("✅ All docs valid")

        return issues

    async def _create_proposal_for_issue(self, issue: Dict) -> Optional[str]:
        """
        Create a change proposal with actual diff for a documentation issue.

        Args:
            issue: Issue dictionary from validate_documentation()

        Returns:
            Proposal ID if created, None otherwise
        """
        proposal_id = f"spec-{issue['type']}-{int(datetime.now().timestamp())}"

        # 1. Read current content
        file_path = issue["file"]
        current_content = read_file_safe(file_path, str(self.workspace_path))

        # 2. Generate proposed content
        if issue["type"] == "missing_doc":
            if self.llm:
                # Use Gemini to generate intelligent content
                proposed_content = await self._generate_doc_with_ai(file_path, issue)
            else:
                # Fallback to template
                proposed_content = self._generate_doc_template(file_path)
        else:
            # For other types, update with AI if available
            if self.llm:
                proposed_content = await self._update_doc_with_ai(
                    file_path, current_content, issue
                )
            else:
                proposed_content = (
                    current_content
                    + f"\n\n<!-- Updated by Spec Agent: {issue['message']} -->\n"
                )

        # 3. Generate diff
        diff_content = generate_unified_diff(
            file_path=file_path,
            old_content=current_content,
            new_content=proposed_content,
        )

        # 4. Create proposal with diff
        proposal = {
            "id": proposal_id,
            "agent_id": "spec",
            "workspace_id": self.workspace_id,
            "title": f"Docs issue: {issue['file']}",
            "description": issue["message"],
            "diff": {"format": "unified", "content": diff_content},
            "proposed_changes": [
                {
                    "file_path": file_path,
                    "change_type": "update" if current_content else "create",
                    "description": issue["message"],
                    "before": current_content,
                    "after": proposed_content,
                    "diff": diff_content,
                }
            ],
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # 5. Save proposal to workspace
        await self._save_proposal(proposal)

        # 6. Publish proposal.created event
        await self.publish_event(
            topic=Topics.PROPOSAL_EVENTS,
            event_type=EventTypes.PROPOSAL_CREATED,
            data={
                "proposal_id": proposal_id,
                "workspace_id": self.workspace_id,
                "issue_type": issue["type"],
                "file": issue["file"],
            },
        )

        logger.info(
            f"[Spec Agent] Created proposal {proposal_id} with diff for {issue['file']}"
        )

        # 7. Remember this proposal
        proposals = self.recall("proposals_created", [])
        proposals.append(proposal_id)
        self.remember("proposals_created", proposals)

        return proposal_id

    async def _generate_doc_with_ai(self, file_path: str, issue: Dict) -> str:
        """Generate documentation content using Gemini"""
        filename = Path(file_path).stem

        # Build context from artifacts
        context_data = self.apply_artifact_rules({})
        artifact_context = ""
        if context_data.get("artifact_rules"):
            artifact_context = "\n\nProject Context:\n"
            for rule in context_data["artifact_rules"]:
                artifact_context += (
                    f"\n{rule['artifact']}:\n{rule['content'][:500]}...\n"
                )

        prompt = f"""You are a technical documentation expert. Generate professional markdown documentation for: {file_path}

File name: {filename}
Issue: {issue['message']}
{artifact_context}

Create a comprehensive, well-structured markdown document with:
1. Clear title and overview
2. Purpose/objectives section
3. Detailed usage instructions
4. Code examples (if applicable)
5. Best practices
6. References

The documentation should be:
- Professional and concise
- Easy to understand
- Following markdown best practices
- Specific to {filename}

Output ONLY the markdown content, no explanations or meta-commentary."""

        try:
            content = await self.llm.generate(prompt, temperature=0.7, max_tokens=2048)
            logger.info(
                f"[Spec Agent] Generated {len(content)} chars of documentation with AI"
            )
            return content
        except Exception as e:
            logger.error(f"[Spec Agent] AI generation failed: {e}, using template")
            return self._generate_doc_template(file_path)

    async def _update_doc_with_ai(
        self, file_path: str, current_content: str, issue: Dict
    ) -> str:
        """Update existing documentation using Gemini"""

        prompt = f"""You are a technical documentation expert. Update this documentation:

File: {file_path}
Issue: {issue['message']}

Current content:
{current_content}

Task: Fix the issue while preserving the document structure and style.
Output ONLY the updated markdown content."""

        try:
            content = await self.llm.generate(prompt, temperature=0.5, max_tokens=2048)
            logger.info(f"[Spec Agent] Updated documentation with AI")
            return content
        except Exception as e:
            logger.error(f"[Spec Agent] AI update failed: {e}, using fallback")
            return (
                current_content
                + f"\n\n<!-- Updated by Spec Agent: {issue['message']} -->\n"
            )

    def _generate_doc_template(self, file_path: str) -> str:
        """Generate basic documentation template (fallback when AI not available)"""
        filename = Path(file_path).stem
        return f"""# {filename.replace('_', ' ').replace('-', ' ').title()}

## Overview

This document describes {filename}.

## Purpose

<!-- Add purpose here -->

## Usage

<!-- Add usage instructions here -->

## Examples

<!-- Add examples here -->

## References

<!-- Add references here -->
"""

    async def _save_proposal(self, proposal: Dict) -> None:
        """Save proposal to Firestore (and optionally local backup)"""

        # Save to Firestore if enabled
        if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
            try:
                repo = get_proposal_repository(project_id=self.project_id)
                repo.create(proposal)
                logger.info(
                    f"[Spec Agent] Saved proposal to Firestore: {proposal['id']}"
                )
            except Exception as e:
                logger.error(f"[Spec Agent] Failed to save to Firestore: {e}")
                # Fall through to local save as backup

        # Also save locally (for backup and local development)
        proposals_dir = Path(self.workspace_path) / "proposals"
        proposals_dir.mkdir(exist_ok=True)

        # Save as JSON
        json_path = proposals_dir / f"{proposal['id']}.json"
        with open(json_path, "w") as f:
            json.dump(proposal, f, indent=2)

        # Save as Markdown
        md_path = proposals_dir / f"{proposal['id']}.md"
        md_content = f"""# {proposal['title']}

**ID:** {proposal['id']}  
**Agent:** {proposal['agent_id']}  
**Status:** {proposal['status']}  
**Created:** {proposal['created_at']}

## Description

{proposal['description']}

## Proposed Changes

"""
        for change in proposal["proposed_changes"]:
            md_content += f"""
### {change['file_path']} ({change['change_type']})

{change['description']}

```diff
{change.get('diff', 'No diff available')}
```
"""

        with open(md_path, "w") as f:
            f.write(md_content)

        logger.debug(f"[Spec Agent] Saved proposal to {json_path} and {md_path}")

    async def create_template(
        self, name: str, sections: List[str], frequency: Optional[str] = None
    ) -> str:
        """
        Create a new custom template.

        Args:
            name: Template name (e.g., "retrospective.md")
            sections: List of section names
            frequency: Optional frequency (daily, weekly, sprint)

        Returns:
            Path to created template
        """
        logger.info(f"Creating custom template: {name}")

        # Generate template structure
        frontmatter = {
            "managed_by": "spec-agent",
            "template": name.replace(".md", ""),
            "version": "1.0.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "auto_update": False,
            "frequency": frequency,
        }

        content = "---\n"
        content += yaml.dump(frontmatter)
        content += "---\n\n"
        content += f"# {name.replace('.md', '').replace('_', ' ').title()}\n\n"

        for section in sections:
            content += f"## {section}\n\n"
            content += "<!-- Add content here -->\n\n"

        content += "---\n\n"
        content += f"*Generated by Spec Agent on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n"

        # Save template
        template_path = self.docs_path / "templates" / name
        template_path.parent.mkdir(parents=True, exist_ok=True)

        with open(template_path, "w") as f:
            f.write(content)

        logger.info(f"✅ Template created: {template_path}")

        # Emit event
        if self.event_bus:
            await self.event_bus.publish(
                topic=Topics.SPEC_EVENTS,
                event_type=EventTypes.SPEC_UPDATE,
                source="spec-agent",
                data={
                    "template_name": name,
                    "path": str(template_path),
                    "sections": sections,
                },
            )

        return str(template_path)

    def generate_context_summary(self, proposal_type: str = "general") -> str:
        """
        Generate intelligent context summary for new chat sessions.

        Args:
            proposal_type: Type of proposal to tailor context

        Returns:
            Condensed context summary
        """
        try:
            # 1. Analyze key .md files
            key_files = self._get_crucial_md_files()

            # 2. Get git log for recent context
            git_context = self._get_git_context()

            # 3. Generate project status
            project_status = self._get_project_status()

            # 4. Create condensed summary
            context_prompt = self._build_context_prompt(
                key_files, git_context, project_status, proposal_type
            )

            logger.info(f"[SpecAgent] Generated context summary for {proposal_type}")
            return context_prompt

        except Exception as e:
            logger.error(f"[SpecAgent] Error generating context: {e}")
            return self._get_basic_context()

    def _get_crucial_md_files(self) -> Dict[str, str]:
        """Get content from crucial .md files."""
        crucial_files = {
            "README.md": "Project overview and setup",
            "PROJECT.md": "Project details and overview",
            "GOAL.md": "Project goals and objectives",
            "STATUS.md": "Current project status",
            "MILESTONES.md": "Project milestones and progress",
            "ARCHITECTURE.md": "System architecture",
            "project_scope.md": "Project goals and scope",
            "project_checklist.md": "Development checklist",
            "daily_checklist.md": "Daily progress tracking",
        }

        content = {}
        for filename, description in crucial_files.items():
            # Look in project root (where README.md actually is)
            # workspace_path is like: /path/to/project/back-end/.contextpilot/workspaces/contextpilot
            # project_root should be: /path/to/project
            project_root = (
                self.workspace_path.parent.parent.parent
            )  # Go up to project root
            file_path = project_root / filename

            if file_path.exists():
                try:
                    content[filename] = {
                        "description": description,
                        "content": file_path.read_text(encoding="utf-8")[
                            :2000
                        ],  # Limit size
                    }
                    logger.debug(f"[SpecAgent] Found {filename} at {file_path}")
                except Exception as e:
                    logger.warning(f"[SpecAgent] Could not read {filename}: {e}")
                    content[filename] = {
                        "description": description,
                        "content": "File exists but could not be read",
                    }
            else:
                logger.debug(f"[SpecAgent] {filename} not found at {file_path}")
                content[filename] = {
                    "description": description,
                    "content": "File not found",
                }

        return content

    def _get_git_context(self) -> Dict:
        """Get rich git context using Git Agent."""
        try:
            from app.agents.git_agent import GitAgent

            # Initialize Git Agent for context
            git_agent = GitAgent(
                workspace_path=str(self.workspace_path),
                workspace_id=self.workspace_id,
                project_id=self.project_id,
            )

            # Get rich git context
            git_context = git_agent.get_git_context_for_proposal("spec")

            # Format for template compatibility
            formatted_commits = []
            for commit in git_context.get("recent_commits", []):
                formatted_commits.append(
                    f"{commit.get('hash', '')} {commit.get('message', '')}"
                )

            return {
                "recent_commits": formatted_commits[:5],  # Last 5 for template
                "total_commits": git_context.get("total_commits", 0),
                "current_branch": git_context.get("current_branch", "unknown"),
                "modified_files": git_context.get("modified_files", []),
                "weekly_commits": git_context.get("weekly_commit_count", 0),
                "rich_context": git_context,  # Full context for advanced use
            }

        except Exception as e:
            logger.warning(f"[SpecAgent] Could not get git context via Git Agent: {e}")
            # Fallback to basic git log
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "log", "--oneline", "-10", "--format=%h %s"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    return {
                        "recent_commits": result.stdout.strip().split("\n")[:5],
                        "total_commits": len(result.stdout.strip().split("\n")),
                        "current_branch": "unknown",
                        "modified_files": [],
                        "weekly_commits": 0,
                    }
                else:
                    return {"recent_commits": [], "total_commits": 0}

            except Exception as e2:
                logger.warning(f"[SpecAgent] Fallback git context also failed: {e2}")
                return {"recent_commits": [], "total_commits": 0}

    def _get_project_status(self) -> Dict:
        """Get current project status."""
        return {
            "phase": "Hackathon + Product Launch",
            "goal": "AI-powered context management with multi-agent system",
            "stack": "Cloud Run + Firestore + Pub/Sub + Gemini + VSCode Extension",
            "status": "Core functionality complete, fine-tuning phase",
            "workspace_id": self.workspace_id,
        }

    def _build_context_prompt(
        self,
        key_files: Dict,
        git_context: Dict,
        project_status: Dict,
        proposal_type: str,
    ) -> str:
        """Build the final context prompt using template."""
        try:
            # Try to use template first
            template_path = self.templates_path / "quick_reference.md"
            if template_path.exists():
                template_content = template_path.read_text(encoding="utf-8")
                return self._render_template(
                    template_content,
                    key_files,
                    git_context,
                    project_status,
                    proposal_type,
                )
        except Exception as e:
            logger.warning(
                f"[SpecAgent] Could not use template, falling back to basic: {e}"
            )

        # Fallback to basic context
        return self._build_basic_context_prompt(
            key_files, git_context, project_status, proposal_type
        )

    def _render_template(
        self,
        template_content: str,
        key_files: Dict,
        git_context: Dict,
        project_status: Dict,
        proposal_type: str,
    ) -> str:
        """Render template with context data."""
        # Simple template rendering (could use Jinja2 in future)
        context = template_content

        # Replace template variables
        context = context.replace("{{ phase }}", project_status["phase"])
        context = context.replace("{{ goal }}", project_status["goal"])
        context = context.replace("{{ stack }}", project_status["stack"])
        context = context.replace("{{ status }}", project_status["status"])
        context = context.replace("{{ workspace_id }}", project_status["workspace_id"])
        context = context.replace("{{ proposal_type }}", proposal_type)
        context = context.replace("{{ agent }}", "Spec Agent")
        context = context.replace(
            "{{ timestamp }}", datetime.now(timezone.utc).isoformat()
        )
        context = context.replace(
            "{{ total_commits }}", str(git_context.get("total_commits", 0))
        )

        # Replace commits
        commits_text = ""
        for commit in git_context.get("recent_commits", []):
            commits_text += f"- {commit}\n"
        context = context.replace(
            "{% for commit in recent_commits %}\n- {{ commit }}\n{% endfor %}",
            commits_text.strip(),
        )

        # Replace file contents
        context = context.replace(
            "{{ readme_content }}", key_files.get("README.md", {}).get("content", "")
        )
        context = context.replace(
            "{{ scope_content }}",
            key_files.get("project_scope.md", {}).get("content", ""),
        )
        context = context.replace(
            "{{ architecture_content }}",
            key_files.get("ARCHITECTURE.md", {}).get("content", ""),
        )
        context = context.replace(
            "{{ checklist_content }}",
            key_files.get("project_checklist.md", {}).get("content", ""),
        )
        context = context.replace(
            "{{ daily_checklist_content }}",
            key_files.get("daily_checklist.md", {}).get("content", ""),
        )

        # Handle conditional content - Replace template variables with actual content
        # This is a simple string replacement approach since we're not using a real template engine
        for filename in [
            "README.md",
            "project_scope.md",
            "ARCHITECTURE.md",
            "project_checklist.md",
            "daily_checklist.md",
        ]:
            content = key_files.get(filename, {}).get("content", "")
            var_name = filename.lower().replace(".md", "")

            # Replace the variable placeholder with actual content or "File not found"
            if content and content != "File not found":
                # Truncate content to 500 chars
                truncated = content[:500] + ("..." if len(content) > 500 else "")
                context = context.replace(f"{{{{ {var_name}_content }}}}", truncated)
            else:
                context = context.replace(
                    f"{{{{ {var_name}_content }}}}", "*File not found*"
                )

        return context

    def _build_basic_context_prompt(
        self,
        key_files: Dict,
        git_context: Dict,
        project_status: Dict,
        proposal_type: str,
    ) -> str:
        """Build basic context prompt without template."""
        context = f"""# ContextPilot - Quick Reference

## Project Status
- **Phase**: {project_status['phase']}
- **Goal**: {project_status['goal']}
- **Stack**: {project_status['stack']}
- **Status**: {project_status['status']}
- **Workspace**: {project_status['workspace_id']}

## Recent Development Context
**Last 5 Commits:**
"""

        for commit in git_context.get("recent_commits", []):
            context += f"- {commit}\n"

        context += f"\n**Total Commits**: {git_context.get('total_commits', 0)}\n\n"

        context += "## Key Project Artifacts\n"
        for filename, data in key_files.items():
            context += f"### {filename}\n"
            context += f"*{data['description']}*\n\n"
            if data["content"] != "File not found":
                # Truncate and add ellipsis if too long
                content = (
                    data["content"][:500] + "..."
                    if len(data["content"]) > 500
                    else data["content"]
                )
                context += f"```\n{content}\n```\n\n"
            else:
                context += "*File not found*\n\n"

        context += f"""## Current Context
- **Proposal Type**: {proposal_type}
- **Agent**: Spec Agent
- **Timestamp**: {datetime.now(timezone.utc).isoformat()}

## Instructions
Use this context to understand the project state and make informed decisions about proposals.
Focus on consistency with existing architecture and project goals.
"""

        return context

    def _get_basic_context(self) -> str:
        """Fallback basic context if generation fails."""
        return f"""# ContextPilot Project

**Phase**: Hackathon + Product Launch
**Goal**: AI-powered context management with multi-agent system  
**Stack**: Cloud Run + Firestore + Pub/Sub + Gemini + VSCode Extension
**Status**: Core functionality complete
**Workspace**: {self.workspace_id}

*Note: Detailed context generation failed, using basic context.*
"""


# Event handlers (will be called by Cloud Run endpoint)


async def handle_context_update(event: Dict):
    """Handle context.update.v1 events."""
    logger.info(f"Received context update: {event['event_id']}")


async def handle_git_commit(event: Dict):
    """Handle git.commit.v1 events."""
    logger.info(f"Received git commit: {event['event_id']}")
    # TODO: Update CHANGELOG.md
    # TODO: Check if docs need updating
