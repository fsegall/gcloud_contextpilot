#!/bin/bash
# Setup Google Cloud Pub/Sub topics and subscriptions for ContextPilot

set -e

PROJECT_ID="${GCP_PROJECT_ID:-contextpilot-hack-4044}"
REGION="${GCP_REGION:-us-central1}"

echo "🚀 Setting up Pub/Sub for project: $PROJECT_ID"

# Enable Pub/Sub API
echo "📡 Enabling Pub/Sub API..."
gcloud services enable pubsub.googleapis.com --project="$PROJECT_ID"

# Topics to create
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

# Create topics
echo "📬 Creating Pub/Sub topics..."
for topic in "${TOPICS[@]}"; do
    if gcloud pubsub topics describe "$topic" --project="$PROJECT_ID" &>/dev/null; then
        echo "  ✓ Topic $topic already exists"
    else
        gcloud pubsub topics create "$topic" --project="$PROJECT_ID"
        echo "  ✅ Created topic: $topic"
    fi
done

# Create subscriptions (one per agent)
echo "📥 Creating Pub/Sub subscriptions..."

# Spec Agent subscription (listens to git-events, context-events)
SPEC_SUB="spec-agent-sub"
if gcloud pubsub subscriptions describe "$SPEC_SUB" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Subscription $SPEC_SUB already exists"
else
    gcloud pubsub subscriptions create "$SPEC_SUB" \
        --topic="git-events" \
        --project="$PROJECT_ID" \
        --ack-deadline=60 \
        --message-retention-duration=7d
    echo "  ✅ Created subscription: $SPEC_SUB"
fi

# Git Agent subscription (listens to proposal-events)
GIT_SUB="git-agent-sub"
if gcloud pubsub subscriptions describe "$GIT_SUB" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Subscription $GIT_SUB already exists"
else
    gcloud pubsub subscriptions create "$GIT_SUB" \
        --topic="proposal-events" \
        --project="$PROJECT_ID" \
        --ack-deadline=60 \
        --message-retention-duration=7d
    echo "  ✅ Created subscription: $GIT_SUB"
fi

# Strategy Agent subscription (listens to git-events, proposal-events, milestone-events)
STRATEGY_SUB="strategy-agent-sub"
if gcloud pubsub subscriptions describe "$STRATEGY_SUB" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Subscription $STRATEGY_SUB already exists"
else
    gcloud pubsub subscriptions create "$STRATEGY_SUB" \
        --topic="git-events" \
        --project="$PROJECT_ID" \
        --ack-deadline=60 \
        --message-retention-duration=7d
    echo "  ✅ Created subscription: $STRATEGY_SUB"
fi

# Coach Agent subscription (listens to ALL events)
COACH_SUB="coach-agent-sub"
if gcloud pubsub subscriptions describe "$COACH_SUB" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Subscription $COACH_SUB already exists"
else
    gcloud pubsub subscriptions create "$COACH_SUB" \
        --topic="git-events" \
        --project="$PROJECT_ID" \
        --ack-deadline=60 \
        --message-retention-duration=7d
    echo "  ✅ Created subscription: $COACH_SUB"
fi

# Retrospective Agent subscription (listens to all events for analysis)
RETRO_SUB="retrospective-agent-sub"
if gcloud pubsub subscriptions describe "$RETRO_SUB" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Subscription $RETRO_SUB already exists"
else
    gcloud pubsub subscriptions create "$RETRO_SUB" \
        --topic="git-events" \
        --project="$PROJECT_ID" \
        --ack-deadline=60 \
        --message-retention-duration=7d
    echo "  ✅ Created subscription: $RETRO_SUB"
fi

# Create dead letter topic for failed messages
DLQ_TOPIC="dead-letter-queue"
if gcloud pubsub topics describe "$DLQ_TOPIC" --project="$PROJECT_ID" &>/dev/null; then
    echo "  ✓ Dead letter topic already exists"
else
    gcloud pubsub topics create "$DLQ_TOPIC" --project="$PROJECT_ID"
    echo "  ✅ Created dead letter topic: $DLQ_TOPIC"
fi

echo ""
echo "✅ Pub/Sub setup complete!"
echo ""
echo "📊 Summary:"
echo "  Topics created: ${#TOPICS[@]}"
echo "  Subscriptions created: 5"
echo ""
echo "🔍 To view topics:"
echo "  gcloud pubsub topics list --project=$PROJECT_ID"
echo ""
echo "🔍 To view subscriptions:"
echo "  gcloud pubsub subscriptions list --project=$PROJECT_ID"
echo ""
echo "🧪 To test publishing an event:"
echo "  gcloud pubsub topics publish git-events --message='{\"event_type\":\"test\"}' --project=$PROJECT_ID"
echo ""
echo "🎯 To enable in backend, set environment variable:"
echo "  export USE_PUBSUB=true"
echo "  export GCP_PROJECT_ID=$PROJECT_ID"

