import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  console.log('ContextPilot extension is now active!');

  // Register a simple connect command
  const disposable = vscode.commands.registerCommand('contextpilot.connect', async () => {
    try {
      vscode.window.showInformationMessage('🔄 Attempting to connect...');
      
      // Simple fetch test
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json() as any;
      
      vscode.window.showInformationMessage(`✅ Connected! Status: ${data.status}`);
    } catch (error) {
      vscode.window.showErrorMessage(`❌ Connection failed: ${error}`);
    }
  });

  context.subscriptions.push(disposable);
}

export function deactivate() {}
