# 🎯 Extension Pronta para Teste!

## ✅ Atualizações Concluídas

Todas as URLs foram atualizadas para o novo Cloud Run:

### Arquivos Atualizados
- ✅ `extension/package.json` - Default apiUrl
- ✅ `extension/src/extension.ts` - Fallback URL
- ✅ `.vscode/settings.json` - Workspace settings

### Nova URL da API
```
https://contextpilot-backend-581368740395.us-central1.run.app
```

## 🔧 Como Testar

### 1. Recarregar a Extension

**Opção A: Fechar e reabrir o Extension Development Host**
1. Feche qualquer janela Extension Development Host aberta
2. No Cursor principal, vá para a pasta `extension/`
3. Pressione `F5` para abrir uma nova instância

**Opção B: Reload Window**
1. No Extension Development Host, pressione `Ctrl+Shift+P`
2. Digite `Reload Window` e pressione Enter

### 2. Verificar Conexão

Após recarregar, você deve ver no Output Console:
```
[ContextPilot] Extension activated - API: https://contextpilot-backend-581368740395.us-central1.run.app
[ContextPilot] Auto-connect completed
```

### 3. Testar Funcionalidades

#### A. Listar Proposals
1. Abra a sidebar do ContextPilot (ícone 🚀)
2. Expanda "Change Proposals"
3. Você deve ver as proposals do Firestore

#### B. Criar Nova Proposal
1. Execute o comando: `ContextPilot: Create Proposals`
2. Aguarde ~5-10 segundos (Gemini está gerando)
3. Verifique se novas proposals aparecem

#### C. Ver Diff de Proposal
1. Clique em uma proposal
2. Deve abrir o diff completo gerado pelo Gemini
3. Opções: Review com Claude, Approve, Reject

### 4. Troubleshooting

Se ainda der erro 503:

```bash
# Verifique se o Cloud Run está respondendo
curl https://contextpilot-backend-581368740395.us-central1.run.app/health

# Deve retornar:
# {"status":"ok","version":"2.0.0","agents":[...]}
```

Se o Cloud Run não responder:
```bash
# Force restart do serviço
gcloud run services update contextpilot-backend \
  --region us-central1 \
  --project gen-lang-client-0805532064 \
  --no-traffic
  
gcloud run services update contextpilot-backend \
  --region us-central1 \
  --project gen-lang-client-0805532064 \
  --to-latest
```

## 📊 Testando a API Diretamente

```bash
# 1. Health Check
curl https://contextpilot-backend-581368740395.us-central1.run.app/health

# 2. Listar Proposals
curl "https://contextpilot-backend-581368740395.us-central1.run.app/proposals?workspace_id=contextpilot" | jq .

# 3. Criar Proposals (vai usar Gemini, demora ~5s)
curl -X POST "https://contextpilot-backend-581368740395.us-central1.run.app/proposals/create?workspace_id=contextpilot" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .
```

## 🎉 O Que Esperar

### Proposals com Gemini
- Títulos: "Docs issue: ARCHITECTURE.md", "Docs issue: README.md"
- Diffs completos (~4000-5000 chars)
- Conteúdo de alta qualidade gerado por IA
- Estrutura profissional (mermaid diagrams, seções, etc)

### Backend Funcionando
- ✅ Firestore persistindo dados
- ✅ Pub/Sub publicando eventos
- ✅ Gemini gerando conteúdo
- ✅ Diffs unificados completos

---

**Projeto:** ContextPilot
**Ambiente:** Produção (GCP `gen-lang-client-0805532064`)
**Status:** ✅ PRONTO PARA TESTE
**Data:** 2025-10-16
