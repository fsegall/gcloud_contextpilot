# 🏗️ ContextPilot Architecture

## Overview

ContextPilot is a **multi-agent AI system** deployed on **Google Cloud Run** that helps developers maintain project context, documentation, and code quality through intelligent automation and gamification.

**Built for:** [Cloud Run Hackathon 2025](https://run.devpost.com/) - AI Agents Category

---

## 🎯 Architecture Objectives

- **Event-Driven**: Agents communicate via Pub/Sub (async, scalable)
- **Cloud-Native**: Fully serverless on Google Cloud Run
- **Local-First**: Code operations happen on developer's machine
- **Secure**: Rate limiting, abuse detection, secrets management
- **Extensible**: Easy to add new agents and features

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Developer Machine (Local)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           VS Code/Cursor Extension                      │ │
│  │                                                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │  │Proposals │  │ Rewards  │  │  Agents  │            │ │
│  │  │   View   │  │   View   │  │  Status  │            │ │
│  │  └──────────┘  └──────────┘  └──────────┘            │ │
│  │                                                         │ │
│  │  ┌──────────────────────────────────────┐             │ │
│  │  │       Git Operations (Local)          │             │ │
│  │  │  • Commits   • Branches   • Files    │             │ │
│  │  └──────────────────────────────────────┘             │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            │ HTTPS/REST API                  │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Run - Backend Service              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              FastAPI REST API (Python)                  │ │
│  │                                                         │ │
│  │  Endpoints:                                             │ │
│  │  • GET  /proposals          • POST /proposals/create   │ │
│  │  • POST /proposals/approve  • GET  /agents/status      │ │
│  │  • GET  /context/summary    • GET  /health             │ │
│  │  • GET  /admin/abuse-stats                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌─────────────────────────┼──────────────────────────────┐ │
│  │                         ▼                               │ │
│  │           Multi-Agent System (6 Agents)                │ │
│  │                                                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │  │   Spec   │  │   Git    │  │ Context  │            │ │
│  │  │  Agent   │  │  Agent   │  │  Agent   │            │ │
│  │  └──────────┘  └──────────┘  └──────────┘            │ │
│  │        │              │              │                 │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │  │  Coach   │  │Milestone │  │ Strategy │            │ │
│  │  │  Agent   │  │  Agent   │  │  Agent   │            │ │
│  │  └──────────┘  └──────────┘  └──────────┘            │ │
│  │        │              │              │                 │ │
│  │        └──────────────┼──────────────┘                │ │
│  │                       │                                │ │
│  └───────────────────────┼────────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Pub/Sub    │  │  Firestore   │  │ Gemini API   │
│  Event Bus   │  │   Database   │  │  (AI Gen)    │
│              │  │              │  │              │
│ • Topics     │  │ • Proposals  │  │ • Gemini 1.5 │
│ • Subscript. │  │ • User Data  │  │   Flash      │
│ • Events     │  │ • State      │  │ • Context    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Secret Manager   │
                │                  │
                │ • GOOGLE_API_KEY │
                │ • GITHUB_TOKEN   │
                └──────────────────┘
```

---

## 🤖 Multi-Agent System

### Agent Responsibilities

| Agent | Purpose | Events Consumed | Events Published |
|-------|---------|-----------------|------------------|
| **Spec Agent** | Generate & validate docs | `spec.analyze.v1` | `spec.update.v1` |
| **Git Agent** | Semantic commits | `proposal.approved.v1` | `git.commit.v1` |
| **Context Agent** | Project analysis | `context.request.v1` | `context.update.v1` |
| **Coach Agent** | Development tips | `coach.ask.v1` | `coach.tip.v1` |
| **Milestone Agent** | Track progress | `milestone.check.v1` | `milestone.complete.v1` |
| **Strategy Agent** | Pattern analysis | `strategy.analyze.v1` | `strategy.suggestion.v1` |

### Agent Communication Flow

```
1. User Action (Extension)
   ↓
2. API Request → Cloud Run Service
   ↓
3. Event Published → Pub/Sub Topic
   ↓
4. Agent Subscription receives event
   ↓
5. Agent processes (may call Gemini API)
   ↓
6. Result saved to Firestore
   ↓
7. Response Event published (if needed)
   ↓
8. Extension receives update
```

---

## 🔄 Event-Driven Architecture

### Pub/Sub Topics

```python
Topics:
- spec-events          # Spec agent events
- git-events           # Git operations
- context-events       # Context updates
- coach-events         # Coaching tips
- milestone-events     # Progress tracking
- strategy-events      # Pattern analysis
- proposal-events      # Proposal lifecycle
- reward-events        # Gamification
```

### Event Format

```json
{
  "event_id": "evt_1234567890",
  "type": "proposal.approved.v1",
  "timestamp": "2025-10-17T12:00:00Z",
  "source": "extension",
  "data": {
    "proposal_id": "spec-missing_doc-1760664997",
    "workspace_id": "default",
    "user_id": "test-user"
  }
}
```

---

## 💾 Data Persistence

### Firestore Collections

```
proposals/
  ├── {proposal_id}
  │   ├── id: string
  │   ├── workspace_id: string
  │   ├── agent_id: string
  │   ├── title: string
  │   ├── description: string
  │   ├── status: "pending" | "approved" | "rejected"
  │   ├── proposed_changes: array
  │   ├── created_at: timestamp
  │   └── updated_at: timestamp

users/
  ├── {user_id}
  │   ├── cpt_balance: number
  │   ├── total_earned: number
  │   ├── achievements: array
  │   └── last_activity: timestamp

agent_state/
  ├── {agent_id}
  │   ├── status: "active" | "idle" | "error"
  │   ├── last_event: timestamp
  │   └── metrics: object
```

---

## 🔐 Security Architecture

### Layers of Protection

1. **Network Level**
   - Rate limiting: 100 requests/hour per IP
   - Abuse detection: Blacklist malicious patterns
   - CORS configured for allowed origins

2. **Application Level**
   - Input validation
   - Path sanitization
   - Error handling with safe messages

3. **Infrastructure Level**
   - Secret Manager for API keys
   - Cloud Run IAM for service access
   - Firestore security rules

4. **Monitoring**
   - Real-time alerts (>1000 req/min)
   - Abuse statistics endpoint
   - Budget alerts ($50/month)

See [SECURITY.md](SECURITY.md) for complete details.

---

## ☁️ Cloud Run Deployment

### Service Configuration

```yaml
Service: contextpilot-backend
  Region: us-central1
  CPU: 1 vCPU
  Memory: 512 MiB
  Min instances: 0 (scale to zero)
  Max instances: 100
  Timeout: 300s
  
  Environment Variables:
    - GCP_PROJECT_ID
    - FIRESTORE_ENABLED=true
    - USE_PUBSUB=true
    - CONTEXTPILOT_AUTO_APPROVE_PROPOSALS=false
  
  Secrets (from Secret Manager):
    - GOOGLE_API_KEY
    - GITHUB_TOKEN
```

### Why Cloud Run?

- ✅ **Auto-scaling**: 0 to 100 instances based on traffic
- ✅ **Pay-per-use**: Only charged when serving requests
- ✅ **Fast deploys**: Docker-based, ~2 min to production
- ✅ **Native integrations**: Pub/Sub, Firestore, Secret Manager
- ✅ **Monitoring**: Built-in logs, metrics, traces

---

## 🔀 Request Flow Examples

### Example 1: Approve Proposal

```
1. User clicks "Approve" in VS Code extension
   ↓
2. Extension → POST /proposals/{id}/approve
   ↓
3. Cloud Run Backend:
   - Marks proposal as approved in Firestore
   - Publishes proposal.approved.v1 event to Pub/Sub
   - Returns success to extension
   ↓
4. Extension (local):
   - Applies changes to local files
   - Creates git commit with semantic message
   - Awards +10 CPT to user
   - Shows success notification
   ↓
5. Git Agent (Cloud Run, async):
   - Receives proposal.approved.v1 event
   - Logs the approval
   - Updates agent metrics
```

### Example 2: Generate Context Summary

```
1. Extension opens new chat
   ↓
2. Extension → GET /context/summary
   ↓
3. Spec Agent (Cloud Run):
   - Reads crucial .md files (README, scope, etc.)
   - Calls Git Agent for recent commits
   - Builds context prompt from template
   - Returns condensed summary
   ↓
4. Extension:
   - Displays summary to user
   - User has full context for decision-making
```

---

## 🧩 Extension Architecture

### VS Code Extension Components

```
extension/
├── src/
│   ├── extension.ts           # Entry point, activation
│   ├── commands/
│   │   └── index.ts           # All extension commands
│   ├── services/
│   │   ├── contextpilot.ts    # API client
│   │   └── rewards.ts         # Local gamification
│   └── views/
│       ├── proposals.ts       # Proposals tree view
│       ├── rewards.ts         # Rewards tree view
│       └── agents.ts          # Agents status view
└── package.json               # Extension manifest
```

### Extension ↔ Backend Communication

```typescript
// Extension uses Axios for HTTP requests
const client = axios.create({
  baseURL: 'https://contextpilot-backend-581368740395.us-central1.run.app',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
});

// Example: Fetch proposals
const response = await client.get('/proposals', {
  params: { workspace_id: 'default', status: 'pending' }
});
```

---

## 🎮 Gamification Architecture

### Local vs Cloud

**Local (Extension):**
- CPT balance stored in memory (Map)
- Achievements calculated locally
- Daily streaks tracked locally
- Fast, no network latency

**Cloud (Future):**
- Firestore for persistent user data
- Blockchain for on-chain token minting
- Leaderboards and global rankings

### Reward Flow

```
User Action (Approve Proposal)
    ↓
Extension: RewardsService.addCPT(userId, +10, 'approve_proposal')
    ↓
Check Achievements (local)
    ↓
Update Balance (memory/storage)
    ↓
Show Notification: "+10 CPT earned! 🎉"
```

---

## 🔧 Infrastructure as Code

### Terraform Resources

All infrastructure is defined in `terraform/`:

```hcl
Resources:
- google_cloud_run_service.backend
- google_pubsub_topic.* (11 topics)
- google_pubsub_subscription.* (11 subscriptions)
- google_firestore_database.main
- google_secret_manager_secret.* (API keys)
- google_monitoring_alert_policy.* (alerts)
- google_monitoring_dashboard.contextpilot_dashboard
```

**Benefits:**
- ✅ Reproducible deployments
- ✅ Version controlled
- ✅ Easy to modify and redeploy
- ✅ Self-documenting infrastructure

---

## 🌊 Data Flow Diagram

```
Extension UI
    ↓ (1. User approves proposal)
API Gateway (Cloud Run)
    ↓ (2. Mark approved in Firestore)
Firestore
    ↓ (3. Publish event)
Pub/Sub Topic
    ↓ (4. Fan-out to subscribers)
Agent Subscriptions
    ↓ (5. Process asynchronously)
Agent Logic + Gemini API
    ↓ (6. Update state)
Firestore (Updated State)
    ↓ (7. Extension polls or receives)
Extension (Refresh UI)
```

---

## 🔌 Integration Points

### Google Cloud Services

| Service | Usage | Why |
|---------|-------|-----|
| Cloud Run | Backend API | Serverless, auto-scale |
| Pub/Sub | Event bus | Async, reliable, persistent |
| Firestore | Database | NoSQL, real-time, scalable |
| Gemini API | AI generation | Powerful, fast, cost-effective |
| Secret Manager | API keys | Secure, versioned, auditable |
| Monitoring | Observability | Dashboards, alerts, logs |

### External Integrations

- **Git**: Local operations via `simple-git` (Node.js)
- **VS Code API**: Extension host, commands, views
- **GitHub API**: Trigger workflows (optional)

---

## 🚀 Scalability Considerations

### Current Capacity

- **Cloud Run**: Auto-scales 0-100 instances
- **Rate Limit**: 100 req/hour/IP = ~2400 users/hour max
- **Pub/Sub**: Millions of messages/sec (far exceeds needs)
- **Firestore**: Handles 10K+ writes/sec
- **Gemini API**: 15 req/min free tier

### Scaling Strategy

**Phase 1 (MVP - Current):**
- Single Cloud Run service
- In-memory rate limiting
- Free tier services

**Phase 2 (100-1000 users):**
- Add Cloud Run Jobs for batch processing
- Redis for distributed rate limiting
- Paid tier for Gemini (more quota)

**Phase 3 (1000+ users):**
- Cloud Run Workers for Pub/Sub
- Multi-region deployment
- CDN for static assets
- Database sharding if needed

---

## 🔒 Security & Privacy

### Data Privacy

**What stays local:**
- ✅ All source code
- ✅ Git history
- ✅ File contents

**What goes to cloud:**
- ⚠️ File paths (for proposals)
- ⚠️ Documentation snippets (for AI context)
- ⚠️ User actions (for gamification)

**What's encrypted:**
- ✅ HTTPS for all API calls
- ✅ Secrets in GCP Secret Manager
- ✅ Firestore encryption at rest

### Threat Model

**Protected against:**
- ✅ DDoS (rate limiting + monitoring)
- ✅ Abuse (pattern detection + blacklist)
- ✅ Excessive costs (budget alerts)
- ✅ Unauthorized access (IAM + service accounts)

**Not protected against:**
- ⚠️ User sharing API endpoint (public for beta)
- ⚠️ Code exfiltration (user controls what's shared)

---

## 📊 Monitoring & Observability

### Metrics Tracked

1. **Cloud Run Metrics**
   - Request count/min
   - Response codes (2xx, 4xx, 5xx)
   - Request latency
   - Instance count

2. **Application Metrics**
   - Proposals created/approved
   - Agent events processed
   - Gemini API calls
   - Rate limit hits

3. **Cost Metrics**
   - Estimated daily spend
   - API quota usage
   - Resource utilization

### Dashboards

**GCP Monitoring Dashboard:**
- Cloud Run Requests/min
- Response Code Distribution
- Gemini API Calls
- Estimated Daily Cost

**Admin Endpoint:**
```bash
curl https://contextpilot-backend-581368740395.us-central1.run.app/admin/abuse-stats
```

---

## 🔮 Future Architecture

### Planned Enhancements

1. **Cloud Run Jobs**
   - Batch processing of proposals
   - Scheduled context analysis
   - Daily CPT token minting

2. **Cloud Run Workers**
   - Dedicated Pub/Sub consumers
   - Parallel event processing
   - Improved throughput

3. **Multi-Region**
   - Deploy to us-central1, europe-west1, asia-east1
   - Reduced latency for global users
   - Higher availability

4. **Blockchain Integration**
   - On-chain CPT token (Polygon)
   - NFT achievements
   - Cross-project leaderboards

---

## 📚 Related Documentation

- **[Agents](docs/architecture/AGENTS.md)** - Detailed agent specifications
- **[Custom Artifacts](docs/architecture/CUSTOM_ARTIFACTS.md)** - Spec-driven development
- **[Event Bus](docs/architecture/EVENT_BUS.md)** - Pub/Sub event system
- **[Deployment](docs/deployment/DEPLOYMENT.md)** - How to deploy
- **[Security](SECURITY.md)** - Security measures

---

## 🎯 Architecture Principles

1. **Separation of Concerns**: Each agent has one clear responsibility
2. **Event-Driven**: Agents react to events, don't poll
3. **Idempotent**: Safe to retry operations
4. **Fail-Safe**: Graceful degradation when services unavailable
5. **Observable**: Comprehensive logging and monitoring
6. **Scalable**: Stateless services, async processing
7. **Secure**: Defense in depth

---

**Last Updated:** October 17, 2025  
**Version:** 1.0.0 (Hackathon Submission)  
**By:** Livre Solutions
