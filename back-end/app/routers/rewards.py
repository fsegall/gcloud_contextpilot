"""
Rewards API endpoints.

Provides REST API for tracking developer actions and querying CPT balances.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.adapters.rewards.ports.rewards_adapter import RewardsAdapter, REWARD_ACTIONS
from app.dependencies import get_rewards_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rewards", tags=["rewards"])


class TrackActionRequest(BaseModel):
    """Request to track a reward-earning action."""
    user_id: str
    action_type: str
    metadata: dict = {}


class TrackActionResponse(BaseModel):
    """Response after tracking an action."""
    success: bool
    points_earned: int
    total_balance: int
    action_type: str


class BalanceResponse(BaseModel):
    """User's CPT balance."""
    user_id: str
    total_points: int
    pending_blockchain: int
    on_chain_balance: int
    recent_actions: List[dict]


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    user_id: str
    total_points: int
    last_updated: str


@router.post("/track", response_model=TrackActionResponse)
async def track_action(
    request: TrackActionRequest = Body(...),
    adapter: RewardsAdapter = Depends(get_rewards_adapter)
):
    """
    Track a developer action and award points.
    
    This is called automatically by AI agents when they detect
    reward-worthy actions (commits, docs, etc).
    
    Example:
    ```json
    {
      "user_id": "user_123",
      "action_type": "spec_commit",
      "metadata": {"file": "README.md", "lines": 50}
    }
    ```
    """
    logger.info(
        f"Tracking action: user={request.user_id}, "
        f"type={request.action_type}"
    )
    
    # Validate action type
    if request.action_type not in REWARD_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_type: {request.action_type}. "
                   f"Valid types: {list(REWARD_ACTIONS.keys())}"
        )
    
    try:
        action = await adapter.track_action(
            user_id=request.user_id,
            action_type=request.action_type,
            metadata=request.metadata
        )
        
        balance = await adapter.get_balance(request.user_id)
        
        return TrackActionResponse(
            success=True,
            points_earned=action.points,
            total_balance=balance.total_points,
            action_type=request.action_type
        )
        
    except Exception as e:
        logger.error(f"Error tracking action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance/{user_id}", response_model=BalanceResponse)
async def get_balance(
    user_id: str,
    adapter: RewardsAdapter = Depends(get_rewards_adapter)
):
    """
    Get user's CPT balance.
    
    Returns both off-chain (Firestore) and on-chain (Polygon) balances.
    """
    try:
        balance = await adapter.get_balance(user_id)
        
        return BalanceResponse(
            user_id=balance.user_id,
            total_points=balance.total_points,
            pending_blockchain=balance.pending_blockchain,
            on_chain_balance=balance.total_points - balance.pending_blockchain,
            recent_actions=[
                {
                    "action_type": action.action_type,
                    "points": action.points,
                    "timestamp": action.timestamp.isoformat(),
                    "tx_hash": action.tx_hash,
                    "metadata": action.metadata
                }
                for action in balance.recent_actions
            ]
        )
        
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    adapter: RewardsAdapter = Depends(get_rewards_adapter)
):
    """
    Get top developers by CPT points.
    
    Returns leaderboard sorted by total points.
    """
    try:
        leaderboard = await adapter.get_leaderboard(limit=limit)
        
        return [
            LeaderboardEntry(
                rank=entry["rank"],
                user_id=entry["user_id"],
                total_points=entry["total_points"],
                last_updated=entry["last_updated"].isoformat() if entry.get("last_updated") else "N/A"
            )
            for entry in leaderboard
        ]
        
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions")
async def list_action_types():
    """
    List all available reward action types and their point values.
    
    Use this to see what actions earn rewards.
    """
    return {
        "actions": [
            {"type": action_type, "points": points}
            for action_type, points in REWARD_ACTIONS.items()
        ]
    }


@router.post("/admin/batch-mint")
async def batch_mint(
    user_ids: List[str] = Body(...),
    adapter: RewardsAdapter = Depends(get_rewards_adapter)
):
    """
    Admin endpoint: Batch mint pending points to blockchain.
    
    This should be called periodically (e.g., daily) by a Cloud Run Worker
    to sync off-chain points to on-chain tokens.
    
    Requires admin authentication (TODO: add auth middleware).
    """
    try:
        results = await adapter.batch_mint(user_ids)
        
        return {
            "success": True,
            "minted": len(results),
            "transactions": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch mint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/burn-expired")
async def burn_expired(
    days: int = Query(30, ge=1, le=365),
    adapter: RewardsAdapter = Depends(get_rewards_adapter)
):
    """
    Admin endpoint: Burn tokens from inactive accounts.
    
    Burns tokens from accounts that haven't been active for X days.
    
    Requires admin authentication (TODO: add auth middleware).
    """
    try:
        burned = await adapter.burn_expired(days=days)
        
        return {
            "success": True,
            "tokens_burned": burned,
            "inactivity_days": days
        }
        
    except Exception as e:
        logger.error(f"Error burning expired tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

