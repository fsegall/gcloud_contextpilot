# 🔌 ContextPilot IDE Extension

## Overview

Extensão para VSCode/Cursor que integra ContextPilot no fluxo de trabalho diário do desenvolvedor.

**Core Principle:** Agents suggest, developers approve. No auto-modifications.

---

## 📦 Extension Name

**Primary:** `contextpilot-vscode`  
**Display Name:** ContextPilot  
**Publisher:** contextpilot-team

---

## 🎨 UI Components

### 1. Sidebar Panel (Primary View)

```
┌─ CONTEXTPILOT ────────────────────────┐
│                                        │
│ [⚙️ Settings] [🔄 Sync] [📊 Dashboard]│
│                                        │
├─ 💡 PROPOSALS (3) ────────────────────┤
│                                        │
│ 🟢 Extract AuthService                │
│    Strategy • 4 files • 45min         │
│    +50 -120 lines                     │
│    [👁️ Preview] [✓ Apply] [✗ Reject] │
│                                        │
│ 🟡 Update API Documentation           │
│    Spec • 1 file • 15min              │
│    +30 -5 lines                       │
│    [👁️ Preview] [✓ Apply] [✗ Reject] │
│                                        │
│ 🔴 Validate User Input                │
│    Strategy • Security • 30min        │
│    +15 -0 lines                       │
│    [👁️ Preview] [✓ Apply] [✗ Reject] │
│                                        │
├─ 🧘 COACH ────────────────────────────┤
│                                        │
│ Validate refactor de auth             │
│                                        │
│ Why: Large change + deadline close    │
│                                        │
│ Next steps:                           │
│ □ Run auth tests (8 min)              │
│ □ Check endpoints (5 min)             │
│ □ Manual login test (7 min)           │
│                                        │
│ [🎯 Start 25min Focus]                │
│                                        │
├─ 💰 REWARDS ──────────────────────────┤
│                                        │
│ 🪙 125 CPT (50 pending)               │
│ Rank: #12 / 150                       │
│                                        │
│ Recent:                               │
│ • spec_commit +5 (2h ago)             │
│ • milestone_saved +20 (1d ago)        │
│                                        │
│ [View Leaderboard]                    │
│                                        │
└────────────────────────────────────────┘
```

### 2. Inline CodeLens

Aparece acima de funções/classes relevantes:

```python
# 💡 Strategy suggests: Extract to service | [Preview] | [Dismiss]
def authenticate_user(username, password):
    if not username or not password:
        return False
    # ... 30 more lines of auth logic
```

### 3. Hover Provider

Ao passar mouse sobre código sugerido:

```
┌─────────────────────────────────────┐
│ 💡 Strategy Agent Suggestion        │
│                                     │
│ Extract duplicate auth logic to     │
│ AuthService class.                  │
│                                     │
│ Impact:                             │
│ • 4 files modified                  │
│ • 120 lines removed (duplication)   │
│ • 50 lines added (new service)      │
│                                     │
│ Benefits:                           │
│ • Single source of truth            │
│ • Easier to test                    │
│ • Maintainability +40%              │
│                                     │
│ [👁️ Preview Changes]                │
└─────────────────────────────────────┘
```

### 4. Diff Preview Webview

Quando clica "Preview":

```html
┌─ PROPOSAL: Extract AuthService ───────────────────────┐
│                                                        │
│ [← Back] [✓ Apply All] [✏️ Edit] [✗ Reject]          │
│                                                        │
├─ Files (4) ────────────────────────────────────────── │
│                                                        │
│ ▼ src/auth/login.py                   [-30] [+8]     │
│   ─────────────────────────────────────────────       │
│   - def login(username, password):                    │
│   -     if not username or not password:              │
│   -         return False                              │
│   -     user = db.query(...).filter(                  │
│   -         username=username                         │
│   -     ).first()                                     │
│   -     if not user:                                  │
│   -         return False                              │
│   -     return bcrypt.verify(password, user.hash)     │
│   +     return AuthService.authenticate(              │
│   +         username, password                        │
│   +     )                                             │
│                                                        │
│ ▼ src/auth/register.py                [-25] [+6]     │
│   Similar changes...                                  │
│                                                        │
│ ▶ src/auth/reset.py                   [-35] [+10]    │
│   Click to expand...                                  │
│                                                        │
│ ▼ src/services/auth_service.py (NEW)  [+50]          │
│   ─────────────────────────────────────────────       │
│   + from bcrypt import verify                         │
│   + from database import db                           │
│   +                                                   │
│   + class AuthService:                                │
│   +     """Centralized authentication service"""     │
│   +                                                   │
│   +     @staticmethod                                 │
│   +     def authenticate(username, password):         │
│   +         if not username or not password:          │
│   +             return False                          │
│   +         user = db.query(...).filter(              │
│   +             username=username                     │
│   +         ).first()                                 │
│   +         if not user:                              │
│   +             return False                          │
│   +         return verify(password, user.hash)        │
│                                                        │
├─ Summary ──────────────────────────────────────────── │
│                                                        │
│ • 3 files modified, 1 file created                    │
│ • 90 lines removed (duplication)                      │
│ • 50 lines added (service)                            │
│ • Net: -40 lines                                      │
│ • Estimated time: 45 minutes                          │
│ • Breaking changes: No                                │
│ • Tests required: Yes (add AuthService tests)         │
│                                                        │
│ [✓ Apply All] [✏️ Edit in VSCode] [✗ Reject]         │
└────────────────────────────────────────────────────────┘
```

### 5. Status Bar

```
┌──────────────────────────────────────────────────────┐
│ [ContextPilot: 3 proposals] [125 CPT] [Synced 2m ago]│
└──────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### User Settings (`.vscode/settings.json`)

```json
{
  "contextpilot.enabled": true,
  "contextpilot.apiUrl": "https://api.contextpilot.dev",
  "contextpilot.userId": "dev_123",
  
  "contextpilot.proposals": {
    "autoFetch": true,
    "fetchIntervalSeconds": 300,
    "showInlineCodeLens": true,
    "showHoverProvider": true
  },
  
  "contextpilot.autoApprove": {
    "docUpdates": true,
    "formatting": false,
    "linting": false
  },
  
  "contextpilot.notifications": {
    "newProposal": "toast",
    "urgentProposal": "modal",
    "rewardsEarned": "badge"
  },
  
  "contextpilot.coach": {
    "enabled": true,
    "nudgeFrequency": "adaptive",
    "focusModeRespect": true
  },
  
  "contextpilot.rewards": {
    "showInSidebar": true,
    "showInStatusBar": true
  }
}
```

### Project Settings (`.contextpilot.yml`)

```yaml
version: 1

# Agent behavior
agents:
  strategy:
    enabled: true
    max_blast_radius:
      files: 10
      lines: 500
    require_approval:
      - security_changes
      - api_changes
  
  spec:
    enabled: true
    auto_approve: true  # Docs only
  
  coach:
    enabled: true
    nudge_interval: 30m

# Proposals
proposals:
  create_pr: true
  pr_labels: ["agent-proposal", "auto-generated"]
  require_review_for:
    - "src/core/**"
    - "migrations/**"
  
  ignore_paths:
    - "legacy/"
    - "third_party/"
    - "*.generated.*"

# Rewards
rewards:
  enabled: true
  auto_track: true

# Notifications
notifications:
  slack_webhook: "https://hooks.slack.com/..."
  notify_team: true
```

---

## 🔌 Extension Commands

### Palette Commands (`Cmd+Shift+P`)

```
ContextPilot: Show Proposals
ContextPilot: Sync Now
ContextPilot: View Rewards Dashboard
ContextPilot: Start Focus Mode (25min)
ContextPilot: Accept All Doc Proposals
ContextPilot: Reject All Proposals
ContextPilot: Open Settings
ContextPilot: View Agent Logs
ContextPilot: Connect Wallet
```

### Keybindings

```json
{
  "key": "ctrl+shift+c p",
  "command": "contextpilot.showProposals"
},
{
  "key": "ctrl+shift+c a",
  "command": "contextpilot.acceptProposal"
},
{
  "key": "ctrl+shift+c r",
  "command": "contextpilot.rejectProposal"
}
```

---

## 🔄 API Integration

### Extension ↔ Cloud Run API

```typescript
// src/api/client.ts
export class ContextPilotAPI {
  private baseUrl: string;
  private userId: string;
  
  constructor(config: Config) {
    this.baseUrl = config.apiUrl;
    this.userId = config.userId;
  }
  
  // Fetch pending proposals
  async getProposals(): Promise<Proposal[]> {
    const response = await fetch(
      `${this.baseUrl}/proposals?user_id=${this.userId}&status=pending`
    );
    return response.json();
  }
  
  // Get proposal details with diff
  async getProposalDetails(id: string): Promise<ProposalDetails> {
    const response = await fetch(
      `${this.baseUrl}/proposals/${id}`
    );
    return response.json();
  }
  
  // Approve proposal
  async approveProposal(id: string): Promise<ApprovalResult> {
    const response = await fetch(
      `${this.baseUrl}/proposals/${id}/approve`,
      { method: 'POST' }
    );
    return response.json();
  }
  
  // Reject proposal with reason
  async rejectProposal(id: string, reason: string): Promise<void> {
    await fetch(
      `${this.baseUrl}/proposals/${id}/reject`,
      {
        method: 'POST',
        body: JSON.stringify({ reason })
      }
    );
  }
  
  // Get rewards balance
  async getRewards(): Promise<RewardsBalance> {
    const response = await fetch(
      `${this.baseUrl}/rewards/balance/${this.userId}`
    );
    return response.json();
  }
}
```

---

## 🎯 Core Features Implementation

### Feature 1: Auto-Sync Proposals

```typescript
// src/services/sync.ts
export class ProposalSyncService {
  private intervalId?: NodeJS.Timer;
  
  start(intervalSeconds: number) {
    this.intervalId = setInterval(
      () => this.sync(),
      intervalSeconds * 1000
    );
  }
  
  async sync() {
    try {
      const proposals = await api.getProposals();
      
      // Update sidebar
      updateProposalsView(proposals);
      
      // Show notifications for new proposals
      const newProposals = proposals.filter(p => !seen(p.id));
      if (newProposals.length > 0) {
        showNotification(
          `${newProposals.length} new proposal(s) from agents`
        );
      }
      
      // Update CodeLens
      refreshCodeLens();
      
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }
}
```

### Feature 2: Diff Preview

```typescript
// src/views/diff-preview.ts
export class DiffPreviewPanel {
  private panel: vscode.WebviewPanel;
  
  async show(proposal: Proposal) {
    this.panel = vscode.window.createWebviewPanel(
      'contextpilot-diff',
      `Proposal: ${proposal.title}`,
      vscode.ViewColumn.Beside,
      { enableScripts: true }
    );
    
    const html = this.renderDiffHTML(proposal);
    this.panel.webview.html = html;
    
    // Handle approve/reject from webview
    this.panel.webview.onDidReceiveMessage(
      async (message) => {
        if (message.command === 'approve') {
          await this.applyProposal(proposal);
        } else if (message.command === 'reject') {
          await api.rejectProposal(proposal.id, message.reason);
        }
      }
    );
  }
  
  private async applyProposal(proposal: Proposal) {
    // Show progress
    await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: `Applying: ${proposal.title}`,
      cancellable: false
    }, async (progress) => {
      
      // Create branch
      const branchName = `agent/${proposal.id}`;
      await git.createBranch(branchName);
      
      progress.report({ increment: 25 });
      
      // Apply changes
      for (const change of proposal.changes) {
        if (change.action === 'create') {
          await fs.writeFile(change.file, change.content);
        } else if (change.action === 'modify') {
          await applyDiff(change.file, change.diff);
        } else if (change.action === 'delete') {
          await fs.unlink(change.file);
        }
      }
      
      progress.report({ increment: 50 });
      
      // Commit
      await git.commit(proposal.title);
      
      progress.report({ increment: 25 });
      
      // Notify backend
      await api.approveProposal(proposal.id);
      
      // Show success
      vscode.window.showInformationMessage(
        `✓ Applied: ${proposal.title}`,
        'View Changes',
        'Push Branch'
      ).then(action => {
        if (action === 'View Changes') {
          vscode.commands.executeCommand('git.openChanges');
        } else if (action === 'Push Branch') {
          git.push();
        }
      });
    });
  }
}
```

### Feature 3: Inline CodeLens

```typescript
// src/providers/codelens.ts
export class ProposalCodeLensProvider implements vscode.CodeLensProvider {
  async provideCodeLenses(document: vscode.TextDocument): Promise<vscode.CodeLens[]> {
    const proposals = await api.getProposals();
    const lenses: vscode.CodeLens[] = [];
    
    for (const proposal of proposals) {
      // Find relevant lines in this document
      for (const change of proposal.changes) {
        if (change.file === document.fileName) {
          const range = this.getAffectedRange(document, change);
          
          lenses.push(new vscode.CodeLens(range, {
            title: `💡 ${proposal.agent} suggests: ${proposal.title}`,
            command: 'contextpilot.previewProposal',
            arguments: [proposal.id]
          }));
        }
      }
    }
    
    return lenses;
  }
}
```

---

## 📦 Distribution

### VSCode Marketplace

```json
{
  "name": "contextpilot-vscode",
  "displayName": "ContextPilot",
  "description": "AI agents that suggest code improvements you can approve",
  "version": "0.1.0",
  "publisher": "contextpilot-team",
  "engines": {
    "vscode": "^1.80.0"
  },
  "categories": ["Other"],
  "keywords": ["ai", "agents", "refactor", "productivity"],
  "repository": {
    "type": "git",
    "url": "https://github.com/contextpilot/vscode-extension"
  }
}
```

### Open VSX (for Cursor, VSCodium)

Same package published to https://open-vsx.org/

---

## 🚀 Development

```bash
# Clone extension repo
git clone https://github.com/contextpilot/vscode-extension
cd vscode-extension

# Install dependencies
npm install

# Run in development mode
npm run dev

# This opens Extension Development Host

# Package for distribution
vsce package

# Publish to marketplace
vsce publish
```

---

## 🎯 Roadmap

### v0.1 (MVP - Week 3-4)
- [x] Proposals panel
- [x] Basic diff preview
- [ ] Apply/Reject actions
- [ ] API integration

### v0.2 (Week 5-6)
- [ ] Inline CodeLens
- [ ] Hover provider
- [ ] Coach nudges
- [ ] Rewards display

### v0.3 (Week 7-8)
- [ ] Batch approval
- [ ] Custom rules
- [ ] PR integration
- [ ] Slack notifications

### v1.0 (Month 3)
- [ ] Full feature parity
- [ ] Cursor support
- [ ] Performance optimization
- [ ] Comprehensive docs

---

**Status:** 📐 **Architecture defined**  
**Next:** Build MVP extension  
**ETA:** Week 3-4 of hackathon prep

