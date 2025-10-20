"""
Blockchain implementation of RewardsAdapter (on-chain).

This adapter interacts with the CPT smart contract on Polygon to mint/burn
tokens based on off-chain activity tracked in Firestore.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import os

from .ports.rewards_adapter import (
    RewardsAdapter,
    RewardAction,
    UserBalance,
    get_points_for_action
)
from .firestore_rewards import FirestoreRewardsAdapter

logger = logging.getLogger(__name__)


class BlockchainRewardsAdapter(RewardsAdapter):
    """
    On-chain rewards implementation using Polygon + CPT smart contract.
    
    This adapter wraps FirestoreRewardsAdapter for off-chain tracking and
    syncs balances to the blockchain via batch minting.
    
    Architecture:
    1. Actions are tracked in Firestore (fast)
    2. Periodically, pending points are batch-minted on-chain
    3. Balance queries check both Firestore (pending) + blockchain (minted)
    """
    
    def __init__(
        self,
        rpc_url: str = None,
        contract_address: str = None,
        private_key: str = None,
        project_id: str = None
    ):
        """
        Initialize blockchain adapter.
        
        Args:
            rpc_url: Polygon RPC endpoint (defaults to env var)
            contract_address: CPT contract address (defaults to env var)
            private_key: Private key for minting (defaults to env var)
            project_id: GCP project for Firestore
        """
        # Initialize off-chain layer (Firestore)
        self.firestore = FirestoreRewardsAdapter(project_id=project_id)
        
        # Setup Web3 connection - Prioritize Google Blockchain Node Engine
        gcne_endpoint = os.getenv("GOOGLE_BLOCKCHAIN_NODE_ENDPOINT")
        
        if gcne_endpoint:
            self.rpc_url = gcne_endpoint
            logger.info(f"✅ Using Google Blockchain Node Engine: {gcne_endpoint[:50]}...")
        else:
            self.rpc_url = rpc_url or os.getenv("SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")
            logger.warning("⚠️  Using public RPC (consider enabling Google Blockchain Node Engine for production)")
        
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add PoA middleware (required for some testnets)
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Contract setup
        self.contract_address = contract_address or os.getenv("CPT_CONTRACT_ADDRESS")
        self.private_key = private_key or os.getenv("MINTER_PRIVATE_KEY")
        
        if not self.contract_address:
            logger.warning("CPT_CONTRACT_ADDRESS not set - blockchain features disabled")
            self.contract = None
        else:
            # Load ABI (should be in same directory)
            abi_path = os.path.join(os.path.dirname(__file__), "CPT_ABI.json")
            with open(abi_path) as f:
                abi = json.load(f)
            
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=abi
            )
            
            logger.info(
                f"BlockchainRewardsAdapter initialized: "
                f"contract={self.contract_address}, "
                f"network={self.w3.eth.chain_id}"
            )
    
    async def track_action(
        self,
        user_id: str,
        action_type: str,
        metadata: Dict
    ) -> RewardAction:
        """Track action in Firestore (off-chain fast path)."""
        return await self.firestore.track_action(user_id, action_type, metadata)
    
    async def get_balance(self, user_id: str) -> UserBalance:
        """
        Get balance from both Firestore (pending) and blockchain (minted).
        
        Returns combined view:
        - total_points = on-chain balance + pending Firestore balance
        - pending_blockchain = points not yet minted
        """
        # Get Firestore balance (includes pending)
        firestore_balance = await self.firestore.get_balance(user_id)
        
        # Get on-chain balance if contract available
        onchain_balance = 0
        if self.contract:
            try:
                # Convert user_id to wallet address (you'll need mapping logic)
                wallet_address = self._user_id_to_wallet(user_id)
                if wallet_address:
                    onchain_balance = self.contract.functions.balanceOf(
                        Web3.to_checksum_address(wallet_address)
                    ).call()
            except Exception as e:
                logger.error(f"Error fetching on-chain balance: {e}")
        
        # Combine balances
        firestore_balance.total_points = onchain_balance + firestore_balance.pending_blockchain
        
        return firestore_balance
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get leaderboard from Firestore."""
        return await self.firestore.get_leaderboard(limit)
    
    async def batch_mint(self, user_ids: List[str]) -> Dict[str, str]:
        """
        Batch mint pending points to blockchain.
        
        This is the key function that syncs off-chain → on-chain.
        Should be called periodically by a Cloud Run Worker.
        
        Args:
            user_ids: Users to process (or empty for all pending)
            
        Returns:
            Dict mapping user_id to transaction hash
        """
        if not self.contract or not self.private_key:
            logger.warning("Contract not configured - skipping batch mint")
            return {}
        
        results = {}
        account = self.w3.eth.account.from_key(self.private_key)
        
        for user_id in user_ids:
            try:
                # Get pending balance
                balance = await self.firestore.get_balance(user_id)
                pending = balance.pending_blockchain
                
                if pending <= 0:
                    logger.debug(f"No pending points for user {user_id}")
                    continue
                
                # Get wallet address
                wallet = self._user_id_to_wallet(user_id)
                if not wallet:
                    logger.warning(f"No wallet mapped for user {user_id}")
                    continue
                
                # Build mint transaction
                tx = self.contract.functions.mint(
                    Web3.to_checksum_address(wallet),
                    pending  # Amount in base units (adjust decimals if needed)
                ).build_transaction({
                    'from': account.address,
                    'nonce': self.w3.eth.get_transaction_count(account.address),
                    'gas': 200000,
                    'gasPrice': self.w3.eth.gas_price
                })
                
                # Sign and send
                signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
                tx_hash_hex = tx_hash.hex()
                
                # Wait for confirmation (optional)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                if receipt['status'] == 1:
                    # Update Firestore: mark as minted
                    await self._mark_minted(user_id, pending, tx_hash_hex)
                    results[user_id] = tx_hash_hex
                    logger.info(
                        f"Minted {pending} CPT to {user_id}: {tx_hash_hex}"
                    )
                else:
                    logger.error(f"Transaction failed for {user_id}: {tx_hash_hex}")
                    
            except Exception as e:
                logger.error(f"Error minting for {user_id}: {e}")
        
        return results
    
    async def burn_expired(self, days: int = 30) -> int:
        """
        Burn on-chain tokens for inactive users.
        
        This requires a burn function in the smart contract that can be
        called by authorized accounts.
        """
        if not self.contract:
            logger.warning("Contract not configured - using Firestore burn only")
            return await self.firestore.burn_expired(days)
        
        # TODO: Implement on-chain burn via contract.functions.burnInactive()
        # For now, just burn in Firestore
        return await self.firestore.burn_expired(days)
    
    def _user_id_to_wallet(self, user_id: str) -> Optional[str]:
        """
        Map user_id to wallet address.
        
        In production, this should query a user_wallets table in Firestore
        or use web3-oauth mapping.
        
        For now, returns None (needs implementation).
        """
        # TODO: Implement wallet mapping
        # Option 1: Query Firestore collection "user_wallets"
        # Option 2: Use web3-oauth linkage
        # Option 3: Direct from Supabase profiles table
        logger.warning(f"Wallet mapping not implemented for user {user_id}")
        return None
    
    async def _mark_minted(self, user_id: str, amount: int, tx_hash: str):
        """Update Firestore to reflect minted tokens."""
        from google.cloud import firestore
        
        balance_ref = self.firestore.balances_col.document(user_id)
        await balance_ref.update({
            "pending_blockchain": firestore.Increment(-amount),
            "last_mint": firestore.SERVER_TIMESTAMP,
            "last_mint_tx": tx_hash
        })
        
        # Log mint action
        await self.firestore.actions_col.add({
            "user_id": user_id,
            "action_type": "minted_on_chain",
            "points": amount,
            "metadata": {"tx_hash": tx_hash},
            "timestamp": firestore.SERVER_TIMESTAMP,
            "blockchain_pending": False,
            "tx_hash": tx_hash
        })

