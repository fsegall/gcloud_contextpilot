#!/bin/bash
# Demo script for Retrospective Agent + Tests
# Shows the two "killer features" for the hackathon

set -e

echo "🎯 ContextPilot Hackathon Demo: Agent Retrospectives + Tests"
echo "=============================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo -e "${BLUE}1️⃣  Checking backend health...${NC}"
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✅ Backend is running!${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not running. Start with: uvicorn app.server:app --reload${NC}"
    exit 1
fi
echo ""

# Trigger a retrospective
echo -e "${BLUE}2️⃣  Triggering Agent Retrospective...${NC}"
echo "This simulates agents having a 'meeting' to discuss their work."
echo ""

RETRO_RESPONSE=$(curl -s -X POST http://localhost:8000/agents/retrospective/trigger \
  -H "Content-Type: application/json" \
  -d '{"trigger": "demo", "use_llm": false}')

echo "$RETRO_RESPONSE" | jq '.'
echo ""

# Extract retrospective ID
RETRO_ID=$(echo "$RETRO_RESPONSE" | jq -r '.retrospective.retrospective_id // empty')

if [ -n "$RETRO_ID" ]; then
    echo -e "${GREEN}✅ Retrospective created: $RETRO_ID${NC}"
    echo ""
    
    # Show insights
    echo -e "${BLUE}3️⃣  Agent Insights:${NC}"
    echo "$RETRO_RESPONSE" | jq -r '.retrospective.insights[]' | while read -r insight; do
        echo "   • $insight"
    done
    echo ""
    
    # Show action items
    echo -e "${BLUE}4️⃣  Action Items:${NC}"
    echo "$RETRO_RESPONSE" | jq -r '.retrospective.action_items[] | "   [\(.priority | ascii_upcase)] \(.action)"'
    echo ""
    
    # Show where it's saved
    echo -e "${BLUE}5️⃣  Retrospective saved to:${NC}"
    echo "   📁 ../workspaces/default/retrospectives/$RETRO_ID.json"
    echo "   📄 ../workspaces/default/retrospectives/$RETRO_ID.md"
    echo ""
else
    echo -e "${YELLOW}⚠️  Retrospective creation failed. Check logs.${NC}"
fi

# List all retrospectives
echo -e "${BLUE}6️⃣  Listing all retrospectives...${NC}"
curl -s http://localhost:8000/agents/retrospective/list | jq '.retrospectives[] | "   • \(.retrospective_id) (\(.trigger)) - \(.insights_count) insights, \(.action_items_count) actions"'
echo ""

# Run tests
echo -e "${BLUE}7️⃣  Running Unit Tests (pytest)...${NC}"
echo "This shows we have professional-grade testing for all API endpoints."
echo ""

if command -v pytest &> /dev/null; then
    pytest tests/test_server.py::test_health_check -v
    pytest tests/test_server.py::test_trigger_retrospective -v
    echo ""
    echo -e "${GREEN}✅ Tests passed! Full suite: pytest -v${NC}"
else
    echo -e "${YELLOW}⚠️  pytest not installed. Install with: pip install -r requirements.txt${NC}"
    echo "Test file created at: tests/test_server.py (30+ tests)"
fi
echo ""

echo "=============================================================="
echo -e "${GREEN}🎉 Demo complete!${NC}"
echo ""
echo "Key takeaways for judges:"
echo "  1. 🤖 Agents have 'retrospectives' - they learn from each other"
echo "  2. 📊 Sophisticated cross-agent coordination and metrics"
echo "  3. ✅ Professional test suite with 30+ API endpoint tests"
echo "  4. 🚀 Production-ready code quality"
echo ""
echo "For video: Show retrospective JSON/MD files + test output"

