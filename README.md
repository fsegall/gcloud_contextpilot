# 🧠 ContextPilot - AI Agents + Web3 Incentive Layer

> **Multi-agent AI system for developer productivity with blockchain-based rewards**

[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Ready-4285F4?logo=googlecloud)](https://cloud.google.com/run)
[![Polygon](https://img.shields.io/badge/Polygon-Mainnet-8247E5?logo=polygon)](https://polygon.technology)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Built for the **Cloud Run Hackathon 2025** - AI Agents Category

---

## 📖 Overview

**ContextPilot** helps developers manage project context through intelligent AI agents while rewarding contributions with CPT tokens on Polygon blockchain.

### The Problem
- Developers lose project context when switching tasks
- No measurable incentives for quality documentation
- Manual tracking of milestones and progress
- Fragmented project state across tools

### Our Solution
- **5 Specialized AI Agents** that collaborate via Google ADK
- **CPT Token** rewards for valuable contributions
- **Blockchain-verified** impact tracking
- **Real-time coaching** with micro-actions

---

## 🏆 Hackathon Category: AI Agents

✅ **Multi-agent system** with 5 specialized agents  
✅ **Google Agent Development Kit (ADK)** for coordination  
✅ **Cloud Run** deployment (Services + Jobs + Workers)  
✅ **Gemini** for LLM reasoning (can switch from OpenAI)  
✅ **Real-world problem** solving with measurable impact

---

## 🤖 AI Agents

| Agent | Purpose | Cloud Run Type |
|-------|---------|---------------|
| **Context** | Index repo state, detect changes | Job |
| **Spec** | Curate .md artifacts, validate docs | Service |
| **Strategy** | Analyze patterns, suggest improvements | Job |
| **Milestone** | Track progress, create checkpoints | Worker Pool |
| **Git** | Git operations, branches, rollbacks | Service |
| **Coach** | Pragmatic guidance, unblocking, micro-actions | Service |

All agents communicate via **Pub/Sub** event bus and share state in **Firestore**.

---

## 🪙 CPT Token (Web3 Layer)

### Dual-Purpose Token
1. **Reward Token**: Earn CPT by contributing (commits, docs, reviews)
2. **Utility Token**: Spend CPT on premium features

### Tokenomics
- **Max Supply per Cycle**: 1,000,000 CPT / 30 days
- **Burn Mechanism**: Inactive accounts (30+ days) auto-burn
- **Distribution**: Off-chain accumulation → On-chain batch minting
- **Blockchain**: Polygon PoS (low fees, fast)

See [TOKENOMICS.md](TOKENOMICS.md) for full economics.

---

## 🏗️ Architecture

```
Frontend (React + RainbowKit)
    ↓
FastAPI Backend (Cloud Run Service)
    ├─► AI Agents (Pub/Sub coordination)
    ├─► Rewards Engine (Firestore + Blockchain)
    └─► CPT Smart Contract (Polygon)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

---

## 🚀 Quick Start

```bash
# 1. Clone repo
git clone https://github.com/yourorg/google-context-pilot.git
cd google-context-pilot

# 2. Install dependencies
cd back-end && pip install -r requirements.txt
cd ../front-end && npm install
cd ../contracts && forge install

# 3. Deploy smart contract to testnet
cd contracts && ./scripts/deploy.sh

# 4. Run locally
cd back-end && uvicorn app.server:app --reload  # Terminal 1
cd front-end && npm run dev                      # Terminal 2

# 5. Open http://localhost:5173
```

See [QUICKSTART.md](QUICKSTART.md) for detailed setup.

---

## 🎯 Key Features

### For Developers
- ✅ **Automated Context Tracking**: Agents monitor your repo
- ✅ **Change Proposals**: Agents suggest, you approve (never auto-modify code)
- ✅ **Actionable Coaching**: Micro-tasks (≤25 min)
- ✅ **IDE Integration**: VSCode/Cursor extensions (coming soon)
- ✅ **Earn While You Code**: CPT rewards for contributions
- ✅ **Leaderboard**: Compete with peers

### For Teams
- ✅ **Standardized Checkpoints**: Git-backed milestones
- ✅ **Quantifiable Impact**: Token-based metrics
- ✅ **Cross-Project Insights**: BigQuery analytics

### Technical Highlights
- ✅ **Event-Driven**: Pub/Sub coordination
- ✅ **Pluggable Adapters**: Off-chain ↔ On-chain switchable
- ✅ **Cloud-Native**: Fully serverless (Cloud Run)
- ✅ **Secure**: OpenZeppelin contracts, Secret Manager

---

## 📊 Tech Stack

### Backend
- **Google Cloud Run** (Services + Jobs + Workers)
- **FastAPI** (Python REST API)
- **Firestore** (NoSQL database)
- **Pub/Sub** (Event bus)
- **BigQuery** (Analytics)

### Frontend
- **React** + TypeScript + Vite
- **RainbowKit** (Wallet connection)
- **wagmi** + **viem** (Ethereum interactions)
- **TailwindCSS** + **shadcn/ui**

### Blockchain
- **Polygon** PoS (Mainnet + Mumbai testnet)
- **Solidity** + **Foundry** (Smart contracts)
- **OpenZeppelin** (Audited libraries)

### AI/LLM
- **OpenAI GPT-4** (current)
- **Google Gemini** (ready to switch)
- **Agent Development Kit** (ADK)

---

## 📈 Rewards System

### Earning CPT

| Action | Points |
|--------|--------|
| CLI usage | +10 |
| Documentation | +5 |
| Strategy implemented | +15 |
| Milestone completed | +20 |
| Coach action done | +10 |

### Utility Consumption

| Action | Cost |
|--------|------|
| Gemini API call | -2 |
| Premium agent | -5 |
| Analytics export | -3 |

### Flow

```
Developer Action
    ↓
Agent Detects
    ↓
Firestore: +Points (instant)
    ↓
Daily Batch Job
    ↓
Smart Contract: mint() → Polygon
    ↓
Wallet Balance Updated
```

---

## 🎬 Demo

### Video (3 min)
- **Problem**: Context loss & lack of incentives
- **Solution**: Multi-agent system + CPT rewards
- **Demo**: Commit → Agents → Rewards → Leaderboard

### Try It Live
- **Testnet Demo**: [demo.contextpilot.dev](https://demo.contextpilot.dev)
- **Contract**: [mumbai.polygonscan.com/...](https://mumbai.polygonscan.com/)

---

## 🏅 Hackathon Submission

### What We Built
1. ✅ **5 AI Agents** using Google ADK
2. ✅ **CPT Smart Contract** (ERC-20 + custom logic)
3. ✅ **Cloud Run Deployment** (multi-service)
4. ✅ **Web3 Integration** (RainbowKit + viem)
5. ✅ **Rewards Engine** (off-chain + on-chain)

### Google Cloud Services Used
- **Cloud Run** (Services, Jobs, Worker Pools)
- **Firestore** (Database)
- **Google Blockchain Node Engine** (Polygon PoS nodes)
- **Cloud Storage** (Snapshots)
- **BigQuery** (Analytics)
- **Pub/Sub** (Event bus)
- **Secret Manager** (Keys)
- **Cloud Build** (CI/CD)
- **Cloud Scheduler** (Cron jobs)

### Bonus Points
- ✅ **Blog Post**: "Building ContextPilot with Cloud Run" (Medium)
- ✅ **Social Posts**: #CloudRunHackathon
- ✅ **Multiple Services**: Frontend + API + Workers
- ✅ **Gemini Ready**: Easy switch from OpenAI

---

## 📚 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started in 15 min
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [TOKENOMICS.md](TOKENOMICS.md) - Token economics
- [contracts/README.md](contracts/README.md) - Smart contract docs

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

### Development Setup
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
cd back-end && pytest
cd contracts && forge test
cd front-end && npm test
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 👥 Team

Built by developers, for developers.

- **Felipe Segall** - [@fsegall](https://github.com/fsegall)
- With AI assistance from: Claude, ChatGPT, Gemini

---

## 🙏 Acknowledgments

- **Google Cloud** for Cloud Run & infrastructure
- **Polygon** for fast & cheap transactions
- **OpenZeppelin** for secure smart contracts
- **RainbowKit** for beautiful wallet UX

---

## 🔗 Links

- **GitHub**: [github.com/yourorg/contextpilot](https://github.com/yourorg/contextpilot)
- **Demo**: [demo.contextpilot.dev](https://demo.contextpilot.dev)
- **Docs**: [docs.contextpilot.dev](https://docs.contextpilot.dev)
- **Discord**: [discord.gg/contextpilot](https://discord.gg/contextpilot)

---

**Built for Cloud Run Hackathon 2025 🚀**

[View on Devpost](https://devpost.com/software/contextpilot) • [Demo Video](https://youtube.com/...)


