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
from app.dependencies import get_rewards_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["proposals"])

# Initialize Firestore
# IMPORTANT: Using 'proposals' collection (NOT 'change_proposals')
# This ensures consistency with firestore_service.py
# BUILD_VERSION: 2025-10-21-18-20 (PROPOSALS collection)
db = firestore.AsyncClient()
proposals_col = db.collection("proposals")  # Unified collection name - v2


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
    logger.info(f"Creating proposal: {proposal.id} by {proposal.agent_id}")

    try:
        # Store in Firestore
        await proposals_col.document(proposal.id).set(proposal.model_dump(mode="json"))

        # Publish event
        event_bus = get_event_bus()
        event_bus.publish(
            topic="proposals-events",
            event_type="proposal.created.v1",
            source=proposal.agent_id,
            data={
                "proposal_id": proposal.id,
                "title": proposal.title,
                "agent_id": proposal.agent_id,
                "workspace_id": proposal.workspace_id,
            },
        )

        logger.info(f"✅ Proposal created: {proposal.id}")
        return proposal

    except Exception as e:
        logger.error(f"Error creating proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ProposalListResponse)
async def list_proposals(
    workspace_id: str = Query("default"),
    user_id: str = Query(..., description="User ID to filter proposals"),
    status: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List proposals for a workspace filtered by user_id.

    Filters:
    - workspace_id: Optional (default: "default")
    - user_id: Required (only show proposals for this user)
    - status: Optional (pending, approved, rejected)
    - agent: Optional (strategy, spec, retrospective, etc)
    """
    logger.info(f"Listing proposals for workspace: {workspace_id}, user: {user_id}")

    try:
        # Build query - NO ORDER BY to avoid composite index requirement
        # We'll sort client-side instead
        query = proposals_col.where("workspace_id", "==", workspace_id)
        query = query.limit(
            200
        )  # Fetch more docs for client-side filtering and sorting

        # Execute
        docs = query.stream()
        proposals = []
        total_docs = 0
        filtered_docs = 0

        async for doc in docs:
            total_docs += 1
            data = doc.to_dict()
            logger.info(
                f"Processing doc {total_docs}: id={data.get('id')}, user_id={data.get('user_id')}, workspace_id={data.get('workspace_id')}"
            )

            # Client-side filtering - user_id is now required
            if data.get("user_id") != user_id:
                logger.info(
                    f"  Skipping doc {total_docs}: user_id mismatch ({data.get('user_id')} != {user_id})"
                )
                continue
            if status and data.get("status") != status:
                logger.info(
                    f"  Skipping doc {total_docs}: status mismatch ({data.get('status')} != {status})"
                )
                continue
            if agent and data.get("agent_id") != agent:
                logger.info(
                    f"  Skipping doc {total_docs}: agent mismatch ({data.get('agent_id')} != {agent})"
                )
                continue

            filtered_docs += 1
            logger.info(
                f"  Adding doc {total_docs} to proposals (filtered doc #{filtered_docs})"
            )
            proposals.append(ChangeProposal(**data))

        logger.info(
            f"Query completed: {total_docs} total docs, {filtered_docs} passed filters, {len(proposals)} proposals before sorting"
        )

        # Sort client-side by created_at descending
        proposals.sort(key=lambda p: p.created_at, reverse=True)

        # Apply limit after sorting
        proposals = proposals[:limit]

        logger.info(f"Returning {len(proposals)} proposals after sorting and limit")

        # Count by status
        pending = sum(1 for p in proposals if p.status == "pending")
        approved = sum(1 for p in proposals if p.status == "approved")
        rejected = sum(1 for p in proposals if p.status == "rejected")

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
        # Allow approval if:
        # 1. User is the owner (proposal.user_id == request.user_id)
        # 2. Proposal is from system/agents (proposal.user_id == "system")
        if proposal.user_id != request.user_id and proposal.user_id != "system":
            raise HTTPException(status_code=403, detail="Not authorized")

        # Check status
        if proposal.status != "pending":
            raise HTTPException(
                status_code=400, detail=f"Proposal already {proposal.status}"
            )

        # Update proposal
        await doc_ref.update(
            {
                "status": "approved",
                "approved_by": request.user_id,
                "approved_at": firestore.SERVER_TIMESTAMP,
            }
        )

        # If user edited changes, update them
        if request.edited_changes:
            await doc_ref.update(
                {
                    "proposed_changes": [
                        c.model_dump() for c in request.edited_changes
                    ],
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
                    c.model_dump()
                    for c in (request.edited_changes or proposal.proposed_changes)
                ],
                "comment": request.comment,
            },
        )

        logger.info(f"✅ Proposal approved: {proposal_id}")

        # Award CPTs for approving a proposal
        try:
            rewards_adapter = get_rewards_adapter()
            await rewards_adapter.track_action(
                user_id=request.user_id,
                action_type="proposal_approval",
                metadata={
                    "proposal_id": proposal_id,
                    "agent_id": proposal.agent_id,
                    "title": proposal.title,
                },
            )
            logger.info(
                f"💰 Rewarded user {request.user_id} for approving proposal {proposal_id}"
            )
        except Exception as e:
            logger.error(f"Failed to award reward: {e}")
            # Don't fail the approval if rewards fail

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
        # Allow rejection if:
        # 1. User is the owner (proposal.user_id == request.user_id)
        # 2. Proposal is from system/agents (proposal.user_id == "system")
        if proposal.user_id != request.user_id and proposal.user_id != "system":
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update proposal
        await doc_ref.update(
            {
                "status": "rejected",
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
                # camelCase for event payload keys
                "agentId": proposal.agent_id,
                "reason": request.reason,
                "feedback": request.feedback,
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
        approved = by_status.get("approved", 0)
        rejected = by_status.get("rejected", 0)
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
        if proposal.status != "pending":
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
