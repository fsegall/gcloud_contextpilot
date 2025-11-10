#!/bin/bash
# Get recent retrospective logs (last N minutes)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project configured. Run: gcloud config set project PROJECT_ID${NC}"
    exit 1
fi

SERVICE_NAME="contextpilot-backend"
REGION="us-central1"

# Default to last 10 minutes, but allow override
MINUTES=${1:-10}
LIMIT=${2:-100}

echo -e "${BLUE}📋 Recent Retrospective Logs (last $MINUTES minutes)${NC}"
echo -e "${CYAN}Project:${NC} $PROJECT_ID"
echo -e "${CYAN}Service:${NC} $SERVICE_NAME"
echo -e "${CYAN}Limit:${NC} $LIMIT entries"
echo ""

# Calculate timestamp for N minutes ago (works on Linux and macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TIMESTAMP=$(date -u -v-${MINUTES}M +%Y-%m-%dT%H:%M:%SZ)
else
    # Linux
    TIMESTAMP=$(date -u -d "$MINUTES minutes ago" +%Y-%m-%dT%H:%M:%SZ)
fi

# Get recent logs - using simpler filter
echo -e "${CYAN}Fetching logs from last $MINUTES minutes...${NC}"
echo ""

gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND timestamp>=\"$TIMESTAMP\"" \
    --project=$PROJECT_ID \
    --limit=$LIMIT \
    --format="table(timestamp,severity,textPayload)" \
    --order=desc \
    | grep -i -E "(retrospective|RetrospectiveAgent|LLM|Gemini|use_llm|ERROR|WARNING|timeout|API.*retrospective)" || echo "No matching logs found."

echo ""
echo -e "${GREEN}✅ Done${NC}"

