# 🚀 ContextPilot - Quick Start Guide

Get up and running with ContextPilot in 15 minutes!

## Prerequisites

- Node.js 18+ & npm
- Python 3.11+
- Google Cloud account
- Polygon wallet with test MATIC
- Git

## Step 1: Clone & Install

```bash
# Clone repository
git clone https://github.com/yourorg/google-context-pilot.git
cd google-context-pilot

# Backend setup
cd back-end
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../front-end
npm install

# Smart contracts setup
cd ../contracts
curl -L https://foundry.paradigm.xyz | bash
foundryup
forge install
```

## Step 2: Configure Environment

### Backend (.env)
```bash
cd back-end
cp .env.example .env
# Edit .env and add:
# - OPENAI_API_KEY
# - GCP_PROJECT_ID
# - POLYGON_RPC_URL (use Mumbai testnet)
```

### Frontend (.env)
```bash
cd front-end
cp .env.example .env
# Edit .env and add:
# - VITE_API_URL=http://localhost:8000
# - VITE_SUPABASE_URL
# - VITE_SUPABASE_ANON_KEY
# - VITE_WALLET_CONNECT_PROJECT_ID (get from https://cloud.walletconnect.com)
```

## Step 3: Deploy Smart Contract (Testnet)

```bash
cd contracts
cp .env.example .env
# Add your deployer private key and PolygonScan API key

# Run deploy script
./scripts/deploy.sh

# Save the contract address shown in output
# Update back-end/.env with: CPT_CONTRACT_ADDRESS=0x...
# Update front-end/.env with: VITE_CPT_CONTRACT_MUMBAI=0x...
```

## Step 4: Initialize Google Cloud

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com

# Create Firestore database
gcloud firestore databases create --location=us-central1

# Store secrets
echo -n "YOUR_OPENAI_KEY" | gcloud secrets create openai-api-key --data-file=-
echo -n "YOUR_CONTRACT_ADDRESS" | gcloud secrets create cpt-contract-address --data-file=-
echo -n "YOUR_MINTER_KEY" | gcloud secrets create minter-private-key --data-file=-
```

## Step 5: Run Locally

### Terminal 1: Backend
```bash
cd back-end
source .venv/bin/activate
uvicorn app.server:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Terminal 2: Frontend
```bash
cd front-end
npm run dev
# UI running at http://localhost:5173
```

### Terminal 3: Test Rewards
```bash
# Track a test action
curl -X POST http://localhost:8000/rewards/track \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "action_type": "spec_commit",
    "metadata": {"file": "README.md"}
  }'

# Check balance
curl http://localhost:8000/rewards/balance/test_user_123
```

## Step 6: Deploy to Cloud Run

```bash
# From project root
gcloud builds submit --config infra/cloudbuild.yaml

# Note the deployed URLs
# API: https://contextpilot-api-HASH-uc.a.run.app
# Update front-end/.env with this URL
```

## Step 7: Test Full Flow

1. **Open UI** at http://localhost:5173
2. **Connect Wallet** (RainbowKit button in top-right)
3. **Create a Project**:
   - Add project name, goal, milestones
   - Save checkpoint
4. **Earn Rewards**:
   - Commit some code
   - Update docs
   - Complete a milestone
5. **Check CPT Balance**:
   - Rewards Widget shows pending points
   - Connect wallet to see on-chain balance (after batch mint)
6. **View Leaderboard**:
   - See top contributors
   - Check your rank

## Common Issues & Solutions

### Issue: "No contract address configured"
**Solution**: Deploy smart contract first (Step 3) and update .env files

### Issue: "Wallet connection failed"
**Solution**: 
- Check VITE_WALLET_CONNECT_PROJECT_ID is set
- Try a different browser/wallet
- Clear browser cache

### Issue: "Firestore permission denied"
**Solution**: 
- Check GCP_PROJECT_ID is correct
- Ensure Firestore is created
- Verify service account permissions

### Issue: "Transaction failed on Polygon"
**Solution**:
- Ensure you have test MATIC in your wallet (get from https://faucet.polygon.technology)
- Check gas price isn't too high
- Verify contract address is correct

## Next Steps

### For Development
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [TOKENOMICS.md](TOKENOMICS.md) for token economics
- Explore API docs at `/docs` endpoint

### For Hackathon Submission
1. **Record Demo Video** (3 min):
   - Show problem (context loss)
   - Demo multi-agent system
   - Show rewards earning
   - Show leaderboard
   
2. **Create Architecture Diagram**:
   - Use provided mermaid diagrams
   - Export as PNG/SVG

3. **Write Description** (Devpost):
   - Use TOKENOMICS.md + ARCHITECTURE.md as base
   - Highlight Google Cloud usage
   - Explain AI Agents coordination

4. **Deploy to Production**:
   - Switch to Polygon mainnet
   - Update RPC URLs
   - Re-deploy smart contract
   - Update frontend .env

5. **Create Blog Post** (optional, bonus points):
   - Topic: "Building Context Pilot with Cloud Run and ADK"
   - Include hashtag: #CloudRunHackathon
   - Publish on Medium/Dev.to

## Support

- 📧 Email: support@contextpilot.dev
- 💬 Discord: discord.gg/contextpilot
- 🐛 Issues: github.com/yourorg/contextpilot/issues

## Resources

- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Polygon Developer Docs](https://docs.polygon.technology)
- [RainbowKit Docs](https://rainbowkit.com)
- [Foundry Book](https://book.getfoundry.sh)

---

**Happy Hacking! 🎉**

Built for [Cloud Run Hackathon 2025](https://run.devpost.com)

