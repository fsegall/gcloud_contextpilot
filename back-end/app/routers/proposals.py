"""
Change Proposals API endpoints.

Provides REST API for agents to create proposals and developers to approve/reject them.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
import logging
from datetime import datetime, timezone
import os
import httpx

from app.models.proposal import (
    ChangeProposal,
    ProposalApprovalRequest,
    ProposalRejectionRequest,
    ProposalListResponse,
    ProposalStats,
    ProposalStatus,
)
from google.cloud import firestore
from app.services.event_bus import get_event_bus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["proposals"])

# Initialize Firestore
db = firestore.AsyncClient()
proposals_col = db.collection("change_proposals")


async def trigger_github_action(proposal_id: str):
    """
    Trigger GitHub Action via repository_dispatch webhook.

    Requires GITHUB_TOKEN and GITHUB_REPO environment variables.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "fsegall/gcloud_contextpilot")

    if not github_token:
        logger.warning("⚠️ GITHUB_TOKEN not set, skipping GitHub Action trigger")
        return

    url = f"https://api.github.com/repos/{github_repo}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "event_type": "proposal-approved",
        "client_payload": {"proposal_id": proposal_id},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=10.0
            )

            if response.status_code == 204:
                logger.info(f"✅ GitHub Action triggered for proposal: {proposal_id}")
            else:
                logger.error(
                    f"❌ GitHub Action trigger failed: {response.status_code} - {response.text}"
                )
    except Exception as e:
        logger.error(f"❌ Error triggering GitHub Action: {e}")


@router.post("/create", response_model=ChangeProposal)
async def create_proposal(proposal: ChangeProposal = Body(...)):
    """
    Create a new change proposal.

    Called by agents (Strategy, Spec) when they identify an improvement opportunity.

    Example:
    ```json
    {
      "proposal_id": "cp_001",
      "agent": "strategy-agent",
      "type": "refactor",
      "title": "Extract AuthService",
      "changes": [...],
      "impact": {...}
    }
    ```
    """
    logger.info(f"Creating proposal: {proposal.proposal_id} by {proposal.agent}")

    try:
        # Store in Firestore
        await proposals_col.document(proposal.proposal_id).set(
            proposal.model_dump(mode="json")
        )

        # Publish event
        event_bus = get_event_bus()
        event_bus.publish(
            topic="proposals-events",
            event_type="proposal.created.v1",
            source=proposal.agent,
            data={
                "proposal_id": proposal.proposal_id,
                "type": proposal.type,
                "title": proposal.title,
                "user_id": proposal.user_id,
                "priority": proposal.priority,
            },
        )

        logger.info(f"✅ Proposal created: {proposal.proposal_id}")
        return proposal

    except Exception as e:
        logger.error(f"Error creating proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ProposalListResponse)
async def list_proposals(
    user_id: str = Query(...),
    workspace_id: str = Query("default"),
    status: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List proposals for a user.

    Filters:
    - user_id: Required
    - workspace_id: Optional (default: "default")
    - status: Optional (pending_approval, approved, etc)
    - agent: Optional (strategy-agent, spec-agent, etc)
    """
    logger.info(f"Listing proposals for user: {user_id}, workspace: {workspace_id}")

    try:
        # Build query - simplified to avoid composite index requirements
        query = proposals_col.where("workspace_id", "==", workspace_id)
        
        # Order by created_at desc
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit * 2)  # Fetch more for filtering

        # Execute
        docs = query.stream()
        proposals = []

        async for doc in docs:
            data = doc.to_dict()
            
            # Client-side filtering
            if data.get("user_id") != user_id:
                continue
            if status and data.get("status") != status:
                continue
            if agent and data.get("agent") != agent:
                continue
            
            proposals.append(ChangeProposal(**data))
            
            # Stop when we have enough
            if len(proposals) >= limit:
                break

        # Count by status
        pending = sum(1 for p in proposals if p.status == ProposalStatus.PENDING)
        approved = sum(1 for p in proposals if p.status == ProposalStatus.APPROVED)
        rejected = sum(1 for p in proposals if p.status == ProposalStatus.REJECTED)

        return ProposalListResponse(
            proposals=proposals,
            total=len(proposals),
            pending=pending,
            approved=approved,
            rejected=rejected,
        )

    except Exception as e:
        logger.error(f"Error listing proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}", response_model=ChangeProposal)
async def get_proposal(proposal_id: str):
    """Get detailed proposal by ID."""

    try:
        doc = await proposals_col.document(proposal_id).get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Proposal not found")

        return ChangeProposal(**doc.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str, request: ProposalApprovalRequest = Body(...)
):
    """
    Approve a proposal.

    This triggers Git Agent to apply the changes.
    """
    logger.info(f"Approving proposal: {proposal_id} by user: {request.user_id}")

    try:
        # Get proposal
        doc_ref = proposals_col.document(proposal_id)
        doc = await doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Proposal not found")

        proposal = ChangeProposal(**doc.to_dict())

        # Verify ownership
        if proposal.user_id != request.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Check status
        if proposal.status != ProposalStatus.PENDING:
            raise HTTPException(
                status_code=400, detail=f"Proposal already {proposal.status}"
            )

        # Update proposal
        await doc_ref.update(
            {
                "status": ProposalStatus.APPROVED.value,
                "approved_by": request.user_id,
                "approved_at": firestore.SERVER_TIMESTAMP,
            }
        )

        # If user edited changes, update them
        if request.edited_changes:
            await doc_ref.update(
                {
                    "changes": [c.model_dump() for c in request.edited_changes],
                    "edited_by_user": True,
                }
            )

        # Publish event for Git Agent
        event_bus = get_event_bus()
        event_bus.publish(
            topic="proposals-events",
            event_type="proposal.approved.v1",
            source="proposals-api",
            data={
                "proposal_id": proposal_id,
                "user_id": request.user_id,
                "changes": [
                    c.model_dump() for c in (request.edited_changes or proposal.changes)
                ],
                "create_pr": request.create_pr,
                "pr_title": request.pr_title,
                "pr_body": request.pr_body,
            },
        )

        logger.info(f"✅ Proposal approved: {proposal_id}")

        # Trigger GitHub Action via repository_dispatch webhook
        await trigger_github_action(proposal_id)

        return {
            "status": "approved",
            "proposal_id": proposal_id,
            "message": "Proposal approved. Git Agent will apply changes.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: str, request: ProposalRejectionRequest = Body(...)
):
    """
    Reject a proposal with reason.

    This helps agents learn from rejections.
    """
    logger.info(f"Rejecting proposal: {proposal_id} by user: {request.user_id}")

    try:
        doc_ref = proposals_col.document(proposal_id)
        doc = await doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Proposal not found")

        proposal = ChangeProposal(**doc.to_dict())

        # Verify ownership
        if proposal.user_id != request.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update proposal
        await doc_ref.update(
            {
                "status": ProposalStatus.REJECTED.value,
                "rejected_by": request.user_id,
                "rejected_at": firestore.SERVER_TIMESTAMP,
                "rejection_reason": request.reason,
                "feedback": request.feedback,
            }
        )

        # Publish event (agents can learn from this)
        event_bus = get_event_bus()
        event_bus.publish(
            topic="proposals-events",
            event_type="proposal.rejected.v1",
            source="proposals-api",
            data={
                "proposal_id": proposal_id,
                "agent": proposal.agent,
                "reason": request.reason,
                "feedback": request.feedback,
                "type": proposal.type,
            },
        )

        logger.info(f"✅ Proposal rejected: {proposal_id}")

        return {
            "status": "rejected",
            "proposal_id": proposal_id,
            "message": "Proposal rejected. Feedback recorded for agent learning.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ProposalStats)
async def get_proposal_stats(
    user_id: Optional[str] = Query(None),
    workspace_id: str = Query("default"),
    days: int = Query(7, ge=1, le=90),
):
    """
    Get proposal statistics.

    Useful for dashboards and agent retrospectives.
    """
    try:
        # Calculate cutoff date
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Build query
        query = proposals_col.where("created_at", ">=", cutoff)

        if user_id:
            query = query.where("user_id", "==", user_id)
        if workspace_id:
            query = query.where("workspace_id", "==", workspace_id)

        # Fetch all
        docs = query.stream()
        proposals = [ChangeProposal(**doc.to_dict()) async for doc in docs]

        # Calculate stats
        by_status = {}
        by_agent = {}
        by_type = {}
        total_review_time = 0
        reviewed_count = 0

        for p in proposals:
            # By status
            by_status[p.status] = by_status.get(p.status, 0) + 1

            # By agent
            by_agent[p.agent] = by_agent.get(p.agent, 0) + 1

            # By type
            by_type[p.type] = by_type.get(p.type, 0) + 1

            # Review time
            if p.approved_at:
                review_time = (p.approved_at - p.created_at).total_seconds() / 60
                total_review_time += review_time
                reviewed_count += 1
            elif p.rejected_at:
                review_time = (p.rejected_at - p.created_at).total_seconds() / 60
                total_review_time += review_time
                reviewed_count += 1

        # Approval rate
        approved = by_status.get(ProposalStatus.APPROVED, 0)
        rejected = by_status.get(ProposalStatus.REJECTED, 0)
        total_reviewed = approved + rejected
        approval_rate = approved / total_reviewed if total_reviewed > 0 else 0

        # Avg review time
        avg_review_time = (
            total_review_time / reviewed_count if reviewed_count > 0 else 0
        )

        return ProposalStats(
            total_proposals=len(proposals),
            by_status=by_status,
            by_agent=by_agent,
            by_type=by_type,
            approval_rate=approval_rate,
            avg_time_to_review_minutes=avg_review_time,
        )

    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proposal_id}")
async def delete_proposal(proposal_id: str, user_id: str = Query(...)):
    """
    Delete a proposal.

    Only allowed for pending proposals by the owner.
    """
    try:
        doc_ref = proposals_col.document(proposal_id)
        doc = await doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Proposal not found")

        proposal = ChangeProposal(**doc.to_dict())

        # Verify ownership
        if proposal.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Only delete pending
        if proposal.status != ProposalStatus.PENDING:
            raise HTTPException(
                status_code=400, detail="Can only delete pending proposals"
            )

        await doc_ref.delete()

        logger.info(f"✅ Proposal deleted: {proposal_id}")

        return {"status": "deleted", "proposal_id": proposal_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
