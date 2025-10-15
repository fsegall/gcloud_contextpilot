# 🔌 VSCode/Cursor Extension Development Guide

Complete guide for developing and deploying the ContextPilot extension.

---

## 📁 Project Structure

```
extension/
├── package.json              # Extension manifest
├── tsconfig.json             # TypeScript config
├── README.md                 # Extension documentation
├── .vscodeignore            # Files to exclude from package
├── .eslintrc.json           # ESLint config
├── .gitignore               # Git ignore
│
└── src/
    ├── extension.ts         # Main entry point
    ├── commands/
    │   └── index.ts         # Command implementations
    ├── services/
    │   └── contextpilot.ts  # API service
    ├── views/
    │   ├── proposals.ts     # Proposals tree view
    │   ├── rewards.ts       # Rewards tree view
    │   ├── agents.ts        # Agents status view
    │   └── coach.ts         # Coach view
    └── types/
        └── index.ts         # Type definitions
```

---

## 🚀 Getting Started

### Prerequisites
```bash
node --version   # v18+
npm --version    # v9+
```

### Install Dependencies
```bash
cd extension
npm install
```

### Compile TypeScript
```bash
npm run compile

# Or watch mode (auto-compile on save)
npm run watch
```

---

## 🧪 Testing

### Run Extension in Development Host

1. Open `extension/` folder in VSCode
2. Press `F5` (or Run > Start Debugging)
3. A new "Extension Development Host" window opens
4. Test your extension there

### Manual Testing Checklist

- [ ] Extension activates on startup
- [ ] Status bar shows connection status
- [ ] Sidebar views appear in Activity Bar
- [ ] Commands are registered in Command Palette
- [ ] API connection works
- [ ] Change proposals load and render
- [ ] Approve/reject actions work
- [ ] Rewards balance displays correctly
- [ ] Coach responses appear
- [ ] File change tracking works

---

## 📦 Packaging

### Install VSCE (VS Code Extension Manager)
```bash
npm install -g @vscode/vsce
```

### Create .vsix Package
```bash
cd extension
npm run package

# Or manually
vsce package
```

This creates `contextpilot-0.1.0.vsix`

---

## 🚢 Publishing

### Option 1: Manual Installation (Development)

Share the `.vsix` file:
```bash
# Install locally
code --install-extension contextpilot-0.1.0.vsix

# Or in VSCode UI:
# Extensions > ... > Install from VSIX
```

### Option 2: VS Code Marketplace (Production)

1. **Create Publisher Account**
   - Go to: https://marketplace.visualstudio.com/manage
   - Sign in with Microsoft account
   - Create a publisher

2. **Get Personal Access Token**
   - Azure DevOps: https://dev.azure.com
   - User Settings > Personal Access Tokens
   - Create new token with "Marketplace (Manage)" scope

3. **Login to VSCE**
```bash
vsce login <publisher-name>
# Enter your Personal Access Token
```

4. **Publish**
```bash
cd extension
vsce publish

# Or publish specific version
vsce publish minor  # 0.1.0 → 0.2.0
vsce publish major  # 0.1.0 → 1.0.0
vsce publish patch  # 0.1.0 → 0.1.1
```

---

## 🎨 Customization

### Add New Command

1. **Register in `package.json`**:
```json
{
  "contributes": {
    "commands": [
      {
        "command": "contextpilot.myCommand",
        "title": "ContextPilot: My Command",
        "icon": "$(icon-name)"
      }
    ]
  }
}
```

2. **Implement in `src/commands/index.ts`**:
```typescript
export async function myCommand(service: ContextPilotService): Promise<void> {
  // Implementation
}
```

3. **Register in `src/extension.ts`**:
```typescript
context.subscriptions.push(
  vscode.commands.registerCommand('contextpilot.myCommand', () => {
    commands.myCommand(contextPilotService);
  })
);
```

### Add New View

1. **Define in `package.json`**:
```json
{
  "views": {
    "contextpilot": [
      {
        "id": "contextpilot.myView",
        "name": "My View"
      }
    ]
  }
}
```

2. **Create Provider** (`src/views/myview.ts`):
```typescript
export class MyViewProvider implements vscode.TreeDataProvider<MyItem> {
  // Implementation
}
```

3. **Register in `src/extension.ts`**:
```typescript
const myViewProvider = new MyViewProvider(contextPilotService);
vscode.window.registerTreeDataProvider('contextpilot.myView', myViewProvider);
```

---

## 🔧 Configuration

### Settings Schema

Define in `package.json`:
```json
{
  "configuration": {
    "properties": {
      "contextpilot.mySetting": {
        "type": "string",
        "default": "default value",
        "description": "My setting description"
      }
    }
  }
}
```

### Read Settings in Code:
```typescript
const config = vscode.workspace.getConfiguration('contextpilot');
const value = config.get<string>('mySetting');
```

---

## 🐛 Debugging

### Enable Debug Logs
```typescript
const channel = vscode.window.createOutputChannel('ContextPilot');
channel.appendLine('Debug message');
channel.show();
```

### Common Issues

**Extension not activating?**
- Check `activationEvents` in `package.json`
- Verify no TypeScript compilation errors
- Check Extension Host logs (Help > Toggle Developer Tools)

**Commands not appearing?**
- Reload window: `Ctrl+Shift+P` → "Reload Window"
- Check `contributes.commands` in `package.json`

**Views not showing?**
- Check `contributes.views` registration
- Verify TreeDataProvider implementation
- Ensure view container is defined

---

## 📊 Performance

### Best Practices

1. **Lazy Loading**: Only load heavy resources when needed
2. **Debounce**: Debounce file watchers (use 500ms+ delay)
3. **Caching**: Cache API responses where appropriate
4. **Async**: Use async/await for all I/O operations
5. **Dispose**: Always dispose subscriptions in `deactivate()`

### Monitor Performance
```typescript
const start = Date.now();
// ... operation
const duration = Date.now() - start;
console.log(`Operation took ${duration}ms`);
```

---

## 🔐 Security

### API Keys

**❌ NEVER** hardcode API keys in extension code.

**✅ Use settings**:
```typescript
const apiKey = config.get<string>('contextpilot.apiKey');
```

### Secrets API (VSCode 1.53+)
```typescript
await context.secrets.store('contextpilot.token', token);
const token = await context.secrets.get('contextpilot.token');
```

---

## 📚 Resources

### Documentation
- [VS Code Extension API](https://code.visualstudio.com/api)
- [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)
- [Publishing Extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)

### Examples
- [VS Code Extension Samples](https://github.com/microsoft/vscode-extension-samples)
- [Tree View Example](https://github.com/microsoft/vscode-extension-samples/tree/main/tree-view-sample)

---

## 🚀 Deployment Checklist

Before publishing:

- [ ] Update version in `package.json`
- [ ] Update `CHANGELOG.md`
- [ ] Test on Windows, Mac, and Linux
- [ ] Test with both VSCode and Cursor
- [ ] Run `npm run lint` with no errors
- [ ] Package with `npm run package`
- [ ] Test the `.vsix` file manually
- [ ] Write release notes
- [ ] Tag Git release
- [ ] Publish to marketplace

---

## 🎯 Roadmap

### v0.2.0 (Next Release)
- [ ] GitHub Copilot integration
- [ ] Inline suggestions (like GitHub Copilot)
- [ ] Webview panel for Change Proposal diffs
- [ ] Keyboard shortcuts

### v0.3.0
- [ ] Multi-workspace support
- [ ] Team features (shared context)
- [ ] Metrics dashboard

### v1.0.0 (Production Ready)
- [ ] Complete test coverage
- [ ] Performance benchmarks
- [ ] Multi-language support
- [ ] Marketplace listing

---

**Last Updated**: 2025-10-14  
**Maintained By**: ContextPilot Team
