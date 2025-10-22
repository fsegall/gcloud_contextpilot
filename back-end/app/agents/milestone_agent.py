"""
Milestone Agent - Project Progress and Deliverables Tracking

Tracks project progress, manages deliverables, and monitors completion criteria.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from pathlib import Path
import json

from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes

logger = logging.getLogger(__name__)


class MilestoneAgent(BaseAgent):
    """
    Milestone Agent tracks project progress and deliverables.

    Responsibilities:
    - Monitor milestone progress
    - Track deliverables and completion criteria
    - Calculate project velocity
    - Identify blockers and risks
    - Generate progress reports
    """

    def __init__(
        self,
        workspace_path: str,
        workspace_id: str = "default",
        project_id: Optional[str] = None,
    ):
        """
        Initialize Milestone Agent.

        Args:
            workspace_path: Path to workspace directory
            workspace_id: Workspace identifier
            project_id: GCP project ID for Pub/Sub
        """
        # Initialize base agent
        super().__init__(
            workspace_id=workspace_id, agent_id="milestone", project_id=project_id
        )

        # Milestone-specific paths
        self.workspace_path = Path(workspace_path)
        self.milestones_path = self.workspace_path / ".milestones"
        self.milestones_path.mkdir(exist_ok=True)

        # Subscribe to events
        self.subscribe_to_event(EventTypes.PROPOSAL_APPROVED)
        self.subscribe_to_event(EventTypes.GIT_COMMIT)
        self.subscribe_to_event(EventTypes.SPEC_UPDATE)

        logger.info(f"[Milestone Agent] Initialized for workspace: {workspace_path}")

    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events.

        Args:
            event_type: Type of event
            data: Event data payload
        """
        logger.info(f"[Milestone Agent] Received event: {event_type}")

        try:
            if event_type == EventTypes.PROPOSAL_APPROVED:
                await self._handle_proposal_approved(data)
            elif event_type == EventTypes.GIT_COMMIT:
                await self._handle_git_commit(data)
            elif event_type == EventTypes.SPEC_UPDATE:
                await self._handle_spec_update(data)

            # Update metrics
            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(f"[Milestone Agent] Error handling {event_type}: {e}")
            self.increment_metric("errors")

    async def _handle_proposal_approved(self, data: Dict) -> None:
        """Handle proposal.approved.v1 event - update progress"""
        proposal_id = data.get("proposal_id")
        agent_id = data.get("agent_id", "unknown")

        logger.info(
            f"[Milestone Agent] Proposal approved: {proposal_id} by {agent_id}"
        )

        # Track completed work
        await self._track_completion(
            item_type="proposal", item_id=proposal_id, agent_id=agent_id
        )

        # Check if milestone completed
        await self._check_milestone_completion()

    async def _handle_git_commit(self, data: Dict) -> None:
        """Handle git.commit.v1 event - track velocity"""
        commit_hash = data.get("commit_hash")
        files_changed = data.get("files_changed", [])

        logger.info(
            f"[Milestone Agent] Tracking commit: {commit_hash} ({len(files_changed)} files)"
        )

        # Track velocity
        await self._track_velocity(commit_hash, len(files_changed))

    async def _handle_spec_update(self, data: Dict) -> None:
        """Handle spec.update.v1 event - track documentation progress"""
        file_path = data.get("file")
        action = data.get("action", "updated")

        logger.info(f"[Milestone Agent] Spec {action}: {file_path}")

        # Track documentation progress
        await self._track_completion(item_type="documentation", item_id=file_path)

    async def _track_completion(
        self, item_type: str, item_id: str, agent_id: str = "unknown"
    ) -> None:
        """Track completed work item"""
        completions_file = self.milestones_path / "completions.json"

        try:
            if completions_file.exists():
                with open(completions_file, "r") as f:
                    completions = json.load(f)
            else:
                completions = {"items": [], "summary": {"total": 0}}

            # Add completion
            completions["items"].append(
                {
                    "type": item_type,
                    "id": item_id,
                    "agent_id": agent_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Update summary
            completions["summary"]["total"] += 1
            type_count = completions["summary"].get(item_type, 0)
            completions["summary"][item_type] = type_count + 1

            # Save
            with open(completions_file, "w") as f:
                json.dump(completions, f, indent=2)

            logger.info(
                f"[Milestone Agent] Tracked completion: {item_type} - {item_id}"
            )

        except Exception as e:
            logger.error(f"[Milestone Agent] Failed to track completion: {e}")

    async def _track_velocity(self, commit_hash: str, files_changed: int) -> None:
        """Track development velocity"""
        velocity_file = self.milestones_path / "velocity.json"

        try:
            if velocity_file.exists():
                with open(velocity_file, "r") as f:
                    velocity = json.load(f)
            else:
                velocity = {"commits": [], "stats": {"total_commits": 0, "total_files": 0}}

            # Add commit
            velocity["commits"].append(
                {
                    "hash": commit_hash,
                    "files_changed": files_changed,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Update stats
            velocity["stats"]["total_commits"] += 1
            velocity["stats"]["total_files"] += files_changed

            # Calculate recent velocity (last 7 days)
            recent_commits = [
                c
                for c in velocity["commits"]
                if (
                    datetime.now(timezone.utc)
                    - datetime.fromisoformat(c["timestamp"])
                ).days
                <= 7
            ]
            velocity["stats"]["recent_velocity"] = {
                "commits_7d": len(recent_commits),
                "files_7d": sum(c["files_changed"] for c in recent_commits),
            }

            # Save
            with open(velocity_file, "w") as f:
                json.dump(velocity, f, indent=2)

            logger.info(
                f"[Milestone Agent] Tracked velocity: {files_changed} files in {commit_hash[:8]}"
            )

        except Exception as e:
            logger.error(f"[Milestone Agent] Failed to track velocity: {e}")

    async def _check_milestone_completion(self) -> None:
        """Check if any milestones are completed"""
        logger.info("[Milestone Agent] Checking milestone completion...")

        # In production, this would:
        # 1. Load milestone definitions
        # 2. Check completion criteria
        # 3. Calculate progress percentage
        # 4. Publish milestone.complete event if done

        # For now, just log
        completions_file = self.milestones_path / "completions.json"
        if completions_file.exists():
            with open(completions_file, "r") as f:
                completions = json.load(f)
                total = completions["summary"]["total"]
                logger.info(f"[Milestone Agent] Total completions: {total}")

                # Example: If we hit 10 completions, consider it a mini-milestone
                if total > 0 and total % 10 == 0:
                    logger.info(
                        f"[Milestone Agent] Mini-milestone reached: {total} completions!"
                    )
                    # Could publish milestone.complete event here

    async def get_progress_summary(self) -> Dict:
        """
        Get summary of project progress.

        Returns:
            Dictionary with progress metrics
        """
        completions_file = self.milestones_path / "completions.json"
        velocity_file = self.milestones_path / "velocity.json"

        summary = {"status": "active"}

        try:
            if completions_file.exists():
                with open(completions_file, "r") as f:
                    completions = json.load(f)
                    summary["completions"] = completions["summary"]

            if velocity_file.exists():
                with open(velocity_file, "r") as f:
                    velocity = json.load(f)
                    summary["velocity"] = velocity["stats"]

            return summary

        except Exception as e:
            logger.error(f"[Milestone Agent] Failed to get progress summary: {e}")
            return {"status": "error", "error": str(e)}

    def provide_perspective(self, topic: str) -> str:
        """
        Provide agent perspective on a topic.

        Args:
            topic: Discussion topic

        Returns:
            Agent's perspective as a string
        """
        # Milestone Agent focuses on progress tracking and deliverables
        return f"Define clear completion criteria and success metrics for '{topic}', focusing on measurable deliverables and a realistic target date for team review and iteration."

