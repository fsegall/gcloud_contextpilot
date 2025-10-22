"""
Context Agent - Knowledge Indexing and Semantic Retrieval

Manages context awareness, knowledge indexing, and semantic retrieval.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
from pathlib import Path
import json

from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics

logger = logging.getLogger(__name__)


class ContextAgent(BaseAgent):
    """
    Context Agent manages knowledge indexing and semantic retrieval.

    Responsibilities:
    - Index codebase and documentation
    - Maintain semantic search capabilities
    - Track knowledge graph of project relationships
    - Provide context-aware suggestions
    - Monitor context freshness and relevance
    """

    def __init__(
        self,
        workspace_path: str,
        workspace_id: str = "default",
        project_id: Optional[str] = None,
    ):
        """
        Initialize Context Agent.

        Args:
            workspace_path: Path to workspace directory
            workspace_id: Workspace identifier
            project_id: GCP project ID for Pub/Sub
        """
        # Initialize base agent
        super().__init__(
            workspace_id=workspace_id, agent_id="context", project_id=project_id
        )

        # Context-specific paths
        self.workspace_path = Path(workspace_path)
        self.index_path = self.workspace_path / ".context_index"
        self.index_path.mkdir(exist_ok=True)

        # Subscribe to events
        self.subscribe_to_event(EventTypes.GIT_COMMIT)
        self.subscribe_to_event(EventTypes.PROPOSAL_APPROVED)
        self.subscribe_to_event(EventTypes.SPEC_UPDATE)

        logger.info(f"[Context Agent] Initialized for workspace: {workspace_path}")

    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events.

        Args:
            event_type: Type of event
            data: Event data payload
        """
        logger.info(f"[Context Agent] Received event: {event_type}")

        try:
            if event_type == EventTypes.GIT_COMMIT:
                await self._handle_git_commit(data)
            elif event_type == EventTypes.PROPOSAL_APPROVED:
                await self._handle_proposal_approved(data)
            elif event_type == EventTypes.SPEC_UPDATE:
                await self._handle_spec_update(data)

            # Update metrics
            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(f"[Context Agent] Error handling {event_type}: {e}")
            self.increment_metric("errors")

    async def _handle_git_commit(self, data: Dict) -> None:
        """Handle git.commit.v1 event - reindex affected files"""
        commit_hash = data.get("commit_hash")
        files_changed = data.get("files_changed", [])

        logger.info(
            f"[Context Agent] Processing commit {commit_hash} with {len(files_changed)} files"
        )

        # Reindex changed files
        await self._reindex_files(files_changed)

        # Publish context delta event
        await self.publish_event(
            topic=Topics.CONTEXT_EVENTS,
            event_type=EventTypes.CONTEXT_DELTA,
            data={
                "type": "file_change",
                "scope": files_changed,
                "commit_hash": commit_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _handle_proposal_approved(self, data: Dict) -> None:
        """Handle proposal.approved.v1 event - update context"""
        proposal_id = data.get("proposal_id")
        changes = data.get("changes", [])

        logger.info(
            f"[Context Agent] Updating context for approved proposal: {proposal_id}"
        )

        # Extract affected files from changes
        affected_files = [change.get("file_path") for change in changes]
        await self._reindex_files(affected_files)

    async def _handle_spec_update(self, data: Dict) -> None:
        """Handle spec.update.v1 event - reindex documentation"""
        file_path = data.get("file")

        logger.info(f"[Context Agent] Reindexing spec update: {file_path}")

        if file_path:
            await self._reindex_files([file_path])

    async def _reindex_files(self, files: List[str]) -> None:
        """
        Reindex specified files for semantic search.

        Args:
            files: List of file paths to reindex
        """
        if not files:
            return

        logger.info(f"[Context Agent] Reindexing {len(files)} files")

        # In production, this would:
        # 1. Extract text content and metadata
        # 2. Generate embeddings
        # 3. Update vector database
        # 4. Update knowledge graph

        # For now, track in simple index
        index_file = self.index_path / "file_index.json"

        try:
            if index_file.exists():
                with open(index_file, "r") as f:
                    index = json.load(f)
            else:
                index = {"files": {}, "last_updated": None}

            # Update index
            timestamp = datetime.now(timezone.utc).isoformat()
            for file_path in files:
                index["files"][file_path] = {
                    "last_indexed": timestamp,
                    "status": "indexed",
                }

            index["last_updated"] = timestamp

            # Save index
            with open(index_file, "w") as f:
                json.dump(index, f, indent=2)

            logger.info(f"[Context Agent] Updated index with {len(files)} files")

        except Exception as e:
            logger.error(f"[Context Agent] Failed to update index: {e}")

    async def get_context_summary(self) -> Dict:
        """
        Get summary of current context state.

        Returns:
            Dictionary with context metrics
        """
        index_file = self.index_path / "file_index.json"

        try:
            if index_file.exists():
                with open(index_file, "r") as f:
                    index = json.load(f)

                return {
                    "total_files_indexed": len(index.get("files", {})),
                    "last_updated": index.get("last_updated"),
                    "status": "active",
                }
            else:
                return {
                    "total_files_indexed": 0,
                    "last_updated": None,
                    "status": "uninitialized",
                }
        except Exception as e:
            logger.error(f"[Context Agent] Failed to get context summary: {e}")
            return {"status": "error", "error": str(e)}

    def provide_perspective(self, topic: str) -> str:
        """
        Provide agent perspective on a topic.

        Args:
            topic: Discussion topic

        Returns:
            Agent's perspective as a string
        """
        # Context Agent focuses on knowledge retrieval and indexing
        return f"We should begin by retrieving all existing patterns, specifications, and relevant system schemas related to '{topic}' to inform our approach with comprehensive context."

