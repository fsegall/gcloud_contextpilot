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

# Load environment variables from consolidated .env (if present)
ENV_FILE="$(dirname "$0")/../../.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${BLUE}📦 Loading environment from ${ENV_FILE}${NC}"
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo -e "${YELLOW}⚠️  .env not found at ${ENV_FILE}. Make sure required variables are set manually.${NC}"
fi

# Auto-detect firestore-service-account.json in project root if not already set
PROJECT_ROOT="$(dirname "$0")/../.."
FIRESTORE_SA_FILE="$PROJECT_ROOT/firestore-service-account.json"
if [ -z "$FIRESTORE_CREDENTIALS_JSON" ] && [ -f "$FIRESTORE_SA_FILE" ]; then
    echo -e "${BLUE}🔑 Auto-detected firestore-service-account.json, exporting FIRESTORE_CREDENTIALS_JSON${NC}"
    export FIRESTORE_CREDENTIALS_JSON="$FIRESTORE_SA_FILE"
fi

# Helper to ensure secrets exist and contain latest values
ensure_secret() {
    local secret_name=$1
    local secret_value=$2

    if [ -z "$secret_value" ]; then
        echo -e "${YELLOW}⚠️  Skipping secret ${secret_name}: value not set in environment.${NC}"
        return
    fi

    if ! gcloud secrets describe "$secret_name" --project "$PROJECT_ID" >/dev/null 2>&1; then
        echo -e "${BLUE}🔐 Creating secret ${secret_name}${NC}"
        gcloud secrets create "$secret_name" \
            --project "$PROJECT_ID" \
            --replication-policy="automatic" >/dev/null
    fi

    echo -e "${BLUE}📥 Updating secret ${secret_name}${NC}"
    if [ -f "$secret_value" ]; then
        echo -e "${BLUE}📥 Updating secret ${secret_name} from file ${secret_value}${NC}"
        gcloud secrets versions add "$secret_name" \
            --project "$PROJECT_ID" \
            --data-file="$secret_value" >/dev/null
    else
        echo -e "${BLUE}📥 Updating secret ${secret_name} from environment variable${NC}"
        echo -n "$secret_value" | gcloud secrets versions add "$secret_name" \
            --project "$PROJECT_ID" \
            --data-file=- >/dev/null
    fi

    # Grant accessor role to Cloud Run compute service account
    local sa="${PROJECT_ID}-compute@developer.gserviceaccount.com"
    gcloud secrets add-iam-policy-binding "$secret_name" \
        --project "$PROJECT_ID" \
        --member "serviceAccount:${sa}" \
        --role roles/secretmanager.secretAccessor >/dev/null 2>&1 || true
}

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

# Sync secrets from environment before deploy
ensure_secret "GOOGLE_API_KEY" "$GOOGLE_API_KEY"
ensure_secret "GEMINI_API_KEY" "$GEMINI_API_KEY"
ensure_secret "SANDBOX_REPO_URL" "$SANDBOX_REPO_URL"
ensure_secret "GITHUB_TOKEN" "$GITHUB_TOKEN"
ensure_secret "PERSONAL_GITHUB_TOKEN" "$PERSONAL_GITHUB_TOKEN"
ensure_secret "CODESPACES_REPO" "$CODESPACES_REPO"
ensure_secret "FIRESTORE_CREDENTIALS_JSON" "$FIRESTORE_CREDENTIALS_JSON"

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
    --set-env-vars "ENVIRONMENT=production,STORAGE_MODE=cloud,REWARDS_MODE=firestore,EVENT_BUS_MODE=pubsub,USE_PUBSUB=true,GCP_PROJECT_ID=$PROJECT_ID,SANDBOX_ENABLED=true,CODESPACES_ENABLED=true" \
    --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,SANDBOX_REPO_URL=SANDBOX_REPO_URL:latest,GITHUB_TOKEN=GITHUB_TOKEN:latest,CODESPACES_REPO=CODESPACES_REPO:latest,PERSONAL_GITHUB_TOKEN=PERSONAL_GITHUB_TOKEN:latest,FIRESTORE_CREDENTIALS_JSON=FIRESTORE_CREDENTIALS_JSON:latest" \
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

