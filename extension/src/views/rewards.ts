import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';
import { RewardsService } from '../services/rewards';

export class RewardsProvider implements vscode.TreeDataProvider<RewardItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<RewardItem | undefined | null | void> = new vscode.EventEmitter<RewardItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<RewardItem | undefined | null | void> = this._onDidChangeTreeData.event;
  private rewardsService = new RewardsService();
  private rewardsMode: string = 'unknown';

  constructor(private contextPilotService: ContextPilotService) {
    this.updateRewardsMode();
  }

  refresh(): void {
    this.updateRewardsMode();
    this._onDidChangeTreeData.fire();
  }

  private async updateRewardsMode(): Promise<void> {
    try {
      console.log('[RewardsProvider] updateRewardsMode - isConnected:', this.contextPilotService.isConnected());
      if (this.contextPilotService.isConnected()) {
        const health = await this.contextPilotService.getHealth();
        console.log('[RewardsProvider] health response:', health);
        console.log('[RewardsProvider] health.config:', health.config);
        // Backend returns config nested: { config: { rewards_mode: "firestore" } }
        this.rewardsMode = health.config?.rewards_mode || 'unknown';
        console.log('[RewardsProvider] rewardsMode set to:', this.rewardsMode);
      } else {
        console.log('[RewardsProvider] Service not connected, keeping unknown');
      }
    } catch (error) {
      console.error('[RewardsProvider] Failed to update rewards mode:', error);
      this.rewardsMode = 'unknown';
    }
  }

  getTreeItem(element: RewardItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: RewardItem): Promise<RewardItem[]> {
    if (!this.contextPilotService.isConnected()) {
      return [];
    }

    if (!element) {
      // Root level - show mode indicator as sub-header
      try {
        const userId = 'test-user'; // TODO: Get actual user ID
        
        // Fetch fresh mode before displaying
        await this.updateRewardsMode();
        
        // Add mode indicator as sub-header
        const modeIcon = this.rewardsMode === 'firestore' ? '🔥' : '⛓️';
        const modeItem = new RewardItem(
          `⚙️ ${modeIcon} Rewards Mode: ${this.rewardsMode}`,
          '',
          'mode-indicator',
          vscode.TreeItemCollapsibleState.Expanded
        );
        modeItem.tooltip = this.rewardsMode === 'firestore' 
          ? 'Firestore Mode: Rewards stored in Firestore (off-chain)'
          : 'Blockchain Mode: Rewards stored on blockchain (on-chain)';
        modeItem.contextValue = 'mode-indicator';
        
        return [modeItem];
      } catch (error) {
        console.error('[RewardsProvider] Error:', error);
        return [new RewardItem('❌ Error loading rewards', '', 'error')];
      }
    } else if (element.contextValue === 'mode-indicator') {
      // Children of mode indicator - show rewards
      try {
        const loadingItem = new RewardItem('⏳ Loading balance...', '', 'loading');
        loadingItem.iconPath = new vscode.ThemeIcon('sync', new vscode.ThemeColor('charts.yellow'));
        loadingItem.tooltip = 'Fetching rewards balance from backend...';
        this._onDidChangeTreeData.fire(loadingItem);

        const balance = await this.contextPilotService.getBalance();
        
        return [
          new RewardItem('💰 Current Balance', `${balance.balance || 0} CPT`, 'balance'),
          new RewardItem('📈 Total Earned', `${balance.total_earned || 0} CPT`, 'total'),
          new RewardItem('🔥 Weekly Streak', `${balance.weeklyStreak || 0} days`, 'streak'),
          new RewardItem('🏆 Achievements', `${balance.achievements?.length || 0} earned`, 'achievements'),
          new RewardItem('📊 Rank', `#${balance.rank || 999}`, 'rank')
        ];
      } catch (error: any) {
        console.error('[RewardsProvider] Error loading balance:', error);
        const message = error?.message || 'Backend did not return balance data.';
        const errorItem = new RewardItem('❌ Error loading balance', message, 'error');
        errorItem.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
        errorItem.tooltip = message;
        return [errorItem];
      }
    }
    
    return [];
  }
}

class RewardItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly type: string,
    collapsibleState: vscode.TreeItemCollapsibleState = vscode.TreeItemCollapsibleState.None
  ) {
    super(label, collapsibleState);
    this.iconPath = new vscode.ThemeIcon('star');
  }
}

