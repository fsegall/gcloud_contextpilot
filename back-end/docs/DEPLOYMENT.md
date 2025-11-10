# ContextPilot Backend Deployment Guide

This guide explains how to run the ContextPilot backend in different environments.

## 🏗️ Architecture Overview

The backend supports two modes:
- **Development**: Local server with in-memory event bus and file storage
- **Production**: Google Cloud Run with Cloud Pub/Sub and Firestore

## 🛠️ Development Mode (Local)

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)
- Gemini API key

### Setup

1. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp env.dev.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. **Run local server:**
```bash
./deploy.sh dev
# Or manually:
python3 -m uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

### Development Configuration

In development mode:
- ✅ **Event Bus**: In-memory (no Pub/Sub needed)
- ✅ **Storage**: Local files (`.contextpilot/workspaces/`)
- ✅ **Hot Reload**: Auto-restarts on code changes
- ✅ **Debug Logs**: Verbose logging enabled

### Testing Locally

```bash
# Check health
curl http://localhost:8000/health

# Trigger retrospective
curl -X POST "http://localhost:8000/agents/retrospective/trigger?workspace_id=test" \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual", "trigger_topic": "How can we improve?", "use_llm": true}'

# Get balance (test mode)
curl http://localhost:8000/balance/test-user
```

## ☁️ Production Mode (Google Cloud Run)

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed and authenticated
- Project with billing enabled
- Gemini API key

### Setup

1. **Authenticate with GCP:**
```bash
gcloud auth login
gcloud config set project gen-lang-client-0805532064
```

2. **Enable required APIs:**
```bash
gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

3. **Create Firestore database:**
```bash
gcloud firestore databases create --location=us-central1
```

4. **Set Gemini API key (if not using default):**
```bash
# Option 1: Add to deploy command
# Option 2: Set in Cloud Run console after deployment
```

### Deploy

```bash
# Simple deploy
./deploy.sh prod

# Or with custom project
PROJECT_ID=your-project-id ./deploy.sh prod
```

### Production Configuration

In production mode:
- ✅ **Event Bus**: Google Cloud Pub/Sub (automatic topic creation)
- ✅ **Storage**: Google Firestore (scalable, managed)
- ✅ **Scaling**: Auto-scales 0-10 instances
- ✅ **Monitoring**: Cloud Logging & Monitoring
- ✅ **Security**: IAM-based authentication

### Production Environment Variables

Set in Cloud Run:
```bash
ENVIRONMENT=production
USE_PUBSUB=true
FIRESTORE_ENABLED=true
GCP_PROJECT_ID=gen-lang-client-0805532064
GEMINI_API_KEY=your-api-key  # Set via Secret Manager recommended
```

### Monitoring Production

```bash
# View logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=contextpilot-backend' --limit 50

# View service details
gcloud run services describe contextpilot-backend --region us-central1

# View revisions
gcloud run revisions list --service contextpilot-backend --region us-central1

# View metrics in Cloud Console
open "https://console.cloud.google.com/run/detail/us-central1/contextpilot-backend/metrics"
```

## 🔄 Environment Comparison

| Feature | Development | Production |
|---------|------------|------------|
| **Event Bus** | In-memory | Cloud Pub/Sub |
| **Storage** | Local files | Firestore |
| **Scaling** | Single instance | 0-10 auto-scale |
| **Logs** | DEBUG level | INFO level |
| **Cost** | Free | Pay-per-use |
| **Setup Time** | Instant | ~3-5 minutes |
| **Best For** | Coding, testing | Live deployment |

## 🔧 VS Code Extension Configuration

### Development
```json
{
  "contextpilot.apiUrl": "http://localhost:8000",
  "contextpilot.userId": "dev-user",
  "contextpilot.walletAddress": "0xdev..."
}
```

### Production
```json
{
  "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app",
  "contextpilot.userId": "your-user-id",
  "contextpilot.walletAddress": "0xyour..."
}
```

## 🚨 Troubleshooting

### Local Development Issues

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Missing API key:**
- Check `.env` file exists
- Verify `GEMINI_API_KEY` is set

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Production Issues

**Deployment fails:**
```bash
# Check authentication
gcloud auth list

# Check project
gcloud config get-value project

# Enable required APIs
gcloud services list --enabled
```

**Cold start timeouts:**
- Normal on first request (can take 10-30s)
- Keep-alive requests help: `curl https://your-service.run.app/health`

**Permission errors:**
```bash
# Grant service account permissions
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/pubsub.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/datastore.user"
```

## 📊 Performance Tips

### Development
- Use `--reload` for hot-reloading during development
- Set `LOG_LEVEL=DEBUG` for verbose logs
- Use local files for faster iteration

### Production
- Monitor Cloud Run metrics for scaling needs
- Use Cloud Scheduler for keep-alive pings
- Enable Cloud Monitoring alerts for errors
- Use Secret Manager for API keys

## 🔐 Security Best Practices

1. **API Keys**: Use Secret Manager in production
2. **Authentication**: Enable IAM auth for production APIs
3. **CORS**: Configure allowed origins
4. **Rate Limiting**: Enable Cloud Armor if needed
5. **Logging**: Don't log sensitive data

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🆘 Support

For issues or questions:
1. Check logs: `./deploy.sh` output or Cloud Logging
2. Review this guide
3. Open an issue on GitHub
4. Contact: your-email@example.com




