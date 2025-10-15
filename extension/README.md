# 🧠 ContextPilot Extension

AI-powered context management extension for VSCode/Cursor with multi-agent system and blockchain rewards.

## Features

### 🤖 Multi-Agent System
- **6 specialized AI agents** working together to improve your code
- Real-time agent status tracking
- Intelligent suggestions and automated improvements

### 📋 Change Proposals
- Review AI-generated code changes before they're applied
- Approve/reject proposals with a single click
- See detailed diffs and explanations

### ⭐ CPT Rewards
- Earn CPT tokens for good development practices
- View your balance directly in the status bar
- Track your position on the leaderboard

### 💬 Coach Agent
- Ask questions about your project
- Get actionable advice and micro-actions
- Pragmatic guidance when you're stuck

### 🔄 Context Management
- Automatic context tracking
- One-click context commits
- Persistent project state

---

## 🚀 Installation

### From VSIX (Development)
1. Download the `.vsix` file
2. Open VSCode/Cursor
3. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
4. Type "Install from VSIX"
5. Select the downloaded file

### From Marketplace (Coming Soon)
Search for "ContextPilot" in the Extensions marketplace.

---

## ⚙️ Configuration

Go to Settings > Extensions > ContextPilot:

| Setting | Default | Description |
|---------|---------|-------------|
| `contextpilot.apiUrl` | `http://localhost:8000` | ContextPilot API URL |
| `contextpilot.userId` | `""` | Your ContextPilot user ID |
| `contextpilot.walletAddress` | `""` | Your wallet address for CPT rewards |
| `contextpilot.autoConnect` | `true` | Auto-connect on startup |
| `contextpilot.showNotifications` | `true` | Show agent activity notifications |

---

## 🎯 Usage

### Quick Start

1. **Connect to Backend**
   - Press `Ctrl+Shift+P`
   - Type "ContextPilot: Connect"
   - Or enable `autoConnect` in settings

2. **View Change Proposals**
   - Click the ContextPilot icon in the sidebar
   - Review pending proposals
   - Click ✓ to approve or ✗ to reject

3. **Check Your Rewards**
   - Your CPT balance shows in the status bar
   - Click it to see detailed breakdown
   - View the leaderboard

4. **Ask the Coach**
   - Press `Ctrl+Shift+P`
   - Type "ContextPilot: Ask Coach"
   - Get instant advice

### Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `ContextPilot: Connect` | Connect to backend | - |
| `ContextPilot: Disconnect` | Disconnect from backend | - |
| `ContextPilot: View Change Proposals` | Open proposals panel | - |
| `ContextPilot: Approve Proposal` | Approve a proposal | Click ✓ |
| `ContextPilot: Reject Proposal` | Reject a proposal | Click ✗ |
| `ContextPilot: View CPT Balance` | Show rewards details | Click status bar |
| `ContextPilot: Ask Coach` | Ask the Coach Agent | - |
| `ContextPilot: Commit Context` | Save current context | - |
| `ContextPilot: Refresh Status` | Refresh all views | - |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│     VSCode/Cursor Extension         │
│  ┌─────────────────────────────┐   │
│  │  Sidebar Views              │   │
│  │  - Change Proposals         │   │
│  │  - Rewards                  │   │
│  │  - Agents Status            │   │
│  │  - Coach                    │   │
│  └─────────────────────────────┘   │
│                │                    │
│  ┌─────────────▼───────────────┐   │
│  │  ContextPilot Service       │   │
│  │  - API Client               │   │
│  │  - Change Tracking          │   │
│  └─────────────┬───────────────┘   │
└────────────────┼────────────────────┘
                 │ HTTP
┌────────────────▼────────────────────┐
│     ContextPilot Backend (FastAPI)  │
│  ┌──────────────────────────────┐  │
│  │  6 AI Agents                 │  │
│  │  Context • Spec • Strategy   │  │
│  │  Milestone • Git • Coach     │  │
│  └──────────────────────────────┘  │
│                │                    │
│  ┌─────────────▼───────────────┐   │
│  │  Rewards Engine              │   │
│  │  CPT Token on Sepolia        │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🎬 Demo

### 1. Change Proposal Workflow
```
Code Change → Context Agent Detects → Strategy Agent Analyzes
    → Change Proposal Created → Developer Reviews in Sidebar
    → Approve → Git Agent Applies → CPT Tokens Earned 🎉
```

### 2. Ask Coach
```
Developer: "How can I improve my API design?"
Coach Agent: "Consider these 3 micro-actions:
  1. Add request validation
  2. Implement rate limiting
  3. Document endpoints with OpenAPI"
```

---

## 🔧 Development

### Prerequisites
- Node.js 18+
- TypeScript
- VSCode Extension API

### Build from Source
```bash
cd extension
npm install
npm run compile
```

### Run in Development
1. Open `extension/` in VSCode
2. Press F5 to start Extension Development Host
3. Test the extension

### Package
```bash
npm run package  # Creates .vsix file
```

---

## 🐛 Troubleshooting

### "Failed to connect to ContextPilot API"
- Ensure the backend is running: `cd back-end && python -m app.server`
- Check `contextpilot.apiUrl` in settings
- Verify firewall/network settings

### "No proposals showing"
- Make sure you've committed context: `ContextPilot: Commit Context`
- Check if agents are running: View "Agents Status" panel
- Refresh: `ContextPilot: Refresh Status`

### "Balance shows 0 CPT"
- Configure your `contextpilot.walletAddress` in settings
- Approve at least one proposal to earn rewards
- Check the backend logs for reward tracking

---

## 📚 Documentation

- **[Architecture](../docs/architecture/ARCHITECTURE.md)** - System design
- **[Agent Autonomy](../docs/architecture/AGENT_AUTONOMY.md)** - How agents work
- **[IDE Extension Spec](../docs/architecture/IDE_EXTENSION_SPEC.md)** - Full specification
- **[Deployment Guide](../docs/deployment/DEPLOYMENT.md)** - Setup instructions

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## 📄 License

MIT License - see [LICENSE](../LICENSE)

---

## 🔗 Links

- **GitHub**: [github.com/fsegall/google-context-pilot](https://github.com/fsegall/google-context-pilot)
- **Documentation**: [docs/INDEX.md](../docs/INDEX.md)
- **Backend API**: [back-end/openapi.yaml](../back-end/openapi.yaml)

---

**Built for Cloud Run Hackathon 2025** 🚀

Made with ❤️ by developers, for developers.

