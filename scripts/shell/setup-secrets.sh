#!/bin/bash
# Setup Google Secret Manager for ContextPilot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 ContextPilot - Secret Manager Setup${NC}"
echo "========================================"

# Get project ID
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ GCP_PROJECT_ID not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Using project: ${YELLOW}$PROJECT_ID${NC}"

# Enable Secret Manager API
echo ""
echo -e "${BLUE}1️⃣ Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID
echo -e "${GREEN}✓${NC} API enabled"

# Create secrets
echo ""
echo -e "${BLUE}2️⃣ Creating secrets...${NC}"

# GOOGLE_API_KEY (Gemini)
echo ""
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_API_KEY not set in environment${NC}"
    echo -n "Enter your Google API Key (Gemini): "
    read -s GOOGLE_API_KEY
    echo ""
fi

if [ -n "$GOOGLE_API_KEY" ]; then
    echo -n "$GOOGLE_API_KEY" | gcloud secrets create GOOGLE_API_KEY \
        --data-file=- \
        --replication-policy="automatic" \
        --project=$PROJECT_ID 2>/dev/null || \
    echo -n "$GOOGLE_API_KEY" | gcloud secrets versions add GOOGLE_API_KEY \
        --data-file=- \
        --project=$PROJECT_ID
    
    echo -e "${GREEN}✓${NC} GOOGLE_API_KEY stored"
else
    echo -e "${YELLOW}⚠️  Skipping GOOGLE_API_KEY (not provided)${NC}"
fi

# SEPOLIA_PRIVATE_KEY (Blockchain)
echo ""
if [ -f "../../contracts/.env" ]; then
    SEPOLIA_KEY=$(grep PRIVATE_KEY ../../contracts/.env | cut -d '=' -f2)
    if [ -n "$SEPOLIA_KEY" ]; then
        echo -n "$SEPOLIA_KEY" | gcloud secrets create SEPOLIA_PRIVATE_KEY \
            --data-file=- \
            --replication-policy="automatic" \
            --project=$PROJECT_ID 2>/dev/null || \
        echo -n "$SEPOLIA_KEY" | gcloud secrets versions add SEPOLIA_PRIVATE_KEY \
            --data-file=- \
            --project=$PROJECT_ID
        
        echo -e "${GREEN}✓${NC} SEPOLIA_PRIVATE_KEY stored"
    fi
fi

# Grant Cloud Run access to secrets
echo ""
echo -e "${BLUE}3️⃣ Granting Cloud Run access to secrets...${NC}"

PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in GOOGLE_API_KEY SEPOLIA_PRIVATE_KEY; do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID 2>/dev/null || true
done

echo -e "${GREEN}✓${NC} Permissions granted"

# List secrets
echo ""
echo -e "${BLUE}4️⃣ Current secrets:${NC}"
gcloud secrets list --project=$PROJECT_ID

echo ""
echo -e "${GREEN}✅ Secret Manager setup complete!${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} Secrets are now available to Cloud Run via environment variables"
echo ""

