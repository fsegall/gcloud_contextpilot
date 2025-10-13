"""
FastAPI dependency injection.

Provides configured adapters based on environment settings.
"""
import os
from functools import lru_cache

from app.adapters.rewards.ports.rewards_adapter import RewardsAdapter
from app.adapters.rewards.firestore_rewards import FirestoreRewardsAdapter
from app.adapters.rewards.blockchain_rewards import BlockchainRewardsAdapter


@lru_cache()
def get_rewards_adapter() -> RewardsAdapter:
    """
    Get rewards adapter based on REWARDS_MODE environment variable.
    
    Modes:
    - "firestore" (default): Off-chain only, fast
    - "blockchain": On-chain with Firestore backing
    
    Returns:
        Configured RewardsAdapter instance
    """
    mode = os.getenv("REWARDS_MODE", "firestore").lower()
    project_id = os.getenv("GCP_PROJECT_ID")
    
    if mode == "blockchain":
        return BlockchainRewardsAdapter(
            rpc_url=os.getenv("POLYGON_RPC_URL"),
            contract_address=os.getenv("CPT_CONTRACT_ADDRESS"),
            private_key=os.getenv("MINTER_PRIVATE_KEY"),
            project_id=project_id
        )
    else:
        return FirestoreRewardsAdapter(project_id=project_id)

