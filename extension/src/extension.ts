import * as vscode from 'vscode';
import { ContextPilotService } from './services/contextpilot';
import { ProposalsProvider } from './views/proposals';
import { RewardsProvider } from './views/rewards';
import { AgentsProvider } from './views/agents';
import { CoachProvider } from './views/coach';
import { ContextTreeProvider } from './views/context';
import * as commands from './commands';

let contextPilotService: ContextPilotService;
let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
  console.log('ContextPilot extension is now active!');

  // Initialize service
  const config = vscode.workspace.getConfiguration('contextpilot');
  const apiUrl = config.get<string>('apiUrl', 'http://localhost:8000');
  const userId = config.get<string>('userId', 'test-user');
  const walletAddress = config.get<string>('walletAddress', '0xtest...');
  
  // Enable test mode if userId is 'test-user' or empty
  const testMode = !userId || userId === 'test-user';
  
  contextPilotService = new ContextPilotService(apiUrl, userId, walletAddress, testMode);
  
  console.log(`[ContextPilot] Extension activated - API: ${apiUrl}, Test Mode: ${testMode}`);

  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBarItem.command = 'contextpilot.viewRewards';
  context.subscriptions.push(statusBarItem);
  updateStatusBar();

  // Register tree data providers
  const proposalsProvider = new ProposalsProvider(contextPilotService);
  const rewardsProvider = new RewardsProvider(contextPilotService);
  const agentsProvider = new AgentsProvider(contextPilotService);
  const coachProvider = new CoachProvider(contextPilotService);
  const contextProvider = new ContextTreeProvider(contextPilotService);

  vscode.window.registerTreeDataProvider('contextpilot.proposals', proposalsProvider);
  vscode.window.registerTreeDataProvider('contextpilot.rewards', rewardsProvider);
  vscode.window.registerTreeDataProvider('contextpilot.agents', agentsProvider);
  vscode.window.registerTreeDataProvider('contextpilot.coach', coachProvider);
  vscode.window.registerTreeDataProvider('contextpilot.context', contextProvider);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('contextpilot.connect', async () => {
      await commands.connect(contextPilotService);
      proposalsProvider.refresh();
      rewardsProvider.refresh();
      agentsProvider.refresh();
      contextProvider.refresh();
      updateStatusBar();
    }),

    vscode.commands.registerCommand('contextpilot.disconnect', () => {
      commands.disconnect(contextPilotService);
      updateStatusBar();
    }),

    vscode.commands.registerCommand('contextpilot.viewProposals', () => {
      vscode.commands.executeCommand('contextpilot.proposals.focus');
    }),

    vscode.commands.registerCommand('contextpilot.approveProposal', async (proposalId: string) => {
      await commands.approveProposal(contextPilotService, proposalId, proposalsProvider);
      rewardsProvider.refresh();
      updateStatusBar();
    }),

    vscode.commands.registerCommand('contextpilot.rejectProposal', async (proposalId: string) => {
      await commands.rejectProposal(contextPilotService, proposalId);
      proposalsProvider.refresh();
    }),

    vscode.commands.registerCommand('contextpilot.viewRewards', async () => {
      await commands.viewRewards(contextPilotService);
    }),

    vscode.commands.registerCommand('contextpilot.askCoach', async () => {
      await commands.askCoach(contextPilotService, coachProvider);
    }),

    vscode.commands.registerCommand('contextpilot.commitContext', async () => {
      await commands.commitContext(contextPilotService);
      proposalsProvider.refresh();
    }),

    vscode.commands.registerCommand('contextpilot.refreshStatus', () => {
      proposalsProvider.refresh();
      rewardsProvider.refresh();
      agentsProvider.refresh();
      coachProvider.refresh();
      contextProvider.refresh();
      updateStatusBar();
    }),

    // Real API commands
    vscode.commands.registerCommand('contextpilot.getContext', async () => {
      await commands.getContextCommand(contextPilotService);
    }),

    vscode.commands.registerCommand('contextpilot.commitContextReal', async () => {
      await commands.commitContextReal(contextPilotService);
    }),

    vscode.commands.registerCommand('contextpilot.getCoachTipReal', async () => {
      await commands.getCoachTipCommand(contextPilotService);
    })
  );

  // Auto-connect if enabled
  if (config.get<boolean>('autoConnect', true)) {
    commands.connect(contextPilotService).then(() => {
      proposalsProvider.refresh();
      rewardsProvider.refresh();
      agentsProvider.refresh();
      contextProvider.refresh();
      updateStatusBar();
    });
  }

  // Watch for file changes (context tracking)
  const fileWatcher = vscode.workspace.createFileSystemWatcher('**/*');
  fileWatcher.onDidChange(() => {
    if (contextPilotService.isConnected()) {
      // Debounce and track changes
      contextPilotService.trackChange();
    }
  });
  context.subscriptions.push(fileWatcher);

  // Update status bar periodically
  const statusInterval = setInterval(() => {
    updateStatusBar();
  }, 30000); // Every 30 seconds

  context.subscriptions.push({
    dispose: () => clearInterval(statusInterval)
  });
}

async function updateStatusBar() {
  if (!contextPilotService.isConnected()) {
    statusBarItem.text = '$(plug) ContextPilot: Disconnected';
    statusBarItem.tooltip = 'Click to view rewards';
    statusBarItem.show();
    return;
  }

  try {
    const balance = await contextPilotService.getBalance();
    statusBarItem.text = `$(star) ${balance.balance} CPT`;
    statusBarItem.tooltip = `ContextPilot Balance\nTotal Earned: ${balance.total_earned} CPT\nClick to view details`;
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

