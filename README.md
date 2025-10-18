# 🚀 ContextPilot - AI-Powered Development Assistant

**By [Livre Solutions](https://livre.solutions)**

> Transform your development workflow with intelligent AI agents, automated documentation, and gamification rewards.

---

## 🏆 **Hackathon Entry**

> **This project was developed for the [Cloud Run Hackathon](https://run.devpost.com/) hosted on Devpost.**
> 
> **Category:** AI Agents  
> **Challenge:** Build a multi-agent application deployed on Cloud Run  
> **Deadline:** November 10, 2025

[![Cloud Run Hackathon](https://img.shields.io/badge/Hackathon-Cloud%20Run%202025-4285F4?logo=googlecloud&logoColor=white)](https://run.devpost.com/)
[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-4285F4?logo=googlecloud)](https://cloud.google.com/run)
[![VS Code Extension](https://img.shields.io/badge/VS%20Code-Extension-blue?logo=visualstudiocode)](https://github.com/fsegall/gcloud_contextpilot/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/fsegall/gcloud_contextpilot)](https://github.com/fsegall/gcloud_contextpilot/releases)

**🎯 Devpost Submission:** [View on Devpost](https://devpost.com/software/contextpilot) _(coming soon)_

---

## 🚀 **Quick Start**

> **⚡ Get started in 5 minutes!** 

**Try it now:**
1. Download the [latest release](https://github.com/fsegall/gcloud_contextpilot/releases/latest) (`.vsix` file)
2. Install via Command Palette:
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Linux/Windows)
   - Type: **"Extensions: Install from VSIX..."**
   - Select the downloaded `.vsix` file
3. Restart VS Code/Cursor completely
4. Test: `Cmd/Ctrl+Shift+P` → type **"ContextPilot: Start Agent Retrospective"**

📘 **Alternative install methods:** [extension/INSTALL.md](extension/INSTALL.md) | 📦 **Docker:** `docker-compose up` | 🔧 **API Docs:** `http://localhost:8000/docs`

---

## 🤖 LLM-Powered Multi-Agent System

**ContextPilot uses Google Gemini AI** to power intelligent agent discussions:

- 🧠 **Real-time Agent Perspectives**: Each agent (Spec, Git, Coach, Context, Milestone, Strategy) generates contextualized insights using Gemini
- 🔄 **Automated Retrospectives**: Trigger team retrospectives that collect metrics and generate improvement proposals
- 🚀 **GitHub Actions Integration**: Approved proposals are automatically applied to your codebase via CI/CD
- 📊 **Metrics-Driven Insights**: Track agent activity, errors, and collaboration patterns

**Models used:**
- `gemini-2.5-flash`: Fast agent perspective generation
- `gemini-2.5-pro`: Deep analysis and summary synthesis

---

## 📖 What is ContextPilot?

**ContextPilot** is an AI-powered development assistant that helps you:

- 📝 **Maintain documentation automatically** through specialized AI agents
- 🤖 **Get intelligent code change proposals** with one-click approval
- 🎮 **Earn rewards** (CPT tokens) for productive development actions
- 📊 **Track project context** in real-time across your entire codebase
- ✅ **Automate git commits** with semantic messages

### The Problem We Solve

- 😓 Developers lose project context when switching tasks
- 📄 Documentation becomes outdated quickly
- 🔄 Manual git operations are time-consuming
- 🎯 No measurable incentives for code quality

### Our Solution

- 🤖 **Multi-Agent System**: 7 specialized AI agents working together
- 🧠 **Agent Retrospectives**: Agents learn from each other and self-improve
- 🎮 **Gamification**: CPT tokens, achievements, daily streaks
- ⚡ **One-Click Workflows**: Approve proposals and commit automatically
- 🔒 **Local-First**: Your code stays on your machine
- ✅ **Production-Ready**: 30+ unit tests with pytest

---

## ✨ Key Features

### 🤖 Multi-Agent System

| Agent | Purpose |
|-------|---------|
| **Spec Agent** | Generates and maintains documentation |
| **Git Agent** | Intelligent semantic commits |
| **Context Agent** | Real-time project analysis |
| **Coach Agent** | Personalized development tips |
| **Milestone Agent** | Progress tracking |
| **Strategy Agent** | Pattern analysis and improvements |
| **Retrospective Agent** 🆕 | Cross-agent learning and coordination |

All agents communicate via **Google Cloud Pub/Sub** and share state in **Firestore**.

#### 🆕 Agent Retrospectives (Hackathon Innovation)

**The Retrospective Agent facilitates "meetings" where real agents collaborate and learn:**

- 🤖 **Instantiates real agent instances** (Spec, Git, Strategy agents)
- 📊 **Collects live metrics** from all agents (events processed, errors, activity levels)
- 💬 **Each agent provides LLM-generated perspectives** via Gemini 2.5 Flash
- 🔍 Analyzes event bus patterns and agent collaboration
- 💡 Generates insights about workflow efficiency
- 🎯 Proposes actionable improvements
- 📝 Creates detailed reports (JSON + Markdown)
- 🧠 **AI-powered summary** using Gemini 2.5 Pro

**🎮 Interactive via Extension:**
1. Open Command Palette: `Cmd/Ctrl+Shift+P`
2. Run: `ContextPilot: Start Agent Retrospective`
3. **Suggest a discussion topic** (e.g., "How can we improve test coverage?")
4. Watch **real agents** generate unique LLM-powered perspectives
5. View beautiful formatted results with clickable file links
6. Review AI synthesis and automated improvement proposals
6. Get actionable recommendations with priorities (High/Medium/Low)
7. **🔄 Automatic proposal creation** - High-priority actions become change proposals
8. Approve the proposal to implement agent improvements

**Complete Feedback Loop:**
```
Retrospective → Insights → Action Items → Proposal → Code Changes → Next Retrospective
```

This creates a **self-improving system** where agents continuously optimize their own behavior!

**Why this matters:** This demonstrates **true multi-agent coordination** where agents don't just execute tasks—they **reflect, learn, and self-improve** as a team. Users can **guide the discussion**, making it interactive rather than automated. A key innovation in AI agent systems!

**Example:** After a development cycle, agents meet to discuss:
- "Spec Agent processed 15 proposals with 2 errors—needs better validation"
- "Git Agent was most active—strong collaboration observed"
- "Action: Review error logs and improve inter-agent communication"

### 🎮 Gamification & Rewards

- **CPT Tokens**: Earn points for productive actions
  - +10 CPT for approving proposals
  - +5 CPT for documentation updates
  - +20 CPT for milestone completion
- **Achievements**: Unlock badges (First Approval, Productivity Pro, Context Champion)
- **Daily Streaks**: Build consistent development habits
- **Leaderboards**: Compete with other developers (coming soon)

### 📊 Smart Change Proposals

AI agents analyze your code and propose:
- Documentation improvements
- Code refactoring suggestions
- Architecture updates
- Missing specs

You review and approve with **one click** - automatic git commit included!

### ✅ Production-Grade Testing

- **30+ Unit Tests** with pytest covering all API endpoints
- **Integration Tests** for full proposal workflow
- **Rate Limiting Tests** to verify abuse protection
- **Error Handling Tests** for edge cases
- **Parametrized Tests** for multiple scenarios
- **Async Test Support** with pytest-asyncio

Run tests: `cd back-end && pytest -v`

---

## 🏗️ Architecture

```
VS Code Extension (Local)
    ↓
Google Cloud Run (Backend API)
    ├─► Multi-Agent System (Pub/Sub coordination)
    ├─► Firestore (Proposals & State)
    ├─► Gemini API (AI Generation)
    └─► Secret Manager (API Keys)
    
Local Git
    ↑
Automatic Commits (After Approval)
```

**Key Design Decisions:**
- 🔒 **Local Git Operations**: Code never leaves your machine
- ☁️ **Cloud-Powered AI**: Leverage GCP's Gemini for intelligence
- 🎯 **Event-Driven**: Agents react to events, not polls
- 🔐 **Secure**: Rate limiting, abuse detection, secrets management

See [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for details.

---

## 🚀 Quick Start

### Option 1: Install VS Code Extension (Recommended)

1. **Download from GitHub Release:**
   ```bash
   # Download the .vsix file
   curl -LO https://github.com/fsegall/gcloud_contextpilot/releases/download/v0.1.0/contextpilot-0.1.0.vsix
   
   # Install in VS Code/Cursor
   code --install-extension contextpilot-0.1.0.vsix
   ```

2. **Or install via UI:**
   - Download `.vsix` from [Releases](https://github.com/fsegall/gcloud_contextpilot/releases)
   - VS Code: Extensions → `...` → Install from VSIX...

3. **Configure API URL** (Settings):
   ```json
   {
     "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app"
   }
   ```

4. **Start using:**
   - Open any project
   - Look for ContextPilot icon (🚀) in sidebar
   - View proposals, approve changes, earn CPT!

### Option 2: Run Backend Locally

```bash
# Clone repository
git clone https://github.com/fsegall/gcloud_contextpilot.git
cd google-context-pilot

# Setup backend
cd back-end
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY (Gemini)

# Run server
uvicorn app.server:app --reload --port 8000

# Extension will connect to http://localhost:8000
```

See [docs/deployment/QUICKSTART.md](docs/deployment/QUICKSTART.md) for detailed setup.

---

## 📚 Documentation

### For Users
- **[Extension README](extension/README.md)** - How to use the VS Code extension
- **[User Guide](docs/guides/EXTENSION_DEVELOPMENT.md)** - Getting started
- **[Troubleshooting](SECURITY.md)** - Common issues

### For Developers
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System design
- **[Agents](docs/architecture/AGENTS.md)** - Multi-agent system
- **[Custom Artifacts](docs/architecture/CUSTOM_ARTIFACTS.md)** - Spec-driven development
- **[API Documentation](back-end/README.md)** - Backend API reference

### For Hackathon Judges
- **[Deployment Guide](docs/deployment/DEPLOYMENT.md)** - How we use Cloud Run
- **[Security & Protection](SECURITY.md)** - Rate limiting and abuse detection
- **[Roadmap](ROADMAP.md)** - Future vision including blockchain

### Project Documentation
- **[📚 Full Documentation Index](docs/INDEX.md)** - Complete navigation
- **[🏗️ Architecture Docs](docs/architecture/)** - Design decisions
- **[🚀 Deployment Guides](docs/deployment/)** - Setup and deployment
- **[🤖 Agent Specifications](docs/agents/)** - Individual agent contracts

---

## 🛡️ Security & Protection

ContextPilot implements multiple layers of protection:

- **Rate Limiting**: 100 requests/hour per IP
- **Abuse Detection**: Automatic blacklisting of malicious patterns
- **Budget Alerts**: GCP cost monitoring and alerts
- **Local Git**: Your code never leaves your machine
- **Secret Management**: API keys secured in GCP Secret Manager

See [SECURITY.md](SECURITY.md) for complete security documentation.

---

## 🎯 Google Cloud Services Used

| Service | Purpose |
|---------|---------|
| **Cloud Run** | Backend API (serverless) |
| **Pub/Sub** | Event bus for agent communication |
| **Firestore** | NoSQL database for proposals and state |
| **Secret Manager** | Secure API key storage |
| **Container Registry** | Docker image storage |
| **Cloud Build** | CI/CD pipeline |
| **Monitoring** | Dashboards and alerts |
| **Gemini API** | AI-powered agent intelligence |

**Infrastructure as Code:** Fully deployed with [Terraform](terraform/) for deterministic, reproducible infrastructure.

---

## 🗺️ Roadmap

### ✅ Phase 1: Beta Launch (Current)
- Multi-agent system with 6 specialized agents
- VS Code extension with gamification
- Google Cloud Run backend
- Local git integration
- GitHub Release distribution

### 🔜 Phase 2: Blockchain Integration
- On-chain CPT token minting (Polygon)
- Leaderboards and competitive features
- Cross-project analytics
- Team collaboration

### 🚀 Phase 3: Scale & Enterprise
- VS Code Marketplace publication
- Open VSX Registry
- Custom agent creation
- Enterprise features (team dashboards, analytics)
- Multi-IDE support

See [ROADMAP.md](ROADMAP.md) for detailed roadmap.

---

## 🤝 Contributing

We welcome contributions! ContextPilot is open source and community-driven.

### Ways to Contribute
- 🐛 Report bugs via [GitHub Issues](https://github.com/fsegall/gcloud_contextpilot/issues)
- 💡 Suggest features via [Discussions](https://github.com/fsegall/gcloud_contextpilot/discussions)
- 🔧 Submit pull requests (see [CONTRIBUTING.md](CONTRIBUTING.md))
- 📖 Improve documentation
- 🎨 Design improvements

### Development Setup
```bash
# Backend
cd back-end
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest

# Extension
cd extension
npm install
npm run compile
npm test
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🏢 About Livre Solutions

**ContextPilot** is developed by [**Livre Solutions**](https://livre.solutions), a technology company focused on creating innovative AI and Web3 applications.

**Our Mission**: Empower developers with intelligent automation and gamification to boost productivity and make coding more rewarding.

**Connect with us:**
- 🌐 Website: [livre.solutions](https://livre.solutions)
- 🐦 Twitter: [@livresolutions](https://twitter.com/livresolutions)
- 💼 LinkedIn: [Livre Solutions](https://linkedin.com/company/livre-solutions)
- 📧 Contact: contact@livresoltech.com

---

## 🔒 Security & API Keys

### Current Beta Model (Shared API Key)

For the **beta launch and hackathon**, ContextPilot uses a **shared Gemini API key** to provide zero-friction onboarding:

- ✅ **Install and use immediately** - no configuration needed
- ✅ **Rate limited** (100 requests/hour per IP) for fair usage
- ✅ **Abuse detection** active to prevent misuse
- ✅ **Free tier** sufficient for beta testing (1,500 requests/day)

**Why shared key for beta?**
This design decision prioritizes **user experience** during the evaluation phase. Similar to how GitHub Copilot and Cursor handle early access, we want judges and early adopters to experience ContextPilot without setup friction.

### 🔮 Bring Your Own Key (BYOK) - Coming Soon

**Post-hackathon (Week 1)**, we're implementing user-provided API keys:

```json
{
  "contextpilot.aiProvider": "shared" | "own-key",
  "contextpilot.geminiApiKey": "your-api-key-here"
}
```

**Benefits:**
- 🚀 Unlimited usage (you control quota)
- 🔒 Enhanced privacy (your key, your data)
- 💰 Pay-as-you-go pricing (Google's Gemini rates)
- ⚡ Priority processing (no shared queue)

**Freemium Model:**
- **Free:** 10 proposals/day on shared key
- **BYOK:** Unlimited with your own Gemini API key
- **Enterprise:** Dedicated infrastructure + support

See [ROADMAP.md](ROADMAP.md) for implementation timeline.

### Historical API Keys

**Note:** Early development commits may contain test API keys in archived documentation. All keys have been rotated and are no longer valid. Current production keys are stored securely in Google Cloud Secret Manager.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/fsegall/gcloud_contextpilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fsegall/gcloud_contextpilot/discussions)
- **Email**: contact@livresoltech.com
- **Documentation**: [docs/INDEX.md](docs/INDEX.md)

---

## 🙏 Acknowledgments

- **Google Cloud** for Cloud Run, Pub/Sub, Firestore, and Gemini API
- **VS Code** team for the excellent extension API
- **OpenZeppelin** for secure smart contract libraries
- **Polygon** for fast and affordable blockchain infrastructure
- **Open source community** for inspiration and tools

---

## 📊 Project Stats

- **6 AI Agents** working in coordination
- **15+ endpoints** in production API
- **100% serverless** architecture
- **Rate limited** and abuse-protected
- **Local-first** git operations
- **Cloud-powered** AI intelligence

---

**Made with ❤️ by Livre Solutions for developers who love productivity and gamification!**

**#AI #VSCode #Productivity #CloudRun #Gemini #GoogleCloud #Hackathon**

---

## 🏅 Hackathon Entry

**Category**: AI Agents  
**Event**: Google Cloud Run Hackathon 2025  
**Demo**: [Extension Download](https://github.com/fsegall/gcloud_contextpilot/releases/v0.1.0)  
**Live Backend**: [API Health Check](https://contextpilot-backend-581368740395.us-central1.run.app/health)
