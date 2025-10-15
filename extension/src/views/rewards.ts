import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';

export class RewardsProvider implements vscode.TreeDataProvider<RewardItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<RewardItem | undefined | null | void> = new vscode.EventEmitter<RewardItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<RewardItem | undefined | null | void> = this._onDidChangeTreeData.event;

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
      const balance = await this.contextPilotService.getBalance();
      return [
        new RewardItem('💰 Current Balance', `${balance.balance} CPT`, 'balance'),
        new RewardItem('📈 Total Earned', `${balance.total_earned} CPT`, 'total'),
        new RewardItem('⏳ Pending', `${balance.pending_rewards} CPT`, 'pending'),
      ];
    } catch (error) {
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

