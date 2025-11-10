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
      console.log('[AgentsProvider] updateEventBusMode - fetching /health');
      // Fetch directly from backend regardless of local connected flag
      const health = await this.contextPilotService.getHealth();
      console.log('[AgentsProvider] health response:', health);
      console.log('[AgentsProvider] health.config:', health?.config);
      // Backend returns config nested: { config: { event_bus_mode: "pubsub" } }
      const mode = health?.config?.event_bus_mode;
      // Normalize to lowercase for comparison (handles "pubsub", "Pub/Sub", "PUBSUB", etc.)
      const normalizedMode = typeof mode === 'string' && mode.length > 0 
        ? mode.toLowerCase().trim() 
        : 'unknown';
      
      // Map common variations to standard values
      if (normalizedMode === 'pubsub' || normalizedMode === 'pub/sub') {
        this.eventBusMode = 'pubsub';
      } else if (normalizedMode === 'in_memory' || normalizedMode === 'in-memory' || normalizedMode === 'memory') {
        this.eventBusMode = 'in_memory';
      } else {
        this.eventBusMode = normalizedMode;
      }
      
      console.log('[AgentsProvider] eventBusMode set to:', this.eventBusMode, '(from:', mode, ')');
      // Do NOT fire here to avoid refresh loops; refresh() controls repaint
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
        // Use last known mode; avoid triggering update here to prevent loops
        let modeIcon: string;
        let modeName: string;
        let tooltipText: string;
        
        if (this.eventBusMode === 'pubsub') {
          modeIcon = '📡';
          modeName = 'Pub/Sub';
          tooltipText = 'Pub/Sub Mode: Agents communicate via Google Pub/Sub (scalable)';
        } else if (this.eventBusMode === 'in_memory') {
          modeIcon = '💾';
          modeName = 'In-Memory';
          tooltipText = 'In-Memory Mode: Agents communicate via in-memory events (local)';
        } else {
          modeIcon = '⚠️';
          modeName = 'Unknown';
          tooltipText = 'Event Bus Mode: Not detected. Ensure EVENT_BUS_MODE is set in Cloud Run (pubsub or in_memory)';
        }
        
        const modeItem = new AgentItem({
          agentId: 'event-bus-mode',
          name: `⚙️ ${modeIcon} Event Bus: ${modeName}`,
          status: 'active',
          lastActivity: 'now'
        }, vscode.TreeItemCollapsibleState.Expanded);
        modeItem.tooltip = tooltipText;
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
        const normalized = agents.map(a => {
          const validStatuses = ['active', 'idle', 'error'] as const;
          const status = validStatuses.includes(a.status as any) ? a.status : 'idle';
          return { ...a, status } as AgentStatus;
        });
        return normalized.map(agent => new AgentItem(agent));
      } catch (error) {
        // Return default agents if API not implemented yet
        // 6 active agents + 1 meta-agent (retrospective)
        return [
          new AgentItem({ agentId: 'spec', name: '📋 Spec Agent', status: 'active', lastActivity: '5m ago' }),
          new AgentItem({ agentId: 'git', name: '🔧 Git Agent', status: 'active', lastActivity: '2m ago' }),
          new AgentItem({ agentId: 'development', name: '💻 Development Agent', status: 'active', lastActivity: '3m ago' }),
          new AgentItem({ agentId: 'context', name: '📦 Context Agent', status: 'active', lastActivity: 'now' }),
          new AgentItem({ agentId: 'strategy-coach', name: '🎯 Strategy Coach Agent', status: 'active', lastActivity: 'now' }),
          new AgentItem({ agentId: 'milestone', name: '🏁 Milestone Agent', status: 'active', lastActivity: '10m ago' }),
          new AgentItem({ agentId: 'retrospective', name: '🔄 Retrospective Agent', status: 'active', lastActivity: '15m ago' }),
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
    this.tooltip = `Last activity: ${agent.lastActivity}`;
    
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

