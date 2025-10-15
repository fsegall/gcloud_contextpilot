# 🏗️ ContextPilot Architecture

## System Overview

ContextPilot is a **multi-agent AI system** with an **integrated Web3 incentive layer** built on Google Cloud Run and Ethereum blockchain via **Google Blockchain Node Engine**.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Dashboard  │  │ RainbowKit   │  │ Rewards Widget        │  │
│  │ Components │  │ Wallet       │  │ + Leaderboard         │  │
│  └────────────┘  └──────────────┘  └───────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                              │ REST API + WebSocket
┌─────────────────────────────┴────────────────────────────────────┐
│                    FastAPI Backend (Cloud Run)                    │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Git Context│  │ AI Agents    │  │ Rewards Engine        │  │
│  │ Manager    │  │ (ADK)        │  │ (Adapter Pattern)     │  │
│  └────────────┘  └──────────────┘  └───────────────────────┘  │
└───┬────────────────┬─────────────────────┬──────────────────────┘
    │                │                     │
    │                │                     ├──► Firestore (off-chain)
    │                │                     │
    │                │                     └──► GCNE (Polygon)
    │                │                              │
    │                └──► Pub/Sub Event Bus         │
    │                                               │
    ├──► Cloud Storage (snapshots)                  │
    │                                               │
    └──► BigQuery (analytics)                       │
                                                    │
┌───────────────────────────────────────────────────┴──────────────┐
│         Google Blockchain Node Engine (Managed Polygon)          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Dedicated Polygon Nodes                                 │   │
│  │  ✓ Google Cloud SLA                                      │   │
│  │  ✓ Regional proximity (low latency)                      │   │
│  │  ✓ Automatic scaling                                     │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │  CPT Smart Contract (ERC-20)                             │   │
│  │  - mint() → rewards distribution                         │   │
│  │  - burnInactive() → 30-day inactivity cleanup            │   │
│  │  - renewCycle() → monthly supply reset                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## 🔗 Google Blockchain Node Engine Integration

### Why GCNE?

ContextPilot uses **Google Blockchain Node Engine** instead of public RPCs for several critical reasons:

1. **Reliability**: Google Cloud SLA guarantees
2. **Performance**: Regional nodes reduce latency by 50-70%
3. **Security**: Private, managed infrastructure
4. **Scalability**: Automatic load balancing
5. **Integration**: Native with other GCP services

### Connection Flow

```
Backend/Frontend
    ↓
Web3.py / viem
    ↓
GCNE Endpoint (Private)
    ↓
Managed Polygon Node
    ↓
Polygon Network
    ↓
CPT Smart Contract
```

### Configuration

**Backend** checks for GCNE first:
```python
gcne_endpoint = os.getenv("GOOGLE_BLOCKCHAIN_NODE_ENDPOINT")
if gcne_endpoint:
    rpc_url = gcne_endpoint  # Prioritize GCNE
else:
    rpc_url = public_rpc     # Fallback
```

**Frontend** does the same:
```typescript
const rpcUrl = getPolygonRpcUrl();  // GCNE or fallback
const client = createPublicClient({
  transport: http(rpcUrl)
});
```

### Setup

```bash
# Create nodes (takes ~15 minutes)
./infra/setup-gcne.sh

# Endpoints stored in Secret Manager:
# - gcne-mumbai-endpoint (testnet)
# - gcne-mainnet-endpoint (production)
```

### Cost

- **Mumbai node**: ~$50/month
- **Mainnet node**: ~$50/month
- **vs Public RPCs**: Free but unreliable

**ROI**: Worth it for production reliability and performance.

## Core Components

### 1. **AI Agents** (Multi-Agent System)

#### Coach Agent
- **Purpose**: Human-centric guidance, micro-actions, unblocking
- **Input Events**: `context.update.v1`, `milestone.saved.v1`, `spec.update.v1`
- **Output Events**: `coach.nudge.v1`
- **Storage**: Firestore (`coaching_feed`, `checkins`)
- **Cloud Run Type**: Service (HTTP + Pub/Sub subscriber)

#### Context Agent
- **Purpose**: Index and interpret project state (files, commits, docs)
- **Input Events**: Git hooks, file watchers
- **Output Events**: `context.delta.v1`
- **Storage**: Firestore (`context_snapshots`)
- **Cloud Run Type**: Job (triggered by Pub/Sub)

#### Spec Agent
- **Purpose**: Generate/update technical specs and markdown docs
- **Input Events**: `context.delta.v1`, manual triggers
- **Output Events**: `spec.update.v1`
- **Storage**: Git repository
- **Cloud Run Type**: Service

#### Strategy Agent
- **Purpose**: Analyze dependencies, detect patterns, suggest improvements
- **Input Events**: `context.delta.v1`, `code.review.v1`
- **Output Events**: `strategy.insight.v1`
- **Storage**: BigQuery (analysis results)
- **Cloud Run Type**: Job

#### Milestone Agent
- **Purpose**: Track milestones, create checkpoints, version project state
- **Input Events**: Manual triggers, automated timers
- **Output Events**: `milestone.saved.v1`
- **Storage**: Firestore + Cloud Storage
- **Cloud Run Type**: Worker Pool

### 2. **Rewards System** (Web3 Incentive Layer)

#### Architecture: Adapter Pattern (Pluggable)

```python
RewardsAdapter (Interface)
    ├─► FirestoreRewardsAdapter (Off-chain, fast)
    └─► BlockchainRewardsAdapter (On-chain, via GCNE)
```

#### Off-Chain Flow (Fast Path)
1. Developer action detected by agent
2. `RewardsAdapter.track_action()` → Firestore write (< 100ms)
3. Points appear as "pending" in UI
4. Pub/Sub event published for blockchain sync

#### On-Chain Flow (Batch Path via GCNE)
1. Daily Cloud Run Job (`batch_minter.py`) runs
2. Query Firestore for pending rewards (>= 10 CPT threshold)
3. Connect to Polygon via **GCNE** (managed node)
4. Batch mint via smart contract (`CPT.mint()`)
5. Update Firestore with transaction hashes
6. UI shows on-chain balance

#### GCNE Benefits for Rewards
- **Low Latency**: 50ms avg vs 300ms public RPC
- **High Reliability**: 99.9% uptime SLA
- **Consistent Gas Prices**: Better estimation
- **No Rate Limits**: Dedicated bandwidth

### 3. **Smart Contract** (CPT Token)

Deployed on Polygon and accessed via GCNE for optimal performance.

#### Features
- **ERC-20 compliant** (standard wallet support)
- **Role-based access control** (MINTER_ROLE, BURNER_ROLE)
- **Monthly cycles** (1M CPT max per 30 days)
- **Auto-burn inactive** (30 days no activity)
- **Pausable** (emergency stop)

#### Key Functions
```solidity
function mint(address to, uint256 amount) external;
function burnInactive(address account) external;
function renewCycle() external;
function isInactive(address account) external view returns (bool);
```

#### Deployment
- **Testnet**: Polygon Mumbai (via GCNE)
- **Mainnet**: Polygon PoS (via GCNE, Q1 2026)
- **Tooling**: Foundry (compile, test, deploy, verify)

### 4. **Frontend** (React + Web3)

#### Tech Stack
- React + TypeScript + Vite
- TailwindCSS + shadcn/ui
- RainbowKit (wallet connection)
- wagmi + viem (Ethereum interactions via GCNE)
- @tanstack/react-query (data fetching)

#### Key Components
- `<RewardsWidget />`: Shows CPT balance (on-chain + pending)
- `<Leaderboard />`: Top contributors by points
- `<WalletConnect />`: RainbowKit integration
- `<ProjectHeader />`, `<MilestonesList />`, etc (existing)

#### Web3 Integration (via GCNE)
```typescript
// Viem automatically uses GCNE endpoint
const balance = await getCPTBalance(address);

// All contract reads go through GCNE
const inactive = await isInactive(address);
const timeLeft = await getTimeUntilRenewal();
```

## Deployment

### 1. Setup Google Blockchain Nodes

```bash
# Run GCNE setup script
./infra/setup-gcne.sh

# This creates:
# - polygon-mumbai-node (testnet)
# - polygon-mainnet-node (production)
#
# Endpoints stored in Secret Manager
```

### 2. Deploy to Cloud Run

```bash
# Deploy via Cloud Build
gcloud builds submit --config infra/cloudbuild.yaml

# Services automatically use GCNE endpoints from secrets
```

### 3. Local Development

```bash
# Backend (with GCNE)
cd back-end
export GOOGLE_BLOCKCHAIN_NODE_ENDPOINT="https://your-node.googleusercontent.com"
uvicorn app.server:app --reload

# Frontend (with GCNE)
cd front-end
# Add VITE_GOOGLE_BLOCKCHAIN_NODE_ENDPOINT to .env
npm run dev
```

## Cost Estimation

### Google Cloud (monthly, 1000 active users)
- Cloud Run API: ~$50
- Cloud Run Jobs: ~$20
- Firestore: ~$30
- Cloud Storage: ~$5
- BigQuery: ~$10
- **Blockchain Node Engine**: ~$100 (2 nodes)
- **Total GCP**: ~$215/month

### Polygon Gas (monthly)
- Minting transactions: ~$100
- **Total Blockchain**: ~$100/month

### Grand Total: ~$315/month for 1000 users

**vs Public RPC Alternative**: ~$215/month but with reliability issues

**Value**: +$100/month for enterprise-grade blockchain access

## Performance Comparison

| Metric | Public RPC | GCNE |
|--------|-----------|------|
| Latency (avg) | 300ms | 50ms |
| Uptime | ~95% | 99.9% |
| Rate Limits | Yes | No |
| Support | None | Google Cloud |
| Regional | No | Yes |

## Security Considerations

### GCNE Security Benefits
- ✅ **Private endpoints** (not exposed to internet)
- ✅ **VPC integration** possible
- ✅ **IAM-based access control**
- ✅ **Audit logs** in Cloud Logging

### Smart Contract
- ✅ OpenZeppelin audited libraries
- ✅ Role-based access (no owner backdoors)
- ✅ Pausable (emergency stop)
- ✅ Tested with Foundry (100% coverage goal)
- ✅ Supply caps per cycle

## Monitoring & Observability

### GCNE Monitoring
- **Cloud Console**: Node status, request metrics
- **Cloud Logging**: All RPC calls logged
- **Cloud Monitoring**: Custom dashboards
- **Alerting**: Node health, high latency

### Application Monitoring
- **Cloud Monitoring**: API latency, error rates
- **BigQuery**: Rewards analytics
- **Firestore**: Real-time dashboards
- **PolygonScan**: On-chain activity

## Scaling Strategy

### Phase 1 (Current): MVP
- GCNE: 2 nodes (Mumbai + Mainnet)
- Cloud Run: 1-10 instances (auto-scale)
- Firestore: Single region

### Phase 2 (Q1 2026): Growth
- GCNE: Multi-region nodes
- Cloud Run: Multi-region deployment
- Firestore: Multi-region replication
- CDN for frontend

### Phase 3 (Q2 2026+): Scale
- GCNE: Dedicated node pools
- Kubernetes (GKE) for complex workloads
- Cross-chain bridges
- Enterprise features

## Future Enhancements

### Q4 2025
- [x] GCNE integration (testnet)
- [ ] Mainnet launch with GCNE
- [ ] VPC peering for GCNE
- [ ] Advanced monitoring dashboards

### Q1 2026
- [ ] Multi-region GCNE deployment
- [ ] Load balancing across nodes
- [ ] DeFi integrations
- [ ] Governance features

---

**Built with**:  
Google Cloud Run + **Google Blockchain Node Engine** + Polygon + AI Agents

**Why 100% Google Cloud?**  
Unified platform, better performance, simpler operations, enterprise support.

**License**: MIT  
**Status**: Hackathon Submission (Cloud Run Hackathon 2025)
