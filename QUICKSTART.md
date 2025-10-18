# 🚀 Quick Start Guide

Get ContextPilot running in **5 minutes**!

## 📋 Prerequisites

- **VS Code** or **Cursor** editor
- **Git** installed
- **Internet connection** (for API access)

## 🎯 Choose Your Testing Method

### Option A: Extension Only (Easiest - 2 minutes)

Perfect for trying out the extension with our hosted backend.

1. **Download the Extension**
   - Go to [GitHub Releases](https://github.com/fsegall/gcloud_contextpilot/releases/latest)
   - Download `contextpilot-0.2.1.vsix`

2. **Install in VS Code**
   ```bash
   code --install-extension contextpilot-0.2.1.vsix
   ```

   **OR in Cursor:**
   ```bash
   cursor --install-extension contextpilot-0.2.1.vsix
   ```

   **OR via GUI:**
   - Open VS Code/Cursor
   - `Cmd/Ctrl+Shift+P` → `Extensions: Install from VSIX...`
   - Select the downloaded `.vsix` file

3. **Configure (Optional)**
   - The extension connects to our hosted backend by default
   - Open settings: `Cmd/Ctrl+,` → search "ContextPilot"
   - API URL is pre-configured: `https://contextpilot-api-123456789.us-central1.run.app`

4. **Test It!**
   - Open any project folder
   - `Cmd/Ctrl+Shift+P` → `ContextPilot: Start Agent Retrospective`
   - Enter a discussion topic (e.g., "How can we improve code quality?")
   - Watch the magic happen! ✨

---

### Option B: Full Local Setup (5 minutes)

For developers who want to run everything locally.

#### 1. Clone the Repository
```bash
git clone https://github.com/fsegall/gcloud_contextpilot.git
cd gcloud_contextpilot
```

#### 2. Backend Setup (Choose One)

**Option B1: Docker Compose (Recommended)**
```bash
cd back-end
docker-compose up -d
```

Backend runs on: `http://localhost:8000`

**Option B2: Python Direct**
```bash
cd back-end
pip install -r requirements.txt
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Install Extension
```bash
cd ../extension
code --install-extension contextpilot-0.2.1.vsix
```

#### 4. Configure for Local Backend
Create `.vscode/settings.json` in your project:
```json
{
  "contextpilot.apiUrl": "http://localhost:8000",
  "contextpilot.autoConnect": true
}
```

#### 5. Test It!
- `Cmd/Ctrl+Shift+P` → `ContextPilot: Start Agent Retrospective`
- Enter a topic and see results!

---

### Option C: API Testing (For Backend Devs)

Test the API directly without the extension.

#### 1. Start Backend
```bash
cd back-end
docker-compose up -d
# OR
uvicorn app.server:app --reload
```

#### 2. Test with cURL
```bash
# Health check
curl http://localhost:8000/health

# Get agent status
curl http://localhost:8000/agents/status

# Trigger retrospective
curl -X POST http://localhost:8000/agents/retrospective/trigger \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "test-workspace", "trigger": "manual", "use_llm": false}'
```

#### 3. OpenAPI Spec
Open `http://localhost:8000/docs` in your browser for interactive API documentation.

---

## 🎮 Key Features to Try

### 1. Agent Retrospective (NEW! 🆕)
```
Cmd/Ctrl+Shift+P → ContextPilot: Start Agent Retrospective
```
- Suggest a discussion topic
- Watch agents collaborate and analyze
- Get actionable improvement proposals
- See automatic code change suggestions

### 2. View Context
```
Cmd/Ctrl+Shift+P → ContextPilot: View Context
```
See AI-maintained project context.

### 3. Check Agents
```
Cmd/Ctrl+Shift+P → ContextPilot: Show Agents
```
Monitor all 7 specialized agents.

### 4. Review Proposals
```
Cmd/Ctrl+Shift+P → ContextPilot: View Proposals
```
See AI-generated code improvement suggestions.

---

## 🐛 Troubleshooting

### Extension Not Loading?

**VS Code:**
```bash
# Verify installation
code --list-extensions | grep contextpilot
# Should show: livresoltech.contextpilot
```

**Cursor:**
```bash
cursor --list-extensions | grep contextpilot
```

If not found, try installing via GUI:
- `Cmd/Ctrl+Shift+P` → `Extensions: Install from VSIX...`

### "No Context Loaded" Error?

1. **Check backend connection:**
   - Open Developer Tools: `Help → Toggle Developer Tools`
   - Check Console for errors

2. **Verify API URL:**
   - Settings → Extensions → ContextPilot → API URL
   - Should be: `https://contextpilot-api-123456789.us-central1.run.app` (hosted)
   - OR: `http://localhost:8000` (local)

3. **Test backend directly:**
   ```bash
   curl https://contextpilot-api-123456789.us-central1.run.app/health
   # Should return: {"status": "healthy"}
   ```

### Backend Issues (Local Setup)?

1. **Check Docker:**
   ```bash
   docker-compose ps
   # Should show contextpilot-backend running
   ```

2. **Check logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Port already in use?**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use 8001 instead
   ```

### Extension Commands Not Appearing?

1. **Reload window:**
   - `Cmd/Ctrl+Shift+P` → `Developer: Reload Window`

2. **Check extension is enabled:**
   - Extensions view → Search "ContextPilot" → Should show "Enabled"

3. **Reinstall:**
   ```bash
   code --uninstall-extension livresoltech.contextpilot
   code --install-extension contextpilot-0.2.1.vsix
   ```

---

## 📚 Next Steps

- **Full Documentation:** [README.md](README.md)
- **Architecture Deep Dive:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Reference:** [openapi.yaml](openapi.yaml)
- **Security Details:** [SECURITY.md](SECURITY.md)
- **Contribute:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💬 Need Help?

- **Issues:** [GitHub Issues](https://github.com/fsegall/gcloud_contextpilot/issues)
- **Email:** contact@livresoltech.com
- **Demo Video:** [Watch on YouTube](#) *(coming soon)*

---

## 🎉 Success!

If you see the Agent Retrospective webview with beautiful formatted results, **you're all set!** 

Try suggesting topics like:
- "How can we improve test coverage?"
- "What are the bottlenecks in our workflow?"
- "How can agents collaborate better?"

Watch as agents analyze, discuss, and propose improvements! 🤖✨
