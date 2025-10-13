# 🪙 CPT Tokenomics
**Context Pilot Token - Developer Incentive Layer**

## 📊 Token Overview

| Property | Value |
|----------|-------|
| Name | Context Pilot Token |
| Symbol | CPT |
| Standard | ERC-20 |
| Blockchain | Polygon PoS |
| Decimals | 18 |
| Initial Supply | 0 (generated via rewards) |
| Max Supply per Cycle | 1,000,000 CPT |
| Cycle Duration | 30 days |

## 🎯 Token Purpose

CPT is a **dual-purpose token** designed to incentivize and power the ContextPilot ecosystem:

### 1. **Reward Token** (Incentive Layer)
Developers earn CPT by contributing valuable actions:
- Writing documentation
- Committing code
- Completing milestones  
- Using AI agents effectively
- Helping other developers

### 2. **Utility Token** (Computational Layer)
CPT can be consumed to:
- Access premium AI agent features
- Increase compute limits
- Unlock advanced analytics
- Priority support

## 💰 Earning CPT (Rewards)

### Action-Based Rewards

| Action Type | CPT Earned | Description |
|-------------|------------|-------------|
| `cli_action` | +10 | Using Context Pilot CLI |
| `spec_commit` | +5 | Updating documentation |
| `strategy_accepted` | +15 | AI suggestion implemented |
| `milestone_saved` | +20 | Project milestone completed |
| `coach_completed` | +10 | Coach feedback acted upon |
| `doc_update` | +8 | Documentation improvements |
| `test_added` | +12 | Adding tests |
| `code_review` | +7 | Reviewing code |

### Utility Consumption

| Action Type | CPT Cost | Description |
|-------------|----------|-------------|
| `gemini_usage` | -2 | Using Gemini AI models |
| `premium_agent` | -5 | Premium agent features |
| `analytics_export` | -3 | Exporting analytics data |

### 🎁 Bonus Multipliers

- **Streak Bonus**: +10% for 7 consecutive days of activity
- **Quality Bonus**: +50% for highly-rated contributions
- **Community Bonus**: +25% for helping other developers
- **Early Adopter**: +100% during first 3 months (Q4 2025)

## 🔄 Token Lifecycle

### Phase 1: Off-Chain Accumulation (Fast)
1. Developer performs action (e.g., commits code)
2. AI agent detects and validates action
3. Points tracked in Firestore (instant)
4. User sees **pending balance** in UI

### Phase 2: On-Chain Minting (Batch)
5. Daily batch process collects pending points
6. Smart contract mints CPT tokens
7. Tokens appear in user's wallet
8. Transaction recorded on Polygon

### Phase 3: Activity or Expiration
9. User can:
   - **Hold**: Keep accumulating rewards
   - **Use**: Consume for utilities
   - **Transfer**: Send to other addresses (standard ERC-20)
10. Inactive for 30 days → tokens **burned automatically**

## 🔥 Burn Mechanics

### Automatic Burn (Inactivity)
- **Trigger**: No activity for 30 consecutive days
- **Result**: All CPT burned from wallet
- **Purpose**: Prevent hoarding, encourage active participation
- **Warning**: Users notified at 25 days of inactivity

### Utility Burn (Consumption)
- CPT spent on services is **burned** (not recycled)
- Reduces circulating supply over time
- Creates deflationary pressure

### Cycle Reset
- Every 30 days, supply counter resets
- Allows new 1M CPT to be minted
- Previous cycle's tokens remain valid (if active)

## 📈 Supply Dynamics

### Supply Formula
```
Circulating Supply = (Minted This Cycle + Previous Active Balances) - Burned Tokens
Max Supply = ∞ (no hard cap, but rate-limited per cycle)
```

### Supply Controls
1. **Per-Cycle Limit**: Max 1,000,000 CPT per 30 days
2. **Activity Requirement**: Inactive tokens auto-burn
3. **Utility Consumption**: Usage burns tokens
4. **Gradual Deflation**: More burn than mint over time (expected)

### Example Scenario
```
Month 1: 
- Minted: 800,000 CPT
- Burned (inactive): 50,000 CPT
- Burned (utility): 30,000 CPT
- Circulating: 720,000 CPT

Month 2:
- Minted: 900,000 CPT
- Previous active: 700,000 CPT (20k burned for inactivity)
- Burned (utility): 60,000 CPT
- Circulating: 1,540,000 CPT
```

## 🏛️ Governance (Future)

### Phase 1 (Current): Centralized
- Admin controls minting/burning
- Rewards engine automated
- No token voting

### Phase 2 (Q2 2026): Decentralized
- CPT holders vote on:
  - Reward amounts per action
  - Utility costs
  - Inactivity period duration
  - New feature priorities
- Weight: 1 CPT = 1 vote
- Quorum: 100,000 CPT minimum

## 🚀 Distribution Strategy

### Launch Phase (Q4 2025)
- **Generous Rewards**: Double points for first 3 months
- **Airdrops**: Monthly airdrops to active users
- **Referral Bonuses**: +50 CPT per referred developer
- **Community Events**: Special challenges with bonus rewards

### Growth Phase (2026)
- Gradual reduction of base rewards
- Introduction of premium features
- Staking mechanisms (earn more by locking CPT)
- Cross-platform integration (other Google Cloud tools)

### Mature Phase (2027+)
- Stable reward rates
- Full governance activation
- Ecosystem expansion (DeFi integrations)
- Enterprise tiers (bulk CPT purchasing)

## 🔐 Security & Trust

### Smart Contract Security
- ✅ OpenZeppelin audited contracts
- ✅ Role-based access control
- ✅ Pausable for emergencies
- ✅ Reentrancy protection
- ✅ No owner backdoors

### Transparency
- 📊 All transactions on-chain (Polygon)
- 📈 Real-time analytics dashboard
- 🔍 Open-source contracts (GitHub)
- 📝 Monthly tokenomics reports

### Compliance
- No securities offering (utility token only)
- No ICO/presale (only earn via work)
- Geographic restrictions where required
- KYC for high-value transactions (future)

## 📊 Economic Model

### Value Drivers
1. **Developer Activity**: More usage = more rewards minted
2. **Utility Demand**: Premium features drive consumption
3. **Scarcity**: Burn mechanics reduce supply
4. **Network Effect**: More devs = more value for all

### Deflationary Pressure
```
Long-term expectation: Burn Rate > Mint Rate

Burn sources:
- Inactivity: ~20-30% of supply annually (estimated)
- Utility: ~10-15% of supply annually (estimated)

Result: Gradual supply reduction, increasing token value
```

## 🌍 Ecosystem Integration

### Google Cloud Integration
- CPT usable across ContextPilot suite
- Future: Other Cloud Run tools accept CPT
- Potential: Google Cloud Marketplace listing

### DeFi Integration (Future)
- DEX listing (Uniswap, QuickSwap)
- Liquidity pools (CPT/MATIC, CPT/USDC)
- Lending protocols (borrow against CPT)
- Yield farming opportunities

### Cross-Chain (Future)
- Bridge to Ethereum mainnet
- Integration with other L2s
- Multi-chain rewards tracking

## 📅 Roadmap

### Q4 2025
- ✅ Testnet deployment (Mumbai)
- ✅ Off-chain rewards system
- ✅ Basic minting/burning
- 🔜 Mainnet launch (Polygon)

### Q1 2026
- Token utility features
- Staking mechanisms
- First governance vote
- DEX listing

### Q2 2026
- Full decentralization
- Advanced governance
- Enterprise features
- Cross-platform expansion

### 2027+
- DeFi integrations
- Cross-chain bridges
- Ecosystem partnerships
- Global developer adoption

## 🤝 Community

### Get Involved
- 💬 Discord: community.contextpilot.dev
- 🐦 Twitter: @ContextPilot
- 📧 Newsletter: updates@contextpilot.dev
- 🎮 Hackathons: Monthly challenges

### Resources
- 📖 Documentation: docs.contextpilot.dev
- 🎓 Tutorials: learn.contextpilot.dev
- 📊 Analytics: analytics.contextpilot.dev
- 🔍 Explorer: polygonscan.com/token/[CPT_ADDRESS]

---

**Built for developers, by developers.**  
**Powered by Google Cloud Run + Polygon + AI Agents.**

_Last Updated: October 2025_  
_Version: 1.0.0_

