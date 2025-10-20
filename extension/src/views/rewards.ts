import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';
import { RewardsService } from '../services/rewards';

export class RewardsProvider implements vscode.TreeDataProvider<RewardItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<RewardItem | undefined | null | void> = new vscode.EventEmitter<RewardItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<RewardItem | undefined | null | void> = this._onDidChangeTreeData.event;
  private rewardsService = new RewardsService();

  constructor(private contextPilotService: ContextPilotService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
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
      
      // Use real API instead of local RewardsService
      const balance = await this.contextPilotService.getBalance();
      
      return [
        new RewardItem('💰 Current Balance', `${balance.balance || 0} CPT`, 'balance'),
        new RewardItem('📈 Total Earned', `${balance.total_earned || 0} CPT`, 'total'),
        new RewardItem('🔥 Weekly Streak', `${balance.weeklyStreak || 0} days`, 'streak'),
        new RewardItem('🏆 Achievements', `${balance.achievements?.length || 0} earned`, 'achievements'),
        new RewardItem('📊 Rank', `#${balance.rank || 999}`, 'rank'),
      ];
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

