# ✅ E2E Checklist - Final Steps to MVP

## 🎯 Status Atual
- ✅ Ask Claude feature implementada
- ✅ Workflow GitHub Actions atualizado para sandbox
- ✅ Configuração de repos na extensão implementada
- ✅ Development Agent salvando proposals no Firestore (modo cloud)
- ✅ 10 proposals aprovadas encontradas

## 📋 Checklist de Verificação

### 1. GitHub Actions Secrets (Repositório Principal)
Verificar em: `Settings → Secrets and variables → Actions`

- [ ] **`SANDBOX_REPO_TOKEN`**: Token com permissão `repo` no repositório de sandbox
- [ ] **`GITHUB_TOKEN`**: Token com permissão `repo` e `workflow` (já configurado)

**Comando para verificar se o workflow está configurado:**
```bash
# Verificar workflows no repositório
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/fsegall/gcloud_contextpilot/actions/workflows
```

### 2. Cloud Run Environment Variables
Verificar em: Cloud Console → Cloud Run → contextpilot-backend → Variables

**Variáveis obrigatórias:**
- [ ] **`GITHUB_TOKEN`**: Token para disparar workflows (via Secret Manager: `github-token`)
- [ ] **`GITHUB_REPO`**: `fsegall/gcloud_contextpilot`
- [ ] **`SANDBOX_REPO_URL`**: URL do repositório de sandbox (ex: `https://github.com/fsegall/contextpilot-sandbox`)
- [ ] **`CODESPACES_ENABLED`**: `true` ou `false`
- [ ] **`GEMINI_API_KEY`**: Chave da API Gemini (via Secret Manager: `gemini-api-key`)
- [ ] **`STORAGE_MODE`**: `cloud` (deve estar como `cloud` em produção)
- [ ] **`EVENT_BUS_MODE`**: `pubsub`

**Comando para verificar:**
```bash
gcloud run services describe contextpilot-backend \
  --project=gen-lang-client-0805532064 \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### 3. Verificar Workflows Disparados
**URL:** https://github.com/fsegall/gcloud_contextpilot/actions/workflows/apply-proposal.yml

Verificar se:
- [ ] Os últimos 4-10 approvals dispararam workflows
- [ ] Workflows completaram com sucesso (verde)
- [ ] PRs foram criados (sandbox e/ou main)

### 4. Verificar Proposals no Firestore
**Comando:**
```bash
API="https://contextpilot-backend-581368740395.us-central1.run.app"
WS="contextpilot"
curl -sS "${API}/proposals/list?workspace_id=${WS}&user_id=system&status=approved" | \
  jq -r '.proposals[] | [.id, .status, (.metadata.sandbox_branch // "N/A")] | @tsv'
```

### 5. Teste E2E Completo
**Passos:**
1. [ ] Criar nova retrospectiva via extensão
2. [ ] Aguardar Development Agent gerar proposal (sandbox)
3. [ ] Verificar que proposal foi salva no Firestore com `metadata.sandbox_branch`
4. [ ] Usar "Ask Claude" para revisar proposal
5. [ ] Aprovar proposal
6. [ ] Verificar que workflow foi disparado
7. [ ] Verificar que PR foi criado no sandbox repo
8. [ ] Verificar que PR cross-repo foi criado no main repo

## 🔧 Comandos Úteis

### Atualizar env vars no Cloud Run
```bash
gcloud run services update contextpilot-backend \
  --project=gen-lang-client-0805532064 \
  --region=us-central1 \
  --set-env-vars=GITHUB_REPO=fsegall/gcloud_contextpilot,SANDBOX_REPO_URL=https://github.com/fsegall/contextpilot-sandbox,CODESPACES_ENABLED=true,STORAGE_MODE=cloud,EVENT_BUS_MODE=pubsub \
  --set-secrets=GITHUB_TOKEN=github-token:latest,GEMINI_API_KEY=gemini-api-key:latest
```

### Ver logs do backend (proposal approvals)
```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="contextpilot-backend" AND jsonPayload.message:"proposal approved"' --project=gen-lang-client-0805532064 --limit=20 --format='table(timestamp, severity, jsonPayload.message)'
```

### Ver logs de GitHub dispatch
```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="contextpilot-backend" AND jsonPayload.message:"GitHub Action"' --project=gen-lang-client-0805532064 --limit=20 --format='table(timestamp, severity, jsonPayload.message)'
```

## 🐛 Problemas Comuns

### Workflow não dispara após approval
- **Causa:** `GITHUB_TOKEN` ausente ou sem permissão `workflow`
- **Solução:** Verificar secret no Cloud Run e permissões do token

### PR não é criado no sandbox
- **Causa:** `SANDBOX_REPO_TOKEN` ausente no GitHub Secrets ou sem permissão `repo`
- **Solução:** Adicionar token com acesso ao sandbox repo

### Proposal não encontrada no workflow
- **Causa:** Proposal salva em modo `local` em vez de `cloud`
- **Solução:** Verificar `STORAGE_MODE=cloud` no Cloud Run e que Dev Agent usa `get_config().is_cloud_storage`

## ✅ Próximos Passos

1. Verificar todos os itens acima
2. Executar teste E2E completo
3. Se tudo funcionar, MVP está pronto para submissão! 🚀


