# Proposal Diffs + AI Review - Implementation Plan

**Date:** October 15, 2025  
**Status:** 🚧 In Progress

## Problem Identified

Users in Cursor want to:
1. See **actual code changes** in proposals (not just metadata)
2. Ask **Claude/AI** to review changes before approving
3. Make **informed decisions** about what to commit

**Current Gap:**
- ❌ Proposals only have metadata (title, description)
- ❌ No diff/patch to show actual changes
- ❌ No integration with Cursor's AI

## Solution Architecture

### 1. Enhanced Proposal Structure

```typescript
interface ChangeProposal {
  id: string;
  agent_id: string;
  title: string;
  description: string;
  
  // NEW: Complete diff
  diff: {
    format: 'unified' | 'git-patch';
    content: string;  // Full diff
  };
  
  // NEW: Per-file changes with before/after
  proposed_changes: Array<{
    file_path: string;
    change_type: 'create' | 'update' | 'delete';
    description: string;
    before?: string;  // Current content
    after?: string;   // Proposed content
    diff?: string;    // File-specific diff
  }>;
  
  status: 'pending' | 'approved' | 'rejected';
  
  // NEW: AI review results
  ai_review?: {
    model: string;
    verdict: 'approve' | 'reject' | 'needs_changes';
    reasoning: string;
    concerns: string[];
    suggestions: string[];
  };
}
```

### 2. Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Spec Agent Generates Proposal with Diff            │
├─────────────────────────────────────────────────────────────┤
│  - Detects issue (e.g., README outdated)                    │
│  - Uses Gemini to generate new content                      │
│  - Creates unified diff                                      │
│  - Saves proposal with diff                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Extension Shows Proposal                           │
├─────────────────────────────────────────────────────────────┤
│  - Notification: "New proposal from Spec Agent"             │
│  - Sidebar: Proposal list with badges                       │
│  - Click to view details                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: User Views Diff                                    │
├─────────────────────────────────────────────────────────────┤
│  - Opens diff in editor                                      │
│  - Syntax highlighted                                        │
│  - Side-by-side or unified view                             │
│  - Quick actions: "Ask Claude" | "Approve" | "Reject"       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Ask Claude to Review (Optional)                    │
├─────────────────────────────────────────────────────────────┤
│  - Extension prepares context with diff                     │
│  - Opens Cursor Chat                                         │
│  - User: "Are these changes good?"                          │
│  - Claude analyzes and responds                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 5: User Approves                                      │
├─────────────────────────────────────────────────────────────┤
│  - Extension calls POST /proposals/{id}/approve             │
│  - Backend publishes proposal.approved event                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Git Agent Applies Patch                            │
├─────────────────────────────────────────────────────────────┤
│  - Receives proposal.approved event                         │
│  - Applies diff/patch to files                              │
│  - Commits with semantic message                            │
│  - Publishes git.commit event                               │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Checklist

### Phase 1: Backend (Current)
- [x] Create Proposal models with diff support
- [x] Create diff_generator utility
- [ ] Update Spec Agent to generate diffs
- [ ] Update API endpoints to return diffs
- [ ] Add endpoint for AI review
- [ ] Update Git Agent to apply patches

### Phase 2: Extension
- [ ] Update ChangeProposal interface
- [ ] Create diff viewer component
- [ ] Add "View Diff" command
- [ ] Add "Ask Claude" integration
- [ ] Update approval flow to show diff first
- [ ] Add side-by-side diff view

### Phase 3: AI Integration
- [ ] Claude prompt templates for review
- [ ] Backend endpoint for AI review
- [ ] Extension: Open Cursor Chat with context
- [ ] Store AI review results in proposal
- [ ] Show AI verdict in UI

### Phase 4: Git Operations
- [ ] Patch application in Git Agent
- [ ] Rollback mechanism
- [ ] Conflict detection
- [ ] Manual merge support

## Files Created/Modified

### New Files
- `back-end/app/models/proposal.py` - Pydantic models
- `back-end/app/agents/diff_generator.py` - Diff utilities
- `PROPOSAL_DIFFS_PLAN.md` - This file

### To Modify
- `back-end/app/agents/spec_agent.py` - Generate diffs
- `back-end/app/agents/git_agent.py` - Apply patches
- `back-end/app/server.py` - API endpoints
- `extension/src/services/contextpilot.ts` - Updated interface
- `extension/src/commands/proposals.ts` - Diff viewer
- `extension/src/views/proposals.ts` - UI updates

## Example: Spec Agent Generating Diff

```python
# back-end/app/agents/spec_agent.py

from app.agents.diff_generator import generate_unified_diff, read_file_safe
from app.models.proposal import ChangeProposal, ProposedChange, ProposalDiff

async def _create_proposal_with_diff(self, issue: Dict) -> str:
    """Create proposal with actual diff"""
    
    # 1. Read current content
    current_content = read_file_safe(issue['file'], self.workspace_path)
    
    # 2. Generate new content using Gemini
    proposed_content = await self._generate_content_with_gemini(
        file_path=issue['file'],
        issue_description=issue['message'],
        current_content=current_content
    )
    
    # 3. Generate diff
    diff_content = generate_unified_diff(
        file_path=issue['file'],
        old_content=current_content,
        new_content=proposed_content
    )
    
    # 4. Create proposal
    proposal = ChangeProposal(
        id=f"spec-{datetime.now().timestamp()}",
        agent_id="spec",
        workspace_id=self.workspace_id,
        title=f"Update {issue['file']}",
        description=issue['message'],
        diff=ProposalDiff(
            format="unified",
            content=diff_content
        ),
        proposed_changes=[
            ProposedChange(
                file_path=issue['file'],
                change_type='update' if current_content else 'create',
                description=issue['message'],
                before=current_content,
                after=proposed_content,
                diff=diff_content
            )
        ]
    )
    
    # 5. Save and publish
    await self._save_proposal(proposal)
    await self.publish_event(
        topic=Topics.PROPOSAL_EVENTS,
        event_type=EventTypes.PROPOSAL_CREATED,
        data={'proposal_id': proposal.id}
    )
    
    return proposal.id
```

## Example: Extension Showing Diff

```typescript
// extension/src/commands/proposals.ts

export async function viewProposalDiff(
  service: ContextPilotService,
  proposalId: string
): Promise<void> {
  // 1. Fetch proposal with diff
  const proposal = await service.getProposal(proposalId);
  
  // 2. Create virtual document
  const uri = vscode.Uri.parse(`contextpilot-diff:${proposalId}.diff`);
  const provider = new DiffContentProvider(proposal);
  vscode.workspace.registerTextDocumentContentProvider('contextpilot-diff', provider);
  
  // 3. Open diff
  const doc = await vscode.workspace.openTextDocument(uri);
  await vscode.window.showTextDocument(doc, { preview: false });
  
  // 4. Show quick actions
  const action = await vscode.window.showQuickPick([
    {
      label: '$(robot) Ask Claude to Review',
      description: 'Get AI feedback on these changes'
    },
    {
      label: '$(check) Approve',
      description: 'Apply these changes'
    },
    {
      label: '$(x) Reject',
      description: 'Decline these changes'
    }
  ]);
  
  if (action?.label.includes('Claude')) {
    await askClaudeToReview(proposal);
  } else if (action?.label.includes('Approve')) {
    await approveProposal(service, proposalId);
  }
}

async function askClaudeToReview(proposal: ChangeProposal): Promise<void> {
  // Prepare context for Claude
  const context = `
# Review Change Proposal

**Title:** ${proposal.title}
**Description:** ${proposal.description}
**Agent:** ${proposal.agent_id}

## Proposed Changes

\`\`\`diff
${proposal.diff.content}
\`\`\`

## Files Affected
${proposal.proposed_changes.map(c => 
  `- **${c.file_path}** (${c.change_type}): ${c.description}`
).join('\n')}

## Review Request

Please analyze these proposed changes and tell me:
1. Are they appropriate for this project?
2. Any potential issues or concerns?
3. Should I approve or reject?

Consider:
- Code quality and best practices
- Project conventions and style
- Potential side effects
- Documentation completeness
- Security implications
`;
  
  // Open Cursor Chat with context
  await vscode.commands.executeCommand(
    'workbench.action.chat.open',
    { query: context }
  );
}
```

## Benefits

1. **Transparency**: Users see exact changes before approving
2. **AI-Assisted**: Claude helps review changes
3. **Safety**: No blind approvals
4. **Learning**: Users learn from AI feedback
5. **Trust**: Builds confidence in agent suggestions

## Next Steps

1. Complete Spec Agent diff generation
2. Update API endpoints
3. Build extension diff viewer
4. Test end-to-end flow
5. Add AI review integration

---

**Status:** 🚧 Phase 1 in progress  
**ETA:** 2-3 hours for complete implementation

