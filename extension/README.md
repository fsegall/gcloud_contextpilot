# 🚀 ContextPilot

**By [Livre Solutions](https://livre.solutions)**

**AI-Powered Development Assistant with Multi-Agent System & Gamification**

Transform your development workflow with intelligent AI agents that manage documentation, automate commits, and reward your progress with gamification!

## ✨ Features

### 🤖 **Multi-Agent System**
- **Spec Agent**: Automatically generates and maintains documentation
- **Git Agent**: Intelligent semantic commits with conventional format
- **Context Agent**: Real-time project analysis and insights
- **Coach Agent**: Personalized development tips and guidance
- **Milestone Agent**: Progress tracking and goal management

### 🎮 **Gamification & Rewards**
- **CPT Tokens**: Earn ContextPilot Tokens for productive actions
- **Achievements**: Unlock badges for milestones and streaks
- **Daily Streaks**: Build consistent development habits
- **Leaderboards**: Compete with other developers worldwide
- **Rewards System**: Get rewarded for documentation, commits, and improvements

### ⚡ **Developer Experience**
- **Instant Commits**: One-click proposal approval with automatic Git commits
- **Smart Context**: Intelligent project context summarization
- **File Management**: Easy access to related files and documentation
- **Real-time Updates**: Live project status and agent activities

## 🚀 Quick Start

### 1. **Installation**
```bash
# Via VS Code Marketplace
# Search for "ContextPilot" and install

# Or install from VSIX
code --install-extension contextpilot-0.1.0.vsix
```

### 2. **First Use**
1. Open any project in VS Code
2. Look for the 🚀 ContextPilot icon in the sidebar
3. Wait for "Connected to ContextPilot!" status
4. Explore the Change Proposals section

### 3. **Earn Your First Rewards**
- Click the ✓ button next to any proposal
- Watch your CPT balance increase: "🎉 +10 CPT!"
- Check the Rewards section to see your progress

## 🎯 Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `ContextPilot: Connect` | Connect to backend services | - |
| `ContextPilot: View Proposals` | Show all pending proposals | - |
| `ContextPilot: Approve Proposal` | Approve and commit changes | - |
| `ContextPilot: View Rewards` | Show CPT balance and achievements | - |
| `ContextPilot: Ask Coach` | Get personalized development tips | - |

## 🏆 Rewards & Achievements

### **CPT Earning Actions:**
- ✅ **Approve Proposal**: +10 CPT
- 📚 **Create Documentation**: +25 CPT
- 🔧 **Fix Issues**: +15 CPT
- 🔥 **Daily Streak**: +5 CPT
- 🏆 **Week Warrior**: +100 CPT (7-day streak)

### **Achievement Badges:**
- 🎯 **First Approval**: Approve your first proposal
- 📚 **Documentation Master**: Create comprehensive docs
- 🔥 **Week Warrior**: 7-day activity streak
- 🚀 **Productivity Pro**: 100+ CPT earned
- 💎 **Context Champion**: 1000+ CPT earned

## 🔧 Configuration

### **Backend URL**

The extension connects to the ContextPilot backend API. By default, it uses the production Cloud Run instance:

```typescript
// Production (default)
const apiUrl = 'https://contextpilot-backend-581368740395.us-central1.run.app';

// Development (local testing)
const apiUrl = 'http://localhost:8000';
```

**To switch between dev and prod:**
1. Edit `extension/src/extension.ts` line 19
2. Rebuild: `npm run webpack`
3. Reinstall: `npx @vscode/vsce package`

### **Environment Differences**

| Feature | Local Dev | Production (Cloud) |
|---------|-----------|-------------------|
| Backend URL | `localhost:8000` | `*.run.app` |
| Workspace Storage | Local `.contextpilot/` | Firestore |
| Event Bus | In-memory | Google Pub/Sub |
| Default Workspace | `default` | `default` |

**Important**: Proposals are stored per workspace. The extension now searches **all workspaces** to avoid missing proposals created in different workspace contexts.

### **Settings**
```json
{
  "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app",
  "contextpilot.autoApprove": false,
  "contextpilot.showRewards": true
}
```

### **Workspace Setup**
1. Ensure your project is a Git repository
2. Have at least one `.md` file (README.md recommended)
3. Grant necessary permissions when prompted

**Note**: If proposals don't appear, check that the backend's `workspace_id` matches where proposals are stored. The extension queries all workspaces by default.

## 🌟 Use Cases

### **Documentation Management**
- Automatically detect missing documentation
- Generate comprehensive project docs
- Keep documentation in sync with code changes

### **Code Quality**
- Identify potential improvements
- Suggest best practices
- Track technical debt

### **Team Collaboration**
- Share proposals across team members
- Maintain consistent coding standards
- Track team productivity metrics

## 🔮 Roadmap

### **Phase 1: Core Features** ✅
- [x] Multi-agent system
- [x] Gamification & rewards
- [x] Local Git integration
- [x] Cloud backend (Google Cloud)

### **Phase 2: Blockchain Integration** 🔮
- [ ] Polygon network support
- [ ] CPT Token (ERC-20) deployment
- [ ] Wallet connection
- [ ] Onchain rewards & DeFi

### **Phase 3: Enterprise Features** 🌟
- [ ] Team collaboration
- [ ] Advanced analytics
- [ ] Custom AI models
- [ ] White-label solutions

## 🛠️ Technical Stack

- **Frontend**: VS Code Extension (TypeScript)
- **Backend**: Google Cloud Run (Python/FastAPI)
- **Database**: Google Cloud Firestore
- **Messaging**: Google Cloud Pub/Sub
- **AI**: Google Gemini API
- **Future**: Polygon Blockchain Integration

## 📊 Metrics & Analytics

Track your development progress with detailed metrics:
- **Productivity Score**: Based on commits, documentation, and improvements
- **Consistency Rating**: Daily activity and streak maintenance
- **Quality Index**: Code quality and documentation completeness
- **Team Ranking**: Compare with other developers globally

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/fsegall/gcloud_contextpilot) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/fsegall/gcloud_contextpilot/issues)
- **Discord**: [ContextPilot Community](https://discord.gg/contextpilot)
- **Email**: contact@livresoltech.com

## 🏢 About Livre Solutions

**ContextPilot** is developed by [**Livre Solutions**](https://livre.solutions), a technology company focused on creating innovative AI and Web3 applications.

**Our Mission**: Empower developers with intelligent automation and gamification to boost productivity and make coding more rewarding.

**Connect with us**:
- 🌐 Website: [livre.solutions](https://livre.solutions)
- 🐦 Twitter: [@livresolutions](https://twitter.com/livresolutions)
- 💼 LinkedIn: [Livre Solutions](https://linkedin.com/company/livre-solutions)
- 📧 Contact: contact@livresoltech.com

---

**Made with ❤️ by Livre Solutions for developers who love productivity and gamification!**

*Start your journey to more productive, rewarding development today!*