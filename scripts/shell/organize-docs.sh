#!/bin/bash
# Organize documentation files into docs/ structure

echo "📁 Organizing documentation..."

# Architecture & Design
mv ARCHITECTURE.md docs/architecture/
mv AGENTS.md docs/architecture/
mv AGENT_AUTONOMY.md docs/architecture/
mv AGENT_RETROSPECTIVE.md docs/architecture/
mv EVENT_BUS.md docs/architecture/
mv TOKENOMICS.md docs/architecture/
mv IDE_EXTENSION_SPEC.md docs/architecture/

# Deployment & Setup
mv DEPLOYMENT.md docs/deployment/
mv FAUCETS_SEPOLIA.md docs/deployment/
mv GET_SEPOLIA_ETH.md docs/deployment/
mv QUICKSTART.md docs/deployment/

# Guides
mv IMPLEMENTATION_GUIDE.md docs/guides/

# Progress Reports
mv DAY2_PROGRESS.md docs/progress/
mv PROGRESS_2025-10-13.md docs/progress/
mv SUMMARY_SESSION_2.md docs/progress/
mv CURRENT_STATUS.md docs/progress/

# Keep README.md in root (standard practice)
# README.md stays in root

echo "✅ Documentation organized!"
echo ""
echo "📂 Structure:"
echo "   docs/"
echo "   ├── architecture/    (7 files)"
echo "   ├── deployment/      (4 files)"
echo "   ├── guides/          (1 file)"
echo "   ├── progress/        (4 files)"
echo "   └── agents/          (AGENT.*.md contracts)"
echo ""
echo "   README.md           (kept in root)"
