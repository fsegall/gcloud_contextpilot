"""
Cloud Run Worker for batch minting CPT tokens.

This worker runs periodically (e.g., daily) to sync off-chain rewards
to on-chain tokens on Polygon.

Deploy as Cloud Run Job:
gcloud run jobs deploy cpt-batch-minter \
  --source . \
  --region us-central1 \
  --schedule="0 2 * * *"  # Daily at 2 AM UTC
"""
import asyncio
import logging
import os
from datetime import datetime, timezone
from google.cloud import firestore

from app.adapters.rewards.blockchain_rewards import BlockchainRewardsAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchMinter:
    """
    Batch processes pending rewards and mints CPT tokens on-chain.
    """
    
    def __init__(self):
        self.adapter = BlockchainRewardsAdapter(
            rpc_url=os.getenv("POLYGON_RPC_URL"),
            contract_address=os.getenv("CPT_CONTRACT_ADDRESS"),
            private_key=os.getenv("MINTER_PRIVATE_KEY"),
            project_id=os.getenv("GCP_PROJECT_ID")
        )
        self.db = firestore.AsyncClient()
        
    async def get_users_with_pending_rewards(self, min_amount: int = 10) -> list[str]:
        """
        Query Firestore for users with pending blockchain rewards.
        
        Args:
            min_amount: Minimum points to mint (avoid gas waste)
            
        Returns:
            List of user IDs to process
        """
        query = (
            self.db.collection("rewards_balances")
            .where("pending_blockchain", ">=", min_amount)
        )
        
        docs = query.stream()
        user_ids = [doc.id async for doc in docs]
        
        logger.info(f"Found {len(user_ids)} users with pending rewards >= {min_amount}")
        return user_ids
    
    async def mint_batch(self, batch_size: int = 50):
        """
        Process a batch of pending mints.
        
        Args:
            batch_size: Number of users to process in this run
        """
        logger.info("Starting batch mint process...")
        
        # Get users with pending rewards
        user_ids = await self.get_users_with_pending_rewards()
        
        if not user_ids:
            logger.info("No pending rewards to mint. Exiting.")
            return {
                "status": "success",
                "minted": 0,
                "message": "No pending rewards"
            }
        
        # Process in batches to avoid timeouts
        total_minted = 0
        total_failed = 0
        
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} users")
            
            try:
                results = await self.adapter.batch_mint(batch)
                total_minted += len(results)
                
                # Log results
                for user_id, tx_hash in results.items():
                    logger.info(f"✅ Minted for {user_id}: {tx_hash}")
                    
            except Exception as e:
                logger.error(f"❌ Batch mint failed: {e}")
                total_failed += len(batch)
        
        # Log summary
        summary = {
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_users": len(user_ids),
            "minted_success": total_minted,
            "minted_failed": total_failed
        }
        
        logger.info(f"Batch mint summary: {summary}")
        
        # Store summary in Firestore for analytics
        await self.db.collection("mint_logs").add(summary)
        
        return summary
    
    async def check_gas_price(self) -> bool:
        """
        Check if gas price is acceptable for batch minting.
        
        Returns:
            True if gas price is acceptable
        """
        try:
            gas_price = self.adapter.w3.eth.gas_price
            max_gas_gwei = int(os.getenv("MAX_GAS_GWEI", "50"))
            max_gas_wei = max_gas_gwei * 10**9
            
            if gas_price > max_gas_wei:
                logger.warning(
                    f"Gas price too high: {gas_price / 10**9:.2f} gwei "
                    f"(max: {max_gas_gwei} gwei). Skipping batch."
                )
                return False
                
            logger.info(f"Gas price acceptable: {gas_price / 10**9:.2f} gwei")
            return True
            
        except Exception as e:
            logger.error(f"Error checking gas price: {e}")
            return False


async def main():
    """Main entry point for Cloud Run Job."""
    logger.info("=== CPT Batch Minter Started ===")
    
    minter = BatchMinter()
    
    # Check gas price before proceeding
    if not await minter.check_gas_price():
        logger.info("Skipping batch due to high gas prices")
        return
    
    # Run batch mint
    result = await minter.mint_batch(batch_size=50)
    
    logger.info(f"=== Batch Mint Completed: {result} ===")


if __name__ == "__main__":
    asyncio.run(main())

