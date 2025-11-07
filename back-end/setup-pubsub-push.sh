#!/bin/bash
# Setup Google Cloud Pub/Sub topics and push subscriptions for ContextPilot
# This configures push subscriptions that send events to Cloud Run /events endpoint

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-gen-lang-client-0805532064}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="contextpilot-backend"

# Get Cloud Run service URL
echo "🔍 Getting Cloud Run service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format='value(status.url)' 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
  echo "❌ Could not find Cloud Run service: $SERVICE_NAME"
  echo "   Please deploy the service first or set SERVICE_URL manually"
  exit 1
fi

PUSH_ENDPOINT="${SERVICE_URL}/events"
echo "✅ Service URL: $SERVICE_URL"
echo "📡 Push endpoint: $PUSH_ENDPOINT"
echo ""

# Enable Pub/Sub API
echo "📡 Enabling Pub/Sub API..."
gcloud services enable pubsub.googleapis.com --project="$PROJECT_ID" --quiet || true

# Topics (based on Topics class in event_bus.py)
echo ""
echo "📬 Creating Pub/Sub topics..."
TOPICS=(
  "git-events"
  "proposal-events"
  "context-events"
  "spec-events"
  "strategy-events"
  "milestone-events"
  "coach-events"
  "retrospective-events"
  "artifact-events"
  "reward-events"
)

for topic in "${TOPICS[@]}"; do
  if gcloud pubsub topics describe "$topic" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Topic $topic already exists"
  else
    gcloud pubsub topics create "$topic" \
      --project="$PROJECT_ID" \
      --message-retention-duration=7d
    echo "  ✅ Created topic: $topic"
  fi
done

echo ""
echo "📥 Creating/updating push subscriptions..."

# Get Cloud Run service account for permissions
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || echo "")

# If no service account, use default compute service account
if [ -z "$SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
fi

echo "   Service account: $SERVICE_ACCOUNT"
echo ""

# Grant Pub/Sub permission to invoke Cloud Run
echo "🔐 Granting Pub/Sub permission to invoke Cloud Run..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --member="serviceAccount:service-$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --quiet || echo "  (permissions may already be set)"

echo ""

# Create one push subscription per topic
# All subscriptions push to the same /events endpoint
# The route_event function will route events to the appropriate agents
echo "📥 Creating push subscriptions for each topic..."
echo ""

for topic in "${TOPICS[@]}"; do
  # Create subscription name: topic-name-sub (e.g., git-events-sub)
  sub_name="${topic}-sub"
  
  echo "📦 Processing subscription: $sub_name -> topic: $topic"
  
  # Check if subscription exists
  if gcloud pubsub subscriptions describe "$sub_name" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Subscription exists, updating to push mode..."
    
    # Update existing subscription to push mode
    gcloud pubsub subscriptions update "$sub_name" \
      --project="$PROJECT_ID" \
      --push-endpoint="$PUSH_ENDPOINT" \
      --ack-deadline=60 \
      --message-retention-duration=7d || echo "  ⚠️  Update failed (may need manual configuration)"
    
    echo "  ✅ Updated subscription: $sub_name"
  else
    # Create new subscription with push endpoint
    echo "  Creating subscription for topic: $topic"
    gcloud pubsub subscriptions create "$sub_name" \
      --topic="$topic" \
      --project="$PROJECT_ID" \
      --push-endpoint="$PUSH_ENDPOINT" \
      --ack-deadline=60 \
      --message-retention-duration=7d
    
    echo "  ✅ Created subscription: $sub_name"
  fi
  echo ""
done

echo "ℹ️  Note: All subscriptions push to $PUSH_ENDPOINT"
echo "   The route_event function will route events to the appropriate agents"
echo ""

echo ""
echo "✅ Pub/Sub setup complete!"
echo ""
echo "📊 Summary:"
echo "  Topics: ${#TOPICS[@]}"
echo "  Subscriptions: ${#TOPICS[@]} (one per topic)"
echo "  Push endpoint: $PUSH_ENDPOINT"
echo ""
echo "🧪 Test the setup:"
echo "  1. Publish a test event:"
echo "     echo '{\"event_type\":\"git.commit.v1\",\"data\":{\"workspace_id\":\"contextpilot\",\"commit_hash\":\"test123\"}}' | \\"
echo "     gcloud pubsub topics publish git-events --message-file=- --project=$PROJECT_ID"
echo ""
echo "  2. Check Cloud Run logs:"
echo "     gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit 20 --project=$PROJECT_ID"
echo ""

