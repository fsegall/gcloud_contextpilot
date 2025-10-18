import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  console.log('ContextPilot extension is now active!');

  // Register a simple test command
  const disposable = vscode.commands.registerCommand('contextpilot.test', () => {
    vscode.window.showInformationMessage('ContextPilot test command works!');
  });

  context.subscriptions.push(disposable);
}

export function deactivate() {}
