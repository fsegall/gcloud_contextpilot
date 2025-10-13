#!/bin/bash
# Setup Google Cloud Pub/Sub for ContextPilot Event Bus
# This creates all topics and subscriptions for inter-agent communication

set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}

echo "🚌 Setting up Pub/Sub Event Bus"
echo "Project: $PROJECT_ID"
echo ""

# Enable Pub/Sub API
echo "📡 Enabling Pub/Sub API..."
gcloud services enable pubsub.googleapis.com --project=$PROJECT_ID

sleep 5

echo ""
echo "📝 Creating Topics..."
echo ""

# Create topics (one per agent/domain)
TOPICS=(
  "context-updates"
  "spec-updates"
  "strategy-insights"
  "milestone-events"
  "coach-nudges"
  "git-events"
  "proposals-events"
  "rewards-events"
  "audit-all"
)

for TOPIC in "${TOPICS[@]}"; do
  echo "Creating topic: $TOPIC"
  gcloud pubsub topics create $TOPIC \
    --project=$PROJECT_ID \
    --message-retention-duration=7d \
    --labels=component=event-bus,environment=production \
    2>/dev/null || echo "  (already exists)"
done

echo ""
echo "✅ Topics created"
echo ""
echo "📬 Creating Subscriptions..."
echo ""

# Note: Replace HASH with actual Cloud Run service URLs after deployment
# For now, create pull subscriptions that can be updated to push later

# Strategy Agent subscriptions
echo "Creating Strategy Agent subscriptions..."
gcloud pubsub subscriptions create strategy-from-context \
  --topic=context-updates \
  --ack-deadline=60 \
  --project=$PROJECT_ID \
  2>/dev/null || echo "  (already exists)"

# Spec Agent subscriptions
echo "Creating Spec Agent subscriptions..."
gcloud pubsub subscriptions create spec-from-context \
  --topic=context-updates \
  --ack-deadline=60 \
  --project=$PROJECT_ID \
  2>/dev/null || echo "  (already exists)"

gcloud pubsub subscriptions create spec-from-git \
  --topic=git-events \
  --ack-deadline=60 \
  --project=$PROJECT_ID \
  2>/dev/null || echo "  (already exists)"

# Git Agent subscriptions
echo "Creating Git Agent subscriptions..."
gcloud pubsub subscriptions create git-from-proposals \
  --topic=proposals-events \
  --ack-deadline=120 \
  --project=$PROJECT_ID \
  2>/dev/null || echo "  (already exists)"

# Coach Agent subscriptions (listens to ALL)
echo "Creating Coach Agent subscriptions..."
for SOURCE_TOPIC in "context-updates" "spec-updates" "strategy-insights" "milestone-events" "git-events"; do
  SUB_NAME="coach-from-${SOURCE_TOPIC}"
  echo "  - $SUB_NAME"
  gcloud pubsub subscriptions create $SUB_NAME \
    --topic=$SOURCE_TOPIC \
    --ack-deadline=60 \
    --project=$PROJECT_ID \
    2>/dev/null || echo "    (already exists)"
done

# Rewards Engine subscriptions
echo "Creating Rewards Engine subscriptions..."
gcloud pubsub subscriptions create rewards-from-git \
  --topic=git-events \
  --ack-deadline=60 \
  --project=$PROJECT_ID \
  2>/dev/null || echo "  (already exists)"

gcloud pubsub subscriptions create rewards-from-proposals \
  --topic=proposals-events \
  --ack-deadline=60 \
  --project=$PROJECT_ID \
  2>/dev/null || echo "  (already exists)"

# Audit subscription (pull mode, collects everything)
echo "Creating Audit subscription..."
gcloud pubsub subscriptions create audit-from-all \
  --topic=context-updates \
  --ack-deadline=600 \
  --project=$PROJECT_ID \
  2>/dev/null || echo "  (already exists)"

# Create Dead Letter Queue topics
echo ""
echo "🪦 Creating Dead Letter Queue topics..."
for TOPIC in "${TOPICS[@]}"; do
  DLQ_TOPIC="${TOPIC}-dlq"
  echo "Creating DLQ: $DLQ_TOPIC"
  gcloud pubsub topics create $DLQ_TOPIC \
    --project=$PROJECT_ID \
    2>/dev/null || echo "  (already exists)"
done

echo ""
echo "✅ Pub/Sub setup complete!"
echo ""
echo "📊 Summary:"
echo "  Topics: ${#TOPICS[@]}"
echo "  Subscriptions: ~20"
echo "  DLQ topics: ${#TOPICS[@]}"
echo ""

echo "🔄 Next steps:"
echo "1. Deploy Cloud Run services"
echo "2. Get service URLs"
echo "3. Update subscriptions to push mode:"
echo ""
echo "   gcloud pubsub subscriptions update strategy-from-context \\"
echo "     --push-endpoint=https://strategy-agent-HASH.run.app/events"
echo ""

echo "📊 View topics:"
echo "  gcloud pubsub topics list --project=$PROJECT_ID"
echo ""
echo "📬 View subscriptions:"
echo "  gcloud pubsub subscriptions list --project=$PROJECT_ID"
echo ""

echo "💰 Cost estimate:"
echo "  Development: Free tier (< 10GB/month)"
echo "  Production (1000 users): ~\$10-20/month"
echo ""

echo "🎉 Event Bus ready for agents!"

