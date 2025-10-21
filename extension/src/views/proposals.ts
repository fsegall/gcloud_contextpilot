import * as vscode from 'vscode';
import { ContextPilotService, ChangeProposal } from '../services/contextpilot';

type ProposalTreeItem = ProposalItem | ProposalChangeItem;

export class ProposalsProvider implements vscode.TreeDataProvider<ProposalTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<ProposalTreeItem | undefined | null | void> = new vscode.EventEmitter<ProposalTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<ProposalTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;
  private storageMode: string = 'unknown';

  constructor(private contextPilotService: ContextPilotService) {
    this.updateStorageMode();
  }

  refresh(): void {
    this.updateStorageMode();
    this._onDidChangeTreeData.fire();
  }

  private async updateStorageMode(): Promise<void> {
    try {
      console.log('[ProposalsProvider] updateStorageMode - isConnected:', this.contextPilotService.isConnected());
      if (this.contextPilotService.isConnected()) {
        const health = await this.contextPilotService.getHealth();
        console.log('[ProposalsProvider] health response:', health);
        console.log('[ProposalsProvider] health.config:', health.config);
        // Backend returns config nested: { config: { storage_mode: "cloud" } }
        this.storageMode = health.config?.storage_mode || 'unknown';
        console.log('[ProposalsProvider] storageMode set to:', this.storageMode);
      } else {
        console.log('[ProposalsProvider] Service not connected, keeping unknown');
      }
    } catch (error) {
      console.error('[ProposalsProvider] Failed to update storage mode:', error);
      this.storageMode = 'unknown';
    }
  }

  getTreeItem(element: ProposalTreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: ProposalTreeItem): Promise<ProposalTreeItem[]> {
    console.log('[ProposalsProvider] getChildren called');
    if (!this.contextPilotService.isConnected()) {
      console.log('[ProposalsProvider] Not connected, returning empty array');
      return [];
    }

    if (!element) {
      // Root level - show mode indicator + proposals
      console.log('[ProposalsProvider] Fetching proposals...');
      
      // Fetch fresh mode before displaying
      await this.updateStorageMode();
      
      const proposals = await this.contextPilotService.getProposals();
      
      // Add mode indicator as first item
      const modeIcon = this.storageMode === 'cloud' ? '☁️' : '📁';
      const modeItem = new ProposalItem(
        `⚙️ ${modeIcon} Storage Mode: ${this.storageMode}`,
        vscode.TreeItemCollapsibleState.None
      );
      modeItem.tooltip = this.storageMode === 'cloud' 
        ? 'Cloud Mode: Proposals stored in Firestore, commits via GitHub Actions'
        : 'Local Mode: Proposals stored in local files, direct Git commits';
      modeItem.contextValue = 'mode-indicator';
      
      const items: ProposalTreeItem[] = [modeItem];
      
      // Add proposals
      const proposalItems = proposals
        .filter(p => p.status === 'pending')
        .map(p => new ProposalItem(p, vscode.TreeItemCollapsibleState.Collapsed));
      
      items.push(...proposalItems);
      return items;
    } else if (element instanceof ProposalItem && element.proposal) {
      // Show proposal changes
      return element.proposal.proposed_changes.map(
        change => new ProposalChangeItem(change)
      );
    }
    
    return [];
  }
}

class ProposalItem extends vscode.TreeItem {
  public readonly proposal?: ChangeProposal;

  constructor(
    proposalOrTitle: ChangeProposal | string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    // Determine title and call super
    const title = typeof proposalOrTitle === 'string' ? proposalOrTitle : proposalOrTitle.title;
    super(title, collapsibleState);
    
    if (typeof proposalOrTitle === 'string') {
      // Mode indicator constructor
      this.iconPath = new vscode.ThemeIcon('settings-gear');
    } else {
      // Proposal constructor
      this.proposal = proposalOrTitle;
      this.tooltip = proposalOrTitle.description;
      this.description = `by ${proposalOrTitle.agent_id}`;
      this.contextValue = 'proposal';
      this.iconPath = new vscode.ThemeIcon('git-pull-request');
    }
    
    // Debug: Log proposal ID (only for actual proposals)
    if (this.proposal) {
      console.log(`[ProposalItem] Creating item with ID: ${this.proposal.id}, Title: ${this.proposal.title}`);
    }
    
    this.command = {
      command: 'contextpilot.viewProposalDiff',
      title: 'View Diff',
      arguments: [this.proposal?.id]
    };
  }
}

class ProposalChangeItem extends vscode.TreeItem {
  constructor(
    public readonly change: {
      file_path: string;
      change_type: string;
      description: string;
    }
  ) {
    super(change.file_path, vscode.TreeItemCollapsibleState.None);
    this.tooltip = change.description;
    this.description = change.change_type;
    this.iconPath = new vscode.ThemeIcon(
      change.change_type === 'create' ? 'new-file' :
      change.change_type === 'update' ? 'edit' :
      'trash'
    );
  }
}

