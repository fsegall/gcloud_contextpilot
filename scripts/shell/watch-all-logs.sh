#!/bin/bash
# Watch ALL Cloud Run logs in real-time (useful for debugging)

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

echo -e "${BLUE}🔍 Watching ALL Cloud Run Logs${NC}"
echo -e "${CYAN}Project:${NC} $PROJECT_ID"
echo -e "${CYAN}Service:${NC} $SERVICE_NAME"
echo -e "${CYAN}Region:${NC} $REGION"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop watching${NC}"
echo ""

# Suppress Python warnings (pkg_resources deprecation warning from gcloud CLI)
export PYTHONWARNINGS="ignore::UserWarning"

# Stream all logs - try beta first, then alpha, then polling
if gcloud beta logging tail --help > /dev/null 2>&1; then
    echo -e "${GREEN}Using: gcloud beta logging tail${NC}"
    echo ""
    gcloud beta logging tail \
        "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
        --project=$PROJECT_ID \
        --format="table(timestamp,severity,textPayload)" \
        2>/dev/null
elif gcloud alpha logging tail --help > /dev/null 2>&1; then
    echo -e "${YELLOW}Using: gcloud alpha logging tail${NC}"
    echo ""
    gcloud alpha logging tail \
        "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
        --project=$PROJECT_ID \
        --format="table(timestamp,severity,textPayload)" \
        2>/dev/null
else
    echo -e "${YELLOW}⚠️  'gcloud logging tail' not available. Using polling mode instead...${NC}"
    echo -e "${CYAN}This will check for new logs every 5 seconds${NC}"
    echo ""
    
    # Polling mode
    LAST_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    while true; do
        CURRENT_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        
        gcloud logging read \
            "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND timestamp>=\"$LAST_TIMESTAMP\"" \
            --project=$PROJECT_ID \
            --limit=100 \
            --format="table(timestamp,severity,textPayload)" \
            --order=asc
        
        LAST_TIMESTAMP=$CURRENT_TIMESTAMP
        sleep 5
    done
fi

