# ContextPilot Extension - Installation Guide

## 📦 Quick Install

### Method 1: Command Palette (Recommended - works for all)
1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Linux/Windows)
2. Type: **"Extensions: Install from VSIX..."**
3. Select file: `extension/contextpilot-0.2.1.vsix`
4. Restart VS Code/Cursor completely

---

### Method 2: Automated Script
```bash
cd extension/
./install.sh
```

Then **restart VS Code/Cursor completely**.

---

### Method 3: Manual Installation (Cursor only - if command palette doesn't work)
```bash
cd extension/
unzip -q extension/contextpilot-0.2.1.vsix -d /tmp/contextpilot-install
mkdir -p ~/.cursor/extensions/livresoltech.contextpilot-0.2.1
cp -r /tmp/contextpilot-install/extension/* ~/.cursor/extensions/livresoltech.contextpilot-0.2.1/
rm -rf /tmp/contextpilot-install
```

Then **restart Cursor completely**.

---

## ⚙️ Configuration

After installation, configure the backend URL:

1. Open Settings: `Cmd+,` (Mac) or `Ctrl+,` (Linux/Windows)
2. Search: **"ContextPilot"**
3. Set **API URL** to:
   ```
   https://contextpilot-backend-581368740395.us-central1.run.app
   ```

---

## 🚀 Usage

1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Linux/Windows)
2. Type: **"ContextPilot"**
3. Try these commands:
   - **ContextPilot: Start Agent Retrospective** - AI-powered team retrospectives
   - **ContextPilot: Ask Coach** - Get development guidance
   - **ContextPilot: View Change Proposals** - Review AI-suggested changes
   - **ContextPilot: Get Project Context** - Analyze project state

---

## ✅ Verify Installation

After restart, check that commands appear:
```
Cmd+Shift+P → type "ContextPilot"
```

You should see multiple ContextPilot commands available.

---

## 🐛 Troubleshooting

### Commands not appearing?
- Make sure you **completely restarted** VS Code/Cursor (not just reloaded window)
- Check Extensions panel: `Cmd+Shift+X` → search "ContextPilot"

### Backend connection issues?
- Verify API URL in settings points to Cloud Run instance
- Check network connectivity

### Need help?
Open an issue at: https://github.com/fsegall/gcloud_contextpilot

