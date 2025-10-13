"""
Abstract interface for rewards system.

This port allows switching between off-chain (Firestore) and on-chain (Blockchain)
implementations without changing the core business logic.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class RewardAction:
    """Represents a reward-earning action."""
    user_id: str
    action_type: str
    points: int
    metadata: Dict
    timestamp: datetime
    tx_hash: Optional[str] = None  # For blockchain implementations
    blockchain_pending: bool = False


@dataclass
class UserBalance:
    """User's reward balance."""
    user_id: str
    total_points: int
    pending_blockchain: int  # Points not yet minted on-chain
    last_updated: datetime
    recent_actions: List[RewardAction]


class RewardsAdapter(ABC):
    """
    Abstract adapter for rewards system.
    
    Implementations:
    - FirestoreRewardsAdapter: Off-chain tracking in Firestore
    - BlockchainRewardsAdapter: On-chain minting/burning via smart contract
    """
    
    @abstractmethod
    async def track_action(
        self, 
        user_id: str, 
        action_type: str, 
        metadata: Dict
    ) -> RewardAction:
        """
        Track a reward-earning action.
        
        Args:
            user_id: User identifier
            action_type: Type of action (e.g., 'cli_action', 'spec_commit')
            metadata: Additional context about the action
            
        Returns:
            RewardAction object with points awarded
        """
        pass
    
    @abstractmethod
    async def get_balance(self, user_id: str) -> UserBalance:
        """
        Get user's current balance and recent activity.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserBalance object
        """
        pass
    
    @abstractmethod
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get top users by points.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user rankings
        """
        pass
    
    @abstractmethod
    async def batch_mint(self, user_ids: List[str]) -> Dict[str, str]:
        """
        Batch mint pending points to blockchain.
        
        Only applies to blockchain adapter; no-op for off-chain.
        
        Args:
            user_ids: List of user IDs to process
            
        Returns:
            Dict mapping user_id to transaction hash
        """
        pass
    
    @abstractmethod
    async def burn_expired(self, days: int = 30) -> int:
        """
        Burn tokens that haven't been used in X days.
        
        Args:
            days: Number of days of inactivity before burning
            
        Returns:
            Number of tokens burned
        """
        pass


# Action type constants with point values
REWARD_ACTIONS = {
    "cli_action": 10,
    "spec_commit": 5,
    "strategy_accepted": 15,
    "milestone_saved": 20,
    "coach_completed": 10,
    "gemini_usage": -2,  # Utility consumption
    "doc_update": 8,
    "test_added": 12,
    "code_review": 7,
}


def get_points_for_action(action_type: str) -> int:
    """Get point value for an action type."""
    return REWARD_ACTIONS.get(action_type, 0)

