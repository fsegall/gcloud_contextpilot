"""
Firestore implementation of RewardsAdapter (off-chain).

This adapter stores all reward data in Firestore, making it fast and suitable
for development/testing or as a fallback when blockchain is unavailable.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from google.cloud import firestore

from .ports.rewards_adapter import (
    RewardsAdapter, 
    RewardAction, 
    UserBalance,
    get_points_for_action
)

logger = logging.getLogger(__name__)


class FirestoreRewardsAdapter(RewardsAdapter):
    """
    Off-chain rewards implementation using Firestore.
    
    Collections:
    - rewards_actions: Individual reward events
    - rewards_balances: User balance aggregations
    """
    
    def __init__(self, project_id: str = None):
        """
        Initialize Firestore client.
        
        Args:
            project_id: GCP project ID (optional, uses default credentials)
        """
        self.db = firestore.AsyncClient(project=project_id)
        self.actions_col = self.db.collection("rewards_actions")
        self.balances_col = self.db.collection("rewards_balances")
        logger.info("FirestoreRewardsAdapter initialized (off-chain mode)")
    
    async def track_action(
        self, 
        user_id: str, 
        action_type: str, 
        metadata: Dict
    ) -> RewardAction:
        """Track action in Firestore."""
        points = get_points_for_action(action_type)
        
        action = RewardAction(
            user_id=user_id,
            action_type=action_type,
            points=points,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc),
            blockchain_pending=True  # Ready for future on-chain mint
        )
        
        # Store action
        await self.actions_col.add({
            "user_id": user_id,
            "action_type": action_type,
            "points": points,
            "metadata": metadata,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "blockchain_pending": True,
            "tx_hash": None
        })
        
        # Update balance
        balance_ref = self.balances_col.document(user_id)
        await balance_ref.set({
            "total_points": firestore.Increment(points),
            "pending_blockchain": firestore.Increment(points),
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        logger.info(
            f"Tracked action: user={user_id}, action={action_type}, "
            f"points={points}"
        )
        
        return action
    
    async def get_balance(self, user_id: str) -> UserBalance:
        """Get user balance from Firestore."""
        balance_ref = self.balances_col.document(user_id)
        balance_doc = await balance_ref.get()
        
        if not balance_doc.exists:
            return UserBalance(
                user_id=user_id,
                total_points=0,
                pending_blockchain=0,
                last_updated=datetime.now(timezone.utc),
                recent_actions=[]
            )
        
        balance_data = balance_doc.to_dict()
        
        # Get recent actions (last 10)
        actions_query = (
            self.actions_col
            .where("user_id", "==", user_id)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(10)
        )
        actions_docs = await actions_query.get()
        
        recent_actions = [
            RewardAction(
                user_id=doc.get("user_id"),
                action_type=doc.get("action_type"),
                points=doc.get("points"),
                metadata=doc.get("metadata", {}),
                timestamp=doc.get("timestamp"),
                tx_hash=doc.get("tx_hash"),
                blockchain_pending=doc.get("blockchain_pending", False)
            )
            async for doc in actions_docs
        ]
        
        return UserBalance(
            user_id=user_id,
            total_points=balance_data.get("total_points", 0),
            pending_blockchain=balance_data.get("pending_blockchain", 0),
            last_updated=balance_data.get("last_updated"),
            recent_actions=recent_actions
        )
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top users by points."""
        query = (
            self.balances_col
            .order_by("total_points", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        docs = await query.get()
        
        leaderboard = []
        async for idx, doc in enumerate(docs, start=1):
            data = doc.to_dict()
            leaderboard.append({
                "rank": idx,
                "user_id": doc.id,
                "total_points": data.get("total_points", 0),
                "last_updated": data.get("last_updated")
            })
        
        return leaderboard
    
    async def batch_mint(self, user_ids: List[str]) -> Dict[str, str]:
        """
        No-op for off-chain adapter.
        
        In off-chain mode, "minting" just marks actions as processed.
        """
        logger.info(
            f"Batch mint called in off-chain mode (no-op). "
            f"Users: {len(user_ids)}"
        )
        
        # Mark pending actions as "minted" (simulated)
        batch = self.db.batch()
        
        for user_id in user_ids:
            balance_ref = self.balances_col.document(user_id)
            batch.update(balance_ref, {
                "pending_blockchain": 0,
                "last_mint": firestore.SERVER_TIMESTAMP
            })
        
        await batch.commit()
        
        return {uid: "off-chain-simulated" for uid in user_ids}
    
    async def burn_expired(self, days: int = 30) -> int:
        """Burn tokens inactive for X days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Find inactive users
        query = self.balances_col.where("last_updated", "<", cutoff)
        docs = await query.get()
        
        burned_total = 0
        batch = self.db.batch()
        
        async for doc in docs:
            data = doc.to_dict()
            points = data.get("total_points", 0)
            
            if points > 0:
                # Burn all points
                batch.update(doc.reference, {
                    "total_points": 0,
                    "burned_at": firestore.SERVER_TIMESTAMP,
                    "burned_amount": points
                })
                burned_total += points
                
                # Log burn action
                await self.actions_col.add({
                    "user_id": doc.id,
                    "action_type": "burn_expired",
                    "points": -points,
                    "metadata": {"days_inactive": days},
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
        
        await batch.commit()
        
        logger.info(f"Burned {burned_total} points from inactive users")
        return burned_total

