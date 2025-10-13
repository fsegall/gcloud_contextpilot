#!/bin/bash
# Master setup script for ContextPilot infrastructure
# Runs all setup scripts in correct order

set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-us-central1}

echo "🚀 ContextPilot - Complete Infrastructure Setup"
echo "=============================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is configured
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GCP_PROJECT_ID not set and no default project configured"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Setup Plan:"
echo "  1. Enable required GCP APIs"
echo "  2. Setup Pub/Sub (Event Bus)"
echo "  3. Setup Google Blockchain Node Engine"
echo "  4. Create Firestore database"
echo "  5. Setup Secret Manager secrets"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Step 1: Enable APIs
echo ""
echo "📡 Step 1: Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  pubsub.googleapis.com \
  blockchainnode.googleapis.com \
  --project=$PROJECT_ID

echo "✅ APIs enabled"

# Step 2: Pub/Sub
echo ""
echo "🚌 Step 2: Setting up Pub/Sub..."
./setup-pubsub.sh

# Step 3: GCNE (runs async)
echo ""
echo "🔗 Step 3: Setting up Google Blockchain Node Engine..."
echo "⚠️  This takes ~15 minutes. Script will continue in background."
./setup-gcne.sh &
GCNE_PID=$!

# Step 4: Firestore
echo ""
echo "💾 Step 4: Setting up Firestore..."
if gcloud firestore databases describe --project=$PROJECT_ID &>/dev/null; then
    echo "  Firestore already exists ✓"
else
    echo "  Creating Firestore database..."
    gcloud firestore databases create \
      --location=$REGION \
      --project=$PROJECT_ID \
      --type=firestore-native
    echo "✅ Firestore created"
fi

# Step 5: Secret Manager (placeholders)
echo ""
echo "🔐 Step 5: Setting up Secret Manager..."

# Helper function to create or update secret
create_or_update_secret() {
    SECRET_NAME=$1
    SECRET_VALUE=$2
    
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
        echo "  Updating $SECRET_NAME..."
        echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME \
          --data-file=- \
          --project=$PROJECT_ID
    else
        echo "  Creating $SECRET_NAME..."
        echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME \
          --data-file=- \
          --project=$PROJECT_ID
    fi
}

# Create placeholder secrets (you'll update these later)
create_or_update_secret "gcp-project-id" "$PROJECT_ID"
create_or_update_secret "polygon-rpc-url" "https://rpc-mumbai.maticvigil.com"

echo ""
echo "⚠️  You need to manually set these secrets:"
echo ""
echo "  1. OpenAI API key:"
echo "     echo -n 'YOUR_KEY' | gcloud secrets create openai-api-key --data-file=-"
echo ""
echo "  2. CPT Contract address (after deploying):"
echo "     echo -n '0x...' | gcloud secrets create cpt-contract-address --data-file=-"
echo ""
echo "  3. Minter private key (after creating wallet):"
echo "     echo -n 'YOUR_KEY' | gcloud secrets create minter-private-key --data-file=-"
echo ""

# Wait for GCNE setup
echo ""
echo "⏳ Waiting for GCNE setup to complete..."
wait $GCNE_PID

echo ""
echo "🎉 Infrastructure setup complete!"
echo ""
echo "📊 Summary:"
echo "  ✅ APIs enabled"
echo "  ✅ Pub/Sub configured (8 topics, ~20 subscriptions)"
echo "  ✅ GCNE nodes created (check status in ~15 min)"
echo "  ✅ Firestore database ready"
echo "  ⚠️  Secrets need manual configuration"
echo ""
echo "🚀 Next steps:"
echo "  1. Deploy smart contract:"
echo "     cd ../contracts && ./scripts/deploy.sh"
echo ""
echo "  2. Update secrets with real values"
echo ""
echo "  3. Deploy backend to Cloud Run:"
echo "     gcloud builds submit --config cloudbuild.yaml"
echo ""
echo "  4. Test everything:"
echo "     ./test-infra.sh"
echo ""

echo "📝 Check status anytime:"
echo "  Pub/Sub: gcloud pubsub topics list"
echo "  GCNE: gcloud blockchain-nodes list --location=$REGION"
echo "  Firestore: gcloud firestore databases list"
echo ""

echo "✨ Ready to build agents!"

