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
from datetime import datetime
from app.git_context_manager import Git_Context_Manager
from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics
from app.agents.diff_generator import apply_patch, read_file_safe
from app.repositories.proposal_repository import get_proposal_repository
from enum import Enum
from pathlib import Path
import json

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

        logger.info(f"[GitAgent] Initialized for workspace: {workspace_id}")

    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events (BaseAgent interface).

        Args:
            event_type: Type of event
            data: Event data payload
        """
        logger.info(f"[GitAgent] Received event: {event_type}")

        try:
            if event_type == EventTypes.PROPOSAL_APPROVED:
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
        workspace_id = data.get("workspace_id")

        logger.info(f"[GitAgent] Proposal {proposal_id} approved, applying changes...")

        # 1. Load proposal to get diff/changes
        proposal = self._load_proposal(proposal_id)
        if not proposal:
            logger.error(f"[GitAgent] Proposal {proposal_id} not found")
            return

        # 2. Apply changes from proposal
        files_changed = await self._apply_proposal_changes(proposal)
        logger.info(f"[GitAgent] Applied changes to {len(files_changed)} files")

        # 3. Generate commit message
        message = self._generate_commit_message(
            commit_type=CommitType.AGENT,
            scope="proposal",
            subject=f"Apply proposal: {proposal.get('title', proposal_id)}",
            body=f"{proposal.get('description', '')}\n\nProposal-ID: {proposal_id}",
            agent_name="git-agent",
        )

        # 4. Commit
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
                f"[GitAgent] Committed {commit_hash} for proposal {proposal_id}"
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

    def _generate_commit_message(
        self,
        commit_type: CommitType,
        scope: str,
        subject: str,
        body: str = "",
        agent_name: str = "git-agent",
    ) -> str:
        """
        Generate semantic commit message following conventional commits

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

    def _commit(self, message: str, agent: str = "git-agent") -> Optional[str]:
        """
        Execute git commit using Git_Context_Manager

        Args:
            message: Commit message
            agent: Agent name for tracking

        Returns:
            Commit hash or None if failed
        """
        try:
            logger.info(f"[GitAgent] Committing with message: {message[:50]}...")
            result = self.git_manager.commit_changes(message=message, agent=agent)
            logger.info(f"[GitAgent] Commit successful: {result}")
            return result
        except Exception as e:
            logger.error(f"[GitAgent] Commit failed: {str(e)}")
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
