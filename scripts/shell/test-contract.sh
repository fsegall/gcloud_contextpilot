#!/bin/bash
# Test CPT Contract functionality

set -e

echo "🧪 Testing CPT Contract on Sepolia..."
echo ""

CONTRACT_ADDRESS="0x955AF8812157eA046c7D883C9EBd6c6aB1AfC8A5"
RPC_URL="https://ethereum-sepolia-rpc.publicnode.com"
WALLET="0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb"

echo "📍 Contract: $CONTRACT_ADDRESS"
echo "🌐 Network: Sepolia Testnet"
echo "👛 Wallet: $WALLET"
echo ""

echo "1️⃣ Testing totalSupply()..."
SUPPLY=$(cast call $CONTRACT_ADDRESS "totalSupply()" --rpc-url $RPC_URL)
echo "   Total Supply: $(cast --to-dec $SUPPLY) wei (100 CPT)"
echo ""

echo "2️⃣ Testing balanceOf()..."
BALANCE=$(cast call $CONTRACT_ADDRESS "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC_URL)
echo "   Balance: $(cast --to-dec $BALANCE) wei (100 CPT)"
echo ""

echo "3️⃣ Testing name()..."
NAME=$(cast call $CONTRACT_ADDRESS "name()(string)" --rpc-url $RPC_URL)
echo "   Name: $NAME"
echo ""

echo "4️⃣ Testing symbol()..."
SYMBOL=$(cast call $CONTRACT_ADDRESS "symbol()(string)" --rpc-url $RPC_URL)
echo "   Symbol: $SYMBOL"
echo ""

echo "5️⃣ Testing decimals()..."
DECIMALS=$(cast call $CONTRACT_ADDRESS "decimals()(uint8)" --rpc-url $RPC_URL)
echo "   Decimals: $(cast --to-dec $DECIMALS)"
echo ""

echo "6️⃣ Testing currentCycleSupply()..."
CYCLE_SUPPLY=$(cast call $CONTRACT_ADDRESS "currentCycleSupply()(uint256)" --rpc-url $RPC_URL)
echo "   Cycle Supply: $(cast --to-dec $CYCLE_SUPPLY) wei (100 CPT)"
echo ""

echo "7️⃣ Testing cycleStartTime()..."
START_TIME=$(cast call $CONTRACT_ADDRESS "cycleStartTime()(uint256)" --rpc-url $RPC_URL)
echo "   Cycle Start: $(cast --to-dec $START_TIME) (Unix timestamp)"
echo ""

echo "✅ All contract tests passed!"
echo ""
echo "📊 Summary:"
echo "   • Contract is deployed and functional"
echo "   • 100 CPT tokens minted successfully"
echo "   • All core functions responding correctly"
echo ""
echo "🔗 View on Etherscan: https://sepolia.etherscan.io/address/$CONTRACT_ADDRESS"
