#!/bin/bash
# Deploy ContextPilot Backend to Google Cloud Run
# Usage: ./deploy.sh [environment]
#   environment: dev (local) or prod (cloud run)

set -e

ENVIRONMENT="${1:-prod}"
PROJECT_ID="gen-lang-client-0805532064"
REGION="us-central1"
SERVICE_NAME="contextpilot-backend"

echo "🚀 Deploying ContextPilot Backend to Google Cloud Run..."
echo "   Environment: $ENVIRONMENT"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

if [ "$ENVIRONMENT" = "dev" ]; then
    echo "⚠️  Development mode: Running locally with uvicorn..."
    echo ""
    
    # Load dev environment variables
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Run local server
    python3 -m uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
    
elif [ "$ENVIRONMENT" = "prod" ]; then
    echo "☁️  Production mode: Deploying to Cloud Run..."
    echo ""
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo "❌ Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi
    
    # Deploy to Cloud Run
    gcloud run deploy $SERVICE_NAME \
        --source . \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars="STORAGE_MODE=cloud,EVENT_BUS_MODE=pubsub,GCP_PROJECT_ID=$PROJECT_ID,ENVIRONMENT=production,USE_PUBSUB=true" \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --max-instances 10 \
        --project $PROJECT_ID
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format='value(status.url)')
    
    echo ""
    echo "✅ Deployment complete!"
    echo "   Service URL: $SERVICE_URL"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Test the API: curl $SERVICE_URL/health"
    echo "   2. Update extension config with new URL"
    echo "   3. Monitor logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit 50"
    echo ""
    
else
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "   Usage: ./deploy.sh [dev|prod]"
    exit 1
fi




