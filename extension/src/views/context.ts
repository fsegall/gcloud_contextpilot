import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';

type ContextTreeItem = ContextItem | MilestoneItem;

export class ContextTreeProvider implements vscode.TreeDataProvider<ContextTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<ContextTreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private service: ContextPilotService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: ContextTreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: ContextTreeItem): Promise<ContextTreeItem[]> {
    if (!this.service.isConnected()) {
      return [new ContextItem('Not connected', '', vscode.TreeItemCollapsibleState.None)];
    }

    // Get workspace ID
    const workspaceId = this.getWorkspaceId();
    
    if (!element) {
      // Root level - load context
      const context = await this.service.getContextReal(workspaceId);
      
      if (!context) {
        return [new ContextItem('No context loaded', '', vscode.TreeItemCollapsibleState.None)];
      }

      const checkpoint = context.checkpoint || {};
      
      return [
        new ContextItem(
          '📦 Project',
          checkpoint.project_name || 'N/A',
          vscode.TreeItemCollapsibleState.None,
          'project'
        ),
        new ContextItem(
          '🎯 Goal',
          checkpoint.goal || 'N/A',
          vscode.TreeItemCollapsibleState.None,
          'goal'
        ),
        new ContextItem(
          '📊 Status',
          checkpoint.current_status || 'N/A',
          vscode.TreeItemCollapsibleState.None,
          'status'
        ),
        new ContextItem(
          '🗓️ Milestones',
          `${(checkpoint.milestones || []).length} total`,
          vscode.TreeItemCollapsibleState.Collapsed,
          'milestones-root',
          checkpoint.milestones
        )
      ];
    } else if (element instanceof ContextItem && element.contextValue === 'milestones-root' && element.milestones) {
      // Show milestones as children
      return element.milestones.map((m: any) => {
        const daysLeft = this.calculateDaysLeft(m.due);
        const status = daysLeft < 0 ? '⚠️ Overdue' : daysLeft === 0 ? '🔥 Today!' : `📅 ${daysLeft}d left`;
        
        return new MilestoneItem(
          m.name,
          `${status} (${m.due})`,
          daysLeft
        );
      });
    }

    return [];
  }

  private getWorkspaceId(): string {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
      const folderName = workspaceFolders[0].name.toLowerCase().replace(/[^a-z0-9]/g, '-');
      if (folderName.includes('context') && folderName.includes('pilot')) {
        return 'contextpilot';
      }
      return folderName;
    }
    return 'contextpilot';
  }

  private calculateDaysLeft(dueDate: string): number {
    const due = new Date(dueDate);
    const now = new Date();
    const diffTime = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  }
}

class ContextItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly contextValue?: string,
    public readonly milestones?: any[]
  ) {
    super(label, collapsibleState);
    this.description = description;
    this.tooltip = `${label}: ${description}`;
    
    // Set icons based on type
    if (contextValue === 'project') {
      this.iconPath = new vscode.ThemeIcon('folder-library');
    } else if (contextValue === 'goal') {
      this.iconPath = new vscode.ThemeIcon('target');
    } else if (contextValue === 'status') {
      this.iconPath = new vscode.ThemeIcon('pulse');
    } else if (contextValue === 'milestones-root') {
      this.iconPath = new vscode.ThemeIcon('milestone');
    }
  }
}

class MilestoneItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly daysLeft: number
  ) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.description = description;
    this.tooltip = `${label}\n${description}`;
    this.contextValue = 'milestone';
    
    // Set icon and color based on days left
    if (daysLeft < 0) {
      this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
    } else if (daysLeft === 0) {
      this.iconPath = new vscode.ThemeIcon('flame', new vscode.ThemeColor('charts.orange'));
    } else if (daysLeft <= 3) {
      this.iconPath = new vscode.ThemeIcon('clock', new vscode.ThemeColor('charts.yellow'));
    } else {
      this.iconPath = new vscode.ThemeIcon('calendar', new vscode.ThemeColor('charts.green'));
    }
  }
}

