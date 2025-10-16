"""
Proposal Repository - Firestore persistence for proposals

Handles all database operations for change proposals.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.services.firestore_service import get_firestore_service, FirestoreService
from app.models.proposal import ChangeProposal

logger = logging.getLogger(__name__)


class ProposalRepository:
    """
    Repository for managing proposals in Firestore.
    
    Provides abstraction over Firestore operations.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize repository.
        
        Args:
            project_id: GCP project ID
        """
        self.firestore: FirestoreService = get_firestore_service(project_id)
        logger.info("[ProposalRepository] Initialized")
    
    def create(self, proposal_data: Dict[str, Any]) -> str:
        """
        Create new proposal.
        
        Args:
            proposal_data: Proposal data (must include 'id')
        
        Returns:
            Proposal ID
        
        Raises:
            ValueError: If proposal data is invalid
        """
        # Validate required fields
        required_fields = ['id', 'workspace_id', 'agent_id', 'title']
        for field in required_fields:
            if field not in proposal_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        if 'status' not in proposal_data:
            proposal_data['status'] = 'pending'
        
        if 'created_at' not in proposal_data:
            proposal_data['created_at'] = datetime.utcnow().isoformat()
        
        # Save to Firestore
        proposal_id = self.firestore.create_proposal(proposal_data)
        
        logger.info(f"[ProposalRepository] Created proposal: {proposal_id}")
        return proposal_id
    
    def get(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get proposal by ID.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            Proposal data or None
        """
        proposal = self.firestore.get_proposal(proposal_id)
        
        if proposal:
            logger.debug(f"[ProposalRepository] Found proposal: {proposal_id}")
        else:
            logger.warning(f"[ProposalRepository] Proposal not found: {proposal_id}")
        
        return proposal
    
    def list(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List proposals with filters.
        
        Args:
            workspace_id: Filter by workspace
            status: Filter by status
            limit: Max results
        
        Returns:
            List of proposals
        """
        proposals = self.firestore.list_proposals(
            workspace_id=workspace_id,
            status=status,
            limit=limit
        )
        
        logger.info(f"[ProposalRepository] Listed {len(proposals)} proposals")
        return proposals
    
    def update_status(
        self,
        proposal_id: str,
        status: str,
        commit_hash: Optional[str] = None
    ) -> bool:
        """
        Update proposal status.
        
        Args:
            proposal_id: Proposal ID
            status: New status (pending, approved, rejected)
            commit_hash: Git commit hash (if applicable)
        
        Returns:
            True if successful
        """
        updates = {'status': status}
        
        if commit_hash:
            updates['commit_hash'] = commit_hash
            updates['auto_committed'] = True
        
        return self.firestore.update_proposal(proposal_id, updates)
    
    def approve(self, proposal_id: str, commit_hash: Optional[str] = None) -> bool:
        """
        Approve proposal.
        
        Args:
            proposal_id: Proposal ID
            commit_hash: Git commit hash (if auto-committed)
        
        Returns:
            True if successful
        """
        logger.info(f"[ProposalRepository] Approving proposal: {proposal_id}")
        return self.update_status(proposal_id, 'approved', commit_hash)
    
    def reject(self, proposal_id: str, reason: Optional[str] = None) -> bool:
        """
        Reject proposal.
        
        Args:
            proposal_id: Proposal ID
            reason: Rejection reason (optional)
        
        Returns:
            True if successful
        """
        logger.info(f"[ProposalRepository] Rejecting proposal: {proposal_id}")
        
        updates = {'status': 'rejected'}
        if reason:
            updates['rejection_reason'] = reason
        
        return self.firestore.update_proposal(proposal_id, updates)
    
    def delete(self, proposal_id: str) -> bool:
        """
        Delete proposal.
        
        Args:
            proposal_id: Proposal ID
        
        Returns:
            True if successful
        """
        logger.info(f"[ProposalRepository] Deleting proposal: {proposal_id}")
        return self.firestore.delete_proposal(proposal_id)
    
    def count(self, workspace_id: Optional[str] = None, status: Optional[str] = None) -> int:
        """
        Count proposals with filters.
        
        Args:
            workspace_id: Filter by workspace
            status: Filter by status
        
        Returns:
            Count of matching proposals
        """
        proposals = self.list(workspace_id=workspace_id, status=status, limit=1000)
        return len(proposals)


# Global repository instance
_proposal_repository: Optional[ProposalRepository] = None


def get_proposal_repository(project_id: Optional[str] = None) -> ProposalRepository:
    """
    Get or create ProposalRepository instance.
    
    Args:
        project_id: GCP project ID
    
    Returns:
        ProposalRepository instance
    """
    global _proposal_repository
    
    if _proposal_repository is None:
        _proposal_repository = ProposalRepository(project_id=project_id)
    
    return _proposal_repository


def reset_proposal_repository():
    """Reset global repository (for testing)"""
    global _proposal_repository
    _proposal_repository = None

