#!/bin/bash

# Test script to validate ContextPilot is production-ready
# Run this before submitting to hackathon

set -e

echo "🔍 Testing ContextPilot Production Readiness..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
FAILURES=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((SUCCESS++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILURES++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test 1: Backend structure
echo "📦 Checking Backend Structure..."
if [ -f "back-end/app/server.py" ] && [ -f "back-end/requirements.txt" ]; then
    check_pass "Backend files exist"
else
    check_fail "Backend files missing"
fi

# Test 2: Agent Orchestrator
echo ""
echo "🤖 Checking Agent Orchestrator..."
if [ -f "back-end/app/agents/agent_orchestrator.py" ]; then
    check_pass "Agent orchestrator exists"
    
    # Check for LLM integration
    if grep -q "gemini-2.5-flash-preview" back-end/app/agents/agent_orchestrator.py; then
        check_pass "Gemini 2.5 Flash configured"
    else
        check_warn "Gemini model may not be configured"
    fi
else
    check_fail "Agent orchestrator missing"
fi

# Test 3: Retrospective Agent
echo ""
echo "🔄 Checking Retrospective Agent..."
if [ -f "back-end/app/agents/retrospective_agent.py" ]; then
    check_pass "Retrospective agent exists"
    
    # Check for Pub/Sub support
    if grep -q "USE_PUBSUB" back-end/app/agents/retrospective_agent.py; then
        check_pass "Pub/Sub integration ready"
    else
        check_fail "Pub/Sub not configured"
    fi
else
    check_fail "Retrospective agent missing"
fi

# Test 4: Extension
echo ""
echo "🔌 Checking VS Code Extension..."
if [ -f "extension/package.json" ]; then
    check_pass "Extension package.json exists"
    
    # Check main entry point
    if grep -q '"main": "./out/extension.js"' extension/package.json; then
        check_pass "Extension entry point correct"
    else
        check_fail "Extension entry point incorrect"
    fi
    
    # Check if compiled
    if [ -f "extension/out/extension.js" ]; then
        check_pass "Extension compiled"
    else
        check_fail "Extension not compiled"
    fi
    
    # Check for VSIX
    if ls extension/*.vsix 1> /dev/null 2>&1; then
        VSIX_FILE=$(ls extension/*.vsix | head -1)
        check_pass "Extension packaged: $(basename $VSIX_FILE)"
    else
        check_warn "Extension not packaged (run: cd extension && npx @vscode/vsce package)"
    fi
else
    check_fail "Extension package.json missing"
fi

# Test 5: Documentation
echo ""
echo "📚 Checking Documentation..."
if [ -f "README.md" ]; then
    check_pass "README.md exists"
else
    check_warn "README.md missing"
fi

if [ -f "PRODUCTION_DEPLOYMENT.md" ]; then
    check_pass "Production deployment guide exists"
else
    check_warn "Production deployment guide missing"
fi

# Test 6: Environment Configuration
echo ""
echo "⚙️  Checking Configuration..."
if [ -f "back-end/.env" ] || [ -f ".env" ]; then
    check_pass "Environment file exists"
    
    # Check for required vars (don't show values)
    if grep -q "GOOGLE_API_KEY" back-end/.env 2>/dev/null || grep -q "GOOGLE_API_KEY" .env 2>/dev/null; then
        check_pass "GOOGLE_API_KEY configured"
    else
        check_warn "GOOGLE_API_KEY not found"
    fi
else
    check_warn "No .env file found (needed for local testing)"
fi

# Test 7: Docker
echo ""
echo "🐳 Checking Docker Configuration..."
if [ -f "back-end/Dockerfile" ]; then
    check_pass "Dockerfile exists"
else
    check_warn "Dockerfile missing (needed for Cloud Run)"
fi

# Test 8: Unit Tests
echo ""
echo "🧪 Checking Tests..."
if [ -f "back-end/test_server.py" ]; then
    check_pass "Backend tests exist"
else
    check_warn "Backend tests not found"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Production Readiness Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: $SUCCESS${NC}"
echo -e "${RED}❌ Failed: $FAILURES${NC}"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}🎉 ContextPilot is READY for production deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Deploy to Google Cloud Run: Follow PRODUCTION_DEPLOYMENT.md"
    echo "2. Install extension: code --install-extension extension/*.vsix"
    echo "3. Test retrospective: Trigger from VS Code Command Palette"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  Please fix the failed checks before deploying to production${NC}"
    echo ""
    exit 1
fi

