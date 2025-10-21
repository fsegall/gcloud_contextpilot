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
      if (this.contextPilotService.isConnected()) {
        const health = await this.contextPilotService.getHealth();
        // Backend returns config nested: { config: { rewards_mode: "firestore" } }
        this.rewardsMode = health.config?.rewards_mode || 'unknown';
      }
    } catch (error) {
      console.error('[RewardsProvider] Failed to update rewards mode:', error);
      this.rewardsMode = 'unknown';
    }
  }

  getTreeItem(element: RewardItem): vscode.TreeItem {
    return element;
  }

  async getChildren(): Promise<RewardItem[]> {
    if (!this.contextPilotService.isConnected()) {
      return [];
    }

    try {
      const userId = 'test-user'; // TODO: Get actual user ID
      
      // Add mode indicator as first item
      const modeIcon = this.rewardsMode === 'firestore' ? '🔥' : '⛓️';
      const modeItem = new RewardItem(
        `⚙️ ${modeIcon} Rewards Mode: ${this.rewardsMode}`,
        '',
        'mode-indicator'
      );
      modeItem.tooltip = this.rewardsMode === 'firestore' 
        ? 'Firestore Mode: Rewards stored in Firestore (off-chain)'
        : 'Blockchain Mode: Rewards stored on blockchain (on-chain)';
      modeItem.contextValue = 'mode-indicator';
      
      const items: RewardItem[] = [modeItem];
      
      // Use real API instead of local RewardsService
      const balance = await this.contextPilotService.getBalance();
      
      // Add reward items
      items.push(
        new RewardItem('💰 Current Balance', `${balance.balance || 0} CPT`, 'balance'),
        new RewardItem('📈 Total Earned', `${balance.total_earned || 0} CPT`, 'total'),
        new RewardItem('🔥 Weekly Streak', `${balance.weeklyStreak || 0} days`, 'streak'),
        new RewardItem('🏆 Achievements', `${balance.achievements?.length || 0} earned`, 'achievements'),
        new RewardItem('📊 Rank', `#${balance.rank || 999}`, 'rank')
      );
      
      return items;
    } catch (error) {
      console.error('[RewardsProvider] Error:', error);
      return [new RewardItem('❌ Error loading rewards', '', 'error')];
    }
  }
}

class RewardItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly type: string
  ) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.iconPath = new vscode.ThemeIcon('star');
  }
}

