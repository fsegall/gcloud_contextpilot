# 🚀 CPT Token Deployment

## Contract Information

- **Contract Address**: `0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5`
- **Network**: Ethereum Sepolia Testnet
- **Chain ID**: 11155111
- **Deployer**: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`
- **Deployment Date**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- **Transaction Hash**: Check `contracts/broadcast/Deploy.s.sol/11155111/run-latest.json`

## View on Etherscan

- **Contract**: https://sepolia.etherscan.io/address/0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5
- **Deployer Wallet**: https://sepolia.etherscan.io/address/0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb

## Contract Details

### Token Info
- **Name**: Context Pilot Token
- **Symbol**: CPT
- **Decimals**: 18
- **Initial Supply**: 0 (minted on demand)
- **Max Supply per Cycle**: 1,000,000 CPT

### Roles
- **DEFAULT_ADMIN_ROLE**: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`
- **MINTER_ROLE**: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`
- **BURNER_ROLE**: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`

### Features
✅ ERC-20 compliant
✅ Role-based access control
✅ Pausable (emergency stop)
✅ Monthly cycle renewal
✅ Inactivity burn mechanism (30 days)
✅ Supply limits per cycle

## Environment Variables

Add these to your backend `.env`:

```bash
CPT_CONTRACT_ADDRESS=0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
MINTER_PRIVATE_KEY=0xd6079f053b592cd06e093a900f1fb360fdb44ecf82aa8840421ce7d047704420
```

Add these to your frontend `.env.local`:

```bash
VITE_CPT_CONTRACT_ADDRESS=0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5
VITE_CHAIN_ID=11155111
```

## Interact with Contract

### Using Cast (Foundry)

```bash
# Get total supply
cast call 0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5 "totalSupply()" --rpc-url https://ethereum-sepolia-rpc.publicnode.com

# Get balance of an address
cast call 0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5 "balanceOf(address)(uint256)" YOUR_ADDRESS --rpc-url https://ethereum-sepolia-rpc.publicnode.com

# Mint tokens (requires MINTER_ROLE)
cast send 0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5 "mint(address,uint256)" YOUR_ADDRESS 100000000000000000000 --rpc-url https://ethereum-sepolia-rpc.publicnode.com --private-key $PRIVATE_KEY
```

### Using Python (Web3.py)

See `back-end/app/adapters/rewards/blockchain_rewards.py` for examples.

## Next Steps

1. ✅ Contract deployed
2. ✅ ABI exported to backend
3. ⏳ Verify contract on Etherscan (optional)
4. ⏳ Update frontend env variables
5. ⏳ Test rewards flow
6. ⏳ Deploy backend to Cloud Run
7. ⏳ Test E2E flow

## Verify Contract (Optional)

To verify the contract on Etherscan:

```bash
forge verify-contract \
  --chain-id 11155111 \
  --num-of-optimizations 200 \
  --watch \
  --etherscan-api-key YOUR_ETHERSCAN_API_KEY \
  0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5 \
  src/CPT.sol:CPT
```

---

**Deployment Status**: ✅ **SUCCESS**
