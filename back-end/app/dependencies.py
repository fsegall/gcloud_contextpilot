"""
FastAPI dependency injection.

Provides configured adapters based on explicit configuration.
"""
from functools import lru_cache

from app.config import get_config, RewardsMode
from app.adapters.rewards.ports.rewards_adapter import RewardsAdapter
from app.adapters.rewards.firestore_rewards import FirestoreRewardsAdapter
from app.adapters.rewards.blockchain_rewards import BlockchainRewardsAdapter


@lru_cache()
def get_rewards_adapter() -> RewardsAdapter:
    """
    Get rewards adapter based on application configuration.
    
    Returns:
        Configured RewardsAdapter instance
    
    Raises:
        ValueError: If configuration is invalid
    """
    config = get_config()
    
    if config.rewards_mode == RewardsMode.BLOCKCHAIN:
        return BlockchainRewardsAdapter(
            rpc_url=config.polygon_rpc_url,
            contract_address=config.cpt_contract_address,
            private_key=config.minter_private_key,
            project_id=config.gcp_project_id
        )
    else:
        return FirestoreRewardsAdapter(project_id=config.gcp_project_id)

