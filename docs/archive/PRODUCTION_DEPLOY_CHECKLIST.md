# Production Deploy Checklist 🚀

**Date:** October 15, 2025  
**Target:** Deploy to GCP Cloud Run + Pub/Sub

---

## ✅ Pre-Deploy Checklist

### Backend Ready
- [x] Event-driven architecture implemented
- [x] BaseAgent with state management
- [x] Spec Agent generates diffs
- [x] Git Agent subscribes to events
- [x] API endpoints with diff support
- [x] No linter errors
- [x] Tests passing

### Extension Ready
- [x] Diff viewer implemented
- [x] Claude integration
- [x] Review panel with persistent context
- [x] Commands registered
- [x] TypeScript compiles
- [x] No linter errors

### Infrastructure Ready
- [x] GCP project created (contextpilot-hack-4044)
- [x] Billing enabled
- [x] setup-pubsub.sh script ready
- [ ] Pub/Sub topics created
- [ ] Cloud Run service deployed
- [ ] Environment variables configured

---

## 🚀 Deploy Steps

### 1. Setup GCP Pub/Sub (5 min)

```bash
export GCP_PROJECT_ID=contextpilot-hack-4044
export GCP_REGION=us-central1

# Run setup script
cd scripts/shell
./setup-pubsub.sh
```

**Expected:**
- ✅ 10 topics created
- ✅ 5 subscriptions created
- ✅ Dead letter queue configured

### 2. Deploy Backend to Cloud Run (10 min)

```bash
cd back-end

# Build container
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/contextpilot-api

# Deploy to Cloud Run
gcloud run deploy contextpilot-api \
  --image gcr.io/$GCP_PROJECT_ID/contextpilot-api \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --set-env-vars="USE_PUBSUB=true,GCP_PROJECT_ID=$GCP_PROJECT_ID,CONTEXTPILOT_AUTO_APPROVE_PROPOSALS=false" \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

**Expected:**
- ✅ Service deployed
- ✅ URL: https://contextpilot-api-xxx-uc.a.run.app
- ✅ Health check passes

### 3. Test Production API (5 min)

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe contextpilot-api --region=$GCP_REGION --format='value(status.url)')

# Test health
curl $SERVICE_URL/health

# Test proposals endpoint
curl "$SERVICE_URL/proposals?workspace_id=contextpilot"
```

### 4. Update Extension Configuration (2 min)

```json
// extension/package.json - Add configuration
"configuration": {
  "title": "ContextPilot",
  "properties": {
    "contextpilot.apiUrl": {
      "type": "string",
      "default": "https://contextpilot-api-xxx-uc.a.run.app",
      "description": "ContextPilot API URL"
    }
  }
}
```

### 5. Test End-to-End (10 min)

1. Update extension API URL to production
2. Open Extension Development Host (F5)
3. Connect to production API
4. Generate proposal
5. View diff
6. Ask Claude to review
7. Approve
8. Verify commit in Cloud Run logs

---

## 📋 Environment Variables

### Backend (Cloud Run)

```bash
USE_PUBSUB=true
GCP_PROJECT_ID=contextpilot-hack-4044
CONTEXTPILOT_AUTO_APPROVE_PROPOSALS=false
GOOGLE_APPLICATION_CREDENTIALS=/secrets/service-account.json
```

### Extension (User Settings)

```json
{
  "contextpilot.apiUrl": "https://contextpilot-api-xxx-uc.a.run.app",
  "contextpilot.userId": "user-email@example.com",
  "contextpilot.autoConnect": true
}
```

---

## 🔐 Security Checklist

- [ ] Service account with minimal permissions
- [ ] API authentication (optional for MVP)
- [ ] CORS configured
- [ ] Rate limiting
- [ ] Input validation
- [ ] Error handling
- [ ] Logging configured

---

## 📊 Monitoring Setup

### Cloud Logging Queries

```
# View all events
resource.type="cloud_run_revision"
jsonPayload.message=~"EventBus"

# View proposal events
resource.type="cloud_run_revision"
jsonPayload.message=~"proposal.created"

# View errors
resource.type="cloud_run_revision"
severity="ERROR"
```

### Metrics to Track

- Event throughput (events/min)
- Proposal creation rate
- Approval rate
- Git Agent commit frequency
- API latency (p50, p95, p99)
- Error rate

---

## 🧪 Smoke Tests

### Test 1: Health Check
```bash
curl $SERVICE_URL/health
# Expected: {"status":"ok","version":"2.0.0"}
```

### Test 2: List Proposals
```bash
curl "$SERVICE_URL/proposals?workspace_id=contextpilot"
# Expected: {"proposals": [...], "count": N}
```

### Test 3: Create Proposal
```bash
curl -X POST "$SERVICE_URL/proposals/create?workspace_id=contextpilot"
# Expected: {"status": "success", "proposals_created": N}
```

### Test 4: Approve Proposal
```bash
curl -X POST "$SERVICE_URL/proposals/PROPOSAL_ID/approve?workspace_id=contextpilot"
# Expected: {"status": "approved", "auto_committed": false}
```

### Test 5: Check Pub/Sub
```bash
gcloud pubsub topics list --project=$GCP_PROJECT_ID
# Expected: 10 topics listed
```

---

## 🐛 Troubleshooting

### Issue: Cloud Run deployment fails
**Solution:**
- Check Dockerfile exists
- Verify requirements.txt is complete
- Check build logs: `gcloud builds list`

### Issue: Pub/Sub not receiving events
**Solution:**
- Verify USE_PUBSUB=true
- Check service account permissions
- View Pub/Sub metrics in console

### Issue: Extension can't connect
**Solution:**
- Verify Cloud Run URL is correct
- Check CORS configuration
- Test with curl first

---

## 📦 Deployment Artifacts

### Required Files
- [x] `back-end/Dockerfile`
- [x] `back-end/requirements.txt`
- [x] `back-end/.dockerignore`
- [x] `infra/cloudrun/api.yaml`
- [x] `scripts/shell/setup-pubsub.sh`

### Optional Files
- [ ] `back-end/.env.production`
- [ ] `infra/terraform/` (for IaC)
- [ ] `k8s/` (if using GKE)

---

## 🎯 Success Criteria

- ✅ Backend deployed to Cloud Run
- ✅ Pub/Sub topics created
- ✅ Events flowing through Pub/Sub
- ✅ Extension connects to production
- ✅ Proposals with diffs working
- ✅ Claude review working
- ✅ Git Agent commits working
- ✅ No errors in logs

---

## 📝 Post-Deploy Tasks

- [ ] Update README with production URL
- [ ] Document API endpoints
- [ ] Create demo video
- [ ] Share with beta testers
- [ ] Monitor logs for 24h
- [ ] Fix any production issues

---

## 🔥 Quick Deploy Commands

```bash
# All-in-one deploy
export GCP_PROJECT_ID=contextpilot-hack-4044
export GCP_REGION=us-central1

# 1. Setup Pub/Sub
./scripts/shell/setup-pubsub.sh

# 2. Deploy backend
cd back-end
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/contextpilot-api
gcloud run deploy contextpilot-api \
  --image gcr.io/$GCP_PROJECT_ID/contextpilot-api \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --set-env-vars="USE_PUBSUB=true,GCP_PROJECT_ID=$GCP_PROJECT_ID"

# 3. Get service URL
gcloud run services describe contextpilot-api \
  --region=$GCP_REGION \
  --format='value(status.url)'

# 4. Test
curl $(gcloud run services describe contextpilot-api --region=$GCP_REGION --format='value(status.url)')/health
```

---

**Status:** 📋 Ready for deployment!  
**ETA:** ~30 minutes total  
**Risk:** 🟢 Low - all components tested locally

**When you're back, we deploy! 🚀**

