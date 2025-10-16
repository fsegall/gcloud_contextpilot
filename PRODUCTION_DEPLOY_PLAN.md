# ContextPilot - Production Deployment Plan

**Goal:** Launch real product + win hackathon  
**Deadline:** October 20, 2025 (Hackathon) + October 27, 2025 (Public Launch)

---

## 🎯 Strategy

### Primary Goal: LAUNCH REAL PRODUCT
- Production deployment on Google Cloud
- VSCode Marketplace publication
- Real users testing
- Traction for investors/judges

### Secondary Goal: WIN HACKATHON
- Demonstrate Google Cloud usage (mandatory)
- Show real traction (users already using it!)
- Impress judges with architecture
- Gain visibility + potential investment

---

## ☁️ Google Cloud Architecture (Mandatory for Hackathon)

```
┌─────────────────────────────────────────────────────────────┐
│                    VSCode/Cursor Extension                    │
│                  (Published on Marketplace)                   │
└────────────────────┬──────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cloud Load Balancer                         │
│                  (contextpilot.dev)                          │
└────────────────────┬──────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Google Cloud Run (Backend API)                 │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Spec    │  │   Git    │  │  Coach   │  │ Strategy │   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Google Pub/Sub                             │
│                                                              │
│  Topics:                                                     │
│  - proposal-events                                           │
│  - git-events                                                │
│  - spec-updates                                              │
│  - context-updates                                           │
│  - reward-events                                             │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Google Firestore                           │
│                                                              │
│  Collections:                                                │
│  - workspaces                                                │
│  - proposals                                                 │
│  - users                                                     │
│  - agent_state                                               │
│  - events                                                    │
└──────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Other Services                             │
│                                                              │
│  - Secret Manager (API keys)                                 │
│  - Cloud Logging (observability)                             │
│  - Cloud Monitoring (metrics)                                │
│  - Gemini API (content generation)                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 📋 Phase 1: Google Cloud Infrastructure (Days 1-3)

### Day 1 (Oct 16) - Cloud Run + Pub/Sub

**Morning:**
- [ ] Create GCP project (if new) or use existing
- [ ] Enable required APIs:
  - Cloud Run
  - Pub/Sub
  - Firestore
  - Secret Manager
  - Cloud Build
  - Cloud Logging
- [ ] Setup Pub/Sub topics (use existing script)
- [ ] Create subscriptions for each agent

**Afternoon:**
- [ ] Update `event_bus.py` to use Pub/Sub (already has code!)
- [ ] Set `USE_PUBSUB=true` environment variable
- [ ] Test Pub/Sub locally with emulator
- [ ] Create `Dockerfile` for backend

**Evening:**
- [ ] Deploy to Cloud Run (initial version)
- [ ] Test basic health endpoint
- [ ] Verify Pub/Sub connection

### Day 2 (Oct 17) - Firestore Integration

**Morning:**
- [ ] Create Firestore database (Native mode)
- [ ] Design collections schema:
  ```
  workspaces/
    {workspace_id}/
      - created_at
      - owner_id
      - settings
      
  proposals/
    {proposal_id}/
      - workspace_id
      - agent_id
      - title
      - description
      - diff
      - proposed_changes
      - status
      - created_at
  
  users/
    {user_id}/
      - email
      - api_key
      - created_at
      - workspaces[]
  
  agent_state/
    {agent_id}_{workspace_id}/
      - state (JSON)
      - last_updated
  ```

**Afternoon:**
- [ ] Create Firestore client wrapper
- [ ] Migrate proposal persistence from JSON to Firestore
- [ ] Migrate agent state from JSON to Firestore
- [ ] Update agents to use Firestore

**Evening:**
- [ ] Test CRUD operations
- [ ] Deploy updated version to Cloud Run
- [ ] Verify data persistence

### Day 3 (Oct 18) - Auth + Rate Limiting

**Morning:**
- [ ] Create API key generation system
- [ ] Store API keys in Secret Manager
- [ ] Add authentication middleware
- [ ] Update extension to use API key

**Afternoon:**
- [ ] Implement rate limiting (per user):
  - 100 requests/hour (free tier)
  - 1000 requests/hour (paid tier)
- [ ] Add Gemini rate limiting:
  - 15 requests/min (free tier limit)
  - Queue system for excess requests
- [ ] Add caching layer (reduce Gemini calls)

**Evening:**
- [ ] Test rate limiting
- [ ] Deploy to Cloud Run
- [ ] Update docs with auth flow

---

## 📋 Phase 2: Extension Publication (Days 4-5)

### Day 4 (Oct 19) - Package Extension

**Morning:**
- [ ] Update `package.json` with production details:
  - Publisher name
  - Repository URL
  - License
  - Keywords
  - Categories
- [ ] Add icon (256x256 PNG)
- [ ] Update README with installation steps
- [ ] Add CHANGELOG.md

**Afternoon:**
- [ ] Test extension packaging:
  ```bash
  npm install -g @vscode/vsce
  vsce package
  ```
- [ ] Test VSIX installation locally
- [ ] Fix any packaging issues

**Evening:**
- [ ] Create publisher account on VSCode Marketplace
- [ ] Prepare screenshots/GIFs for marketplace
- [ ] Write compelling marketplace description

### Day 5 (Oct 20) - Hackathon Submission

**Morning:**
- [ ] Final Cloud Run deployment
- [ ] Verify all Google Cloud services working
- [ ] Create demo video (3-5 min):
  - Show Google Cloud architecture
  - Live demo end-to-end
  - Highlight custom artifacts
  - Show real traction (if any users)

**Afternoon:**
- [ ] Create presentation slides:
  - Problem statement
  - Solution architecture
  - Google Cloud usage (EMPHASIZE!)
  - Custom artifacts innovation
  - Demo
  - Traction (users, metrics)
  - Future vision
- [ ] Practice presentation (3x)

**Evening:**
- [ ] **SUBMIT TO HACKATHON**
- [ ] Celebrate! 🎉

---

## 📋 Phase 3: Public Launch (Days 6-10)

### Week 2 (Oct 21-27) - VSCode Marketplace + Landing Page

**Tasks:**
- [ ] Publish extension to VSCode Marketplace
- [ ] Buy domain: contextpilot.dev
- [ ] Create landing page:
  - Hero section
  - Features
  - Demo video
  - Installation instructions
  - Pricing (free tier + paid)
  - Testimonials (if any)
- [ ] Setup analytics (Google Analytics)
- [ ] Create documentation site (docs.contextpilot.dev)

### Week 3 (Oct 28-Nov 3) - Beta Testing + Iteration

**Tasks:**
- [ ] Recruit 10-20 beta testers
- [ ] Create onboarding flow
- [ ] Setup feedback system
- [ ] Fix bugs reported
- [ ] Iterate based on feedback

---

## 💰 Cost Estimation

### Google Cloud (Production)

**Free Tier (sufficient for beta):**
- Cloud Run: 2M requests/month free
- Pub/Sub: 10GB messages/month free
- Firestore: 1GB storage + 50k reads/day free
- Secret Manager: 6 secrets free
- Cloud Logging: 50GB/month free

**Estimated Cost (100 users):**
- Cloud Run: $0 (within free tier)
- Pub/Sub: $0 (within free tier)
- Firestore: $0 (within free tier)
- Gemini API: $0 (free tier, 15 req/min)

**Estimated Cost (1000 users):**
- Cloud Run: ~$20/month
- Pub/Sub: ~$10/month
- Firestore: ~$15/month
- Gemini API: ~$50/month (need to upgrade)

**Total:** ~$95/month for 1000 active users

### Domain + Hosting
- Domain: $12/year
- Landing page hosting: $0 (Vercel/Netlify free tier)

---

## 🔐 Security Checklist

- [ ] API keys stored in Secret Manager (not env vars)
- [ ] HTTPS only (Cloud Run enforces)
- [ ] Input validation on all endpoints
- [ ] Rate limiting per user
- [ ] CORS configured properly
- [ ] No sensitive data in logs
- [ ] Regular security audits

---

## 📊 Success Metrics

### For Hackathon (Oct 20)
- ✅ Cloud Run deployed and running
- ✅ Pub/Sub event bus operational
- ✅ Firestore persistence working
- ✅ Demo video showing Google Cloud architecture
- ✅ Live demo during presentation
- 🎯 **Bonus:** Real users already using it!

### For Public Launch (Oct 27)
- ✅ Extension published on VSCode Marketplace
- ✅ Landing page live
- ✅ 10+ beta testers signed up
- ✅ Documentation complete
- 🎯 **Goal:** 50 installations in first week

### Month 1 (Nov 30)
- 🎯 500 installations
- 🎯 100 active weekly users
- 🎯 5+ testimonials
- 🎯 1000+ proposals generated

---

## 🚀 Deployment Checklist

### Before First Deploy
- [ ] Environment variables configured
- [ ] Secrets in Secret Manager
- [ ] Database initialized
- [ ] Pub/Sub topics created
- [ ] Cloud Run service configured
- [ ] Domain mapped (if custom domain)

### Deploy Process
```bash
# 1. Build Docker image
docker build -t gcr.io/${PROJECT_ID}/contextpilot-backend:latest .

# 2. Push to Google Container Registry
docker push gcr.io/${PROJECT_ID}/contextpilot-backend:latest

# 3. Deploy to Cloud Run
gcloud run deploy contextpilot-backend \
  --image gcr.io/${PROJECT_ID}/contextpilot-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_PUBSUB=true,FIRESTORE_ENABLED=true
```

### Post-Deploy Verification
- [ ] Health check passes: `GET /health`
- [ ] Agents status: `GET /agents/status`
- [ ] Pub/Sub receiving events
- [ ] Firestore writing data
- [ ] Extension can connect

---

## 📚 Documentation Requirements

### For Hackathon
- [x] Architecture diagram (showing Google Cloud)
- [ ] README with installation (Cloud Run URL)
- [ ] API documentation
- [ ] Demo script

### For Public Launch
- [ ] User guide (getting started)
- [ ] Extension installation guide
- [ ] Troubleshooting guide
- [ ] API reference (for advanced users)
- [ ] Custom artifacts guide (already done!)
- [ ] Video tutorials

---

## 🎯 Hackathon Presentation Strategy

### Slide 1: Problem (30 seconds)
"Developers lose context. Docs get outdated. Reviews are manual."

### Slide 2: Solution (30 seconds)
"ContextPilot: Multi-agent AI system on Google Cloud."

### Slide 3: Architecture (60 seconds)
**EMPHASIZE GOOGLE CLOUD:**
- "Deployed on Cloud Run for auto-scaling"
- "Pub/Sub for reliable event processing"
- "Firestore for data persistence"
- "Gemini API for intelligent content"
- "Fully serverless, pay-per-use"

### Slide 4: Innovation (45 seconds)
"Custom Artifacts: Users control AI agents with natural language rules."

### Slide 5: Demo (90 seconds)
Live demo showing end-to-end flow.

### Slide 6: Traction (30 seconds)
"Already in production! X users, Y proposals generated."

### Slide 7: Q&A (30 seconds)
"Questions?"

**Total:** 5 minutes

---

## 🏆 Winning the Hackathon

### What Judges Look For
1. **Google Cloud Usage** (40%) - CRITICAL
   - Cloud Run deployment
   - Pub/Sub integration
   - Firestore usage
   - Gemini API
   
2. **Innovation** (30%)
   - Custom artifacts system
   - Multi-agent coordination
   - Spec-driven development
   
3. **Technical Excellence** (20%)
   - Clean architecture
   - Production-ready
   - Scalable
   
4. **Presentation** (10%)
   - Clear value prop
   - Good demo
   - Traction

### Our Strengths
- ✅ Extensive Google Cloud usage
- ✅ Unique custom artifacts
- ✅ Production deployment (not just demo!)
- ✅ Real users (if we launch before hackathon!)
- ✅ Comprehensive docs
- ✅ Beautiful architecture

### Competitive Edge
**"We didn't just build for the hackathon - we launched a real product using Google Cloud in production!"**

---

## 🎯 Next Steps (Immediate)

1. **TODAY (Oct 15 - Evening):**
   - Review this plan
   - Agree on timeline
   - Get good rest!

2. **TOMORROW (Oct 16 - Morning):**
   - Start Cloud Run setup
   - Enable GCP APIs
   - Deploy Pub/Sub topics

3. **TOMORROW (Oct 16 - Afternoon):**
   - Create Dockerfile
   - First Cloud Run deployment
   - Test basic functionality

---

**Status:** 📋 **PLAN READY**  
**Timeline:** 🎯 **5 days to hackathon, 12 days to launch**  
**Confidence:** 🟢 **HIGH - We can do this!**

---

*"Launch real product. Win hackathon. Gain visibility. Scale from there."*

