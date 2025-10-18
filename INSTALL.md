# 📦 Installation Guide for Judges & Testers

> **⏱️ Installation time: 2 minutes**

## Method 1: Extension Only (Recommended for Testing)

### Step 1: Download
Go to: https://github.com/fsegall/gcloud_contextpilot/releases/latest

Download: `contextpilot-0.2.1.vsix`

### Step 2: Install

**In VS Code:**
```bash
code --install-extension contextpilot-0.2.1.vsix
```

**In Cursor:**
```bash
cursor --install-extension contextpilot-0.2.1.vsix
```

**OR via GUI (works in both):**
1. Open VS Code or Cursor
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type: `Extensions: Install from VSIX...`
4. Select the downloaded `contextpilot-0.2.1.vsix` file
5. Click "Install"
6. Reload the window if prompted

### Step 3: Test
1. Open any project folder
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type: `ContextPilot: Start Agent Retrospective`
4. Enter a discussion topic (e.g., "How can we improve code quality?")
5. **Watch the agents work!** 🤖✨

**Expected Result:**
- Notification: "Starting agent retrospective..."
- Beautiful webview opens with:
  - Agent metrics
  - Collaboration insights
  - Action items with priorities
  - Automatic improvement proposals

---

## Method 2: Full Local Setup (For Deep Testing)

### Prerequisites
- Docker Desktop installed
- Git installed

### Step 1: Clone
```bash
git clone https://github.com/fsegall/gcloud_contextpilot.git
cd gcloud_contextpilot
```

### Step 2: Start Backend
```bash
cd back-end
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Step 3: Install Extension
```bash
cd ../extension
code --install-extension contextpilot-0.2.1.vsix
```

### Step 4: Configure
Create `.vscode/settings.json` in your project:
```json
{
  "contextpilot.apiUrl": "http://localhost:8000",
  "contextpilot.autoConnect": true
}
```

### Step 5: Test
Same as Method 1, Step 3!

---

## 🎯 What to Test

### 1. Agent Retrospective (Star Feature! ⭐)
```
Cmd/Ctrl+Shift+P → ContextPilot: Start Agent Retrospective
```

**Suggested Topics:**
- "How can we improve test coverage?"
- "What bottlenecks exist in our workflow?"
- "How can agents collaborate better?"

**What You'll See:**
- 📊 Real-time agent metrics
- 🔍 Event pattern analysis
- 💡 AI-generated insights
- 🎯 Prioritized action items
- 📝 Automatic code improvement proposals

### 2. View Active Agents
```
Cmd/Ctrl+Shift+P → ContextPilot: Show Agents
```
See all 7 specialized agents and their status.

### 3. Check Project Context
```
Cmd/Ctrl+Shift+P → ContextPilot: View Context
```
See AI-maintained project documentation.

### 4. Review Proposals
```
Cmd/Ctrl+Shift+P → ContextPilot: View Proposals
```
See agent-generated code change suggestions.

---

## 🐛 Troubleshooting

### Extension Not Found?
```bash
# Verify installation
code --list-extensions | grep contextpilot
# Should show: livresoltech.contextpilot
```

If not found, try GUI installation method above.

### "No Context Loaded" Error?

**Check backend connection:**
1. Open Developer Tools: `Help → Toggle Developer Tools`
2. Check Console tab for errors
3. Look for API connection messages

**Fix:**
- **Using hosted backend?** No action needed, it should work automatically
- **Using local backend?** Ensure Docker is running: `docker ps`

### Commands Don't Appear?

**Reload the window:**
1. `Cmd/Ctrl+Shift+P`
2. Type: `Developer: Reload Window`
3. Try again

**Check extension is enabled:**
1. Go to Extensions view (`Cmd/Ctrl+Shift+X`)
2. Search "ContextPilot"
3. Should show "Enabled" (not "Disabled")

### Backend Issues (Local Setup)?

**Check Docker:**
```bash
docker-compose ps
# Should show: contextpilot-backend (Up)
```

**View logs:**
```bash
docker-compose logs -f
```

**Restart:**
```bash
docker-compose down
docker-compose up -d
```

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Extension appears in Extensions list
- [ ] Commands appear in Command Palette (`Cmd/Ctrl+Shift+P`)
- [ ] "ContextPilot: Start Agent Retrospective" works
- [ ] Webview opens with formatted results
- [ ] No errors in Developer Console

---

## 📞 Support

**Issues?** Open a ticket: https://github.com/fsegall/gcloud_contextpilot/issues

**Email:** contact@livresoltech.com

**Documentation:**
- [QUICKSTART.md](QUICKSTART.md) - Full setup guide
- [README.md](README.md) - Project overview
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical details
- [openapi.yaml](openapi.yaml) - API reference

---

## 🎉 Success!

If you see the Agent Retrospective webview, **you're ready to explore!**

The extension connects to our hosted Cloud Run backend by default, so you can test immediately after installation.

**Enjoy exploring ContextPilot!** 🚀




