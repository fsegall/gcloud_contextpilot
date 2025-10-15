import * as vscode from 'vscode';
import { ContextPilotService, AgentStatus } from '../services/contextpilot';

export class AgentsProvider implements vscode.TreeDataProvider<AgentItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<AgentItem | undefined | null | void> = new vscode.EventEmitter<AgentItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<AgentItem | undefined | null | void> = this._onDidChangeTreeData.event;

  constructor(private contextPilotService: ContextPilotService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: AgentItem): vscode.TreeItem {
    return element;
  }

  async getChildren(): Promise<AgentItem[]> {
    if (!this.contextPilotService.isConnected()) {
      return [];
    }

    try {
      const agents = await this.contextPilotService.getAgentsStatus();
      return agents.map(agent => new AgentItem(agent));
    } catch (error) {
      // Return default agents if API not implemented yet
      return [
        new AgentItem({ agent_id: 'context', name: 'Context Agent', status: 'active', last_activity: 'now' }),
        new AgentItem({ agent_id: 'spec', name: 'Spec Agent', status: 'active', last_activity: '5m ago' }),
        new AgentItem({ agent_id: 'strategy', name: 'Strategy Agent', status: 'idle', last_activity: '1h ago' }),
        new AgentItem({ agent_id: 'milestone', name: 'Milestone Agent', status: 'active', last_activity: '10m ago' }),
        new AgentItem({ agent_id: 'git', name: 'Git Agent', status: 'active', last_activity: '2m ago' }),
        new AgentItem({ agent_id: 'coach', name: 'Coach Agent', status: 'active', last_activity: 'now' }),
      ];
    }
  }
}

class AgentItem extends vscode.TreeItem {
  constructor(public readonly agent: AgentStatus) {
    super(agent.name, vscode.TreeItemCollapsibleState.None);
    this.description = agent.status;
    this.tooltip = `Last activity: ${agent.last_activity}`;
    
    const icon = agent.status === 'active' ? 'circle-filled' :
                 agent.status === 'idle' ? 'circle-outline' :
                 'error';
    
    this.iconPath = new vscode.ThemeIcon(
      icon,
      agent.status === 'active' ? new vscode.ThemeColor('charts.green') :
      agent.status === 'idle' ? new vscode.ThemeColor('charts.yellow') :
      new vscode.ThemeColor('charts.red')
    );
  }
}

