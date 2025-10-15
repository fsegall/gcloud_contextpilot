import * as vscode from 'vscode';
import { ContextPilotService, ChangeProposal } from '../services/contextpilot';
import { CoachProvider } from '../views/coach';

export async function connect(service: ContextPilotService): Promise<void> {
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Connecting to ContextPilot...',
        cancellable: false,
      },
      async () => {
        await service.connect();
      }
    );

    vscode.window.showInformationMessage('✅ Connected to ContextPilot!');
    vscode.commands.executeCommand('setContext', 'contextpilot.connected', true);
  } catch (error) {
    vscode.window.showErrorMessage(
      '❌ Failed to connect to ContextPilot. Is the backend running?'
    );
  }
}

export function disconnect(service: ContextPilotService): void {
  service.disconnect();
  vscode.window.showInformationMessage('Disconnected from ContextPilot');
  vscode.commands.executeCommand('setContext', 'contextpilot.connected', false);
}

export async function approveProposal(
  service: ContextPilotService,
  proposalId: string,
  proposalsProvider?: any
): Promise<void> {
  const confirmed = await vscode.window.showWarningMessage(
    'Approve this change proposal?',
    { modal: true },
    'Approve'
  );

  if (confirmed !== 'Approve') {
    return;
  }

  const result = await service.approveProposal(proposalId);
  if (result.ok) {
    // Refresh proposals view
    if (proposalsProvider) {
      proposalsProvider.refresh();
    }
    
    if (result.autoCommitted) {
      vscode.window.showInformationMessage(
        `✅ Proposal approved and committed! (${result.commitHash?.slice(0,7)})`
      );
    } else {
      vscode.window.showInformationMessage(
        '✅ Proposal approved (pending commit by Git Agent)'
      );
    }
  } else {
    vscode.window.showErrorMessage('❌ Failed to approve proposal');
  }
}

export async function rejectProposal(
  service: ContextPilotService,
  proposalId: string
): Promise<void> {
  const reason = await vscode.window.showInputBox({
    prompt: 'Why are you rejecting this proposal? (optional)',
    placeHolder: 'Reason for rejection...',
  });

  const success = await service.rejectProposal(proposalId, reason);
  if (success) {
    vscode.window.showInformationMessage('Proposal rejected');
  } else {
    vscode.window.showErrorMessage('Failed to reject proposal');
  }
}

export async function viewRewards(service: ContextPilotService): Promise<void> {
  try {
    const balance = await service.getBalance();
    const leaderboard = await service.getLeaderboard();

    const panel = vscode.window.createWebviewPanel(
      'contextpilotRewards',
      'CPT Rewards',
      vscode.ViewColumn.One,
      {}
    );

    panel.webview.html = getRewardsWebviewContent(balance, leaderboard);
  } catch (error) {
    vscode.window.showErrorMessage('Failed to load rewards');
  }
}

export async function askCoach(
  service: ContextPilotService,
  coachProvider: CoachProvider
): Promise<void> {
  const question = await vscode.window.showInputBox({
    prompt: 'Ask the Coach Agent anything about your project',
    placeHolder: 'How can I improve my code structure?',
  });

  if (!question) {
    return;
  }

  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Coach is thinking...',
        cancellable: false,
      },
      async () => {
        const answer = await service.askCoach(question);
        coachProvider.addMessage(question, answer);
        vscode.window.showInformationMessage('Coach responded!');
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage('Failed to get coach response');
  }
}

export async function commitContext(service: ContextPilotService): Promise<void> {
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Committing context...',
        cancellable: false,
      },
      async () => {
        await service.commitContext();
      }
    );

    vscode.window.showInformationMessage(
      '✅ Context committed! Agents will analyze your changes.'
    );
  } catch (error) {
    vscode.window.showErrorMessage('Failed to commit context');
  }
}

// ===== COMMANDS USING REAL API =====

// Helper to get workspace ID
function getWorkspaceId(): string {
  // Try to get from workspace folder name
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (workspaceFolders && workspaceFolders.length > 0) {
    const folderName = workspaceFolders[0].name.toLowerCase().replace(/[^a-z0-9]/g, '-');
    // If it's "google-context-pilot" or similar, use "contextpilot"
    if (folderName.includes('context') && folderName.includes('pilot')) {
      return 'contextpilot';
    }
    return folderName;
  }
  // Default fallback
  return 'contextpilot';
}

export async function getContextCommand(service: ContextPilotService): Promise<void> {
  try {
    const workspaceId = getWorkspaceId();
    vscode.window.showInformationMessage(`📦 Loading context from workspace: ${workspaceId}...`);
    
    const context = await service.getContextReal(workspaceId);
    
    if (context) {
      const checkpoint = context.checkpoint || {};
      const message = `📦 Project: ${checkpoint.project_name || 'N/A'}
🎯 Goal: ${checkpoint.goal || 'N/A'}
📊 Status: ${checkpoint.current_status || 'N/A'}
🗓️ Milestones: ${(checkpoint.milestones || []).length}`;
      
      vscode.window.showInformationMessage(message);
    } else {
      vscode.window.showErrorMessage('Failed to load context');
    }
  } catch (error) {
    vscode.window.showErrorMessage('Error loading context');
  }
}

export async function commitContextReal(service: ContextPilotService): Promise<void> {
  try {
    const workspaceId = getWorkspaceId();
    const message = await vscode.window.showInputBox({
      prompt: 'Enter commit message',
      placeHolder: 'Updated project context',
      value: 'Context update via ContextPilot extension'
    });

    if (!message) {
      return; // User cancelled
    }

    vscode.window.showInformationMessage(`💾 Committing to workspace: ${workspaceId}...`);
    
    const success = await service.commitChangesReal(message, 'extension', workspaceId);
    
    if (success) {
      vscode.window.showInformationMessage('✅ Context committed successfully!');
    } else {
      vscode.window.showErrorMessage('❌ Failed to commit context');
    }
  } catch (error) {
    vscode.window.showErrorMessage('Error committing context');
  }
}

export async function getCoachTipCommand(service: ContextPilotService): Promise<void> {
  try {
    const workspaceId = getWorkspaceId();
    vscode.window.showInformationMessage(`🧠 Coach is thinking (workspace: ${workspaceId})...`);
    
    const tip = await service.getCoachTipReal(workspaceId);
    
    vscode.window.showInformationMessage(`🧠 Coach: ${tip}`, 'OK');
  } catch (error) {
    vscode.window.showErrorMessage('Error getting coach tip');
  }
}

// ===== PROPOSAL DIFF COMMANDS =====

export async function viewProposalDiff(
  service: ContextPilotService,
  proposalId: string
): Promise<void> {
  try {
    // Fetch proposal with diff
    const proposal = await service.getProposal(proposalId);
    
    if (!proposal) {
      vscode.window.showErrorMessage('Proposal not found');
      return;
    }
    
    // Create virtual document with diff
    const uri = vscode.Uri.parse(`contextpilot-diff:${proposalId}.diff`);
    const content = proposal.diff?.content || 'No diff available';
    
    // Show diff in editor
    const doc = await vscode.workspace.openTextDocument({
      content: content,
      language: 'diff'
    });
    
    await vscode.window.showTextDocument(doc, { preview: false });
    
    // Show quick actions
    const action = await vscode.window.showQuickPick([
      {
        label: '$(robot) Ask Claude to Review',
        description: 'Get AI feedback on these changes',
        action: 'review'
      },
      {
        label: '$(check) Approve',
        description: 'Apply these changes',
        action: 'approve'
      },
      {
        label: '$(x) Reject',
        description: 'Decline these changes',
        action: 'reject'
      },
      {
        label: '$(eye) View Files',
        description: 'See affected files',
        action: 'files'
      }
    ], {
      placeHolder: `Review proposal: ${proposal.title}`
    });
    
    if (action?.action === 'review') {
      await askClaudeToReview(proposal);
    } else if (action?.action === 'approve') {
      await approveProposal(service, proposalId);
    } else if (action?.action === 'reject') {
      await rejectProposal(service, proposalId);
    } else if (action?.action === 'files') {
      await showProposalFiles(proposal);
    }
  } catch (error) {
    vscode.window.showErrorMessage('Failed to view proposal diff');
  }
}

// Global review panel for maintaining context
let reviewPanel: any = null;

export function setReviewPanel(panel: any): void {
  reviewPanel = panel;
}

// Global chat session ID for maintaining context
let contextPilotChatSessionId: string | undefined;

async function askClaudeToReview(proposal: ChangeProposal): Promise<void> {
  // If review panel is available, use it
  if (reviewPanel) {
    await reviewPanel.showReview(proposal);
    return;
  }
  
  // Fallback to clipboard + chat
  // Prepare context for Claude
  const filesAffected = proposal.proposed_changes
    .map(c => `- **${c.file_path}** (${c.change_type}): ${c.description}`)
    .join('\n');
  
  const context = `# Review Change Proposal #${proposal.id}

**Title:** ${proposal.title}
**Description:** ${proposal.description}
**Agent:** ${proposal.agent_id}

## Proposed Changes

\`\`\`diff
${proposal.diff.content}
\`\`\`

## Files Affected
${filesAffected}

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
  
  try {
    // Try to use Cursor's chat API with session persistence
    // Option 1: Use chat participant API (if available)
    const chatOptions = {
      prompt: context,
      // Try to maintain session
      sessionId: contextPilotChatSessionId
    };
    
    // Try to open chat with context directly
    const result = await vscode.commands.executeCommand(
      'workbench.action.chat.open',
      chatOptions
    );
    
    // Store session ID if returned
    if (result && typeof result === 'object' && 'sessionId' in result) {
      contextPilotChatSessionId = (result as any).sessionId;
    }
    
    // Also copy to clipboard as fallback
    await vscode.env.clipboard.writeText(context);
    
    vscode.window.showInformationMessage(
      '🤖 Chat opened with review context. If not auto-filled, paste from clipboard (Cmd+V).'
    );
  } catch (error) {
    // Fallback: Just copy to clipboard and open chat
    await vscode.env.clipboard.writeText(context);
    
    const result = await vscode.window.showInformationMessage(
      '📋 Review context copied to clipboard! Open Cursor Chat and paste to ask Claude.',
      'Open Chat',
      'OK'
    );
    
    if (result === 'Open Chat') {
      await vscode.commands.executeCommand('workbench.action.chat.open');
    }
  }
}

// Export function to reset chat session if needed
export function resetChatSession(): void {
  contextPilotChatSessionId = undefined;
  
  // Also clear review panel history
  if (reviewPanel) {
    reviewPanel.clearHistory();
  }
  
  vscode.window.showInformationMessage('🔄 Chat session reset. Next review will start a fresh conversation.');
}

async function showProposalFiles(proposal: ChangeProposal): Promise<void> {
  const files = proposal.proposed_changes.map(c => c.file_path);
  
  const selected = await vscode.window.showQuickPick(files, {
    placeHolder: 'Select file to view'
  });
  
  if (selected) {
    // Try to open the file
    const uri = vscode.Uri.file(vscode.workspace.workspaceFolders?.[0].uri.fsPath + '/' + selected);
    try {
      await vscode.window.showTextDocument(uri);
    } catch {
      vscode.window.showWarningMessage(`File ${selected} does not exist yet`);
    }
  }
}

function getRewardsWebviewContent(balance: any, leaderboard: any[]): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPT Rewards</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
        }
        .balance-card {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .balance-value {
            font-size: 48px;
            font-weight: bold;
            color: var(--vscode-charts-yellow);
        }
        .leaderboard {
            margin-top: 20px;
        }
        .leaderboard-item {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        .leaderboard-item:hover {
            background: var(--vscode-list-hoverBackground);
        }
    </style>
</head>
<body>
    <div class="balance-card">
        <h2>Your Balance</h2>
        <div class="balance-value">⭐ ${balance.balance} CPT</div>
        <p>Total Earned: ${balance.total_earned} CPT</p>
        <p>Pending Rewards: ${balance.pending_rewards} CPT</p>
    </div>

    <div class="leaderboard">
        <h2>🏆 Leaderboard</h2>
        ${leaderboard
          .slice(0, 10)
          .map(
            (item, index) => `
            <div class="leaderboard-item">
                <span>${index + 1}. ${item.user_id.substring(0, 8)}...</span>
                <span>${item.balance} CPT</span>
            </div>
        `
          )
          .join('')}
    </div>
</body>
</html>`;
}

