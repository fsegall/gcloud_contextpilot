# 📚 ContextPilot Documentation Index

Welcome to the ContextPilot documentation! This guide will help you navigate all available documentation.

---

## 🏗️ Architecture & Design

Core system architecture and design decisions.

- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Complete system architecture overview
- **[AGENTS.md](architecture/AGENTS.md)** - Multi-agent system design and interactions
- **[AGENT_AUTONOMY.md](architecture/AGENT_AUTONOMY.md)** - Agent autonomy philosophy and Change Proposal System
- **[AGENT_RETROSPECTIVE.md](architecture/AGENT_RETROSPECTIVE.md)** - Meta-learning layer and agent meetings
- **[EVENT_BUS.md](architecture/EVENT_BUS.md)** - Pub/Sub event bus architecture
- **[TOKENOMICS.md](architecture/TOKENOMICS.md)** - CPT token economics and distribution
- **[IDE_EXTENSION_SPEC.md](architecture/IDE_EXTENSION_SPEC.md)** - VSCode/Cursor extension specification
- **[DEPLOYMENT_MODELS.md](architecture/DEPLOYMENT_MODELS.md)** - 🆕 SaaS vs Self-hosted deployment models

---

## 🚀 Deployment & Setup

Everything you need to deploy and configure ContextPilot.

- **[DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - CPT smart contract deployment guide
- **[QUICKSTART.md](deployment/QUICKSTART.md)** - Quick start guide for developers
- **[GET_SEPOLIA_ETH.md](deployment/GET_SEPOLIA_ETH.md)** - How to get Sepolia ETH for testing
- **[FAUCETS_SEPOLIA.md](deployment/FAUCETS_SEPOLIA.md)** - Sepolia faucet comparison
- **[USER_ONBOARDING.md](deployment/USER_ONBOARDING.md)** - 🆕 User onboarding flow for extension

---

## 📖 Guides

Step-by-step guides and tutorials.

- **[IMPLEMENTATION_GUIDE.md](guides/IMPLEMENTATION_GUIDE.md)** - Comprehensive implementation guide
- **[EXTENSION_DEVELOPMENT.md](guides/EXTENSION_DEVELOPMENT.md)** - 🆕 VSCode extension development guide

---

## 📊 Progress Reports

Development progress and session summaries.

- **[DAY2_PROGRESS.md](progress/DAY2_PROGRESS.md)** - Day 2 progress report (2025-10-14)
- **[PROGRESS_2025-10-13.md](progress/PROGRESS_2025-10-13.md)** - Day 1 progress report
- **[SUMMARY_SESSION_2.md](progress/SUMMARY_SESSION_2.md)** - Session 2 summary
- **[CURRENT_STATUS.md](progress/CURRENT_STATUS.md)** - Overall current status

## 📝 Project Planning

Strategy and planning documents.

- **[EXTENSION_COMPLETE.md](EXTENSION_COMPLETE.md)** - 🆕 Extension completion summary
- **[../LAUNCH_PLAN.md](../LAUNCH_PLAN.md)** - 🆕 Pre-hackathon launch plan
- **[../E2E_TEST_PLAN.md](../E2E_TEST_PLAN.md)** - 🆕 Complete E2E testing plan
- **[../QUICKTEST.md](../QUICKTEST.md)** - 🆕 15-minute quick test guide

---

## 🤖 Agent Contracts

Individual agent specifications and contracts.

- **[AGENT.coach.md](agents/AGENT.coach.md)** - Coach Agent contract
- **[AGENT.spec.md](agents/AGENT.spec.md)** - Spec Agent contract
- **[AGENT.git.md](agents/AGENT.git.md)** - Git Agent contract

---

## 🔗 Quick Links

### 🎯 Essential Reading (Start Here)
1. [README.md](../README.md) - Project overview
2. **[QUICKTEST.md](../QUICKTEST.md)** - 🆕 Test the extension in 15 min!
3. [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Understand the system

### 🏆 For Hackathon Judges
1. [README.md](../README.md) - Project pitch
2. [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Technical deep dive
3. [AGENTS.md](architecture/AGENTS.md) - Multi-agent innovation
4. [DAY2_PROGRESS.md](progress/DAY2_PROGRESS.md) - What we built
5. **[EXTENSION_COMPLETE.md](EXTENSION_COMPLETE.md)** - 🆕 IDE integration showcase

### 👨‍💻 For Developers
1. **[QUICKTEST.md](../QUICKTEST.md)** - 🆕 Quick test (15 min)
2. [QUICKSTART.md](deployment/QUICKSTART.md) - Full setup instructions
3. [IMPLEMENTATION_GUIDE.md](guides/IMPLEMENTATION_GUIDE.md) - Implementation details
4. **[EXTENSION_DEVELOPMENT.md](guides/EXTENSION_DEVELOPMENT.md)** - 🆕 Extension development

### 🤝 For Contributors
1. [AGENTS.md](architecture/AGENTS.md) - Agent system overview
2. [EVENT_BUS.md](architecture/EVENT_BUS.md) - Event-driven architecture
3. [Agent Contracts](agents/) - Individual agent specs
4. **[E2E_TEST_PLAN.md](../E2E_TEST_PLAN.md)** - 🆕 Complete testing plan

### 🚀 For Product Launch
1. **[LAUNCH_PLAN.md](../LAUNCH_PLAN.md)** - 🆕 27-day launch strategy
2. **[DEPLOYMENT_MODELS.md](architecture/DEPLOYMENT_MODELS.md)** - 🆕 SaaS vs Self-hosted
3. **[USER_ONBOARDING.md](deployment/USER_ONBOARDING.md)** - 🆕 User onboarding flow

---

## 📁 Repository Structure

```
google-context-pilot/
├── README.md                    # Main project README
├── LAUNCH_PLAN.md               # 🆕 Launch strategy
├── E2E_TEST_PLAN.md             # 🆕 Testing plan
├── QUICKTEST.md                 # 🆕 Quick test guide
├── docs/                        # 📚 All documentation (you are here)
│   ├── INDEX.md                 # This file
│   ├── architecture/            # System design & architecture (8 files)
│   ├── deployment/              # Deployment guides (5 files)
│   ├── guides/                  # Tutorials & guides (2 files)
│   ├── progress/                # Development progress (4 files)
│   └── agents/                  # Agent contracts (3 files)
├── back-end/                    # FastAPI backend
├── front-end/                   # React frontend
├── contracts/                   # Solidity smart contracts (deployed ✅)
├── extension/                   # 🆕 VSCode/Cursor extension
├── scripts/shell/               # 🆕 Shell scripts
└── infra/                       # Cloud infrastructure configs
```

---

## 🎯 Document Conventions

### File Naming
- `UPPERCASE.md` - Major documentation files
- `AGENT.*.md` - Agent contract specifications
- `lowercase.md` - Supporting documentation

### Emoji Usage
- 🏗️ Architecture & Design
- 🚀 Deployment & Operations
- 📖 Guides & Tutorials
- 📊 Progress & Reports
- 🤖 Agents & AI
- 🔗 Links & References
- ⚡ Quick Actions
- ✅ Completed Items
- ⏳ In Progress
- 📌 Important Notes

---

## 💡 Contributing to Documentation

When adding new documentation:

1. Place files in the appropriate category folder
2. Update this INDEX.md with a link
3. Use consistent formatting (H1 for title, emoji prefixes)
4. Include a "Last Updated" date at the bottom
5. Cross-reference related documents

---

**Last Updated**: 2025-10-14  
**For**: Cloud Run Hackathon 2025  
**Status**: 🟢 Active Development
