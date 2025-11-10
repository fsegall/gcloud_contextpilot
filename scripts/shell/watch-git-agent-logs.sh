#!/bin/bash
# Monitor Git Agent logs from Cloud Run
# Usage: ./scripts/shell/watch-git-agent-logs.sh [minutes]

set -e

FRESHNESS="${1:-30}"  # Default: last 30 minutes
PROJECT_ID="${GCP_PROJECT_ID:-gen-lang-client-0805532064}"

echo "🔍 Monitoring Git Agent logs from Cloud Run"
echo "📊 Project: $PROJECT_ID"
echo "⏰ Time range: Last $FRESHNESS minutes"
echo ""

# Try to use tail if available, otherwise use read with polling
if command -v gcloud &> /dev/null; then
    # Try beta/alpha logging tail first
    if gcloud beta logging tail "resource.type=cloud_run_revision AND textPayload:\"GitAgent\"" --project="$PROJECT_ID" 2>/dev/null; then
        exit 0
    elif gcloud alpha logging tail "resource.type=cloud_run_revision AND textPayload:\"GitAgent\"" --project="$PROJECT_ID" 2>/dev/null; then
        exit 0
    fi
fi

# Fallback: Polling mode
echo "📡 Using polling mode (checking every 5 seconds)..."
echo ""

LAST_CHECK=$(date -u +%Y-%m-%dT%H:%M:%SZ)

while true; do
    CURRENT_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # Get logs since last check
    LOGS=$(gcloud logging read \
        "resource.type=cloud_run_revision AND textPayload:\"GitAgent\" AND timestamp>=\"$LAST_CHECK\"" \
        --project="$PROJECT_ID" \
        --limit=50 \
        --format="table(timestamp,textPayload)" \
        --freshness="${FRESHNESS}m" 2>/dev/null || echo "")
    
    if [ -n "$LOGS" ] && [ "$LOGS" != "TIMESTAMP  TEXT_PAYLOAD" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$LOGS" | grep -v "^TIMESTAMP" | head -20
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    fi
    
    LAST_CHECK="$CURRENT_TIME"
    sleep 5
done

