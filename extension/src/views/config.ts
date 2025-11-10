import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';

class ConfigItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly command?: vscode.Command,
    public readonly contextValue?: string
  ) {
    super(label, collapsibleState);
    this.tooltip = description;
    this.description = description;
    if (command) {
      this.command = command;
    }
    if (contextValue) {
      this.contextValue = contextValue;
    }
  }
}

export class ConfigProvider implements vscode.TreeDataProvider<ConfigItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<ConfigItem | undefined | null | void> = new vscode.EventEmitter<ConfigItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<ConfigItem | undefined | null | void> = this._onDidChangeTreeData.event;

  constructor(private service: ContextPilotService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: ConfigItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: ConfigItem): Promise<ConfigItem[]> {
    try {
      if (!element) {
        // Root level - show configuration sections
        const config = vscode.workspace.getConfiguration('contextpilot');
        const apiUrl = config.get<string>('apiUrl', '');

        return [
          new ConfigItem(
            '🔧 Repositories',
            'Configure GitHub repositories',
            vscode.TreeItemCollapsibleState.Collapsed,
            undefined,
            'repos-section'
          ),
          new ConfigItem(
            '🌐 Backend',
            `API: ${apiUrl || 'Not configured'}`,
            vscode.TreeItemCollapsibleState.Collapsed,
            undefined,
            'backend-section'
          )
        ];
      } else if (element.contextValue === 'repos-section') {
      // Show repository configuration
      const config = vscode.workspace.getConfiguration('contextpilot');
      const mainRepo = config.get<string>('mainRepo', '');
      const sandboxRepoUrl = config.get<string>('sandboxRepoUrl', '');

      return [
        new ConfigItem(
          '📦 Main Repository',
          mainRepo || 'Not configured',
          vscode.TreeItemCollapsibleState.None,
          {
            command: 'contextpilot.configureRepos',
            title: 'Configure Repositories',
            arguments: []
          },
          'main-repo'
        ),
        new ConfigItem(
          '🏖️ Sandbox Repository',
          sandboxRepoUrl || 'Not configured',
          vscode.TreeItemCollapsibleState.None,
          {
            command: 'contextpilot.configureRepos',
            title: 'Configure Repositories',
            arguments: []
          },
          'sandbox-repo'
        )
      ];
    } else if (element.contextValue === 'backend-section') {
      // Show backend configuration
      const config = vscode.workspace.getConfiguration('contextpilot');
      const apiUrl = config.get<string>('apiUrl', '');
      const userId = config.get<string>('userId', '');

      return [
        new ConfigItem(
          '🔗 API URL',
          apiUrl || 'Not configured',
          vscode.TreeItemCollapsibleState.None,
          {
            command: 'workbench.action.openSettings',
            title: 'Open Settings',
            arguments: ['contextpilot.apiUrl']
          },
          'api-url'
        ),
        new ConfigItem(
          '👤 User ID',
          userId || 'Not configured',
          vscode.TreeItemCollapsibleState.None,
          {
            command: 'workbench.action.openSettings',
            title: 'Open Settings',
            arguments: ['contextpilot.userId']
          },
          'user-id'
        )
      ];
    }

    return [];
    } catch (error) {
      console.error('[ConfigProvider] Error loading children:', error);
      return [
        new ConfigItem(
          '⚠️ Error loading configuration',
          String(error),
          vscode.TreeItemCollapsibleState.None
        )
      ];
    }
  }
}

