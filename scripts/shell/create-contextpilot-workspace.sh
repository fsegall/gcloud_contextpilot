#!/bin/bash

# Script to create the "contextpilot" workspace via API
# Run this after starting the backend

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏗️  Creating workspace 'contextpilot' via API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if backend is running
echo "🔍 Checking if backend is running..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend is not running!"
    echo ""
    echo "Please start the backend first:"
    echo "  cd back-end"
    echo "  source .venv/bin/activate"
    echo "  python -m uvicorn app.server:app --reload --port 8000"
    echo ""
    exit 1
fi

echo "✅ Backend is running!"
echo ""

# Create workspace
echo "📦 Creating workspace 'contextpilot'..."
echo ""

response=$(curl -s -X POST "http://localhost:8000/generate-context?workspace_id=contextpilot" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "ContextPilot - Multi-Agent Dev Assistant",
    "goal": "Build a multi-agent system that helps developers manage project context, deployed on Google Cloud Run for the Cloud Run Hackathon",
    "initial_status": "Extension integration in progress. Backend API working, smart contract deployed on Sepolia. Next: E2E testing with real workspace.",
    "milestones": [
      {
        "name": "Extension MVP with real API integration",
        "due": "2025-10-16"
      },
      {
        "name": "Multi-agent system fully integrated",
        "due": "2025-10-20"
      },
      {
        "name": "Deploy to Cloud Run",
        "due": "2025-10-25"
      },
      {
        "name": "Beta launch with 50 users",
        "due": "2025-11-01"
      },
      {
        "name": "Hackathon submission",
        "due": "2025-11-10"
      }
    ]
  }')

echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
echo ""

# Verify workspace was created
if [ -d "back-end/.contextpilot/workspaces/contextpilot" ]; then
    echo "✅ Workspace created successfully!"
    echo ""
    echo "📁 Location: back-end/.contextpilot/workspaces/contextpilot/"
    echo ""
    echo "📋 Checkpoint:"
    cat back-end/.contextpilot/workspaces/contextpilot/checkpoint.yaml
    echo ""
    echo "📝 Git log:"
    cd back-end/.contextpilot/workspaces/contextpilot
    git log --oneline -3
    cd - > /dev/null
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Done! Workspace 'contextpilot' is ready to use!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🧪 Test it:"
    echo "  curl 'http://localhost:8000/context?workspace_id=contextpilot'"
    echo ""
else
    echo "❌ Workspace was not created. Check the error above."
    exit 1
fi

