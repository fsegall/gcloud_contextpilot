"""
Proposal Data Models

Defines the structure for change proposals with diffs.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ProposedChange(BaseModel):
    """Individual file change in a proposal"""

    file_path: str = Field(..., description="Path to file being changed")
    change_type: Literal["create", "update", "delete"] = Field(
        ..., description="Type of change"
    )
    description: str = Field(..., description="Human-readable description of change")

    # Content before/after
    before: Optional[str] = Field(None, description="Current file content (if exists)")
    after: Optional[str] = Field(None, description="Proposed file content")

    # Diff
    diff: Optional[str] = Field(None, description="Unified diff for this file")


class ProposalDiff(BaseModel):
    """Complete diff for a proposal"""

    format: Literal["unified", "git-patch"] = Field(
        default="unified", description="Diff format"
    )
    content: str = Field(..., description="Complete diff content")


class ChangeProposal(BaseModel):
    """Change proposal from an agent"""

    id: str = Field(..., description="Unique proposal ID")
    agent_id: str = Field(..., description="Agent that created proposal")
    workspace_id: str = Field(..., description="Workspace ID")

    title: str = Field(..., description="Short title")
    description: str = Field(..., description="Detailed description")

    # Diff
    diff: ProposalDiff = Field(..., description="Complete diff")

    # Individual changes
    proposed_changes: List[ProposedChange] = Field(
        ..., description="List of file changes"
    )

    # Status
    status: Literal["pending", "approved", "rejected"] = Field(default="pending")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None

    # Rejection reason
    rejection_reason: Optional[str] = None

    # AI Review (optional)
    ai_review: Optional[dict] = Field(
        None, description="AI review results if requested"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "spec-001",
                "agent_id": "spec",
                "workspace_id": "contextpilot",
                "title": "Update README.md with event-driven architecture",
                "description": "README is outdated, needs to reflect new event bus",
                "diff": {
                    "format": "unified",
                    "content": "--- a/README.md\n+++ b/README.md\n@@ -1,3 +1,5 @@\n # ContextPilot\n \n-Old architecture\n+Event-driven architecture with Pub/Sub\n",
                },
                "proposed_changes": [
                    {
                        "file_path": "README.md",
                        "change_type": "update",
                        "description": "Add event-driven architecture section",
                        "before": "# ContextPilot\n\nOld architecture",
                        "after": "# ContextPilot\n\nEvent-driven architecture with Pub/Sub",
                        "diff": "--- a/README.md\n+++ b/README.md\n@@ -1,3 +1,5 @@\n # ContextPilot\n \n-Old architecture\n+Event-driven architecture with Pub/Sub\n",
                    }
                ],
                "status": "pending",
                "created_at": "2025-10-15T12:00:00Z",
            }
        }


class ProposalApprovalRequest(BaseModel):
    """Request to approve a proposal"""

    user_id: Optional[str] = None
    comment: Optional[str] = None
    edited_changes: Optional[List[ProposedChange]] = None


class ProposalRejectionRequest(BaseModel):
    """Request to reject a proposal"""

    user_id: Optional[str] = None
    reason: str = Field(..., description="Reason for rejection")


class ProposalAIReviewRequest(BaseModel):
    """Request AI review of a proposal"""

    model: str = Field(default="claude-3-5-sonnet", description="AI model to use")
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus on (e.g., 'security', 'performance')",
    )


class ProposalListResponse(BaseModel):
    """Response with list of proposals"""

    proposals: List[ChangeProposal] = Field(..., description="List of proposals")
    total: int = Field(..., description="Total number of proposals")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=50, description="Items per page")


class ProposalStats(BaseModel):
    """Statistics about proposals"""

    total: int = Field(..., description="Total proposals")
    pending: int = Field(..., description="Pending proposals")
    approved: int = Field(..., description="Approved proposals")
    rejected: int = Field(..., description="Rejected proposals")
    by_agent: dict = Field(default={}, description="Proposals by agent")


class ProposalStatus(BaseModel):
    """Status information for a proposal"""

    id: str = Field(..., description="Proposal ID")
    status: Literal["pending", "approved", "rejected"] = Field(
        ..., description="Current status"
    )
    updated_at: datetime = Field(..., description="Last updated timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated")
