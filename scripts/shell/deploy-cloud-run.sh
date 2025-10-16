#!/bin/bash
# Deploy ContextPilot Backend to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ContextPilot - Cloud Run Deployment${NC}"
echo "========================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Get project ID
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ GCP_PROJECT_ID not set. Please set it or configure gcloud default project.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Using project: ${YELLOW}$PROJECT_ID${NC}"

# Configuration
SERVICE_NAME="contextpilot-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo ""
echo -e "${BLUE}📋 Configuration:${NC}"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Image: $IMAGE_NAME:latest"
echo ""

# Step 1: Enable required APIs
echo -e "${BLUE}1️⃣ Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --project=$PROJECT_ID

echo -e "${GREEN}✓${NC} APIs enabled"

# Step 2: Build Docker image
echo ""
echo -e "${BLUE}2️⃣ Building Docker image...${NC}"
cd "$(dirname "$0")/../../back-end"

docker build -t $IMAGE_NAME:latest .

echo -e "${GREEN}✓${NC} Image built successfully"

# Step 3: Push to Google Container Registry
echo ""
echo -e "${BLUE}3️⃣ Pushing image to Container Registry...${NC}"

# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker --quiet

docker push $IMAGE_NAME:latest

echo -e "${GREEN}✓${NC} Image pushed successfully"

# Step 4: Deploy to Cloud Run
echo ""
echo -e "${BLUE}4️⃣ Deploying to Cloud Run...${NC}"

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_API_KEY not set. Gemini API will not work.${NC}"
    echo "   Set it with: export GOOGLE_API_KEY=your-key"
fi

gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 300 \
    --set-env-vars "USE_PUBSUB=true,FIRESTORE_ENABLED=false,ENVIRONMENT=production" \
    --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
    --project=$PROJECT_ID

echo -e "${GREEN}✓${NC} Deployment complete!"

# Step 5: Get service URL
echo ""
echo -e "${BLUE}5️⃣ Getting service URL...${NC}"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)' \
    --project=$PROJECT_ID)

echo ""
echo -e "${GREEN}✅ ContextPilot Backend is live!${NC}"
echo ""
echo -e "${BLUE}Service URL:${NC}"
echo "  $SERVICE_URL"
echo ""
echo -e "${BLUE}Test endpoints:${NC}"
echo "  Health: curl $SERVICE_URL/health"
echo "  Agents: curl $SERVICE_URL/agents/status"
echo ""

# Step 6: Test health endpoint
echo -e "${BLUE}6️⃣ Testing health endpoint...${NC}"
sleep 5 # Wait for service to be ready

if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo -e "${GREEN}✓${NC} Health check passed!"
else
    echo -e "${YELLOW}⚠️  Health check failed. Service may still be starting up.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Update extension API URL to: $SERVICE_URL"
echo "  2. Configure Pub/Sub (run scripts/shell/setup-pubsub.sh)"
echo "  3. Enable Firestore and update env vars"
echo ""

