#!/bin/bash

# Test Agent Retrospective in Cloud Run (Production)

set -e

# Get backend URL from Cloud Run
BACKEND_URL=$(gcloud run services describe contextpilot-backend \
    --region us-central1 \
    --format='value(status.url)' 2>/dev/null)

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend not deployed to Cloud Run"
    exit 1
fi

echo "🚀 Testing ContextPilot in Production"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Backend URL: $BACKEND_URL"
echo ""

# Test 1: Health check
echo "1️⃣  Testing health endpoint..."
if curl -s "$BACKEND_URL/health" | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

echo ""

# Test 2: Trigger retrospective with real agents and LLM
echo "2️⃣  Triggering Agent Retrospective (with Pub/Sub + Firestore + LLM)..."
RESPONSE=$(curl -s -X POST "$BACKEND_URL/agents/retrospective/trigger?workspace_id=production-test" \
    -H "Content-Type: application/json" \
    -d '{
        "trigger": "How can we improve code quality and testing coverage?",
        "use_llm": true
    }')

echo "Response:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

# Check if retrospective was created
RETRO_ID=$(echo "$RESPONSE" | jq -r '.retrospective_id // empty' 2>/dev/null)

if [ -n "$RETRO_ID" ]; then
    echo ""
    echo "✅ Retrospective created: $RETRO_ID"
    
    # Extract key information
    echo ""
    echo "📊 Agent Metrics:"
    echo "$RESPONSE" | jq '.agent_metrics // {}' 2>/dev/null
    
    echo ""
    echo "💡 Insights:"
    echo "$RESPONSE" | jq -r '.insights[]? // "No insights"' 2>/dev/null | head -5
    
    echo ""
    echo "🎯 Proposal ID:"
    echo "$RESPONSE" | jq -r '.proposal_id // "No proposal"' 2>/dev/null
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Agent Retrospective WORKING in production!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "❌ Retrospective failed to create"
    exit 1
fi

# Test 3: Check Pub/Sub activity
echo ""
echo "3️⃣  Checking Pub/Sub activity..."
MESSAGES=$(gcloud pubsub subscriptions pull retrospective-agent-sub \
    --limit 5 \
    --format="value(message.data)" 2>/dev/null || echo "")

if [ -n "$MESSAGES" ]; then
    echo "✅ Pub/Sub messages detected"
else
    echo "⚠️  No Pub/Sub messages (may be normal for new deployment)"
fi

# Test 4: Check Cloud Run logs
echo ""
echo "4️⃣  Checking recent logs..."
echo "Recent retrospective activity:"
gcloud run logs read contextpilot-backend \
    --region us-central1 \
    --limit 10 \
    --format="value(textPayload)" 2>/dev/null | grep -i "retrospective" | tail -5 || echo "No logs yet"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Production Testing Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Backend URL: $BACKEND_URL"
echo "🔗 Health: $BACKEND_URL/health"
echo "📖 API Docs: $BACKEND_URL/docs"
echo ""
echo "🎯 Ready for Hackathon Demo!"

