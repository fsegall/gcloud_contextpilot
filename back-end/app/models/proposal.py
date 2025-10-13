"""
Change Proposal data models.

Represents agent-suggested changes that require developer approval.
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime
from enum import Enum


class ProposalStatus(str, Enum):
    """Status of a change proposal."""
    PENDING = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class ProposalType(str, Enum):
    """Type of change being proposed."""
    REFACTOR = "refactor"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    DOCS = "docs"
    TESTS = "tests"
    SECURITY = "security"
    PERFORMANCE = "performance"


class ChangeAction(str, Enum):
    """Action to perform on a file."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class FileChange(BaseModel):
    """Represents a change to a single file."""
    file: str = Field(..., description="File path relative to repo root")
    action: ChangeAction
    diff: Optional[str] = Field(None, description="Unified diff for modify actions")
    content: Optional[str] = Field(None, description="Full content for create actions")
    reason: str = Field(..., description="Why this change is needed")
    lines_added: int = 0
    lines_removed: int = 0


class ImpactAnalysis(BaseModel):
    """Impact analysis of the proposal."""
    files_affected: int
    lines_added: int
    lines_removed: int
    test_coverage: Literal["maintained", "improved", "reduced", "unknown"]
    breaking_changes: bool
    blast_radius: Literal["low", "medium", "high"]
    estimated_time_minutes: int


class ChangeProposal(BaseModel):
    """
    Complete change proposal from an agent.
    
    This is the core data structure for the "agents suggest, devs approve" workflow.
    """
    proposal_id: str = Field(..., description="Unique proposal identifier")
    created_at: datetime
    agent: str = Field(..., description="Agent that created proposal (e.g., 'strategy-agent')")
    type: ProposalType
    
    # Description
    title: str = Field(..., max_length=100, description="Short title (≤100 chars)")
    description: str = Field(..., description="Detailed explanation of the change")
    
    # Changes
    changes: List[FileChange] = Field(..., min_items=1)
    
    # Impact
    impact: ImpactAnalysis
    
    # Benefits & Risks
    benefits: List[str] = Field(..., description="Expected benefits")
    risks: List[str] = Field(default_factory=list, description="Potential risks")
    
    # Status & Tracking
    status: ProposalStatus = ProposalStatus.PENDING
    user_id: str = Field(..., description="Target developer")
    workspace_id: str = Field(default="default")
    
    # Git integration
    preview_branch: Optional[str] = Field(None, description="Branch created for preview")
    applied_commit: Optional[str] = Field(None, description="Commit hash after applying")
    
    # Approval tracking
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Metadata
    related_events: List[str] = Field(default_factory=list, description="Event IDs that triggered this proposal")
    related_issues: List[str] = Field(default_factory=list, description="GitHub issues, etc")
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class ProposalApprovalRequest(BaseModel):
    """Request to approve a proposal."""
    proposal_id: str
    user_id: str
    edited_changes: Optional[List[FileChange]] = Field(
        None,
        description="If user edited the changes before approving"
    )
    create_pr: bool = Field(True, description="Create PR after applying")
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None


class ProposalRejectionRequest(BaseModel):
    """Request to reject a proposal."""
    proposal_id: str
    user_id: str
    reason: str = Field(..., description="Why rejected (helps agents learn)")
    feedback: Optional[str] = Field(None, description="Additional feedback for agent")


class ProposalListResponse(BaseModel):
    """Response for listing proposals."""
    proposals: List[ChangeProposal]
    total: int
    pending: int
    approved: int
    rejected: int


class ProposalStats(BaseModel):
    """Statistics about proposals."""
    total_proposals: int
    by_status: dict[ProposalStatus, int]
    by_agent: dict[str, int]
    by_type: dict[ProposalType, int]
    approval_rate: float
    avg_time_to_review_minutes: float


# Example proposal
EXAMPLE_PROPOSAL = {
    "proposal_id": "cp_001",
    "created_at": "2025-10-14T10:00:00Z",
    "agent": "strategy-agent",
    "type": "refactor",
    "title": "Extract AuthService from duplicated code",
    "description": "Authentication logic is duplicated across 3 files (login.py, register.py, reset.py). Extracting to a centralized AuthService will improve maintainability and testability.",
    "changes": [
        {
            "file": "src/auth/login.py",
            "action": "modify",
            "diff": "@@ -10,30 +10,8 @@ ...",
            "reason": "Remove duplicated auth logic",
            "lines_added": 8,
            "lines_removed": 30
        },
        {
            "file": "src/services/auth_service.py",
            "action": "create",
            "content": "class AuthService:\n    ...",
            "reason": "Centralize auth logic",
            "lines_added": 50,
            "lines_removed": 0
        }
    ],
    "impact": {
        "files_affected": 4,
        "lines_added": 50,
        "lines_removed": 120,
        "test_coverage": "maintained",
        "breaking_changes": False,
        "blast_radius": "medium",
        "estimated_time_minutes": 45
    },
    "benefits": [
        "Reduce duplication from 3x to 1x",
        "Easier to test (single service)",
        "Single source of truth for auth"
    ],
    "risks": [
        "Need to update imports in 8 files",
        "Potential merge conflicts"
    ],
    "status": "pending_approval",
    "user_id": "dev_123",
    "workspace_id": "default",
    "priority": "medium"
}

