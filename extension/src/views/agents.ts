import * as vscode from 'vscode';
import { ContextPilotService, AgentStatus } from '../services/contextpilot';

export class AgentsProvider implements vscode.TreeDataProvider<AgentItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<AgentItem | undefined | null | void> = new vscode.EventEmitter<AgentItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<AgentItem | undefined | null | void> = this._onDidChangeTreeData.event;
  private eventBusMode: string = 'unknown';

  constructor(private contextPilotService: ContextPilotService) {
    this.updateEventBusMode();
  }

  refresh(): void {
    this.updateEventBusMode();
    this._onDidChangeTreeData.fire();
  }

  private async updateEventBusMode(): Promise<void> {
    try {
      console.log('[AgentsProvider] updateEventBusMode - isConnected:', this.contextPilotService.isConnected());
      if (this.contextPilotService.isConnected()) {
        const health = await this.contextPilotService.getHealth();
        console.log('[AgentsProvider] health response:', health);
        console.log('[AgentsProvider] health.config:', health.config);
        // Backend returns config nested: { config: { event_bus_mode: "pubsub" } }
        this.eventBusMode = health.config?.event_bus_mode || 'unknown';
        console.log('[AgentsProvider] eventBusMode set to:', this.eventBusMode);
      } else {
        console.log('[AgentsProvider] Service not connected, keeping unknown');
      }
    } catch (error) {
      console.error('[AgentsProvider] Failed to update event bus mode:', error);
      this.eventBusMode = 'unknown';
    }
  }

  getTreeItem(element: AgentItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: AgentItem): Promise<AgentItem[]> {
    if (!this.contextPilotService.isConnected()) {
      return [];
    }

    if (!element) {
      // Root level - show mode indicator as sub-header
      try {
        // Fetch fresh mode before displaying
        await this.updateEventBusMode();
        
        // Add mode indicator as sub-header
        const modeIcon = this.eventBusMode === 'pubsub' ? '📡' : '💾';
        const modeItem = new AgentItem({
          agent_id: 'event-bus-mode',
          name: `⚙️ ${modeIcon} Event Bus: ${this.eventBusMode}`,
          status: 'active',
          last_activity: 'now'
        }, vscode.TreeItemCollapsibleState.Expanded);
        modeItem.tooltip = this.eventBusMode === 'pubsub' 
          ? 'Pub/Sub Mode: Agents communicate via Google Pub/Sub (scalable)'
          : 'In-Memory Mode: Agents communicate via in-memory events (local)';
        modeItem.contextValue = 'mode-indicator';
        modeItem.description = ''; // Remove "active" from mode indicator
        
        return [modeItem];
      } catch (error) {
        console.error('[AgentsProvider] Error:', error);
        return [];
      }
    } else if (element.contextValue === 'mode-indicator') {
      // Children of mode indicator - show agents
      try {
        const agents = await this.contextPilotService.getAgentsStatus();
        return agents.map(agent => new AgentItem(agent));
      } catch (error) {
        // Return default agents if API not implemented yet
        return [
          new AgentItem({ agent_id: 'context', name: 'Context Agent', status: 'active', last_activity: 'now' }),
          new AgentItem({ agent_id: 'spec', name: 'Spec Agent', status: 'active', last_activity: '5m ago' }),
          new AgentItem({ agent_id: 'development', name: 'Development Agent', status: 'active', last_activity: '3m ago' }),
          new AgentItem({ agent_id: 'retrospective', name: 'Retrospective Agent', status: 'active', last_activity: '15m ago' }),
          new AgentItem({ agent_id: 'strategy', name: 'Strategy Agent', status: 'idle', last_activity: '1h ago' }),
          new AgentItem({ agent_id: 'milestone', name: 'Milestone Agent', status: 'active', last_activity: '10m ago' }),
          new AgentItem({ agent_id: 'git', name: 'Git Agent', status: 'active', last_activity: '2m ago' }),
          new AgentItem({ agent_id: 'coach', name: 'Coach Agent', status: 'active', last_activity: 'now' }),
        ];
      }
    }
    
    return [];
  }
}

class AgentItem extends vscode.TreeItem {
  constructor(
    public readonly agent: AgentStatus,
    collapsibleState: vscode.TreeItemCollapsibleState = vscode.TreeItemCollapsibleState.None
  ) {
    super(agent.name, collapsibleState);
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

