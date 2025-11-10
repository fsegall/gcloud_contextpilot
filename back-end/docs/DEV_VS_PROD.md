# 🔄 Dev vs Production Configuration Guide

This document explains the key differences between development and production environments for ContextPilot.

---

## 📊 Quick Comparison

| Feature | Development (Local) | Production (Cloud Run) |
|---------|-------------------|----------------------|
| **Event Bus** | In-Memory | Google Cloud Pub/Sub |
| **Database** | Local JSON files | Google Firestore |
| **Workspace Storage** | `./.contextpilot/workspaces/` | Firestore (ephemeral filesystem) |
| **Default Workspace** | `default` | `default` (configurable) |
| **API URL** | `http://localhost:8000` | `https://contextpilot-backend-*.run.app` |
| **Gemini API** | Your personal key | Cloud Run secret |
| **Logging** | DEBUG | INFO |

---

## 🛠️ Development Environment

### Setup

1. **Copy environment template:**
   ```bash
   cp env.dev.example .env
   ```

2. **Set your Gemini API key:**
   ```bash
   echo "GEMINI_API_KEY=your_key_here" >> .env
   ```

3. **Run backend:**
   ```bash
   python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
   ```

### Characteristics

- ✅ **Fast iteration**: Hot reload enabled
- ✅ **Local storage**: All data in `.contextpilot/` directory
- ✅ **No GCP costs**: In-memory event bus
- ✅ **Easy debugging**: Full logs in terminal
- ⚠️ **Single instance**: No horizontal scaling
- ⚠️ **No persistence**: Data lost on restart (unless saved to files)

### Workspace Behavior

- **Proposals** saved to: `.contextpilot/workspaces/{workspace_id}/proposals/*.md`
- **Retrospectives** saved to: `.contextpilot/workspaces/{workspace_id}/retrospectives/*.md`
- **Agent state** saved to: `.contextpilot/workspaces/{workspace_id}/.agent_state/*.json`

**Default workspace:** `default` (can be changed via `DEFAULT_WORKSPACE_ID` env var)

---

## ☁️ Production Environment

### Setup

1. **Set environment variables in Cloud Run:**
   ```bash
   gcloud run services update contextpilot-backend \
     --set-env-vars="USE_PUBSUB=true,FIRESTORE_ENABLED=true,GCP_PROJECT_ID=your-project-id,DEFAULT_WORKSPACE_ID=default" \
     --update-secrets="GEMINI_API_KEY=gemini-api-key:latest"
   ```

2. **Or use the deployment script:**
   ```bash
   ./deploy.sh
   ```

### Characteristics

- ✅ **Scalable**: Auto-scales from 0 to N instances
- ✅ **Persistent**: Firestore for durable storage
- ✅ **Event-driven**: Pub/Sub for async agent communication
- ✅ **Secure**: Managed secrets, IAM policies
- ⚠️ **Slower iteration**: Requires build + deploy (5-10 min)
- ⚠️ **GCP costs**: Firestore + Pub/Sub + Cloud Run charges

### Workspace Behavior

- **Proposals** saved to: Firestore collection `proposals`
- **Retrospectives** saved to: Firestore collection `retrospectives`
- **Agent state** saved to: Firestore collection `agent_states`
- **Temporary files** saved to: `/app/.contextpilot/workspaces/` (ephemeral, lost on restart)

**Default workspace:** `default` (but should be passed as `workspace_id` query param)

---

## 🔑 Key Configuration Differences

### 1. Event Bus

**Dev (`USE_PUBSUB=false`):**
```python
# In-memory event bus
event_bus = InMemoryEventBus()
event_bus.publish("agent-events", event)  # Handled immediately in-process
```

**Prod (`USE_PUBSUB=true`):**
```python
# Google Cloud Pub/Sub
event_bus = PubSubEventBus(project_id="gen-lang-client-0805532064")
event_bus.publish("agent-events", event)  # Published to Pub/Sub topic
```

### 2. Data Storage

**Dev (`FIRESTORE_ENABLED=false`):**
```python
# Local JSON files
proposal_repo = FileSystemProposalRepository(base_path="./.contextpilot/workspaces")
proposal_repo.create(proposal_data)  # Saves to .md + .json files
```

**Prod (`FIRESTORE_ENABLED=true`):**
```python
# Google Firestore
proposal_repo = FirestoreProposalRepository(project_id="gen-lang-client-0805532064")
proposal_repo.create(proposal_data)  # Saves to Firestore collection
```

### 3. Workspace ID Resolution

**Both environments:**
```python
# Priority order:
workspace_id = (
    request.query_params.get("workspace_id")  # 1. Query param (highest priority)
    or detect_from_git_context()              # 2. Git context
    or os.getenv("DEFAULT_WORKSPACE_ID")      # 3. Environment variable
    or "default"                               # 4. Hardcoded fallback
)
```

**Extension must match:**
```typescript
// Dev: workspace_id=default (or detected from local git)
// Prod: workspace_id should be passed explicitly or omitted to search all
const response = await client.get('/proposals', {
  params: { status: 'pending' }  // No workspace_id = search all workspaces
});
```

---

## 🎯 Common Pitfalls & Solutions

### Problem 1: Proposals not appearing in extension

**Symptom:** Backend creates proposals but extension shows empty list

**Cause:** Workspace ID mismatch
- Backend creates proposal in workspace `'contextpilot'`
- Extension queries workspace `'default'`

**Solution:**
```typescript
// Extension: Remove workspace_id filter to search all workspaces
const response = await client.get('/proposals', {
  params: { status: 'pending' }  // Don't filter by workspace_id
});
```

### Problem 2: "Resource not found" in Cloud Run

**Symptom:** `404 Resource not found (resource=retrospective-events)`

**Cause:** Missing Pub/Sub topics or IAM permissions

**Solution:**
```bash
# Create topics
gcloud pubsub topics create retrospective-events
gcloud pubsub topics create agent-events

# Grant permissions
gcloud projects add-iam-policy-binding gen-lang-client-0805532064 \
  --member="serviceAccount:581368740395-compute@developer.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

### Problem 3: LLM timeouts in production

**Symptom:** `Read timed out. (read timeout=10)`

**Cause:** Gemini API latency

**Solution:**
- Use faster model: `gemini-2.5-flash` instead of `gemini-2.5-pro`
- Increase timeouts: `timeout=20` in requests
- Implement parallel processing for multiple agent calls

### Problem 4: Missing proposals in Firestore

**Symptom:** `Failed to create proposal: Missing required field: id`

**Cause:** Firestore repository expects `id` field in proposal data

**Solution:**
```python
# Generate ID before creating
proposal_id = f"retro-proposal-{retrospective['retrospective_id']}"
proposal_data = {
    "id": proposal_id,  # ← Add this!
    "workspace_id": workspace_id,
    "title": "...",
    # ... rest of data
}
repo.create(proposal_data)
```

---

## 🚀 Deployment Workflow

### For local development:
```bash
cd back-end
cp env.dev.example .env
# Edit .env with your GEMINI_API_KEY
python3 -m uvicorn app.server:app --reload
```

### For production deployment:
```bash
cd back-end
./deploy.sh  # Uses env.prod.example as reference
```

### For extension testing:

**Against local backend:**
```typescript
// extension/src/extension.ts
const apiUrl = 'http://localhost:8000';
```

**Against production backend:**
```typescript
// extension/src/extension.ts
const apiUrl = 'https://contextpilot-backend-581368740395.us-central1.run.app';
```

Then recompile and reinstall:
```bash
cd extension
npm run webpack
npx @vscode/vsce package
# Install the .vsix in Cursor/VS Code
```

---

## 📝 Best Practices

1. **Always specify workspace_id explicitly** in API requests when you know it
2. **Use environment variables** for configuration (never hardcode URLs/keys)
3. **Test locally first** before deploying to production
4. **Monitor Cloud Run logs** after deployment to catch issues early
5. **Use `DEFAULT_WORKSPACE_ID=default`** consistently across dev and prod

---

## 🔍 Debugging Tips

### Check backend configuration:
```bash
# Local
cat .env | grep -E "USE_PUBSUB|FIRESTORE_ENABLED|DEFAULT_WORKSPACE_ID"

# Cloud Run
gcloud run services describe contextpilot-backend --region=us-central1 --format="value(spec.template.spec.containers[0].env)"
```

### Test proposal creation:
```bash
# Local
curl -X POST "http://localhost:8000/agents/retrospective/trigger?workspace_id=default" \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual", "trigger_topic": "Test", "use_llm": true}'

# Production
curl -X POST "https://contextpilot-backend-581368740395.us-central1.run.app/agents/retrospective/trigger?workspace_id=default" \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual", "trigger_topic": "Test", "use_llm": true}'
```

### List proposals:
```bash
# Local
curl "http://localhost:8000/proposals?status=pending"

# Production
curl "https://contextpilot-backend-581368740395.us-central1.run.app/proposals?status=pending"
```

---

## 📚 Related Documentation

- **DEPLOYMENT.md** - Cloud Run deployment guide
- **env.dev.example** - Development configuration template
- **env.prod.example** - Production configuration template
- **deploy.sh** - Automated deployment script

---

*Last updated: 2025-10-18*

