# Production Deployment Guide - ContextPilot

## 🚀 Deploy to Google Cloud Run with Pub/Sub

### Prerequisites
1. Google Cloud Project with billing enabled
2. `gcloud` CLI installed and authenticated
3. Docker installed locally
4. Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Step 1: Enable Required APIs

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Create Pub/Sub Topics and Subscriptions

```bash
# Create topics
gcloud pubsub topics create git-events
gcloud pubsub topics create spec-events
gcloud pubsub topics create proposal-events
gcloud pubsub topics create strategy-events
gcloud pubsub topics create coach-events
gcloud pubsub topics create retrospective-events

# Create subscriptions
gcloud pubsub subscriptions create git-agent-sub \
    --topic=git-events \
    --ack-deadline=60

gcloud pubsub subscriptions create spec-agent-sub \
    --topic=spec-events \
    --ack-deadline=60

gcloud pubsub subscriptions create retrospective-agent-sub \
    --topic=retrospective-events \
    --ack-deadline=60

# For milestone events (using git-events topic)
gcloud pubsub subscriptions create milestone-agent-sub \
    --topic=git-events \
    --ack-deadline=60
```

### Step 3: Setup Firestore

```bash
# Create Firestore database (Native mode)
gcloud firestore databases create --region=us-central1
```

### Step 4: Set Environment Variables

Create a `.env.production` file:

```bash
# Google Cloud
PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1

# Gemini API
GOOGLE_API_KEY=your-gemini-api-key-here

# Feature Flags
USE_PUBSUB=true
FIRESTORE_ENABLED=true

# CORS (adjust for your domain)
CORS_ORIGINS=https://your-frontend-domain.com,https://extension.your-domain.com

# Optional: OpenAI for Git Context Manager
OPENAI_API_KEY=your-openai-key-if-needed
```

### Step 5: Deploy Backend to Cloud Run

```bash
cd back-end

# Build and deploy
gcloud run deploy contextpilot-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="USE_PUBSUB=true,FIRESTORE_ENABLED=true,PROJECT_ID=$PROJECT_ID" \
    --set-secrets="GOOGLE_API_KEY=gemini-api-key:latest" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10

# Get the service URL
export BACKEND_URL=$(gcloud run services describe contextpilot-backend \
    --region us-central1 --format='value(status.url)')

echo "Backend deployed to: $BACKEND_URL"
```

### Step 6: Create Secret for Gemini API Key

```bash
# Create secret
echo -n "your-gemini-api-key-here" | \
    gcloud secrets create gemini-api-key --data-file=-

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 7: Configure VS Code Extension

Update extension `.env` file with production backend URL:

```bash
cd ../extension
cat > .env << EOF
VITE_BACKEND_URL=$BACKEND_URL
VITE_ENVIRONMENT=production
EOF
```

### Step 8: Install Extension in VS Code/Cursor

```bash
# Package the extension
npm run compile
npx @vscode/vsce package

# Install in VS Code/Cursor
code --install-extension contextpilot-v0.2.1-production.vsix
# OR for Cursor:
cursor --install-extension contextpilot-v0.2.1-production.vsix
```

## ✅ Verify Production Deployment

### Test Backend

```bash
# Health check
curl $BACKEND_URL/health

# Test retrospective with real agents
curl -X POST "$BACKEND_URL/agents/retrospective/trigger?workspace_id=test" \
    -H "Content-Type: application/json" \
    -d '{"trigger":"How can we improve system performance?","use_llm":true}'
```

### Test Pub/Sub Integration

```bash
# Publish test event
gcloud pubsub topics publish git-events \
    --message='{"event_type":"git.commit.v1","source":"test","data":{"commit":"abc123"}}'

# Check logs
gcloud run logs read contextpilot-backend --region us-central1 --limit 50
```

### Test Firestore

```bash
# Check proposals in Firestore
gcloud firestore export gs://your-bucket/firestore-export/

# Or use Firebase Console: https://console.firebase.google.com/
```

## 🔍 Monitoring

### View Logs

```bash
# Real-time logs
gcloud run logs tail contextpilot-backend --region us-central1

# Filter for errors
gcloud run logs read contextpilot-backend \
    --region us-central1 \
    --filter="severity>=ERROR" \
    --limit 100
```

### Monitor Pub/Sub

```bash
# Check subscription metrics
gcloud pubsub subscriptions describe retrospective-agent-sub

# Monitor message backlog
gcloud pubsub subscriptions list --format="table(name,numUndeliveredMessages)"
```

### Check Cloud Run Metrics

Visit: https://console.cloud.google.com/run/detail/$GCP_REGION/contextpilot-backend/metrics

## 🎯 Production Features Enabled

When `USE_PUBSUB=true` and `FIRESTORE_ENABLED=true`:

✅ **Multi-Agent Retrospectives** with real agent instances
✅ **Gemini 2.5 Flash** for AI-powered agent perspectives  
✅ **Google Cloud Pub/Sub** for event-driven architecture
✅ **Firestore** for persistent proposal storage
✅ **Cloud Run** auto-scaling and high availability
✅ **Secret Manager** for secure API key management

## 🐛 Troubleshooting

### Extension Not Working Outside Development Host

**Problem**: Extension commands don't appear when installed via `.vsix`

**Solution**:
1. Verify `package.json` has correct `main` entry: `"main": "./out/extension.js"`
2. Ensure all TypeScript is compiled: `npm run compile`
3. Check extension loads: Open Command Palette → "Developer: Show Running Extensions"
4. View extension logs: "Developer: Open Extension Logs" → Select ContextPilot

### Pub/Sub Messages Not Being Delivered

**Problem**: Events published but not received by agents

**Solution**:
1. Check subscriptions exist: `gcloud pubsub subscriptions list`
2. Verify subscription has no backlog: `gcloud pubsub subscriptions describe <sub-name>`
3. Check Cloud Run logs for connection errors
4. Ensure service account has Pub/Sub permissions

### Retrospective Timeouts

**Problem**: Agent perspectives timeout with LLM

**Solution**:
1. Verify `GOOGLE_API_KEY` is set correctly
2. Check Gemini API quota: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com
3. Increase Cloud Run timeout: `--timeout 300`
4. Review logs for specific Gemini API errors

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Pub/Sub Best Practices](https://cloud.google.com/pubsub/docs/best-practices)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [VS Code Extension API](https://code.visualstudio.com/api)

## 🎊 Ready for Hackathon Demo!

Your ContextPilot system is now production-ready with:
- ✅ Real multi-agent orchestration
- ✅ AI-powered agent perspectives (Gemini 2.5 Flash)
- ✅ Event-driven architecture (Pub/Sub)
- ✅ Persistent storage (Firestore)
- ✅ Scalable deployment (Cloud Run)
- ✅ VS Code/Cursor extension

**Demo Flow**:
1. Show extension in VS Code
2. Trigger agent retrospective via command palette
3. Show real agents discussing a topic with LLM-generated perspectives
4. Display clickable links to generated proposals
5. Show Cloud Run logs for Pub/Sub events
6. Demonstrate Firestore proposal storage

Good luck with your hackathon submission! 🚀

