# ⚡ ContextPilot - Quick Start Guide

**Get up and running in 2 minutes!**

---

## 🎯 For Hackathon Judges & Evaluators

### Option 1: Install Extension (Recommended - 2 minutes)

**Try the full ContextPilot experience:**

```bash
# 1. Download extension
curl -LO https://github.com/fsegall/gcloud_contextpilot/releases/download/v0.1.1/contextpilot-0.1.1.vsix

# 2. Install in VS Code/Cursor
code --install-extension contextpilot-0.1.1.vsix

# 3. Open VS Code, look for ContextPilot icon (🚀) in sidebar

# 4. Done! Extension connects automatically to our Cloud Run backend
```

**What you'll see:**
- 📋 AI-generated proposals in sidebar
- 🎮 CPT token balance and rewards
- ✅ One-click approve → Auto git commit
- 🏆 Achievement notifications

**No configuration needed!** Uses shared Gemini API key (rate-limited for fair usage).

---

### Option 2: Test Backend API (1 minute)

**See Cloud Run in action:**

```bash
# Health check
curl https://contextpilot-backend-581368740395.us-central1.run.app/health

# Get proposals
curl "https://contextpilot-backend-581368740395.us-central1.run.app/proposals?workspace_id=default&status=pending"

# Get agent status
curl https://contextpilot-backend-581368740395.us-central1.run.app/agents/status

# View abuse protection stats
curl https://contextpilot-backend-581368740395.us-central1.run.app/admin/abuse-stats
```

**Explore the API:** [OpenAPI Spec](https://contextpilot-backend-581368740395.us-central1.run.app/docs)

---

### Option 3: Deploy Your Own (30 minutes)

**Deploy full infrastructure with Terraform:**

```bash
# 1. Clone repository
git clone https://github.com/fsegall/gcloud_contextpilot.git
cd gcloud_contextpilot

# 2. Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. Create Gemini API key
# Visit: https://makersuite.google.com/app/apikey
# Copy your key

# 4. Deploy infrastructure
cd terraform
terraform init
terraform apply

# 5. Add API key to Secret Manager
echo -n "YOUR_GEMINI_KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

# 6. Build and deploy backend
cd ../back-end
docker build -t gcr.io/YOUR_PROJECT_ID/contextpilot-backend:latest .
docker push gcr.io/YOUR_PROJECT_ID/contextpilot-backend:latest
gcloud run deploy contextpilot-backend \
  --image gcr.io/YOUR_PROJECT_ID/contextpilot-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# 7. Install extension and configure to use your backend
code --install-extension ../extension/contextpilot-0.1.1.vsix
# Settings → contextpilot.apiUrl → YOUR_CLOUD_RUN_URL
```

**See:** [Deployment Guide](docs/deployment/DEPLOYMENT.md) for detailed steps.

---

## 🎬 Video Demo

**Coming soon:** 3-minute walkthrough showing:
1. Extension installation
2. Viewing AI proposals
3. One-click approval
4. Automatic git commit
5. Earning CPT tokens

---

## 📊 What You're Testing

### Multi-Agent System
- **6 specialized agents** (Spec, Git, Context, Coach, Milestone, Strategy)
- **Event-driven coordination** via Google Cloud Pub/Sub
- **Persistent state** in Firestore
- **AI generation** with Gemini 1.5 Flash

### Cloud Run Architecture
- **Serverless backend** (auto-scales 0-100 instances)
- **Event bus** (Pub/Sub for agent communication)
- **NoSQL database** (Firestore for proposals)
- **Secret management** (API keys in Secret Manager)
- **Monitoring** (dashboards, alerts, abuse detection)

### Developer Experience
- **VS Code integration** (native sidebar, commands)
- **Local git operations** (code never leaves machine)
- **One-click workflows** (approve → commit → reward)
- **Gamification** (CPT tokens, achievements, streaks)

---

## 🐛 Troubleshooting

### Extension not connecting?
```bash
# Check backend is online
curl https://contextpilot-backend-581368740395.us-central1.run.app/health

# Reload VS Code window
Ctrl+Shift+P → "Developer: Reload Window"
```

### No proposals showing?
```bash
# Create test proposal
curl -X POST "https://contextpilot-backend-581368740395.us-central1.run.app/proposals/create" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "default",
    "agent_id": "spec",
    "title": "Test proposal",
    "description": "Testing ContextPilot",
    "proposed_changes": [
      {
        "file_path": "TEST.md",
        "change_type": "create",
        "description": "Test file",
        "after": "# Test\n\nThis is a test."
      }
    ]
  }'

# Refresh extension
Click refresh button in ContextPilot sidebar
```

### Extension installed but no icon?
```bash
# Verify installation
code --list-extensions | grep contextpilot

# Should show: livresoltech.contextpilot

# If not showing, reinstall:
code --uninstall-extension livresoltech.contextpilot
code --install-extension contextpilot-0.1.1.vsix
```

---

## 📚 More Information

- **Full Documentation:** [README.md](README.md)
- **Architecture Details:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Hackathon Submission:** [HACKATHON.md](HACKATHON.md)
- **Security & Protection:** [SECURITY.md](SECURITY.md)
- **Project Roadmap:** [ROADMAP.md](ROADMAP.md)

---

## 🆘 Support

**Questions?**
- **GitHub Issues:** https://github.com/fsegall/gcloud_contextpilot/issues
- **Email:** contact@livresoltech.com

---

**Built with ❤️ by Livre Solutions for the Cloud Run Hackathon 2025**

**#CloudRunHackathon #AIAgents #VSCode**

