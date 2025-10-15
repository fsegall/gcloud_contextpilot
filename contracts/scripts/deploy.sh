#!/bin/bash
# Deploy CPT smart contract to Ethereum Sepolia testnet

set -e

echo "🚀 Deploying CPT Contract to Sepolia..."

# Load environment variables
source .env

# Compile contracts
echo "📝 Compiling contracts..."
forge build

# Run tests
echo "🧪 Running tests..."
forge test -vv

# Deploy to Sepolia testnet
echo "🌐 Deploying to Sepolia testnet..."
forge script script/Deploy.s.sol:DeployCPT \
  --rpc-url $SEPOLIA_RPC_URL \
  --broadcast \
  --verify \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  -vvvv

# Extract deployed address
CONTRACT_ADDRESS=$(forge script script/Deploy.s.sol:DeployCPT \
  --rpc-url $SEPOLIA_RPC_URL \
  --broadcast \
  --verify \
  --json | jq -r '.returns.token.value')

echo "✅ Contract deployed to: $CONTRACT_ADDRESS"

# Export ABI for backend
echo "📤 Exporting ABI..."
forge inspect CPT abi > ../back-end/app/adapters/rewards/CPT_ABI.json

echo "✅ ABI exported to backend"

# Update .env with contract address
echo ""
echo "📋 Add this to your backend .env:"
echo "CPT_CONTRACT_ADDRESS=$CONTRACT_ADDRESS"
echo "CPT_CONTRACT_SEPOLIA=$CONTRACT_ADDRESS"

echo ""
echo "🎉 Deployment complete!"
echo "View on Etherscan: https://sepolia.etherscan.io/address/$CONTRACT_ADDRESS"

