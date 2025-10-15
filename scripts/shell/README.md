# 🔧 Shell Scripts

Utility scripts for ContextPilot project maintenance and testing.

---

## 📜 Available Scripts

### 🏗️ Workspace Management

#### `create-contextpilot-workspace.sh` 🆕
Create workspace "contextpilot" for dogfooding - use ContextPilot to develop ContextPilot!

**Usage:**
```bash
# Make sure backend is running first!
bash scripts/shell/create-contextpilot-workspace.sh
```

**What it does:**
- Checks if backend is running
- Creates workspace via `/generate-context` API
- Sets up project context (name, goal, milestones)
- Initializes git repository for workspace
- Shows checkpoint and git log

**Output:**
- Workspace: `back-end/.contextpilot/workspaces/contextpilot/`
- Initial commit with project setup
- 5 milestones (Extension MVP → Hackathon submission)

**Example verification:**
```bash
# View checkpoint
cat back-end/.contextpilot/workspaces/contextpilot/checkpoint.yaml

# View git log
cd back-end/.contextpilot/workspaces/contextpilot && git log --oneline
```

---

### 🧪 Testing

#### `test-contract.sh`
Test CPT smart contract functionality on Sepolia.

**Usage:**
```bash
bash scripts/shell/test-contract.sh
```

**Tests:**
- Total supply
- Balance queries
- Token metadata (name, symbol, decimals)
- Cycle management

---

#### `test-infra-quick.sh`
Quick infrastructure validation.

**Usage:**
```bash
bash scripts/shell/test-infra-quick.sh
```

**Checks:**
- ✅ Smart contract responsiveness
- ✅ GCP project access
- ✅ Pub/Sub topics
- ✅ Dependencies (backend/frontend)
- ✅ Contract ABI export
- ✅ Documentation completeness

---

### 📁 Organization

#### `organize-docs.sh`
Organize documentation files into `docs/` structure.

**Usage:**
```bash
bash scripts/shell/organize-docs.sh
```

**Actions:**
- Moves `.md` files to appropriate categories
- Creates organized structure:
  - `docs/architecture/`
  - `docs/deployment/`
  - `docs/guides/`
  - `docs/progress/`
  - `docs/agents/`

**Note:** This was already run. Files are organized.

---

## 🚀 Other Scripts

### Infrastructure (`infra/`)

Located in `infra/` directory:

- **`setup-pubsub.sh`** - Setup Google Pub/Sub topics and subscriptions
- **`setup-gcne.sh`** - Setup Google Blockchain Node Engine (cancelled - Polygon not supported)
- **`setup-all.sh`** - Run all infrastructure setup scripts
- **`test-infra.sh`** - Test deployed infrastructure

**Usage:**
```bash
cd infra
bash setup-pubsub.sh
```

---

### Smart Contracts (`contracts/scripts/`)

Located in `contracts/scripts/` directory:

- **`deploy.sh`** - Deploy CPT smart contract to Sepolia

**Usage:**
```bash
cd contracts
bash scripts/deploy.sh
```

---

## 🎯 Quick Reference

### Test Everything
```bash
# Test contract
bash scripts/shell/test-contract.sh

# Test infrastructure
bash scripts/shell/test-infra-quick.sh
```

### Setup Infrastructure
```bash
# Setup all
cd infra && bash setup-all.sh

# Or individually
cd infra && bash setup-pubsub.sh
```

### Deploy Contract
```bash
cd contracts && bash scripts/deploy.sh
```

---

## 📝 Script Conventions

### Exit Codes
- `0` - Success
- `1` - General error
- `2` - Missing dependency

### Output Format
- 🔧 Action in progress
- ✅ Success
- ❌ Error
- ⚠️  Warning
- 📊 Information

### Error Handling
All scripts use `set -e` to exit on first error.

---

## 🔗 Related Documentation

- [DEPLOYMENT.md](../../docs/deployment/DEPLOYMENT.md) - Deployment guide
- [QUICKSTART.md](../../docs/deployment/QUICKSTART.md) - Quick start guide
- [IMPLEMENTATION_GUIDE.md](../../docs/guides/IMPLEMENTATION_GUIDE.md) - Implementation details

---

**Last Updated**: 2025-10-14  
**Maintained By**: ContextPilot Team
