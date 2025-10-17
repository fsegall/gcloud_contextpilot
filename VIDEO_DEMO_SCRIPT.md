# 🎬 ContextPilot - Demo Video Script (3 min)

## 🎯 Objetivo
Mostrar o funcionamento completo: Backend local + Extension + Git + Gamification

---

## ⏱️ Timeline (3 minutos)

### **00:00-00:15** - Introdução (15s)
**Mostrar:**
- Terminal com `docker-compose up` rodando
- Backend health check: `curl http://localhost:8000/health`
- "ContextPilot running locally with Docker Compose"

**Narração:**
> "ContextPilot is a multi-agent AI system for developers.
> Let's see it in action with local backend and VS Code extension."

---

### **00:15-00:45** - Extension UI Tour (30s)
**Mostrar:**
- Abrir VS Code/Cursor
- Sidebar com ícone ContextPilot 🚀
- Tree view com seções:
  - 📋 Proposals (2 pending)
  - 🏆 Rewards (100 CPT, achievements)
  - 📊 Status

**Narração:**
> "The extension connects to our backend and shows AI-generated proposals.
> It also includes a gamification system with CPT tokens and achievements."

**Ações:**
1. Click em Proposals → Expandir
2. Mostrar proposal details
3. Highlight "Docker Compose documentation"

---

### **00:45-01:30** - Approve Proposal Flow (45s)
**Mostrar:**
1. Right-click na proposal → "Approve Proposal"
2. VS Code dialog: "Are you sure?"
3. Loading...
4. Arquivo criado: `docs/DOCKER_SETUP.md`
5. Terminal mostra: `git log --oneline -1`
   - Commit message: "docs(contextpilot): Add Docker Compose documentation"
6. Toast notification: "✅ Proposal approved (+10 CPT)"
7. Rewards tree atualiza: 110 CPT

**Narração:**
> "When I approve a proposal, the extension applies changes locally,
> creates a semantic git commit, and rewards me with CPT tokens.
> All without leaving my editor."

---

### **01:30-02:00** - Backend API Demo (30s)
**Mostrar Terminal:**
```bash
# List proposals
curl http://localhost:8000/proposals?workspace_id=default&status=pending | jq

# Health check
curl http://localhost:8000/health | jq

# Agent status
curl http://localhost:8000/agents/status | jq
```

**Narração:**
> "Behind the scenes, 6 AI agents coordinate via Pub/Sub:
> Spec, Git, Context, Coach, Milestone, and Strategy agents.
> Each agent has a specific role in maintaining project context."

---

### **02:00-02:30** - Cloud Run Deployment (30s)
**Mostrar:**
1. GCP Console → Cloud Run
2. Service running: `contextpilot-backend`
3. Terraform code: `terraform/main.tf`
4. Architecture diagram (mostrar ARCHITECTURE.md)

**Narração:**
> "For production, we deploy to Google Cloud Run using Terraform.
> The entire infrastructure is code: Pub/Sub, Firestore, Secret Manager.
> Serverless, scalable, and deployed in minutes."

---

### **02:30-03:00** - Wrap Up (30s)
**Mostrar:**
- GitHub repo: https://github.com/fsegall/gcloud_contextpilot
- README.md badges
- Extension download link
- Quick stats:
  - ✅ 6 AI Agents
  - ✅ Event-driven architecture
  - ✅ Gamification with blockchain roadmap
  - ✅ Open source

**Narração:**
> "ContextPilot keeps your documentation in sync with your code,
> using AI agents that never sleep. Try it today - fully open source.
> Built for the Cloud Run Hackathon. Thank you!"

---

## 🎬 Setup Before Recording

### Backend:
```bash
cd google-context-pilot
docker-compose up -d
curl http://localhost:8000/health
```

### Extension:
```bash
cd extension
npm run compile
# Open in Extension Development Host
# Ensure .vscode/settings.json has "apiUrl": "http://localhost:8000"
```

### Proposals:
```bash
# Create test proposal if none exist
curl -X POST "http://localhost:8000/proposals/create" \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "default", "agent_id": "spec", "title": "Add Docker Compose documentation", ...}'
```

---

## 📸 Screen Recording Tips

1. **Use OBS Studio** or similar
2. **1080p resolution** (1920x1080)
3. **Show terminal + VS Code side by side**
4. **Use zoom for important details**
5. **No sensitive data** (API keys, tokens)
6. **Clean desktop** (close unnecessary apps)
7. **Test audio** before final recording

---

## 🎙️ Narration Tips

- **Clear and slow** (English, international audience)
- **Emphasize "Cloud Run", "Pub/Sub", "Firestore"** (hackathon requirements)
- **Show excitement** (but professional)
- **Practice 2-3 times** before final take

---

## ✅ Final Checklist

- [ ] Docker Compose running smoothly
- [ ] Extension compiled and working
- [ ] At least 2 pending proposals
- [ ] Git configured (user.name, user.email)
- [ ] Test approve flow once before recording
- [ ] Clean terminal history
- [ ] Close unnecessary browser tabs
- [ ] Disable notifications
- [ ] Test microphone
- [ ] Practice narration script

---

**Good luck! 🎬🚀**
