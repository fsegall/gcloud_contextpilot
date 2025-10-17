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
      const userId = 'local_dev'; // TODO: Get actual user ID
      const userReward = await this.rewardsService.getUserReward(userId);
      
      return [
        new RewardItem('💰 Current Balance', `${userReward.cptBalance} CPT`, 'balance'),
        new RewardItem('📈 Total Earned', `${userReward.totalEarned} CPT`, 'total'),
        new RewardItem('🔥 Weekly Streak', `${userReward.weeklyStreak} days`, 'streak'),
        new RewardItem('🏆 Achievements', `${userReward.achievements.length} earned`, 'achievements'),
        new RewardItem('📊 Rank', `#${userReward.rank}`, 'rank'),
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

