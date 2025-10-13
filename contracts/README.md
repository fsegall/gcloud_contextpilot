# CPT Smart Contract

Context Pilot Token (CPT) - ERC-20 token for developer incentives in the ContextPilot ecosystem.

## Features

- ✅ **ERC-20 Standard**: Full compatibility with wallets and DEXs
- ✅ **Role-Based Access**: Minter and Burner roles for automation
- ✅ **Monthly Cycles**: Supply resets every 30 days to control inflation
- ✅ **Auto-Burn**: Inactive accounts (30+ days) can be burned
- ✅ **Pausable**: Emergency stop mechanism
- ✅ **Activity Tracking**: Automatic timestamp updates on transfers

## Architecture

```
Off-chain (Firestore) → Batch Mint → On-chain (Polygon)
                                          ↓
                                    CPT Contract
                                          ↓
                            User Wallets (RainbowKit)
```

## Setup

### 1. Install Dependencies

```bash
cd contracts
curl -L https://foundry.paradigm.xyz | bash
foundryup
forge install OpenZeppelin/openzeppelin-contracts
```

### 2. Compile

```bash
forge build
```

### 3. Test

```bash
forge test -vv
```

### 4. Deploy to Mumbai Testnet

```bash
# Set environment variables
export PRIVATE_KEY="your_private_key"
export POLYGONSCAN_API_KEY="your_api_key"

# Deploy
forge script script/Deploy.s.sol:DeployCPT \
  --rpc-url mumbai \
  --broadcast \
  --verify
```

### 5. Export ABI

```bash
# Extract ABI for Python backend
forge inspect CPT abi > ../back-end/app/adapters/rewards/CPT_ABI.json
```

## Contract Interface

### Minting (Rewards Engine)

```solidity
function mint(address to, uint256 amount) external;
```

### Burning (Inactivity)

```solidity
function burnInactive(address account) external;
function isInactive(address account) external view returns (bool);
```

### Cycle Management

```solidity
function renewCycle() external;
function timeUntilRenewal() external view returns (uint256);
```

## Token Economics

| Parameter | Value |
|-----------|-------|
| Max Supply per Cycle | 1,000,000 CPT |
| Cycle Duration | 30 days |
| Inactivity Period | 30 days |
| Decimals | 18 |

## Security

- ✅ OpenZeppelin contracts (audited)
- ✅ Role-based access control
- ✅ Pausable for emergencies
- ✅ Reentrancy protection (via OpenZeppelin)
- ✅ Supply caps per cycle

## Roles

- `DEFAULT_ADMIN_ROLE`: Can manage roles, pause, renew cycles
- `MINTER_ROLE`: Can mint tokens (assigned to rewards engine)
- `BURNER_ROLE`: Can burn inactive accounts (assigned to cleanup worker)

## Testnet Addresses

| Network | Contract Address |
|---------|-----------------|
| Mumbai  | TBD (after deployment) |
| Polygon | TBD (mainnet launch Q1 2026) |

## Integration with Backend

The Python backend uses `web3.py` to interact with this contract via the `BlockchainRewardsAdapter`.

See: `back-end/app/adapters/rewards/blockchain_rewards.py`

