# 🚰 Como Conseguir Sepolia ETH (SEM saldo mainnet)

Sua wallet: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`

---

## ⚡ OPÇÃO MAIS RÁPIDA: Google Cloud Web3 Faucet

Você já tem conta Google Cloud ativa!

1. **Acesse**: https://cloud.google.com/application/web3/faucet/ethereum/sepolia
2. **Cole o endereço**: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`
3. **Receba**: 0.05 ETH instantaneamente

✅ **Sem restrições de saldo**
✅ **Instantâneo**
✅ **Você já está autenticado**

---

## 🔄 OPÇÃO 2: PoW Mining Faucet (100% sem restrições)

Se o Google Cloud não funcionar:

1. **Acesse**: https://sepolia-faucet.pk910.de/
2. **Cole**: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`
3. **Clique em "Start Mining"**
4. **Aguarde 10-15 minutos** (deixe a aba aberta)
5. **Pare e reclame os fundos**

✅ Não requer conta
✅ Não requer saldo mainnet
✅ Não requer social media
⏱️ Demora ~15 min, mas é garantido

---

## 🔗 OPÇÃO 3: Chainlink Faucet (GitHub/Google)

1. **Acesse**: https://faucets.chain.link/sepolia
2. **Login com GitHub ou Google**
3. **Cole**: `0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb`
4. **Receba**: 0.1 ETH

---

## ✅ Verificar Saldo Depois

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/contracts
cast balance 0x1b554a295785a4BfdE8d72Baa4E1793D5b35e2bb --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

Quando aparecer um valor > 0, pode fazer deploy:

```bash
bash scripts/deploy.sh
```

---

**🎯 Recomendação**: Tente primeiro o **Google Cloud Faucet** (você já está logado) e se não funcionar, use o **PoW Faucet** (100% garantido).
