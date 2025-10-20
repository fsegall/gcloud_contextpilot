# ContextPilot Backend Configuration Guide

## Overview

The ContextPilot backend supports **explicit configuration modes** instead of silent fallbacks. This ensures predictable behavior and makes it clear which backend implementation is being used.

## Configuration Modes

### Storage Mode (`STORAGE_MODE`)

Controls where proposals and data are stored:

- **`local`** (default): File-based storage in the workspace
  - Use for: Local development, testing
  - Requirements: None
  - Data location: `.contextpilot/workspaces/{workspace_id}/`

- **`cloud`**: Google Firestore
  - Use for: Production, Cloud Run deployments
  - Requirements: `GCP_PROJECT_ID` must be set
  - Data location: Firestore collections

### Rewards Mode (`REWARDS_MODE`)

Controls how rewards/points are tracked:

- **`firestore`** (default): Off-chain tracking in Firestore
  - Fast, simple, recommended for most use cases
  - Requirements: `GCP_PROJECT_ID` must be set

- **`blockchain`**: On-chain with Polygon
  - Uses smart contract for minting/burning CPT tokens
  - Requirements: `POLYGON_RPC_URL`, `CPT_CONTRACT_ADDRESS`, `MINTER_PRIVATE_KEY`

### Event Bus Mode (`USE_PUBSUB`)

Controls agent communication:

- **`false`** (default): In-memory event bus
  - Use for: Local development, single-instance deployments
  
- **`true`**: Google Pub/Sub
  - Use for: Production, multi-instance Cloud Run
  - Requirements: `GCP_PROJECT_ID` must be set

## Common Configurations

### Local Development

```bash
STORAGE_MODE=local
REWARDS_MODE=firestore
USE_PUBSUB=false
GCP_PROJECT_ID=your-project-id  # Optional, for rewards
GEMINI_API_KEY=your-key
```

**Result**: All data stored locally, fast development cycle.

### Production (Cloud Run)

```bash
ENVIRONMENT=production
STORAGE_MODE=cloud
REWARDS_MODE=firestore
USE_PUBSUB=true
GCP_PROJECT_ID=your-project-id
GEMINI_API_KEY=your-key
```

**Result**: Firestore for all data, Pub/Sub for events, scalable.

### Production with Blockchain

```bash
ENVIRONMENT=production
STORAGE_MODE=cloud
REWARDS_MODE=blockchain
USE_PUBSUB=true
GCP_PROJECT_ID=your-project-id
POLYGON_RPC_URL=https://polygon-rpc.com
CPT_CONTRACT_ADDRESS=0x...
MINTER_PRIVATE_KEY=0x...
GEMINI_API_KEY=your-key
```

**Result**: On-chain rewards, Firestore for proposals, production-ready.

## API Behavior

### Storage Mode Impact

**LOCAL Mode** (`STORAGE_MODE=local`):
- Endpoints: `/proposals/list`, `/proposals/{id}`, `/proposals/{id}/approve`, `/proposals/{id}/reject`
- Implementation: Custom endpoints in `server.py` using file I/O
- Firestore router: **Disabled**
- Commits: Direct Git commits via Git Agent (local repository)
- Use case: Development, testing, local workflows

**CLOUD Mode** (`STORAGE_MODE=cloud`):
- Endpoints: `/proposals/list`, `/proposals/{id}`, `/proposals/{id}/approve`, `/proposals/{id}/reject`
- Implementation: `app.routers.proposals` using Firestore
- File-based endpoints: **Return 501 (Not Implemented)**
- Commits: Triggers GitHub Actions via `repository_dispatch` webhook
- Use case: Production, Cloud Run, automated CI/CD

### Approval Workflow Differences

#### Local Mode Approval Flow

1. User approves proposal in extension
2. Backend receives `POST /proposals/{id}/approve`
3. **Git Agent commits directly** to local repository
4. Changes are immediately in your working directory
5. Developer can review and push manually

**Pros:**
- Immediate feedback
- Full control over commits
- Can test before pushing
- Works offline

**Cons:**
- Manual push required
- No CI/CD integration
- Not suitable for multi-user scenarios

#### Cloud Mode Approval Flow

1. User approves proposal in extension
2. Backend stores approval in Firestore
3. **GitHub Actions triggered** via `repository_dispatch` webhook
4. GitHub runner:
   - Clones repository
   - Applies changes
   - Runs tests
   - Creates commit
   - Pushes to repository
5. Changes appear in GitHub (not local immediately)

**Pros:**
- Automated CI/CD pipeline
- Changes go through all checks
- Audit trail in GitHub
- Multi-user safe
- Production-ready

**Cons:**
- Slight delay (GitHub Actions startup)
- Requires `GITHUB_TOKEN` configuration
- Changes not immediately local

### Configuration for GitHub Actions

To enable GitHub Actions workflow in **CLOUD mode**, set:

```bash
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPO=your-org/your-repo  # e.g., fsegall/gcloud_contextpilot
```

The backend will call:
```
POST https://api.github.com/repos/{GITHUB_REPO}/dispatches
{
  "event_type": "proposal-approved",
  "client_payload": {
    "proposal_id": "..."
  }
}
```

Your repository needs a workflow file (`.github/workflows/apply-proposal.yml`) to handle this event.

### Auto-Approve Configuration

The `AUTO_APPROVE_ENABLED` environment variable controls whether approved proposals are automatically committed.

```bash
AUTO_APPROVE_ENABLED=true   # Commits happen automatically on approval
AUTO_APPROVE_ENABLED=false  # Approval stored, but no commit (default)
```

**Behavior by Mode:**

| Mode | AUTO_APPROVE_ENABLED | Result |
|------|---------------------|--------|
| LOCAL | `true` | Git Agent commits directly to local repo |
| LOCAL | `false` | Approval stored, no commit |
| CLOUD | `true` | GitHub Actions triggered |
| CLOUD | `false` | Approval stored in Firestore, no workflow trigger |

**When to enable:**
- ✅ Development with trusted AI-generated code
- ✅ Production with comprehensive test suite in GitHub Actions
- ❌ Production without tests (manual review recommended)
- ❌ When learning the system (review changes first)

### Choosing the Right Mode

**Use LOCAL mode when:**
- 👨‍💻 Developing the ContextPilot system itself
- 🧪 Testing new agent features
- 📝 Working on documentation
- 🔌 Working offline or with intermittent connectivity
- 🎓 Learning how the system works

**Use CLOUD mode when:**
- 🚀 Running in production (Cloud Run)
- 👥 Multiple developers on the same project
- 🔄 Want automated CI/CD integration
- ✅ Need all changes to go through test suite
- 📊 Need centralized audit trail in Firestore
- 🌐 Backend is stateless/serverless

### Checking Current Mode

```bash
curl https://your-backend.run.app/health
```

Response includes:
```json
{
  "status": "ok",
  "version": "2.1.0",
  "config": {
    "environment": "production",
    "storage_mode": "cloud",
    "rewards_mode": "firestore",
    "event_bus_mode": "pubsub"
  }
}
```

## Migration Guide

### From Implicit to Explicit Mode

**Old approach** (deprecated):
```bash
FIRESTORE_ENABLED=true  # Ambiguous fallback behavior
```

**New approach** (recommended):
```bash
STORAGE_MODE=cloud  # Explicit, clear intent
```

### Legacy Support

For backward compatibility, `FIRESTORE_ENABLED=true` is still supported but will log a deprecation warning:

```
Using deprecated FIRESTORE_ENABLED. Please set STORAGE_MODE=cloud explicitly.
```

## Troubleshooting

### "Configuration errors" on startup

Check that required environment variables are set:
- `STORAGE_MODE=cloud` requires `GCP_PROJECT_ID`
- `REWARDS_MODE=blockchain` requires blockchain-specific vars
- `USE_PUBSUB=true` requires `GCP_PROJECT_ID`

### "This endpoint is for LOCAL mode"

You're calling a file-based endpoint while in `STORAGE_MODE=cloud`.
Use the Firestore router instead (same endpoint path).

### "This endpoint is for CLOUD mode"

You're calling a Firestore endpoint while in `STORAGE_MODE=local`.
The endpoint path is the same, but the backend needs to be in cloud mode.

## Environment Variables Reference

| Variable | Values | Default | Required For |
|----------|--------|---------|--------------|
| `STORAGE_MODE` | `local`, `cloud` | `local` | Always |
| `REWARDS_MODE` | `firestore`, `blockchain` | `firestore` | Always |
| `USE_PUBSUB` | `true`, `false` | `false` | Always |
| `GCP_PROJECT_ID` | Project ID | - | Cloud mode, Rewards, Pub/Sub |
| `GEMINI_API_KEY` | API key | - | AI features |
| `GITHUB_TOKEN` | Token | - | GitHub Actions integration |
| `POLYGON_RPC_URL` | URL | - | Blockchain rewards |
| `CPT_CONTRACT_ADDRESS` | Address | - | Blockchain rewards |
| `MINTER_PRIVATE_KEY` | Private key | - | Blockchain rewards |
| `ENVIRONMENT` | `development`, `production` | `development` | Deployment context |

## Best Practices

1. **Always set `STORAGE_MODE` explicitly** - Don't rely on defaults in production
2. **Match modes to environment** - Use `local` for dev, `cloud` for prod
3. **Check `/health` after deployment** - Verify configuration is correct
4. **Use environment-specific configs** - Separate `.env.dev` and `.env.prod`
5. **Never commit secrets** - Use Cloud Run secrets or `.env` (gitignored)

## Next Steps

- For deployment: See `DEPLOYMENT.md`
- For development: See main `README.md`
- For blockchain setup: See `TOKENOMICS.md` (coming soon)

