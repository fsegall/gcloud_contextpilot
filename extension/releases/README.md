# ContextPilot Extension Releases

## 📦 Latest Release

**Version 0.4.2** (October 22, 2025)
- Located in: `latest/contextpilot-0.4.2.vsix`
- **New Features:**
  - ✅ 6 Active Agents + Retrospective Agent
  - ✅ Strategy Coach Agent (unified strategic + technical + motivational guidance)
  - ✅ Development Agent integration
  - ✅ Context Agent for semantic search
  - ✅ Milestone Agent for progress tracking
  - ✅ CPT Rewards System (25 CPT per proposal approval)
  - ✅ Dashboard view with 5 panels
  - ✅ Event Bus: Pub/Sub mode indicator
  - ✅ Git Agent: Enhanced with Markdown management, rewards tracking, rich history, and optional LLM commit messages
  - ✅ Zero code duplication between GitAgent and Git_Context_Manager
  - ✅ Real-time agent status endpoint (no more hardcoded mocks)
  - ✅ Integrated Coach endpoint with Gemini API

### Installation
```bash
code --install-extension releases/latest/contextpilot-0.4.2.vsix --force
```

---

## 📚 Archive

Older versions stored in `archive/`:
- **0.2.x series**: Initial multi-agent architecture (10 versions)
- **0.3.x series**: Rewards system beta (3 versions)
- **0.4.0-0.4.1**: Previous builds

---

## 🗂️ Structure

```
extension/
└── releases/
    ├── README.md                     ← This file
    ├── latest/
    │   └── contextpilot-0.4.2.vsix  ← Latest stable
    └── archive/
        ├── contextpilot-0.2.x.vsix
        ├── contextpilot-0.3.x.vsix
        └── contextpilot-0.4.0.vsix
```

---

## 🚀 Release Notes

### v0.4.2 (2025-10-22) - **LATEST**
- **Git Architecture Enhancements**
  - Eliminated code duplication between GitAgent and Git_Context_Manager
  - GitAgent now delegates all core Git operations to Git_Context_Manager
  - Enhanced with Markdown file management (context.md, timeline.md, task_history.md)
  - Integrated rewards tracking after commits
  - Rich history logging (history.json)
  - Optional LLM-generated commit messages (Gemini API)
- **Backend Improvements**
  - Real-time `/agents/status` endpoint (no more hardcoded mocks)
  - Integrated `/agents/coach/ask` with Gemini API and fallback
  - Translated all Portuguese comments to English
  - Created comprehensive Git & GitHub architecture documentation
- **Extension Fixes**
  - Updated agent list in UI to match backend (Strategy Coach Agent)
  - Fixed hardcoded agent names and prompts
  - Version bump to 0.4.2 for correct packaging

### v0.4.0-0.4.1 (2025-10-21)
- **Agent Architecture Overhaul**
  - Unified Strategy + Coach → Strategy Coach Agent
  - Added Development, Context, Milestone agents
  - All 6 agents now appear in retrospectives
- **Rewards System**
  - Firestore integration
  - +25 CPT for proposal approvals
  - Real-time balance updates
- **UI Improvements**
  - Dashboard command
  - Agent Status view with emojis
  - Event Bus mode indicator

### v0.3.x (2025-10-20)
- Rewards system beta
- Leaderboard integration
- Proposal review panel improvements

### v0.2.x (2025-10-18 to 10-20)
- Initial agent system
- Proposal creation and approval
- TUI integration
- Cloud Run backend connection

