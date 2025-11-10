import * as vscode from 'vscode';
import { ContextPilotService, ChangeProposal, ProposedChange } from '../services/contextpilot';

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
        vscode.TreeItemCollapsibleState.Expanded
      );
      modeItem.tooltip = this.storageMode === 'cloud' 
        ? 'Cloud Mode: Proposals stored in Firestore, commits via GitHub Actions'
        : 'Local Mode: Proposals stored in local files, direct Git commits';
      modeItem.contextValue = 'mode-indicator';
      
      const items: ProposalTreeItem[] = [modeItem];
      
      return items;
    } else if (element.contextValue === 'mode-indicator') {
      // Children of mode indicator - show proposals
      const proposals = await this.contextPilotService.getProposals();
      return proposals
        .filter(p => p.status === 'pending')
        .map(p => new ProposalItem(p, vscode.TreeItemCollapsibleState.Collapsed));
    } else if (element instanceof ProposalItem && element.proposal) {
      // Lazy-load full proposal details if changes are missing
      if (!element.hasLoadedChanges()) {
        const fullProposal = await this.contextPilotService.getProposal(element.proposal.id);
        if (fullProposal) {
          element.updateProposal(fullProposal);
        }
      }

      const changes = element.proposal.proposedChanges || [];
      return changes.map((change: ProposedChange) => new ProposalChangeItem(element.proposal!.id, change));
    }
    
    return [];
  }
}

class ProposalItem extends vscode.TreeItem {
  public readonly proposal?: ChangeProposal;
  private changesLoaded = false;

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
      const fileCount = proposalOrTitle.proposedChanges?.length || 0;
      this.tooltip = `${proposalOrTitle.description}\n\n💡 Click ➕ to expand files\n💡 Right-click for actions (View Diff, Approve, Reject)`;
      this.description = `by ${proposalOrTitle.agentId} • ${fileCount} file${fileCount !== 1 ? 's' : ''}`;
      this.contextValue = 'proposal';
      this.iconPath = new vscode.ThemeIcon('git-pull-request');
    }
    
    // Debug: Log proposal ID (only for actual proposals)
    if (this.proposal) {
      console.log(`[ProposalItem] Creating item with ID: ${this.proposal.id}, Title: ${this.proposal.title}`);
      if (this.proposal.proposedChanges && this.proposal.proposedChanges.length > 0) {
        this.changesLoaded = true;
      }
    }
    
    // Only set command if this is NOT an expandable proposal with changes
    // This allows the tree to expand/collapse naturally
    if (this.proposal && this.proposal.proposedChanges && this.proposal.proposedChanges.length > 0) {
      // Don't set command - let the tree handle expansion
      // User can right-click -> "View Diff" or click on individual files
    } else if (this.proposal) {
      // Proposal with no changes - make clickable
      this.command = {
        command: 'contextpilot.viewProposalDiff',
        title: 'View Diff',
        arguments: [this.proposal.id]
      };
    }
  }

  hasLoadedChanges(): boolean {
    return this.changesLoaded;
  }

  updateProposal(proposal: ChangeProposal) {
    if (!this.proposal) {
      return;
    }

    this.proposal.proposedChanges = proposal.proposedChanges || [];
    this.proposal.diff = proposal.diff;
    this.proposal.description = proposal.description;
    this.proposal.status = proposal.status;
    this.changesLoaded = true;
  }
}

class ProposalChangeItem extends vscode.TreeItem {
  constructor(
    public readonly proposalId: string,
    public readonly change: ProposedChange
  ) {
    super(change.filePath, vscode.TreeItemCollapsibleState.None);
    this.tooltip = `${change.changeType}: ${change.description}`;
    this.description = change.changeType;
    this.iconPath = new vscode.ThemeIcon(
      change.changeType === 'create' ? 'new-file' :
      change.changeType === 'update' ? 'edit' :
      'trash'
    );
    this.contextValue = 'proposalChange';

    this.command = {
      command: 'contextpilot.viewProposalChange',
      title: 'View Proposal Change Diff',
      arguments: [this.proposalId, this.change]
    };
  }
}

