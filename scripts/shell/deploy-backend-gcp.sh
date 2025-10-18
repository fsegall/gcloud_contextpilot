#!/bin/bash
# Deploy rápido do backend no GCP Cloud Run

set -e

PROJECT_ID="contextpilot"
SERVICE_NAME="contextpilot-backend"
REGION="us-central1"

echo "🚀 Deploy Backend ContextPilot para GCP Cloud Run"
echo "=================================================="
echo ""

# Verificar se gcloud está configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI não encontrado. Instale: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "📦 Projeto: $PROJECT_ID"
echo "🌍 Região: $REGION"
echo "🔧 Serviço: $SERVICE_NAME"
echo ""

# Navegar para a pasta do backend
cd "$(dirname "$0")/back-end"

echo "🔨 Passo 1: Building Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --project=$PROJECT_ID \
    --timeout=10m

echo ""
echo "🚀 Passo 2: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --project=$PROJECT_ID

echo ""
echo "✅ DEPLOY COMPLETO!"
echo ""
echo "🌐 URL do serviço:"
gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)'

echo ""
echo "🔍 Para testar:"
echo "   curl \$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project=$PROJECT_ID --format='value(status.url)')/health"
echo ""







