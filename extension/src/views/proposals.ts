import * as vscode from 'vscode';
import { ContextPilotService, ChangeProposal } from '../services/contextpilot';

type ProposalTreeItem = ProposalItem | ProposalChangeItem;

export class ProposalsProvider implements vscode.TreeDataProvider<ProposalTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<ProposalTreeItem | undefined | null | void> = new vscode.EventEmitter<ProposalTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<ProposalTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

  constructor(private contextPilotService: ContextPilotService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: ProposalTreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: ProposalTreeItem): Promise<ProposalTreeItem[]> {
    if (!this.contextPilotService.isConnected()) {
      return [];
    }

    if (!element) {
      // Root level - show proposals
      const proposals = await this.contextPilotService.getProposals();
      return proposals
        .filter(p => p.status === 'pending')
        .map(p => new ProposalItem(p, vscode.TreeItemCollapsibleState.Collapsed));
    } else if (element instanceof ProposalItem) {
      // Show proposal changes
      return element.proposal.proposed_changes.map(
        change => new ProposalChangeItem(change)
      );
    }
    
    return [];
  }
}

class ProposalItem extends vscode.TreeItem {
  constructor(
    public readonly proposal: ChangeProposal,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(proposal.title, collapsibleState);
    this.tooltip = proposal.description;
    this.description = `by ${proposal.agent_id}`;
    this.contextValue = 'proposal';
    this.iconPath = new vscode.ThemeIcon('git-pull-request');
    this.command = {
      command: 'contextpilot.approveProposal',
      title: 'Approve Proposal',
      arguments: [proposal.id]
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

