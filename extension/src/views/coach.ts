import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';

export class CoachProvider implements vscode.TreeDataProvider<CoachItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<CoachItem | undefined | null | void> = new vscode.EventEmitter<CoachItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<CoachItem | undefined | null | void> = this._onDidChangeTreeData.event;

  private messages: { question: string; answer: string; timestamp: Date }[] = [];

  constructor(private contextPilotService: ContextPilotService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  addMessage(question: string, answer: string): void {
    this.messages.unshift({ question, answer, timestamp: new Date() });
    if (this.messages.length > 10) {
      this.messages = this.messages.slice(0, 10);
    }
    this.refresh();
  }

  getTreeItem(element: CoachItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: CoachItem): Promise<CoachItem[]> {
    if (!this.contextPilotService.isConnected()) {
      return [
        new CoachItem(
          'Not connected',
          'Connect to ContextPilot to use Coach',
          vscode.TreeItemCollapsibleState.None
        )
      ];
    }

    if (!element) {
      // Root level
      if (this.messages.length === 0) {
        return [
          new CoachItem(
            'Ask Coach a question',
            'Use Command Palette: ContextPilot: Ask Coach',
            vscode.TreeItemCollapsibleState.None
          )
        ];
      }

      return this.messages.map(
        msg => new CoachItem(
          msg.question,
          msg.answer.substring(0, 100) + '...',
          vscode.TreeItemCollapsibleState.Collapsed,
          msg
        )
      );
    } else {
      // Show full answer
      if (element.message) {
        return [
          new CoachItem(
            'Answer',
            element.message.answer,
            vscode.TreeItemCollapsibleState.None
          )
        ];
      }
      return [];
    }
  }
}

class CoachItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly message?: { question: string; answer: string; timestamp: Date }
  ) {
    super(label, collapsibleState);
    this.tooltip = description;
    this.iconPath = new vscode.ThemeIcon('comment');
  }
}

