import * as vscode from 'vscode';
import { ContextPilotService, ChangeProposal, ProposedChange } from '../services/contextpilot';
import { CoachProvider } from '../views/coach';
import * as path from 'path';
import * as fs from 'fs';
import * as yaml from 'js-yaml';
import simpleGit from 'simple-git';

function inferLanguageId(filePath: string): string {
  const ext = path.extname(filePath || '').toLowerCase();
  switch (ext) {
    case '.ts':
    case '.tsx':
      return 'typescript';
    case '.js':
    case '.mjs':
      return 'javascript';
    case '.jsx':
      return 'javascriptreact';
    case '.py':
      return 'python';
    case '.json':
      return 'json';
    case '.md':
      return 'markdown';
    case '.yml':
    case '.yaml':
      return 'yaml';
    case '.sh':
    case '.bash':
      return 'shellscript';
    case '.rb':
      return 'ruby';
    case '.go':
      return 'go';
    case '.java':
      return 'java';
    case '.cs':
      return 'csharp';
    case '.cpp':
    case '.cxx':
      return 'cpp';
    case '.c':
      return 'c';
    case '.swift':
      return 'swift';
    case '.rs':
      return 'rust';
    case '.kt':
      return 'kotlin';
    default:
      return 'plaintext';
  }
}

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
    
    // Refresh all views by calling refresh methods directly
    // Note: We can't use executeCommand for refresh as those commands don't exist
    // The providers will auto-refresh when needed
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
  console.log(`[approveProposal] Called with proposalId: ${proposalId}`);
  
  try {
    // 1. Get workspace root
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
      vscode.window.showErrorMessage('No workspace folder open');
      return;
    }
    
    // 2. Get full proposal with diff
    const proposal = await service.getProposal(proposalId);
    if (!proposal) {
      vscode.window.showErrorMessage('Proposal not found');
      return;
    }
    
    // 3. Confirm approval
    const confirmed = await vscode.window.showWarningMessage(
      `Approve: ${proposal.title}?`,
      { modal: true },
      'Approve & Commit'
    );

    if (confirmed !== 'Approve & Commit') {
      return;
    }

    // 4. Approve in backend (updates Firestore and awards CPTs automatically)
    console.log(`[approveProposal] Marking as approved in backend: ${proposalId}`);
    const result = await service.approveProposal(proposalId);
    if (!result.ok) {
      vscode.window.showErrorMessage('Failed to approve proposal in backend');
      return;
    }

    // 5. Get updated balance and show reward notification
    try {
      const balanceData = await service.getBalance();
      const rewardPoints = 25; // Backend awards 25 CPT for proposal approval
      
      // Show reward notification with actual balance from backend
      vscode.window.showInformationMessage(
        `🎉 +${rewardPoints} CPT! Total: ${balanceData.balance} CPT`,
        'View Rewards'
      ).then(selection => {
        if (selection === 'View Rewards') {
          vscode.commands.executeCommand('contextpilot.viewRewards');
        }
      });
    } catch (rewardError) {
      console.warn('[approveProposal] Failed to fetch updated balance:', rewardError);
      // Don't fail the approval for reward errors
      vscode.window.showInformationMessage('✅ Proposal approved!');
    }
    
    // 6. Apply changes locally
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Applying proposal changes...',
        cancellable: false
      },
      async (progress) => {
        progress.report({ message: 'Applying diff to files...' });
        
        for (const change of proposal.proposed_changes) {
          const filePath = path.join(workspaceRoot, change.file_path);
          
          if (change.change_type === 'delete') {
            if (fs.existsSync(filePath)) {
              await fs.promises.unlink(filePath);
              console.log(`[approveProposal] Deleted: ${change.file_path}`);
            }
          } else {
            // Create or update file
            await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
            const content = change.after || '';
            await fs.promises.writeFile(filePath, content, 'utf-8');
            console.log(`[approveProposal] ${change.change_type}: ${change.file_path}`);
          }
        }
        
        progress.report({ message: 'Committing changes...' });
        
        // 6. Git commit
        const git = simpleGit(workspaceRoot);
        await git.add('.');
        
        const commitMsg = `feat(contextpilot): ${proposal.title}

${proposal.description}

Applied by ContextPilot Extension.
Proposal-ID: ${proposalId}
Agent: ${proposal.agent_id}`;
        
        const commitResult = await git.commit(commitMsg);
        console.log(`[approveProposal] Committed: ${commitResult.commit}`);
        
        // 7. Refresh UI
        if (proposalsProvider) {
          proposalsProvider.refresh();
        }
        
        vscode.window.showInformationMessage(
          `✅ ${proposal.title} - Committed: ${commitResult.commit.slice(0, 7)}`
        );
      }
    );
    
    // 8. Start polling for new proposal after retrospective
    // After approving, agents may run a retrospective and create a new proposal
    const workspaceId = 'contextpilot'; // Default workspace
    const startTime = new Date().toISOString();
    
    // Poll for new proposals (agents may create proposals after retrospective)
    const pollInterval = setInterval(async () => {
      try {
        const status = await service.getRetrospectiveStatus(workspaceId, startTime);
        
        if (status.has_new_proposal && status.latest_proposal) {
          clearInterval(pollInterval);
          
          // Force refresh of proposals tree
          if (proposalsProvider) {
            proposalsProvider.refresh();
          }
          
          // Show notification and reload window
          const action = await vscode.window.showInformationMessage(
            `🎉 Nova proposta criada após retrospectiva: ${status.latest_proposal.title}`,
            'Recarregar Janela'
          );
          
          if (action === 'Recarregar Janela') {
            // Reload the window to show the new proposal
            await vscode.commands.executeCommand('workbench.action.reloadWindow');
          }
        }
      } catch (error) {
        console.error('[approveProposal] Error polling retrospective status:', error);
      }
    }, 5000); // Poll every 5 seconds
    
    // Stop polling after 5 minutes (retrospectives usually complete within 2-5 minutes)
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 5 * 60 * 1000);
    
  } catch (error: any) {
    console.error('[approveProposal] Error:', error);
    vscode.window.showErrorMessage(`Error approving proposal: ${error.message}`);
  }
}

export async function rejectProposal(
  service: ContextPilotService,
  proposalId: string,
  proposalsProvider?: any
): Promise<void> {
  const reason = await vscode.window.showInputBox({
    prompt: 'Why are you rejecting this proposal? (optional)',
    placeHolder: 'Reason for rejection...',
  });

  const success = await service.rejectProposal(proposalId, reason);
  if (success) {
    vscode.window.showInformationMessage('Proposal rejected');
    // Refresh the proposals list to remove rejected proposal
    if (proposalsProvider) {
      proposalsProvider.refresh();
    }
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
    prompt: 'Ask the Strategy Coach Agent anything about your project',
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
    console.log(`[viewProposalDiff] Called with proposalId: ${proposalId}`);
    
    // Fetch proposal with diff
    const proposal = await service.getProposal(proposalId);
    
    if (!proposal) {
      vscode.window.showErrorMessage('Proposal not found');
      return;
    }
    
    // Generate content - try diff first, fallback to description + changes
    let content = proposal.diff?.content || '';
    
    if (!content) {
      // Fallback: generate pseudo-diff from proposed_changes
      content = `# ${proposal.title}\n\n${proposal.description}\n\n`;
      content += `## Proposed Changes:\n\n`;
      
      for (const change of proposal.proposed_changes) {
        content += `### ${change.file_path} (${change.change_type})\n\n`;
        content += `${change.description}\n\n`;
        
        if (change.diff) {
          content += `\`\`\`diff\n${change.diff}\n\`\`\`\n\n`;
        } else if (change.after) {
          content += `**New Content:**\n\`\`\`\n${change.after}\`\`\`\n\n`;
        }
      }
    }
    
    // Create virtual document
    const uri = vscode.Uri.parse(`contextpilot-diff:${proposalId}.diff`);
    const language = proposal.diff?.content ? 'diff' : 'markdown';
    
    // Show diff in editor
    const doc = await vscode.workspace.openTextDocument({
      content: content,
      language: language
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
      await askClaudeToReview(service, proposal);
    } else if (action?.action === 'approve') {
      const next = await vscode.window.showQuickPick([
        { label: '$(robot) Ask Claude first', description: 'Open review with context, then approve', value: 'ask' },
        { label: '$(check) Approve now', description: 'Skip AI review', value: 'approve' },
        { label: '$(x) Cancel', value: 'cancel' }
      ], { placeHolder: 'Would you like to ask Claude to review before approving?' });

      if (next?.value === 'ask') {
        await askClaudeToReview(service, proposal);
        const confirmApprove = await vscode.window.showQuickPick([
          { label: '$(check) Approve after review', value: 'approve' },
          { label: '$(x) Cancel', value: 'cancel' }
        ], { placeHolder: 'Proceed to approve after Claude review?' });
        if (confirmApprove?.value === 'approve') {
          await approveProposal(service, proposalId);
        }
      } else if (next?.value === 'approve') {
        await approveProposal(service, proposalId);
      }
    } else if (action?.action === 'reject') {
      await rejectProposal(service, proposalId);
    } else if (action?.action === 'files') {
      await showProposalFiles(proposal);
    }
  } catch (error) {
    vscode.window.showErrorMessage('Failed to view proposal diff');
  }
}

export async function viewProposalChange(
  service: ContextPilotService,
  proposalId: string,
  change: ProposedChange
): Promise<void> {
  try {
    const proposal = await service.getProposal(proposalId);
    const targetChange =
      proposal?.proposed_changes.find(
        (c) => c.file_path === change.file_path && c.change_type === change.change_type
      ) || change;

    if (!targetChange) {
      vscode.window.showWarningMessage('Change details not available for this proposal.');
      return;
    }

    const languageId = inferLanguageId(targetChange.file_path);

    if (targetChange.diff) {
      const doc = await vscode.workspace.openTextDocument({
        content: targetChange.diff,
        language: 'diff'
      });
      await vscode.window.showTextDocument(doc, { preview: false });
      return;
    }

    const hasBefore = typeof targetChange.before === 'string' && targetChange.before.length > 0;
    const hasAfter = typeof targetChange.after === 'string' && targetChange.after.length > 0;

    if (hasBefore && hasAfter) {
      const beforeDoc = await vscode.workspace.openTextDocument({
        content: targetChange.before || '',
        language: languageId
      });
      const afterDoc = await vscode.workspace.openTextDocument({
        content: targetChange.after || '',
        language: languageId
      });

      await vscode.commands.executeCommand(
        'vscode.diff',
        beforeDoc.uri,
        afterDoc.uri,
        `${targetChange.file_path} (${targetChange.change_type})`
      );
      return;
    }

    if (hasAfter) {
      const doc = await vscode.workspace.openTextDocument({
        content: targetChange.after || '',
        language: languageId
      });
      await vscode.window.showTextDocument(doc, { preview: false });
      return;
    }

    if (hasBefore) {
      const doc = await vscode.workspace.openTextDocument({
        content: targetChange.before || '',
        language: languageId
      });
      await vscode.window.showTextDocument(doc, { preview: false });
      return;
    }

    vscode.window.showInformationMessage('No diff content available for this change yet.');
  } catch (error) {
    console.error('Error viewing proposal change:', error);
    vscode.window.showErrorMessage('Failed to open proposal change diff');
  }
}

export async function askClaudeReviewCommand(
  service: ContextPilotService,
  proposalId: string
): Promise<void> {
  try {
    console.log(`[askClaudeReviewCommand] Triggered for proposalId=${proposalId}`);
    const proposal = await service.getProposal(proposalId);
    console.log('[askClaudeReviewCommand] Loaded proposal:', proposal?.id, proposal?.title);
    if (!proposal) {
      vscode.window.showErrorMessage('Proposal not found');
      return;
    }

    await askClaudeToReview(service, proposal);
  } catch (error) {
    console.error('Error triggering Claude review:', error);
    vscode.window.showErrorMessage('Failed to request Claude review');
  }
}

// Global review panel for maintaining context
let reviewPanel: any = null;

export function setReviewPanel(panel: any): void {
  reviewPanel = panel;
}

// Global chat session ID for maintaining context
let contextPilotChatSessionId: string | undefined;

async function askClaudeToReview(
  service: ContextPilotService,
  proposal: ChangeProposal
): Promise<void> {
  console.log('[askClaudeToReview] Preparing review for proposal:', proposal.id);
  const workspaceId = getWorkspaceId();
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const workspaceContextDir = workspaceRoot
    ? path.join(workspaceRoot, '.contextpilot', 'workspaces', workspaceId)
    : undefined;

  // If review panel is available, use it but still attempt to open chat automatically
  let usedReviewPanel = false;
  if (reviewPanel) {
    usedReviewPanel = true;
    await reviewPanel.showReview(proposal);
  }

  const truncate = (value: string, maxLength: number) => {
    if (!value) {
      return '';
    }
    if (value.length <= maxLength) {
      return value;
    }
    return `${value.slice(0, maxLength)}\n...\n[truncated ${value.length - maxLength} chars]`;
  };

  let checkpointData: any = {};
  try {
    const contextPayload = await service.getContextReal(workspaceId);
    checkpointData = contextPayload?.checkpoint || {};
  } catch (error) {
    console.warn('[askClaudeToReview] Failed to load workspace checkpoint:', error);
  }

  const projectName = checkpointData?.project_name || '(project name not set)';
  const goal = checkpointData?.goal || '(goal not set)';
  const status = checkpointData?.current_status || '(status not set)';
  const milestoneArr: any[] = Array.isArray(checkpointData?.milestones)
    ? checkpointData.milestones
    : [];
  const milestoneLines = milestoneArr.slice(0, 6).map((m) => {
    const name = m?.name || 'Unnamed milestone';
    const state = m?.status ? ` [${m.status}]` : '';
    const due = m?.due ? ` (due ${m.due})` : '';
    return `- ${name}${state}${due}`;
  });

  let projectContextSection = `## Project Brief (workspace: ${workspaceId})
- **Name:** ${projectName}
- **Goal:** ${goal}
- **Status:** ${status}
- **Milestones tracked:** ${milestoneArr.length}`;

  if (milestoneLines.length) {
    projectContextSection += `\n\n### Milestone Snapshot\n${milestoneLines.join('\n')}`;
  }

  const artifactSections: string[] = [];
  if (workspaceContextDir && fs.existsSync(workspaceContextDir)) {
    const artifacts: Array<{ label: string; file: string; maxLength: number }> = [
      { label: 'Context', file: 'context.md', maxLength: 2000 },
      { label: 'Project Scope', file: 'project_scope.md', maxLength: 2000 },
      { label: 'Milestones Notes', file: 'milestones.md', maxLength: 2000 },
      { label: 'Project Checklist', file: 'project_checklist.md', maxLength: 1600 },
      { label: 'Daily Checklist', file: 'daily_checklist.md', maxLength: 1200 },
      { label: 'Timeline', file: 'timeline.md', maxLength: 1500 },
      { label: 'Decisions', file: 'DECISIONS.md', maxLength: 1500 },
      { label: 'Coding Standards', file: 'coding_standards.md', maxLength: 1500 },
    ];

    for (const artifact of artifacts) {
      const artifactPath = path.join(workspaceContextDir, artifact.file);
      if (fs.existsSync(artifactPath)) {
        try {
          const raw = fs.readFileSync(artifactPath, 'utf-8').trim();
          if (raw.length > 0) {
            const truncated = truncate(raw, artifact.maxLength);
            artifactSections.push(
              `### ${artifact.label}\n_Source: .contextpilot/workspaces/${workspaceId}/${artifact.file}_\n\n${truncated}`
            );
          }
        } catch (error) {
          console.warn(`[askClaudeToReview] Failed to read artifact ${artifact.file}:`, error);
        }
      }
    }
  }

  const artifactContextSection = artifactSections.length
    ? `## Workspace Artifacts\n${artifactSections.join('\n\n')}`
    : '';

  const filesAffected = proposal.proposed_changes
    .map(c => `- **${c.file_path}** (${c.change_type}): ${c.description}`)
    .join('\n');

  const fallbackDiff = proposal.proposed_changes
    .map((c) => {
      if (c.diff) { return c.diff; }
      if (c.after) { return `+++ ${c.file_path}\n${c.after}`; }
      if (c.before) { return `--- ${c.file_path}\n${c.before}`; }
      return `# ${c.change_type.toUpperCase()} ${c.file_path}`;
    })
    .join('\n\n');

  const diffContent = proposal.diff?.content || fallbackDiff || '(no diff available)';

  const promptBody = [
    projectContextSection,
    artifactContextSection,
    `## Proposed Changes\n\n\`\`\`diff\n${diffContent}\n\`\`\`\n\n## Files Affected\n${filesAffected || '- (none listed)'}`
  ].filter(Boolean).join('\n\n');

  const context = `# Review Change Proposal #${proposal.id}\n\n**Title:** ${proposal.title}\n**Description:** ${proposal.description}\n**Agent:** ${proposal.agent_id}\n\n${promptBody}\n`;

  try {
    const chatOptions = {
      prompt: context,
      sessionId: contextPilotChatSessionId
    };

    const result = await vscode.commands.executeCommand(
      'workbench.action.chat.open',
      chatOptions
    );

    if (result && typeof result === 'object' && 'sessionId' in result) {
      contextPilotChatSessionId = (result as any).sessionId;
    }

    await vscode.env.clipboard.writeText(context);

    if (!usedReviewPanel) {
      vscode.window.showInformationMessage(
        '🤖 Chat opened with review context. If not auto-filled, paste from clipboard (Cmd+V).'
      );
    }
  } catch (error) {
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

export async function viewRelatedFiles(service: ContextPilotService, proposalId: string): Promise<void> {
    try {
        // Get proposal details
        const proposal = await service.getProposal(proposalId);
        if (!proposal) {
            vscode.window.showErrorMessage('Proposal not found');
            return;
        }

        // Get related files from proposal
        const relatedFiles: string[] = [];
        const workspaceId = getWorkspaceId();
        
        // Add files from proposed changes
        if (proposal.proposed_changes) {
            for (const change of proposal.proposed_changes) {
                if (change.file_path && !relatedFiles.includes(change.file_path)) {
                    relatedFiles.push(change.file_path);
                }
            }
        }

        // Add context files if available
        const contextFiles = [
            `.contextpilot/workspaces/${workspaceId}/context.md`,
            `.contextpilot/workspaces/${workspaceId}/project_scope.md`,
            `.contextpilot/workspaces/${workspaceId}/project_checklist.md`,
            `.contextpilot/workspaces/${workspaceId}/daily_checklist.md`,
            `.contextpilot/workspaces/${workspaceId}/milestones.md`,
            `.contextpilot/workspaces/${workspaceId}/timeline.md`,
            `.contextpilot/workspaces/${workspaceId}/DECISIONS.md`
        ];

        // Show files in a quick pick
        if (relatedFiles.length === 0) {
            vscode.window.showInformationMessage('No related files found for this proposal');
            return;
        }

        const fileItems = relatedFiles.map(filePath => ({
            label: `$(file) ${filePath}`,
            description: 'Related file',
            filePath: filePath
        }));

        // Add context files option
        fileItems.push({
            label: '$(folder) View Context Files',
            description: 'Show project context files',
            filePath: 'context_files'
        });

        const selectedItem = await vscode.window.showQuickPick(fileItems, {
            placeHolder: `Related files for: ${proposal.title}`,
            title: 'View Related Files'
        });

        if (!selectedItem) return;

        if (selectedItem.filePath === 'context_files') {
            // Show context files
            const contextItems = contextFiles.map(filePath => ({
                label: `$(file-text) ${filePath}`,
                description: 'Project context file',
                filePath: filePath
            }));

            const contextFile = await vscode.window.showQuickPick(contextItems, {
                placeHolder: 'Select context file to view',
                title: 'Project Context Files'
            });

            if (contextFile) {
                await openFileInEditor(contextFile.filePath);
            }
        } else {
            // Open the selected file
            await openFileInEditor(selectedItem.filePath);
        }

    } catch (error) {
        console.error('[viewRelatedFiles] Error:', error);
        vscode.window.showErrorMessage(`Failed to view related files: ${error}`);
    }
}

async function openFileInEditor(filePath: string): Promise<void> {
    try {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspaceRoot) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }

        const fullPath = require('path').join(workspaceRoot, filePath);
        const uri = vscode.Uri.file(fullPath);

        // Check if file exists
        try {
            await vscode.workspace.fs.stat(uri);
        } catch (error) {
            // File doesn't exist, offer to create it
            const createFile = await vscode.window.showWarningMessage(
                `File ${filePath} doesn't exist. Create it?`,
                'Create File',
                'Cancel'
            );

            if (createFile === 'Create File') {
                // Create directory if needed
                const dirPath = require('path').dirname(fullPath);
                await vscode.workspace.fs.createDirectory(vscode.Uri.file(dirPath));
                
                // Create empty file
                await vscode.workspace.fs.writeFile(uri, new Uint8Array());
                vscode.window.showInformationMessage(`Created ${filePath}`);
            } else {
                return;
            }
        }

        // Open file in editor
        const document = await vscode.workspace.openTextDocument(uri);
        await vscode.window.showTextDocument(document);

    } catch (error) {
        console.error('[openFileInEditor] Error:', error);
        vscode.window.showErrorMessage(`Failed to open file: ${error}`);
    }
}

// ===== AGENT RETROSPECTIVE COMMAND =====

export async function triggerRetrospective(service: ContextPilotService): Promise<void> {
  try {
    // Ask user for optional discussion topic
    const topic = await vscode.window.showInputBox({
      prompt: '💬 Suggest a topic for the agent retrospective (optional)',
      placeHolder: 'e.g., "How can we improve code quality?", "Better documentation workflow"',
      value: ''
    });

    // Get workspace ID
    const workspaceId = getWorkspaceId();
    
    // Show progress
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: '🤖 Agents are meeting...',
        cancellable: false,
      },
      async (progress) => {
        progress.report({ message: 'Collecting metrics from all agents...' });
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        progress.report({ message: 'Analyzing collaboration patterns...' });
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        progress.report({ message: 'Generating insights...' });
        
        // Call backend API to trigger retrospective
        const response = await service.triggerRetrospective(workspaceId, topic || 'manual');
        
        if (response && response.retrospective) {
          const retro = response.retrospective;
          
          // Show results in a webview
          const panel = vscode.window.createWebviewPanel(
            'contextpilotRetrospective',
            '🤖 Agent Retrospective',
            vscode.ViewColumn.One,
            { enableScripts: true }
          );
          
          // Handle messages from webview (for clickable links)
          panel.webview.onDidReceiveMessage(
            async (message) => {
              if (message.command === 'openFile') {
                const backendPath = '/home/fsegall/Desktop/New_Projects/google-context-pilot/back-end';
                const workspaceId = getWorkspaceId();
                
                let filePath = '';
                if (message.type === 'retrospective') {
                  filePath = `${backendPath}/.contextpilot/workspaces/${workspaceId}/retrospectives/${message.retrospectiveId}.md`;
                } else if (message.type === 'proposal') {
                  filePath = `${backendPath}/.contextpilot/workspaces/${workspaceId}/proposals/${message.proposalId}.md`;
                }
                
                if (filePath) {
                  const uri = vscode.Uri.file(filePath);
                  await vscode.window.showTextDocument(uri);
                }
              }
            },
            undefined,
            []
          );
          
          panel.webview.html = getRetrospectiveWebviewContent(retro, topic);
          
          // Show completion notification (non-blocking)
          const insightCount = retro.insights?.length || 0;
          const actionCount = retro.action_items?.length || 0;
          const proposalCreated = retro.proposal_id ? true : false;
          
          const message = proposalCreated
            ? `✅ Retrospective complete! ${insightCount} insights, ${actionCount} actions → Check Proposals view!`
            : `✅ Retrospective complete! ${insightCount} insights, ${actionCount} actions`;
          
          // Show simple notification that auto-dismisses
          vscode.window.showInformationMessage(message);
          
          // Refresh proposals view to show new proposal
          if (proposalCreated) {
            vscode.commands.executeCommand('contextpilot.refreshProposals');
          }
          
          // No await - let user continue working
          return;
          
        } else {
          vscode.window.showErrorMessage('Failed to conduct retrospective');
        }
      }
    );
    
  } catch (error: any) {
    console.error('[triggerRetrospective] Error:', error);
    vscode.window.showErrorMessage(`Failed to trigger retrospective: ${error.message}`);
  }
}

function getRetrospectiveWebviewContent(retro: any, topic?: string): string {
  const insights = retro.insights || [];
  const actionItems = retro.action_items || [];
  const metrics = retro.agent_metrics || {};
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Retrospective</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            line-height: 1.6;
        }
        h1, h2, h3 {
            color: var(--vscode-editor-foreground);
        }
        .header {
            background: var(--vscode-editor-background);
            border: 2px solid var(--vscode-charts-blue);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0 0 10px 0;
            color: var(--vscode-charts-blue);
        }
        .meta {
            color: var(--vscode-descriptionForeground);
            font-size: 0.9em;
        }
        .section {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .agent-metric {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-left: 3px solid var(--vscode-charts-green);
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .agent-name {
            font-weight: bold;
            color: var(--vscode-charts-green);
            text-transform: uppercase;
        }
        .insight {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-left: 3px solid var(--vscode-charts-yellow);
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .action-item {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-left: 3px solid var(--vscode-charts-red);
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            display: flex;
            align-items: center;
        }
        .priority {
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 10px;
            font-size: 0.8em;
        }
        .priority-high {
            background: var(--vscode-errorForeground);
            color: white;
        }
        .priority-medium {
            background: var(--vscode-charts-orange);
            color: white;
        }
        .priority-low {
            background: var(--vscode-charts-green);
            color: white;
        }
        .topic-box {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 2px dashed var(--vscode-charts-purple);
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Agent Retrospective</h1>
        <div class="meta">
            <strong>ID:</strong> ${retro.retrospective_id}<br/>
            <strong>Date:</strong> ${new Date(retro.timestamp).toLocaleString()}<br/>
            <strong>Trigger:</strong> ${retro.trigger}
        </div>
    </div>

    ${topic ? `
    <div class="topic-box">
        <strong>💬 Discussion Topic:</strong> ${topic}
    </div>
    ` : ''}

    <div class="section">
        <h2>📊 Agent Metrics</h2>
        ${Object.entries(metrics).map(([agentId, agentMetrics]: [string, any]) => `
            <div class="agent-metric">
                <div class="agent-name">${agentId}</div>
                ${Object.entries(agentMetrics).map(([key, value]) => `
                    <div><strong>${key}:</strong> ${value}</div>
                `).join('')}
            </div>
        `).join('')}
    </div>

    <div class="section">
        <h2>💡 Insights</h2>
        ${insights.length > 0 ? insights.map((insight: string) => `
            <div class="insight">💡 ${insight}</div>
        `).join('') : '<p>No insights generated.</p>'}
    </div>

    <div class="section">
        <h2>🎯 Action Items</h2>
        ${actionItems.length > 0 ? actionItems.map((item: any) => `
            <div class="action-item">
                <span class="priority priority-${item.priority}">${item.priority.toUpperCase()}</span>
                <div>
                    <strong>${item.action}</strong><br/>
                    <small>Assigned to: ${item.assigned_to}</small>
                </div>
            </div>
        `).join('') : '<p>No action items.</p>'}
    </div>

    ${retro.llm_summary ? `
    <div class="section">
        <h2>🤖 AI Summary</h2>
        <div style="white-space: pre-wrap;">${retro.llm_summary}</div>
    </div>
    ` : ''}

    ${retro.proposal_id ? `
    <div class="section" style="background: var(--vscode-editor-selectionBackground); border: 2px solid var(--vscode-charts-green);">
        <h2>🎯 Improvement Proposal Created</h2>
        <p><strong>Proposal ID:</strong> <code>${retro.proposal_id}</code></p>
        <p>A change proposal has been automatically generated from the high-priority action items.</p>
        <p>The proposal includes:</p>
        <ul>
            <li>Detailed implementation steps for each action</li>
            <li>Expected benefits and outcomes</li>
            <li>Testing recommendations</li>
        </ul>
        <p><strong>Next step:</strong> Review and approve the proposal to implement agent improvements!</p>
    </div>
    ` : ''}

    <div class="section">
        <h3>📁 Report Saved</h3>
        <p>Full retrospective saved to:<br/>
        <a href="#" onclick="openFile('retrospective')" style="color: var(--vscode-textLink-foreground); text-decoration: underline;">
            workspaces/${getWorkspaceId()}/retrospectives/${retro.retrospective_id}.md
        </a></p>
        ${retro.proposal_id ? `
        <p>Proposal saved to:<br/>
        <a href="#" onclick="openFile('proposal')" style="color: var(--vscode-textLink-foreground); text-decoration: underline;">
            workspaces/${getWorkspaceId()}/proposals/${retro.proposal_id}.md
        </a></p>
        ` : ''}
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        function openFile(type) {
            vscode.postMessage({
                command: 'openFile',
                type: type,
                retrospectiveId: '${retro.retrospective_id}',
                proposalId: '${retro.proposal_id || ''}'
            });
        }
    </script>
</body>
</html>`;
}

// ===== CONTEXT DETAIL VIEW COMMAND =====

export async function viewContextDetail(item: any): Promise<void> {
  try {
    const contextValue = item.contextValue;
    const label = item.label;
    const description = item.description;
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const workspaceId = getWorkspaceId();
    const workspaceContextDir = workspaceRoot
      ? path.join(workspaceRoot, '.contextpilot', 'workspaces', workspaceId)
      : undefined;
    
    const panel = vscode.window.createWebviewPanel(
      'contextpilotContextDetail',
      label,
      vscode.ViewColumn.One,
      { enableScripts: true }
    );
    
    let content = '';
    
    const checkpointPath = workspaceContextDir
      ? path.join(workspaceContextDir, 'checkpoint.yaml')
      : undefined;
    const milestonesPath = workspaceContextDir
      ? path.join(workspaceContextDir, 'milestones.md')
      : undefined;
    
    const checkpointExists = checkpointPath ? fs.existsSync(checkpointPath) : false;
    const checkpointData = checkpointExists
      ? ((yaml.load(fs.readFileSync(checkpointPath, 'utf-8')) as any) || {})
      : {};
    const checkpointYaml = checkpointExists
      ? fs.readFileSync(checkpointPath!, 'utf-8')
      : getTemplateContent('project', workspaceId);
    const milestonesText =
      milestonesPath && fs.existsSync(milestonesPath)
        ? fs.readFileSync(milestonesPath, 'utf-8')
        : getTemplateContent('milestones-root', workspaceId);
    
    if (contextValue === 'project') {
      const projectName = checkpointData?.project_name || description || 'N/A';
      content = `
        <h1>📦 Project</h1>
        <div class="content-box">
          <p><strong>Current name:</strong> ${projectName}</p>
        </div>
        <h2>About</h2>
        <p>This is your project name and description. It helps agents understand the context of your work.</p>
        <h2>How to Update</h2>
        <p>Edit <code>.contextpilot/workspaces/${workspaceId}/checkpoint.yaml</code> and update the <code>project_name</code> field:</p>
        <pre><code>${checkpointYaml}</code></pre>
      `;
    } else if (contextValue === 'goal') {
      const goal = checkpointData?.goal || description || 'N/A';
      content = `
        <h1>🎯 Goal</h1>
        <div class="content-box">
          <p><strong>Current goal:</strong> ${goal}</p>
        </div>
        <h2>About</h2>
        <p>This is your main project goal. It guides the AI agents in making relevant suggestions.</p>
        <h2>How to Update</h2>
        <p>Edit <code>.contextpilot/workspaces/${workspaceId}/checkpoint.yaml</code> and update the <code>goal</code> field:</p>
        <pre><code>${checkpointYaml}</code></pre>
      `;
    } else if (contextValue === 'status') {
      const status = checkpointData?.current_status || description || 'N/A';
      content = `
        <h1>📊 Status</h1>
        <div class="content-box">
          <p><strong>Current status:</strong> ${status}</p>
        </div>
        <h2>About</h2>
        <p>Your current project status helps agents understand what phase you're in.</p>
        <h2>How to Update</h2>
        <p>Edit <code>.contextpilot/workspaces/${workspaceId}/checkpoint.yaml</code> and update the <code>current_status</code> field:</p>
        <pre><code>${checkpointYaml}</code></pre>
      `;
    } else if (contextValue === 'milestones-root') {
      content = `
        <h1>🗓️ Milestones</h1>
        <div class="content-box">
          <p><strong>Total milestones tracked:</strong> ${(item.milestones || []).length}</p>
        </div>
        <h2>How to Update</h2>
        <p>Edit <code>.contextpilot/workspaces/${workspaceId}/milestones.md</code> or update the <code>milestones</code> array inside <code>checkpoint.yaml</code>:</p>
        <pre><code>${milestonesText}</code></pre>
      `;
    }
    
    panel.webview.html = getContextDetailWebviewContent(content);
    
  } catch (error: any) {
    console.error('[viewContextDetail] Error:', error);
    vscode.window.showErrorMessage(`Failed to view context detail: ${error.message}`);
  }
}

function getContextDetailWebviewContent(content: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Context Detail</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            line-height: 1.6;
        }
        h1 {
            color: var(--vscode-charts-blue);
            border-bottom: 2px solid var(--vscode-charts-blue);
            padding-bottom: 10px;
        }
        h2 {
            color: var(--vscode-editor-foreground);
            margin-top: 30px;
        }
        .content-box {
            background: var(--vscode-editor-background);
            border: 2px solid var(--vscode-charts-blue);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-size: 1.1em;
        }
        pre {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }
        code {
            font-family: var(--vscode-editor-font-family);
            background: var(--vscode-editor-background);
            padding: 2px 6px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    ${content}
</body>
</html>`;
}

// ===== OPEN CONTEXT FILE COMMAND =====

export async function resetAgentMetrics(
  service: ContextPilotService,
  agentId?: string,
  agentsProvider?: any
): Promise<void> {
  try {
    const agentName = agentId ? `agent '${agentId}'` : 'all agents';
    
    const confirm = await vscode.window.showWarningMessage(
      `Reset metrics for ${agentName}? This will clear errors, events_processed, and events_published counters.`,
      'Yes, Reset',
      'Cancel'
    );
    
    if (confirm !== 'Yes, Reset') {
      return;
    }
    
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `Resetting metrics for ${agentName}...`,
        cancellable: false,
      },
      async () => {
        const success = await service.resetAgentMetrics(agentId);
        if (success) {
          vscode.window.showInformationMessage(
            `✅ Metrics reset successfully for ${agentName}`
          );
          // Refresh agents view
          if (agentsProvider) {
            agentsProvider.refresh();
          }
        } else {
          vscode.window.showErrorMessage(
            `❌ Failed to reset metrics for ${agentName}`
          );
        }
      }
    );
  } catch (error) {
    console.error('[resetAgentMetrics] Error:', error);
    vscode.window.showErrorMessage(
      `Failed to reset agent metrics: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

export async function openContextFile(item: any): Promise<void> {
  try {
    const contextValue = item.contextValue;
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const workspaceId = getWorkspaceId();
    
    if (!workspaceRoot) {
      vscode.window.showErrorMessage('No workspace folder open');
      return;
    }
    
    const workspaceContextDir = path.join(
      workspaceRoot,
      '.contextpilot',
      'workspaces',
      workspaceId
    );
    
    const fileMap: { [key: string]: string } = {
      project: 'checkpoint.yaml',
      goal: 'checkpoint.yaml',
      status: 'checkpoint.yaml',
      'milestones-root': 'milestones.md'
    };
    
    const fileName = fileMap[contextValue];
    if (!fileName) {
      vscode.window.showErrorMessage('Unknown context type');
      return;
    }
    
    const filePath = path.join(workspaceContextDir, fileName);
    const uri = vscode.Uri.file(filePath);
    
    try {
      await vscode.workspace.fs.stat(uri);
    } catch {
      const createFile = await vscode.window.showWarningMessage(
        `Artifact ${fileName} doesn't exist. Create it now?`,
        'Create Artifact',
        'Cancel'
      );
      
      if (createFile !== 'Create Artifact') {
        return;
      }
      
      await vscode.workspace.fs.createDirectory(
        vscode.Uri.file(path.dirname(filePath))
      );
      
      const template = getTemplateContent(contextValue, workspaceId);
      await vscode.workspace.fs.writeFile(uri, Buffer.from(template, 'utf-8'));
      vscode.window.showInformationMessage(`✅ Created ${fileName} in workspace ${workspaceId}`);
    }
    
    const document = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(document);
    
  } catch (error: any) {
    console.error('[openContextFile] Error:', error);
    vscode.window.showErrorMessage(`Failed to open context file: ${error.message}`);
  }
}

function getTemplateContent(contextValue: string, workspaceId?: string): string {
  switch (contextValue) {
    case 'project':
    case 'goal':
    case 'status':
      return `# Workspace context for "${workspaceId || 'default'}"
# Update the YAML below to align agents and tooling.

project_name: ${workspaceId || 'my-project'}
goal: >
  Describe the primary objective driving this project.
current_status: >
  Summarize the current status so agents know what changed recently.
milestones:
  - name: Example milestone
    status: planned
    due: ${new Date().toISOString().slice(0, 10)}
`;
    case 'milestones-root':
      return `# 🗓️ Project Milestones

- [ ] 2025-12-31 — Describe the milestone outcome
- [ ] YYYY-MM-DD — Add more milestones and keep them synced with checkpoint.yaml
`;
    default:
      return '# Context Artifact\n\nUpdate this file to keep agents informed.\n';
  }
}

