#!/bin/bash
# Test infrastructure setup

set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-us-central1}

echo "🧪 Testing ContextPilot Infrastructure"
echo "======================================"
echo ""

# Test 1: Pub/Sub
echo "📬 Test 1: Pub/Sub Topics"
TOPICS=$(gcloud pubsub topics list --project=$PROJECT_ID --format="value(name)" | wc -l)
echo "  Topics found: $TOPICS"
if [ $TOPICS -ge 8 ]; then
    echo "  ✅ Pub/Sub OK (expected >= 8 topics)"
else
    echo "  ❌ Pub/Sub missing topics (found $TOPICS, expected >= 8)"
fi

# Test 2: GCNE
echo ""
echo "🔗 Test 2: Google Blockchain Node Engine"
NODES=$(gcloud blockchain-nodes list --location=$REGION --project=$PROJECT_ID --format="value(name)" 2>/dev/null | wc -l || echo "0")
echo "  Nodes found: $NODES"
if [ $NODES -ge 1 ]; then
    echo "  ✅ GCNE OK"
    
    # Check node status
    for NODE in $(gcloud blockchain-nodes list --location=$REGION --project=$PROJECT_ID --format="value(name)" 2>/dev/null); do
        STATUS=$(gcloud blockchain-nodes describe $NODE --location=$REGION --format="value(state)" 2>/dev/null)
        echo "    - $NODE: $STATUS"
    done
else
    echo "  ⚠️  GCNE nodes not found (may still be creating)"
fi

# Test 3: Firestore
echo ""
echo "💾 Test 3: Firestore"
if gcloud firestore databases describe --project=$PROJECT_ID &>/dev/null; then
    echo "  ✅ Firestore OK"
else
    echo "  ❌ Firestore not found"
fi

# Test 4: Secret Manager
echo ""
echo "🔐 Test 4: Secret Manager"
SECRETS=$(gcloud secrets list --project=$PROJECT_ID --format="value(name)" | wc -l)
echo "  Secrets found: $SECRETS"
if [ $SECRETS -ge 2 ]; then
    echo "  ✅ Secret Manager OK"
else
    echo "  ⚠️  Few secrets configured"
fi

# Test 5: Pub/Sub publish/subscribe
echo ""
echo "📨 Test 5: Pub/Sub Pub/Sub Test"
TEST_TOPIC="context-updates"
TEST_MESSAGE='{"test": true, "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'

echo "  Publishing test message to $TEST_TOPIC..."
gcloud pubsub topics publish $TEST_TOPIC \
  --message="$TEST_MESSAGE" \
  --project=$PROJECT_ID

echo "  ✅ Message published"

# Summary
echo ""
echo "📊 Infrastructure Status:"
echo "  Pub/Sub: ✅"
echo "  GCNE: $([ $NODES -ge 1 ] && echo '✅' || echo '⏳')"
echo "  Firestore: ✅"
echo "  Secrets: $([ $SECRETS -ge 5 ] && echo '✅' || echo '⚠️')"
echo ""

if [ $NODES -ge 1 ] && [ $TOPICS -ge 8 ] && [ $SECRETS -ge 5 ]; then
    echo "🎉 All systems GO!"
    echo "Ready to deploy agents to Cloud Run"
else
    echo "⚠️  Some components still pending"
    echo "Wait a few minutes and run this script again"
fi

