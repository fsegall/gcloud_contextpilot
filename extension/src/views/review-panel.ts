/**
 * Review Panel - Dedicated chat interface for proposal reviews
 * 
 * Maintains conversation context across multiple proposal reviews.
 */

import * as vscode from 'vscode';
import { ChangeProposal } from '../services/contextpilot';

export class ReviewPanelProvider {
  private panel: vscode.WebviewPanel | undefined;
  private conversationHistory: Array<{
    role: 'user' | 'assistant';
    content: string;
    proposalId?: string;
  }> = [];

  constructor(private context: vscode.ExtensionContext) {}

  public async showReview(proposal: ChangeProposal): Promise<void> {
    // Create or show existing panel
    if (!this.panel) {
      this.panel = vscode.window.createWebviewPanel(
        'contextpilotReview',
        'ContextPilot AI Review',
        vscode.ViewColumn.Beside,
        {
          enableScripts: true,
          retainContextWhenHidden: true // Keep context when hidden!
        }
      );

      this.panel.onDidDispose(() => {
        this.panel = undefined;
      });
    } else {
      this.panel.reveal(vscode.ViewColumn.Beside);
    }

    // Add proposal to conversation history
    const reviewRequest = this.formatReviewRequest(proposal);
    this.conversationHistory.push({
      role: 'user',
      content: reviewRequest,
      proposalId: proposal.id
    });

    // Update panel with conversation
    this.panel.webview.html = this.getWebviewContent();
    
    // Also copy to clipboard for easy pasting
    await vscode.env.clipboard.writeText(reviewRequest);
    
    vscode.window.showInformationMessage(
      '🤖 Review panel opened! Context also copied to clipboard for Cursor Chat.'
    );
  }

  private formatReviewRequest(proposal: ChangeProposal): string {
    const filesAffected = proposal.proposed_changes
      .map(c => `- **${c.file_path}** (${c.change_type}): ${c.description}`)
      .join('\n');

    return `# Review Proposal #${proposal.id}

**Title:** ${proposal.title}
**Agent:** ${proposal.agent_id}

## Changes

\`\`\`diff
${proposal.diff.content}
\`\`\`

## Files
${filesAffected}

## Question
Are these changes appropriate? Should I approve?`;
  }

  private getWebviewContent(): string {
    const conversationHtml = this.conversationHistory
      .map((msg, idx) => {
        const isUser = msg.role === 'user';
        const bgColor = isUser ? 'var(--vscode-editor-background)' : 'var(--vscode-input-background)';
        const icon = isUser ? '👤' : '🤖';
        
        return `
          <div style="
            background: ${bgColor};
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 3px solid ${isUser ? 'var(--vscode-charts-blue)' : 'var(--vscode-charts-green)'};
          ">
            <div style="font-weight: bold; margin-bottom: 10px;">
              ${icon} ${isUser ? 'You' : 'Claude'} ${msg.proposalId ? `(Proposal: ${msg.proposalId})` : ''}
            </div>
            <div style="white-space: pre-wrap; font-family: var(--vscode-editor-font-family);">
              ${this.escapeHtml(msg.content)}
            </div>
          </div>
        `;
      })
      .join('');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ContextPilot AI Review</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            line-height: 1.6;
        }
        .header {
            background: var(--vscode-editor-background);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid var(--vscode-panel-border);
        }
        .conversation {
            max-width: 800px;
        }
        .instructions {
            background: var(--vscode-textCodeBlock-background);
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            border-left: 3px solid var(--vscode-charts-yellow);
        }
        code {
            background: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>🤖 ContextPilot AI Review Session</h2>
        <p>This panel maintains conversation context across multiple proposal reviews.</p>
    </div>

    <div class="conversation">
        ${conversationHtml}
    </div>

    <div class="instructions">
        <h3>💡 How to Use</h3>
        <ol>
            <li><strong>Review context copied to clipboard</strong> - Ready to paste!</li>
            <li>Open <strong>Cursor Chat</strong> (Cmd+L or Ctrl+L)</li>
            <li><strong>Paste</strong> the context (Cmd+V)</li>
            <li>Claude will analyze and respond</li>
            <li>Come back here to see conversation history</li>
            <li>Next proposal review will continue in same conversation</li>
        </ol>
        <p><strong>Tip:</strong> Use <code>ContextPilot: Reset Chat Session</code> to start fresh.</p>
    </div>
</body>
</html>`;
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  public clearHistory(): void {
    this.conversationHistory = [];
    if (this.panel) {
      this.panel.webview.html = this.getWebviewContent();
    }
  }

  public addAssistantResponse(response: string, proposalId?: string): void {
    this.conversationHistory.push({
      role: 'assistant',
      content: response,
      proposalId
    });
    
    if (this.panel) {
      this.panel.webview.html = this.getWebviewContent();
    }
  }
}

