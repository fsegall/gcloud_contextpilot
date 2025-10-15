import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';
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
  proposalId: string
): Promise<void> {
  const confirmed = await vscode.window.showWarningMessage(
    'Approve this change proposal?',
    { modal: true },
    'Approve'
  );

  if (confirmed !== 'Approve') {
    return;
  }

  const success = await service.approveProposal(proposalId);
  if (success) {
    vscode.window.showInformationMessage(
      '✅ Proposal approved! You earned CPT tokens 🎉'
    );
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

