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

**CLOUD Mode** (`STORAGE_MODE=cloud`):
- Endpoints: `/proposals/list`, `/proposals/{id}`, `/proposals/{id}/approve`, `/proposals/{id}/reject`
- Implementation: `app.routers.proposals` using Firestore
- File-based endpoints: **Return 501 (Not Implemented)**

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

