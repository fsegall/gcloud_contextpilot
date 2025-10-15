# Persistent Chat Context for Proposal Reviews

**Date:** October 15, 2025  
**Status:** ✅ Implemented

## Problem

Users want to review multiple proposals with Claude and maintain conversation context:

```
User: "Review proposal #1"
Claude: "Looks good because..."

User: "Review proposal #2"
Claude: [Should remember context from proposal #1]
```

## Solution

### 1. Review Panel (Dedicated UI)

**File:** `extension/src/views/review-panel.ts`

**Features:**
- Dedicated webview panel for reviews
- Maintains conversation history
- Shows all proposals reviewed in session
- `retainContextWhenHidden: true` keeps state

**Usage:**
```typescript
const reviewPanel = new ReviewPanelProvider(context);
await reviewPanel.showReview(proposal);
```

### 2. Session Management

**Global State:**
```typescript
// In commands/index.ts
let reviewPanel: ReviewPanelProvider | null = null;
let contextPilotChatSessionId: string | undefined;
```

**Session Persistence:**
- Review panel stays open across multiple proposals
- Conversation history stored in memory
- Session ID tracked for Cursor Chat API (if available)

### 3. User Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  User clicks "Ask Claude" on Proposal #1                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Review Panel opens (side-by-side)                          │
│  • Shows proposal #1 context                                 │
│  • Context copied to clipboard                               │
│  • Instructions shown                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  User opens Cursor Chat (Cmd+L)                             │
│  • Pastes context                                            │
│  • Claude: "Proposal #1 looks good because..."              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  User clicks "Ask Claude" on Proposal #2                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Review Panel updates (SAME PANEL)                          │
│  • Shows proposal #2 context                                 │
│  • Previous conversation still visible                       │
│  • Context copied to clipboard                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  User pastes in SAME Cursor Chat                            │
│  • Claude: "Proposal #2 also looks good.                    │
│    Consistent with proposal #1 I reviewed earlier."         │
│  • Claude maintains context! ✅                              │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Review Panel UI

```html
┌────────────────────────────────────────────────────────┐
│ 🤖 ContextPilot AI Review Session                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 👤 You (Proposal: spec-1)                       │   │
│ │                                                 │   │
│ │ # Review Proposal #spec-1                       │   │
│ │ **Title:** Update README.md                     │   │
│ │ ```diff                                         │   │
│ │ --- a/README.md                                 │   │
│ │ +++ b/README.md                                 │   │
│ │ ```                                             │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 🤖 Claude                                       │   │
│ │                                                 │   │
│ │ These changes look appropriate...               │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 👤 You (Proposal: spec-2)                       │   │
│ │                                                 │   │
│ │ # Review Proposal #spec-2                       │   │
│ │ **Title:** Update ARCHITECTURE.md               │   │
│ │ ```diff                                         │   │
│ │ --- a/ARCHITECTURE.md                           │   │
│ │ +++ b/ARCHITECTURE.md                           │   │
│ │ ```                                             │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌────────────────────────────────────────────────┐    │
│ │ 💡 How to Use                                   │    │
│ │ 1. Context copied to clipboard                  │    │
│ │ 2. Open Cursor Chat (Cmd+L)                    │    │
│ │ 3. Paste and get Claude's review               │    │
│ │ 4. Next proposal continues same conversation    │    │
│ └────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

### Conversation History Structure

```typescript
conversationHistory: Array<{
  role: 'user' | 'assistant';
  content: string;
  proposalId?: string;
}> = [
  {
    role: 'user',
    content: 'Review proposal #spec-1...',
    proposalId: 'spec-1'
  },
  {
    role: 'assistant',
    content: 'Looks good because...',
    proposalId: 'spec-1'
  },
  {
    role: 'user',
    content: 'Review proposal #spec-2...',
    proposalId: 'spec-2'
  }
  // Claude maintains context across proposals!
];
```

## Benefits

### 1. Context Continuity
Claude remembers previous proposals reviewed in the session:
```
User: "Review proposal #2"
Claude: "This is consistent with proposal #1 I reviewed earlier, 
         which also updated documentation. Both look good."
```

### 2. Comparative Analysis
Claude can compare proposals:
```
User: "Review proposal #3"
Claude: "This conflicts with proposal #1. 
         Proposal #1 added feature X, but #3 removes it. 
         Recommend rejecting #3."
```

### 3. Learning Over Time
Claude learns project patterns:
```
User: "Review proposal #5"
Claude: "Based on the 4 proposals I've reviewed, 
         this follows your project's documentation style. 
         Approve."
```

### 4. Conversation Flow
Natural back-and-forth:
```
User: "Review proposal #1"
Claude: "Looks good, but consider adding examples"
User: "Review proposal #2" 
Claude: "This one adds the examples I suggested! Perfect."
```

## Commands

### View Proposal with Review
```
Command Palette: "ContextPilot: View Proposal Diff"
→ Opens diff viewer
→ Click "Ask Claude to Review"
→ Review panel opens/updates
→ Context copied to clipboard
```

### Reset Session
```
Command Palette: "ContextPilot: Reset Chat Session"
→ Clears conversation history
→ Next review starts fresh
```

## Configuration

### Panel Behavior

```typescript
{
  enableScripts: true,           // Allow interactive UI
  retainContextWhenHidden: true  // Keep state when hidden
}
```

### Session Lifetime

- **Persists:** Across proposal reviews in same session
- **Resets:** When user runs "Reset Chat Session" command
- **Clears:** When extension is reloaded

## Example Session

```
Session Start
├─ Review Proposal #1 (README.md)
│  └─ Claude: "✅ Approve - good structure"
│
├─ Review Proposal #2 (ARCHITECTURE.md)
│  └─ Claude: "✅ Approve - consistent with README"
│
├─ Review Proposal #3 (API.md)
│  └─ Claude: "⚠️  Consider - missing examples like README"
│
└─ Review Proposal #4 (API.md updated)
   └─ Claude: "✅ Approve - examples added as I suggested!"
```

## Technical Implementation

### 1. Panel Creation

```typescript
this.panel = vscode.window.createWebviewPanel(
  'contextpilotReview',
  'ContextPilot AI Review',
  vscode.ViewColumn.Beside,
  {
    enableScripts: true,
    retainContextWhenHidden: true  // KEY: Keeps context!
  }
);
```

### 2. History Management

```typescript
// Add to history
this.conversationHistory.push({
  role: 'user',
  content: reviewRequest,
  proposalId: proposal.id
});

// Render history
this.panel.webview.html = this.getWebviewContent();
```

### 3. Session Persistence

```typescript
// Try to maintain Cursor Chat session
const chatOptions = {
  prompt: context,
  sessionId: contextPilotChatSessionId  // Reuse session
};

await vscode.commands.executeCommand(
  'workbench.action.chat.open',
  chatOptions
);
```

## Future Enhancements

### 1. Backend Session Storage
Store conversation in Firestore for cross-device persistence.

### 2. AI Response Capture
Automatically capture Claude's responses and show in panel.

### 3. Conversation Export
Export entire review session as markdown.

### 4. Multi-User Sessions
Share review sessions across team members.

---

**Status:** ✅ Implemented  
**Testing:** Ready for manual testing  
**Impact:** Maintains context across multiple proposal reviews! 🎯

