import * as vscode from 'vscode';
import { ContextPilotService } from './services/contextpilot';
import { ProposalsProvider } from './views/proposals';
import { RewardsProvider } from './views/rewards';
import { AgentsProvider } from './views/agents';
import { CoachProvider } from './views/coach';
import { ContextTreeProvider } from './views/context';
import { ReviewPanelProvider } from './views/review-panel';
import * as commands from './commands';

let contextPilotService: ContextPilotService;
let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
  console.log('ContextPilot extension is now active!');

  // Initialize service
  const config = vscode.workspace.getConfiguration('contextpilot');
  const apiUrl = config.get<string>('apiUrl', 'https://contextpilot-backend-581368740395.us-central1.run.app');
  const userId = config.get<string>('userId', 'test-user');
  const walletAddress = config.get<string>('walletAddress', '0xtest...');
  
  // Enable test mode if userId is 'test-user' or empty
  const testMode = false; // Force real mode for testing
  
  contextPilotService = new ContextPilotService(apiUrl, userId, walletAddress, testMode);
  
  console.log(`[ContextPilot] Extension activated - API: ${apiUrl}, Test Mode: ${testMode}`);

  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBarItem.command = 'contextpilot.showBackendConfig';
  context.subscriptions.push(statusBarItem);
  updateStatusBar();

  // Register tree data providers
  const proposalsProvider = new ProposalsProvider(contextPilotService);
  const rewardsProvider = new RewardsProvider(contextPilotService);
  const agentsProvider = new AgentsProvider(contextPilotService);
  const coachProvider = new CoachProvider(contextPilotService);
  const contextProvider = new ContextTreeProvider(contextPilotService);
  
  // Create review panel provider (maintains conversation context)
  const reviewPanelProvider = new ReviewPanelProvider(context);
  commands.setReviewPanel(reviewPanelProvider);

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

    vscode.commands.registerCommand('contextpilot.configureRepos', async () => {
      const extConfig = vscode.workspace.getConfiguration('contextpilot');
      const currentMain = extConfig.get<string>('mainRepo', '');
      const currentSandbox = extConfig.get<string>('sandboxRepoUrl', '');

      const mainRepo = await vscode.window.showInputBox({
        title: 'Main GitHub Repository',
        placeHolder: 'owner/repo',
        value: currentMain,
        ignoreFocusOut: true,
        validateInput: (val) => {
          if (!val) { return null; }
          return /.+\/.+/.test(val) ? null : 'Use format owner/repo';
        }
      });

      if (mainRepo === undefined) { return; }

      const sandboxRepoUrl = await vscode.window.showInputBox({
        title: 'Sandbox Repository URL',
        placeHolder: 'https://github.com/owner/sandbox.git',
        value: currentSandbox,
        ignoreFocusOut: true,
        validateInput: (val) => {
          if (!val) { return null; }
          try { new URL(val); return null; } catch { return 'Provide a valid URL'; }
        }
      });

      if (sandboxRepoUrl === undefined) { return; }

      await extConfig.update('mainRepo', mainRepo || '', vscode.ConfigurationTarget.Global);
      await extConfig.update('sandboxRepoUrl', sandboxRepoUrl || '', vscode.ConfigurationTarget.Global);

      vscode.window.showInformationMessage('ContextPilot repositories saved.');
    }),

    vscode.commands.registerCommand('contextpilot.disconnect', () => {
      commands.disconnect(contextPilotService);
      updateStatusBar();
    }),
    
    vscode.commands.registerCommand('contextpilot.showBackendConfig', async () => {
      try {
        const health = await contextPilotService.getHealth();
        
        let message = `**ContextPilot v${health.version}**\n\n`;
        
        // Backend returns config nested: { config: { storage_mode: "cloud", ... } }
        if (health.config) {
          message += `**Configuration:**\n`;
          message += `• Storage Mode: \`${health.config.storage_mode}\`\n`;
          message += `• Rewards Mode: \`${health.config.rewards_mode}\`\n`;
          message += `• Event Bus: \`${health.config.event_bus_mode}\`\n`;
          message += `• Environment: \`${health.config.environment}\`\n\n`;
          
          // Add description
          if (health.config.storage_mode === 'cloud') {
            message += `☁️  **Cloud Mode**: Proposals in Firestore, commits via GitHub Actions\n`;
          } else {
            message += `📁 **Local Mode**: Proposals in local files, direct Git commits\n`;
          }
        }
        
        // Show extension-side repo configuration
        const extConfig = vscode.workspace.getConfiguration('contextpilot');
        const mainRepo = extConfig.get<string>('mainRepo', '');
        const sandboxRepoUrl = extConfig.get<string>('sandboxRepoUrl', '');
        if (mainRepo || sandboxRepoUrl) {
          message += `\n**Repositories:**\n`;
          if (mainRepo) message += `• Main Repo: \`${mainRepo}\`\n`;
          if (sandboxRepoUrl) message += `• Sandbox Repo URL: \`${sandboxRepoUrl}\`\n`;
        }

        message += `\n**Active Agents:** ${health.agents?.length || 0}`;
        
        vscode.window.showInformationMessage(message, { modal: false });
      } catch (error) {
        vscode.window.showErrorMessage('Failed to fetch backend configuration');
      }
    }),

    vscode.commands.registerCommand('contextpilot.dashboard', () => {
      vscode.commands.executeCommand('workbench.view.extension.contextpilot');
    }),

    vscode.commands.registerCommand('contextpilot.approveProposal', async (item: any) => {
      console.log('[approveProposal] Item received:', item);
      console.log('[approveProposal] Item type:', typeof item);
      console.log('[approveProposal] Item.proposal:', item?.proposal);
      console.log('[approveProposal] Item.proposal?.id:', item?.proposal?.id);
      
      // When called from tree view inline button, item is ProposalItem
      // When called directly, item is proposalId string
      const proposalId = typeof item === 'string' ? item : item?.proposal?.id;
      if (!proposalId) {
        vscode.window.showErrorMessage('No proposal ID provided');
        return;
      }
      await commands.approveProposal(contextPilotService, proposalId, proposalsProvider);
      proposalsProvider.refresh(); // Refresh proposals list
      rewardsProvider.refresh();
      updateStatusBar();
    }),

    vscode.commands.registerCommand('contextpilot.rejectProposal', async (item: any) => {
      console.log('[rejectProposal] Item received:', item);
      console.log('[rejectProposal] Item type:', typeof item);
      console.log('[rejectProposal] Item.proposal:', item?.proposal);
      console.log('[rejectProposal] Item.proposal?.id:', item?.proposal?.id);
      
      // Try multiple ways to get the proposal ID
      let proposalId: string | undefined;
      
      if (typeof item === 'string') {
        proposalId = item;
      } else if (item?.proposal?.id) {
        proposalId = item.proposal.id;
      } else if (item?.id) {
        proposalId = item.id;
      } else if (item?.label) {
        // If it's a ProposalItem, try to extract from label or other properties
        console.log('[rejectProposal] Trying to extract ID from label:', item.label);
        // This might be the proposal title, we need to find the actual proposal
        const proposals = await contextPilotService.getProposals();
        const matchingProposal = proposals.find(p => p.title === item.label);
        if (matchingProposal) {
          proposalId = matchingProposal.id;
        }
      }
      
      if (!proposalId) {
        vscode.window.showErrorMessage('No proposal ID provided');
        return;
      }
      
      console.log('[rejectProposal] Using proposal ID:', proposalId);
      await commands.rejectProposal(contextPilotService, proposalId, proposalsProvider);
    }),

    vscode.commands.registerCommand('contextpilot.viewRewards', async () => {
      await commands.viewRewards(contextPilotService);
    }),

    vscode.commands.registerCommand('contextpilot.viewRelatedFiles', async (item: any) => {
      const proposalId = typeof item === 'string' ? item : item?.proposal?.id;
      if (!proposalId) {
        vscode.window.showErrorMessage('No proposal ID provided');
        return;
      }
      await commands.viewRelatedFiles(contextPilotService, proposalId);
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
    }),

    // Proposal diff commands
    vscode.commands.registerCommand('contextpilot.viewProposalDiff', async (proposalId: string) => {
      await commands.viewProposalDiff(contextPilotService, proposalId);
    }),

    vscode.commands.registerCommand('contextpilot.viewContextDetail', async (item: any) => {
      await commands.viewContextDetail(item);
    }),

    vscode.commands.registerCommand('contextpilot.resetChatSession', () => {
      commands.resetChatSession();
    }),

    vscode.commands.registerCommand('contextpilot.triggerRetrospective', async () => {
      await commands.triggerRetrospective(contextPilotService);
    }),

    vscode.commands.registerCommand('contextpilot.openContextFile', async (item: any) => {
      await commands.openContextFile(item);
    })
  );

  // Auto-connect if enabled
  if (config.get<boolean>('autoConnect', true)) {
    console.log('[ContextPilot] Starting auto-connect...');
    commands.connect(contextPilotService).then(() => {
      console.log('[ContextPilot] Auto-connect completed, refreshing providers...');
      proposalsProvider.refresh();
      rewardsProvider.refresh();
      agentsProvider.refresh();
      contextProvider.refresh();
      updateStatusBar();
    }).catch((error) => {
      console.error('[ContextPilot] Auto-connect failed:', error);
      updateStatusBar(); // Update status bar even if connection fails
    });
  } else {
    console.log('[ContextPilot] Auto-connect disabled, updating status bar...');
    updateStatusBar();
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
  console.log('[ContextPilot] Updating status bar...');
  
  if (!contextPilotService.isConnected()) {
    console.log('[ContextPilot] Not connected, showing disconnected status');
    statusBarItem.text = '$(plug) ContextPilot: Disconnected';
    statusBarItem.tooltip = 'Click to view backend configuration';
    statusBarItem.show();
    return;
  }

  try {
    console.log('[ContextPilot] Fetching health and balance...');
    const health = await contextPilotService.getHealth();
    const balance = await contextPilotService.getBalance();
    
    console.log('[ContextPilot] Health data:', health);
    console.log('[ContextPilot] Balance data:', balance);
    
    // Backend returns config nested: { config: { storage_mode: "cloud", ... } }
    const storageMode = health.config?.storage_mode || 'unknown';
    
    // Show balance + mode indicator
    const modeIcon = storageMode === 'cloud' ? '☁️' : '📁';
    statusBarItem.text = `${modeIcon} $(star) ${balance.balance} CPT`;
    
    const tooltip = [
      `ContextPilot v${health.version || '2.0.0'}`,
      ``,
      `💰 Balance: ${balance.balance} CPT`,
      `📊 Total Earned: ${balance.total_earned} CPT`,
      ``
    ];
    
    if (health.config) {
      tooltip.push(`⚙️  Configuration:`);
      tooltip.push(`  Storage: ${health.config.storage_mode}`);
      tooltip.push(`  Rewards: ${health.config.rewards_mode}`);
      tooltip.push(`  Environment: ${health.config.environment}`);
    }
    
    tooltip.push(``, `Click for details`);
    
    statusBarItem.tooltip = tooltip.join('\n');
    statusBarItem.show();
    console.log('[ContextPilot] Status bar updated successfully');
  } catch (error) {
    console.error('[ContextPilot] Error updating status bar:', error);
    statusBarItem.text = '$(warning) ContextPilot: Error';
    statusBarItem.tooltip = 'Failed to fetch status';
    statusBarItem.show();
  }
}

export function deactivate() {
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}

