# 🚰 Sepolia ETH Faucets

Sua wallet: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`

## Faucets Recomendados (mais rápidos)

### 1. 🥇 Alchemy Sepolia Faucet (RECOMENDADO)
- **URL**: https://www.alchemy.com/faucets/ethereum-sepolia
- **Valor**: 0.5 ETH/dia
- **Requer**: Conta Alchemy (gratuita)
- **Tempo**: Instantâneo

### 2. 🥈 QuickNode Faucet
- **URL**: https://faucet.quicknode.com/ethereum/sepolia
- **Valor**: 0.1 ETH
- **Requer**: Conta Discord ou Twitter
- **Tempo**: 1-2 min

### 3. 🥉 Infura Faucet
- **URL**: https://www.infura.io/faucet/sepolia
- **Valor**: 0.5 ETH/dia
- **Requer**: Conta Infura (gratuita)
- **Tempo**: Instantâneo

### 4. Sepolia PoW Faucet
- **URL**: https://sepolia-faucet.pk910.de/
- **Valor**: Variável (mining)
- **Requer**: Nada (PoW no navegador)
- **Tempo**: 5-10 min de mining

## Quanto você precisa?

Para deploy do CPT contract: **~0.01 ETH** é suficiente

## Verificar saldo

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/contracts
cast balance 0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

## Quando tiver fundos

Execute:
```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/contracts
bash scripts/deploy.sh
```

---

**Dica**: Use o faucet da Alchemy - é o mais confiável e rápido! 🚀
