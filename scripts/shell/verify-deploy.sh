#!/bin/bash
# Verify deployment and test critical features
# Usage: ./scripts/shell/verify-deploy.sh

set -e

PROJECT_ID="${GCP_PROJECT_ID:-gen-lang-client-0805532064}"
SERVICE_NAME="contextpilot-backend"
REGION="us-central1"

echo "🔍 Verificando deploy do ContextPilot Backend..."
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Serviço não encontrado. Verifique se o deploy foi concluído."
    exit 1
fi

echo "✅ Serviço encontrado: $SERVICE_URL"
echo ""

# Test 1: Health endpoint
echo "1️⃣ Testando health endpoint..."
if curl -f -s "$SERVICE_URL/health" | jq -r '.config.event_bus_mode' 2>/dev/null; then
    EVENT_BUS_MODE=$(curl -f -s "$SERVICE_URL/health" | jq -r '.config.event_bus_mode' 2>/dev/null)
    echo "   ✅ Health check OK"
    echo "   📊 Event Bus Mode: $EVENT_BUS_MODE"
    if [ "$EVENT_BUS_MODE" = "pubsub" ]; then
        echo "   ✅ Pub/Sub está configurado!"
    else
        echo "   ⚠️  Event Bus Mode não é 'pubsub' (é: $EVENT_BUS_MODE)"
    fi
else
    echo "   ❌ Health check falhou"
fi
echo ""

# Test 2: Check logs for Git Agent initialization
echo "2️⃣ Verificando logs do Git Agent..."
RECENT_LOGS=$(gcloud logging read \
    "resource.type=cloud_run_revision AND textPayload:\"GitAgent\"" \
    --project=$PROJECT_ID \
    --limit=5 \
    --format="table(timestamp,textPayload)" \
    --freshness=10m 2>/dev/null || echo "")

if [ -n "$RECENT_LOGS" ]; then
    echo "   ✅ Logs do Git Agent encontrados"
    echo "$RECENT_LOGS" | head -5
else
    echo "   ⚠️  Nenhum log do Git Agent encontrado (pode ser normal se não houver eventos)"
fi
echo ""

# Test 3: Check if PubSubEventBus is being used
echo "3️⃣ Verificando se PubSubEventBus está sendo usado..."
PUBSUB_LOGS=$(gcloud logging read \
    "resource.type=cloud_run_revision AND textPayload:\"PubSubEventBus\"" \
    --project=$PROJECT_ID \
    --limit=3 \
    --format="table(timestamp,textPayload)" \
    --freshness=10m 2>/dev/null || echo "")

if [ -n "$PUBSUB_LOGS" ]; then
    echo "   ✅ PubSubEventBus está sendo usado!"
    echo "$PUBSUB_LOGS" | head -3
else
    echo "   ⚠️  Nenhum log do PubSubEventBus encontrado"
    echo "   💡 Isso pode significar que está usando InMemoryEventBus"
fi
echo ""

# Test 4: Check recent deployments
echo "4️⃣ Verificando revisões recentes..."
RECENT_REVISIONS=$(gcloud run revisions list \
    --service=$SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --limit=3 \
    --format="table(metadata.name,status.conditions[0].lastTransitionTime,status.conditions[0].status)" 2>/dev/null || echo "")

if [ -n "$RECENT_REVISIONS" ]; then
    echo "   ✅ Revisões encontradas:"
    echo "$RECENT_REVISIONS"
else
    echo "   ⚠️  Nenhuma revisão encontrada"
fi
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "📋 PRÓXIMOS PASSOS:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Aprovar uma proposal e verificar:"
echo "   - Se o Git Agent recebe o evento"
echo "   - Se a GitHub Action é disparada"
echo "   - Se os logs aparecem corretamente"
echo ""
echo "2. Monitorar logs em tempo real:"
echo "   ./scripts/shell/watch-git-agent-logs.sh 60"
echo ""
echo "3. Verificar se a retrospectiva funciona:"
echo "   - Trigger uma retrospectiva"
echo "   - Verificar se cria proposal corretamente"
echo "   - Verificar se não há erros"
echo ""
echo "✅ Verificação concluída!"

