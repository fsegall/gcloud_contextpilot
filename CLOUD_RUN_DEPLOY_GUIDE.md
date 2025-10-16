# Cloud Run Deployment Guide

**ContextPilot Backend - Production Deployment**

---

## 📋 Prerequisites

### 1. Google Cloud Setup
```bash
# Install gcloud CLI (if not installed)
# Ubuntu/Debian:
sudo snap install google-cloud-cli --classic

# Verify installation
gcloud --version
```

### 2. Authentication
```bash
# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config get-value project
```

### 3. Docker Setup
```bash
# Verify Docker is installed
docker --version

# If not installed:
sudo apt-get update
sudo apt-get install docker.io
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

---

## 🚀 Quick Deploy (Automated)

### Option 1: One-Command Deploy
```bash
# Set your project ID
export GCP_PROJECT_ID=your-project-id

# Run deployment script
cd /home/fsegall/Desktop/New_Projects/google-context-pilot
./scripts/shell/deploy-cloud-run.sh
```

**This will:**
- ✅ Enable required APIs
- ✅ Build Docker image
- ✅ Push to Container Registry
- ✅ Deploy to Cloud Run
- ✅ Test health endpoint
- ✅ Display service URL

---

## 🔧 Manual Deploy (Step by Step)

### Step 1: Enable Google Cloud APIs
```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    pubsub.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    --project=$PROJECT_ID
```

### Step 2: Setup Secrets
```bash
# Store Gemini API key
./scripts/shell/setup-secrets.sh

# Or manually:
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GOOGLE_API_KEY \
    --data-file=- \
    --replication-policy="automatic"
```

### Step 3: Build Docker Image
```bash
cd back-end

# Build image
docker build -t gcr.io/$PROJECT_ID/contextpilot-backend:latest .

# Test locally (optional)
docker run -p 8080:8080 \
    -e GOOGLE_API_KEY=your-key \
    gcr.io/$PROJECT_ID/contextpilot-backend:latest
```

### Step 4: Push to Container Registry
```bash
# Configure Docker auth
gcloud auth configure-docker

# Push image
docker push gcr.io/$PROJECT_ID/contextpilot-backend:latest
```

### Step 5: Deploy to Cloud Run
```bash
gcloud run deploy contextpilot-backend \
    --image gcr.io/$PROJECT_ID/contextpilot-backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 300 \
    --set-env-vars "USE_PUBSUB=false,FIRESTORE_ENABLED=false,ENVIRONMENT=production" \
    --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest"
```

**Note:** Initially deploy with `USE_PUBSUB=false` and `FIRESTORE_ENABLED=false`. We'll enable them after setup.

### Step 6: Get Service URL
```bash
SERVICE_URL=$(gcloud run services describe contextpilot-backend \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### Step 7: Test Deployment
```bash
# Health check
curl $SERVICE_URL/health

# Expected response:
# {"status":"ok","timestamp":"..."}

# Agents status
curl $SERVICE_URL/agents/status

# Create a test proposal (requires workspace)
curl -X POST "$SERVICE_URL/proposals/create" \
    -H "Content-Type: application/json" \
    -d '{"workspace_id": "test", "title": "Test Proposal"}'
```

---

## 📡 Setup Pub/Sub (After Initial Deploy)

### Run Pub/Sub Setup Script
```bash
./scripts/shell/setup-pubsub.sh
```

This creates topics:
- `proposal-events`
- `git-events`
- `spec-updates`
- `context-updates`
- `reward-events`
- etc.

### Update Cloud Run with Pub/Sub Enabled
```bash
gcloud run services update contextpilot-backend \
    --region us-central1 \
    --set-env-vars "USE_PUBSUB=true"
```

---

## 🗄️ Setup Firestore (After Pub/Sub)

### Create Firestore Database
```bash
# Create Firestore in Native mode
gcloud firestore databases create \
    --region=us-central1 \
    --project=$PROJECT_ID
```

### Update Cloud Run with Firestore Enabled
```bash
gcloud run services update contextpilot-backend \
    --region us-central1 \
    --set-env-vars "FIRESTORE_ENABLED=true"
```

---

## 🔄 Update Deployment

### After Code Changes
```bash
# Rebuild and redeploy
cd back-end
docker build -t gcr.io/$PROJECT_ID/contextpilot-backend:latest .
docker push gcr.io/$PROJECT_ID/contextpilot-backend:latest

gcloud run services update contextpilot-backend \
    --image gcr.io/$PROJECT_ID/contextpilot-backend:latest \
    --region us-central1
```

### Or use Cloud Build (Automated CI/CD)
```bash
# Trigger build from GitHub
gcloud builds submit --config cloudbuild.yaml
```

---

## 🔍 Monitoring & Logs

### View Logs
```bash
# Stream logs
gcloud run services logs tail contextpilot-backend \
    --region us-central1

# View in console
gcloud run services logs read contextpilot-backend \
    --region us-central1 \
    --limit 50
```

### View Metrics
```bash
# Open Cloud Console
gcloud run services describe contextpilot-backend \
    --region us-central1 \
    --format "value(status.url)"

# Navigate to: Cloud Console > Cloud Run > contextpilot-backend > Metrics
```

---

## 🐛 Troubleshooting

### Container fails to start
```bash
# Check logs
gcloud run services logs read contextpilot-backend --region us-central1 --limit 100

# Common issues:
# 1. Missing GOOGLE_API_KEY secret
# 2. Port not set to $PORT
# 3. Dependencies not installed
```

### "Permission denied" errors
```bash
# Grant Cloud Run service account Pub/Sub permissions
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/pubsub.subscriber"
```

### "Secret not found" errors
```bash
# Verify secrets exist
gcloud secrets list

# Recreate if needed
./scripts/shell/setup-secrets.sh
```

### Health check failing
```bash
# Test locally first
docker run -p 8080:8080 \
    -e GOOGLE_API_KEY=test \
    gcr.io/$PROJECT_ID/contextpilot-backend:latest

# Then test health endpoint
curl http://localhost:8080/health
```

---

## 💰 Cost Optimization

### Free Tier Limits
- **Cloud Run:** 2M requests/month free
- **Container Registry:** 0.5GB storage free
- **Pub/Sub:** 10GB messages/month free
- **Firestore:** 1GB storage + 50k reads/day free

### Recommended Settings for Beta
```bash
# Minimal resources for testing
--memory 256Mi \
--cpu 1 \
--max-instances 3 \
--min-instances 0 \
--concurrency 10
```

### For Production (100+ users)
```bash
# Scale up for production
--memory 512Mi \
--cpu 2 \
--max-instances 10 \
--min-instances 1 \
--concurrency 80
```

---

## 🔐 Security Best Practices

### 1. Use Secret Manager (Never env vars for secrets)
```bash
# ✅ GOOD
--set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest"

# ❌ BAD
--set-env-vars "GOOGLE_API_KEY=AIza..."
```

### 2. Restrict Access (if needed)
```bash
# Remove --allow-unauthenticated
# Add authentication
gcloud run services update contextpilot-backend \
    --region us-central1 \
    --no-allow-unauthenticated

# Require authentication for requests
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    $SERVICE_URL/health
```

### 3. Enable VPC Connector (for private resources)
```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create contextpilot-connector \
    --region us-central1 \
    --subnet default

# Use in Cloud Run
gcloud run services update contextpilot-backend \
    --vpc-connector contextpilot-connector \
    --vpc-egress all-traffic
```

---

## 📊 Post-Deployment Checklist

- [ ] Service deployed successfully
- [ ] Health endpoint returns 200 OK
- [ ] Secrets configured correctly
- [ ] Pub/Sub topics created
- [ ] Firestore database initialized
- [ ] Logs are readable
- [ ] Metrics dashboard accessible
- [ ] Extension can connect to service URL
- [ ] Test proposal creation works
- [ ] Agents can publish/subscribe to events

---

## 🎯 Next Steps

1. **Update Extension:**
   ```typescript
   // extension/src/services/contextpilot.ts
   const apiUrl = 'https://contextpilot-backend-xxx.run.app';
   ```

2. **Test End-to-End:**
   - Create proposal in extension
   - Verify backend receives request
   - Check Pub/Sub messages
   - Verify Firestore writes

3. **Enable Monitoring:**
   - Setup alerting for errors
   - Configure uptime checks
   - Add custom metrics

4. **Prepare for Launch:**
   - Load testing
   - Security audit
   - Documentation update

---

## 🚀 Full Production Stack

When everything is ready:

```bash
# Final production deployment
gcloud run deploy contextpilot-backend \
    --image gcr.io/$PROJECT_ID/contextpilot-backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 2 \
    --max-instances 10 \
    --min-instances 1 \
    --timeout 300 \
    --set-env-vars "USE_PUBSUB=true,FIRESTORE_ENABLED=true,ENVIRONMENT=production" \
    --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest,SEPOLIA_PRIVATE_KEY=SEPOLIA_PRIVATE_KEY:latest"
```

---

**Status:** 📚 **READY TO DEPLOY**  
**Estimated Time:** 15-30 minutes  
**Difficulty:** ⭐⭐ Intermediate

---

*"From local development to global production in minutes with Google Cloud Run!"*

