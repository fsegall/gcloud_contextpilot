#!/bin/bash
# Deploy CPT smart contract to Polygon Mumbai testnet

set -e

echo "🚀 Deploying CPT Contract to Polygon Mumbai..."

# Load environment variables
source .env

# Compile contracts
echo "📝 Compiling contracts..."
forge build

# Run tests
echo "🧪 Running tests..."
forge test -vv

# Deploy to Mumbai testnet
echo "🌐 Deploying to Mumbai testnet..."
forge script script/Deploy.s.sol:DeployCPT \
  --rpc-url $POLYGON_RPC_URL \
  --broadcast \
  --verify \
  --etherscan-api-key $POLYGONSCAN_API_KEY \
  -vvvv

# Extract deployed address
CONTRACT_ADDRESS=$(forge script script/Deploy.s.sol:DeployCPT \
  --rpc-url $POLYGON_RPC_URL \
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
echo "CPT_CONTRACT_MUMBAI=$CONTRACT_ADDRESS"

echo ""
echo "🎉 Deployment complete!"
echo "View on PolygonScan: https://mumbai.polygonscan.com/address/$CONTRACT_ADDRESS"

