import * as vscode from 'vscode';
import { ContextPilotService } from './services/contextpilot';

let contextPilotService: ContextPilotService;
let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
  console.log('ContextPilot extension is now active!');

  // Initialize service
  const config = vscode.workspace.getConfiguration('contextpilot');
  const apiUrl = config.get<string>('apiUrl', 'https://contextpilot-backend-581368740395.us-central1.run.app');
  const userId = config.get<string>('userId', 'test-user');
  const walletAddress = config.get<string>('walletAddress', '0xtest...');
  
  contextPilotService = new ContextPilotService(apiUrl, userId, walletAddress, false);
  
  console.log(`[ContextPilot] Extension activated - API: ${apiUrl}`);

  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBarItem.command = 'contextpilot.connect';
  context.subscriptions.push(statusBarItem);
  updateStatusBar();

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('contextpilot.connect', async () => {
      await connect(contextPilotService);
      updateStatusBar();
    }),

    vscode.commands.registerCommand('contextpilot.disconnect', () => {
      disconnect(contextPilotService);
      updateStatusBar();
    }),

    vscode.commands.registerCommand('contextpilot.triggerRetrospective', async () => {
      await triggerRetrospective(contextPilotService);
    })
  );

  // Auto-connect if enabled
  if (config.get<boolean>('autoConnect', true)) {
    connect(contextPilotService).then(() => {
      console.log('[ContextPilot] Auto-connect completed');
      updateStatusBar();
    });
  }
}

async function connect(service: ContextPilotService): Promise<void> {
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

function disconnect(service: ContextPilotService): void {
  service.disconnect();
  vscode.window.showInformationMessage('Disconnected from ContextPilot');
  vscode.commands.executeCommand('setContext', 'contextpilot.connected', false);
}

async function triggerRetrospective(service: ContextPilotService): Promise<void> {
  try {
    const topic = await vscode.window.showInputBox({
      prompt: 'Enter discussion topic for agent retrospective',
      placeHolder: 'e.g., "How can we improve code review process?"',
      value: 'General team improvement discussion'
    });

    if (!topic) return;

    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Running agent retrospective...',
        cancellable: false,
      },
      async () => {
        const result = await service.triggerRetrospective('default', topic);
        
        // Show results in a webview
        const panel = vscode.window.createWebviewPanel(
          'contextpilotRetrospective',
          'Agent Retrospective Results',
          vscode.ViewColumn.One,
          {}
        );

        panel.webview.html = `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Agent Retrospective</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; }
              .header { background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
              .section { margin-bottom: 20px; }
              .section h3 { color: #333; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
              .insight { background: #e8f4fd; padding: 10px; border-left: 4px solid #2196F3; margin: 10px 0; }
              .action-item { background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>🤖 Agent Retrospective Results</h1>
              <p><strong>Topic:</strong> ${topic}</p>
              <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
            </div>
            
            <div class="section">
              <h3>📊 Key Insights</h3>
              ${result.insights?.map((insight: any) => `<div class="insight">${insight}</div>`).join('') || '<p>No insights generated.</p>'}
            </div>
            
            <div class="section">
              <h3>✅ Action Items</h3>
              ${result.action_items?.map((item: any) => `<div class="action-item">${item}</div>`).join('') || '<p>No action items generated.</p>'}
            </div>
            
            <div class="section">
              <h3>📈 Metrics</h3>
              <p><strong>Total Events Analyzed:</strong> ${result.total_events || 'N/A'}</p>
              <p><strong>Agents Participated:</strong> ${result.agents_participated || 'N/A'}</p>
            </div>
          </body>
          </html>
        `;
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to run retrospective: ${error}`);
  }
}

async function updateStatusBar() {
  if (!contextPilotService.isConnected()) {
    statusBarItem.text = '$(plug) ContextPilot: Disconnected';
    statusBarItem.tooltip = 'Click to connect';
    statusBarItem.show();
    return;
  }

  try {
    const balance = await contextPilotService.getBalance();
    statusBarItem.text = `$(star) ${balance.balance} CPT`;
    statusBarItem.tooltip = `ContextPilot Balance\nTotal Earned: ${balance.total_earned} CPT`;
    statusBarItem.show();
  } catch (error) {
    statusBarItem.text = '$(warning) ContextPilot: Error';
    statusBarItem.tooltip = 'Failed to fetch balance';
    statusBarItem.show();
  }
}

export function deactivate() {
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}
