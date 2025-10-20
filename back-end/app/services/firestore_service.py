"""
Firestore Service - Database abstraction for ContextPilot

Provides CRUD operations for all Firestore collections.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)


class FirestoreService:
    """
    Firestore database service for ContextPilot.

    Collections:
    - proposals: Change proposals from agents
    - workspaces: User workspaces
    - users: User profiles
    - agent_state: Agent state snapshots
    - events: Event log (optional)
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Firestore client.

        Args:
            project_id: GCP project ID (defaults to env var GCP_PROJECT_ID)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID not set. Cannot initialize Firestore.")

        try:
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"[Firestore] Connected to project: {self.project_id}")
        except Exception as e:
            logger.error(f"[Firestore] Failed to connect: {e}")
            raise

    # ========== PROPOSALS COLLECTION ==========

    def create_proposal(self, proposal: Dict[str, Any]) -> str:
        """
        Create a new proposal in Firestore.

        Args:
            proposal: Proposal data (must include 'id')

        Returns:
            Proposal ID
        """
        proposal_id = proposal.get("id")
        if not proposal_id:
            raise ValueError("Proposal must have 'id' field")

        # Ensure created_at is set
        if "created_at" not in proposal:
            proposal["created_at"] = datetime.utcnow().isoformat()

        # Store in Firestore
        doc_ref = self.db.collection("proposals").document(proposal_id)
        doc_ref.set(proposal)

        logger.info(f"[Firestore] Created proposal: {proposal_id}")
        return proposal_id

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get proposal by ID.

        Args:
            proposal_id: Proposal ID

        Returns:
            Proposal data or None if not found
        """
        doc_ref = self.db.collection("proposals").document(proposal_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        else:
            logger.warning(f"[Firestore] Proposal not found: {proposal_id}")
            return None

    def list_proposals(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List proposals with optional filters.

        Args:
            workspace_id: Filter by workspace
            status: Filter by status (pending, approved, rejected)
            limit: Max number of results

        Returns:
            List of proposals
        """
        query = self.db.collection("proposals")

        # Apply filters (simplified to avoid composite index requirement)
        if workspace_id:
            query = query.where(filter=FieldFilter("workspace_id", "==", workspace_id))

        if status:
            query = query.where(filter=FieldFilter("status", "==", status))

        # Don't order by created_at if we're filtering (to avoid index requirement)
        # Instead, we'll sort in memory

        # Limit results
        query = query.limit(limit)

        # Execute query
        docs = query.stream()
        proposals = [doc.to_dict() for doc in docs]

        # Sort in memory by created_at (handle datetime objects properly)
        def sort_key(proposal):
            created_at = proposal.get("created_at")
            if isinstance(created_at, str):
                return created_at
            elif hasattr(created_at, "isoformat"):
                return created_at.isoformat()
            else:
                return str(created_at) if created_at else ""

        proposals.sort(key=sort_key, reverse=True)

        logger.info(
            f"[Firestore] Listed {len(proposals)} proposals (workspace: {workspace_id}, status: {status})"
        )
        return proposals

    def update_proposal(self, proposal_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update proposal fields.

        Args:
            proposal_id: Proposal ID
            updates: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()

            doc_ref = self.db.collection("proposals").document(proposal_id)
            doc_ref.update(updates)

            logger.info(f"[Firestore] Updated proposal: {proposal_id}")
            return True
        except Exception as e:
            logger.error(f"[Firestore] Failed to update proposal {proposal_id}: {e}")
            return False

    def delete_proposal(self, proposal_id: str) -> bool:
        """
        Delete proposal.

        Args:
            proposal_id: Proposal ID

        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection("proposals").document(proposal_id)
            doc_ref.delete()

            logger.info(f"[Firestore] Deleted proposal: {proposal_id}")
            return True
        except Exception as e:
            logger.error(f"[Firestore] Failed to delete proposal {proposal_id}: {e}")
            return False

    # ========== WORKSPACES COLLECTION ==========

    def create_workspace(self, workspace_id: str, data: Dict[str, Any]) -> str:
        """Create workspace in Firestore"""
        data["id"] = workspace_id
        data["created_at"] = datetime.utcnow().isoformat()

        doc_ref = self.db.collection("workspaces").document(workspace_id)
        doc_ref.set(data)

        logger.info(f"[Firestore] Created workspace: {workspace_id}")
        return workspace_id

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get workspace by ID"""
        doc_ref = self.db.collection("workspaces").document(workspace_id)
        doc = doc_ref.get()

        return doc.to_dict() if doc.exists else None

    def list_workspaces(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all workspaces, optionally filtered by user"""
        query = self.db.collection("workspaces")

        if user_id:
            query = query.where(filter=FieldFilter("owner_id", "==", user_id))

        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    # ========== USERS COLLECTION ==========

    def create_user(self, user_id: str, data: Dict[str, Any]) -> str:
        """Create user profile"""
        data["id"] = user_id
        data["created_at"] = datetime.utcnow().isoformat()

        doc_ref = self.db.collection("users").document(user_id)
        doc_ref.set(data)

        logger.info(f"[Firestore] Created user: {user_id}")
        return user_id

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        doc_ref = self.db.collection("users").document(user_id)
        doc = doc_ref.get()

        return doc.to_dict() if doc.exists else None

    # ========== AGENT STATE COLLECTION ==========

    def save_agent_state(
        self, agent_id: str, workspace_id: str, state: Dict[str, Any]
    ) -> str:
        """Save agent state snapshot"""
        state_id = f"{agent_id}_{workspace_id}"
        state["agent_id"] = agent_id
        state["workspace_id"] = workspace_id
        state["updated_at"] = datetime.utcnow().isoformat()

        doc_ref = self.db.collection("agent_state").document(state_id)
        doc_ref.set(state)

        logger.debug(f"[Firestore] Saved agent state: {state_id}")
        return state_id

    def get_agent_state(
        self, agent_id: str, workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get agent state"""
        state_id = f"{agent_id}_{workspace_id}"
        doc_ref = self.db.collection("agent_state").document(state_id)
        doc = doc_ref.get()

        return doc.to_dict() if doc.exists else None

    # ========== EVENTS COLLECTION (Optional) ==========

    def log_event(self, event: Dict[str, Any]) -> str:
        """Log event to Firestore (for audit trail)"""
        event["logged_at"] = datetime.utcnow().isoformat()

        doc_ref = self.db.collection("events").document()
        doc_ref.set(event)

        return doc_ref.id

    def query_events(
        self,
        event_type: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query events with filters"""
        query = self.db.collection("events")

        if event_type:
            query = query.where(filter=FieldFilter("event_type", "==", event_type))

        if workspace_id:
            query = query.where(filter=FieldFilter("workspace_id", "==", workspace_id))

        query = query.order_by("logged_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        docs = query.stream()
        return [doc.to_dict() for doc in docs]


# Global Firestore instance
_firestore_service: Optional[FirestoreService] = None


def get_firestore_service(project_id: Optional[str] = None) -> FirestoreService:
    """
    Get or create Firestore service instance.

    Args:
        project_id: GCP project ID

    Returns:
        FirestoreService instance
    """
    global _firestore_service

    if _firestore_service is None:
        _firestore_service = FirestoreService(project_id=project_id)

    return _firestore_service


def reset_firestore_service():
    """Reset global Firestore service (for testing)"""
    global _firestore_service
    _firestore_service = None
