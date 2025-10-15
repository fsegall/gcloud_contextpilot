#!/bin/bash
# Setup Google Blockchain Node Engine for ContextPilot
# This script creates managed blockchain nodes for Polygon

set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION="us-central1"

echo "🔗 Setting up Google Blockchain Node Engine"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Enable API
echo "📡 Enabling Blockchain Node API..."
gcloud services enable blockchainnodeengine.googleapis.com --project=$PROJECT_ID

# Wait for API to be enabled
sleep 10

# Create Mumbai testnet node
echo ""
echo "🌐 Creating Polygon Mumbai (testnet) node..."
gcloud blockchain-nodes create polygon-mumbai-node \
  --blockchain-node-type=POLYGON_MUMBAI \
  --location=$REGION \
  --project=$PROJECT_ID \
  --async

echo "✅ Mumbai node creation started (this takes ~10-15 minutes)"

# Create Polygon mainnet node (for production)
echo ""
echo "🌐 Creating Polygon Mainnet node..."
gcloud blockchain-nodes create polygon-mainnet-node \
  --blockchain-node-type=POLYGON_MAINNET \
  --location=$REGION \
  --project=$PROJECT_ID \
  --async

echo "✅ Mainnet node creation started (this takes ~10-15 minutes)"

echo ""
echo "⏳ Waiting for nodes to be ready..."
echo "You can check status with:"
echo "  gcloud blockchain-nodes list --location=$REGION"
echo ""

# Function to wait for node
wait_for_node() {
  NODE_NAME=$1
  echo "Waiting for $NODE_NAME..."
  
  for i in {1..30}; do
    STATUS=$(gcloud blockchain-nodes describe $NODE_NAME \
      --location=$REGION \
      --format="value(state)" 2>/dev/null || echo "CREATING")
    
    if [ "$STATUS" = "RUNNING" ]; then
      echo "✅ $NODE_NAME is ready!"
      return 0
    fi
    
    echo "  Status: $STATUS (attempt $i/30)"
    sleep 30
  done
  
  echo "⚠️  $NODE_NAME is taking longer than expected"
  return 1
}

# Wait for both nodes
wait_for_node "polygon-mumbai-node"
wait_for_node "polygon-mainnet-node"

# Get endpoints
echo ""
echo "📋 Node Endpoints:"
echo ""

MUMBAI_ENDPOINT=$(gcloud blockchain-nodes describe polygon-mumbai-node \
  --location=$REGION \
  --format="value(connectionInfo.httpConnectionInfo.uri)" 2>/dev/null || echo "PENDING")

MAINNET_ENDPOINT=$(gcloud blockchain-nodes describe polygon-mainnet-node \
  --location=$REGION \
  --format="value(connectionInfo.httpConnectionInfo.uri)" 2>/dev/null || echo "PENDING")

echo "Mumbai (testnet):"
echo "  $MUMBAI_ENDPOINT"
echo ""
echo "Mainnet (production):"
echo "  $MAINNET_ENDPOINT"
echo ""

# Store in Secret Manager
if [ "$MUMBAI_ENDPOINT" != "PENDING" ]; then
  echo "🔐 Storing endpoints in Secret Manager..."
  
  echo -n "$MUMBAI_ENDPOINT" | gcloud secrets create gcne-mumbai-endpoint \
    --data-file=- \
    --project=$PROJECT_ID \
    2>/dev/null || \
  echo -n "$MUMBAI_ENDPOINT" | gcloud secrets versions add gcne-mumbai-endpoint \
    --data-file=- \
    --project=$PROJECT_ID
  
  echo -n "$MAINNET_ENDPOINT" | gcloud secrets create gcne-mainnet-endpoint \
    --data-file=- \
    --project=$PROJECT_ID \
    2>/dev/null || \
  echo -n "$MAINNET_ENDPOINT" | gcloud secrets versions add gcne-mainnet-endpoint \
    --data-file=- \
    --project=$PROJECT_ID
  
  echo "✅ Endpoints stored in Secret Manager"
fi

# Output .env format
echo ""
echo "📝 Add these to your .env files:"
echo ""
echo "# back-end/.env"
echo "GOOGLE_BLOCKCHAIN_NODE_ENDPOINT=$MUMBAI_ENDPOINT"
echo ""
echo "# front-end/.env"
echo "VITE_GOOGLE_BLOCKCHAIN_NODE_ENDPOINT=$MUMBAI_ENDPOINT"
echo ""

# Cost estimate
echo "💰 Cost Estimate:"
echo "  - Mumbai node: ~\$50/month"
echo "  - Mainnet node: ~\$50/month"
echo "  - Total: ~\$100/month"
echo ""

echo "🎉 Google Blockchain Node Engine setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env files with endpoints above"
echo "2. Redeploy backend: gcloud builds submit"
echo "3. Test connection: curl \$MUMBAI_ENDPOINT -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}'"

