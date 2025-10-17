# 🐛 Firestore/Pub/Sub Issue - Client proxies argument

## Problema

Erro ao aprovar proposals:
```
Client.__init__() got an unexpected keyword argument 'proxies'
```

## Causa

O erro ocorre quando:
1. `FIRESTORE_ENABLED=true` OU `USE_PUBSUB=true`
2. O Git Agent é inicializado para fazer o commit automático
3. Algum cliente Google Cloud (Firestore ou Pub/Sub) está sendo inicializado com argumentos incorretos

## Hipótese

Pode ser incompatibilidade de versões entre:
- `google-cloud-firestore==2.19.0`
- `google-cloud-pubsub==2.18.0`
- Bibliotecas base do Google Cloud

## Solução Temporária

Desabilitar Firestore e Pub/Sub para permitir aprovação manual:

```bash
gcloud run deploy contextpilot-backend \
  --image gcr.io/gen-lang-client-0805532064/contextpilot-backend:latest \
  --region us-central1 \
  --project gen-lang-client-0805532064 \
  --update-env-vars USE_PUBSUB=false,FIRESTORE_ENABLED=false \
  --quiet
```

## Status Atual

✅ **Extension funcionando:**
- Conecta ao backend
- Lista proposals
- Mostra diffs

❌ **Aprovação automática não funciona:**
- Erro ao inicializar Git Agent
- Não executa commits automáticos

## Próximos Passos

1. **Opção A:** Investigar versões compatíveis das bibliotecas Google Cloud
2. **Opção B:** Modificar `GitAgent` para não depender de Pub/Sub
3. **Opção C:** Fazer commits manuais (bypass do Git Agent)

## Workaround

Usar apenas local file storage (sem Firestore/Pub/Sub):
- Proposals salvas em `/app/.contextpilot/workspaces/contextpilot/proposals/*.json`
- Extension pode aprovar, mas sem commit automático
- Usuário precisa fazer commit manual

---

**Data:** 2025-10-16T20:00:00Z
**Status:** 🔍 Investigando
