# 📋 Scripts de Monitoramento de Logs

Scripts para monitorar logs do Cloud Run durante a execução de retrospectives.

## 🎯 Scripts Disponíveis

### 1. `watch-retrospective-logs.sh`
**Monitora logs em tempo real durante uma retrospective**

```bash
./scripts/shell/watch-retrospective-logs.sh
```

- Filtra logs relacionados a retrospective, LLM, Gemini, erros e warnings
- Atualização em tempo real (streaming)
- Cores: Verde (INFO), Amarelo (WARNING), Vermelho (ERROR)
- Pressione `Ctrl+C` para parar

**Uso recomendado:** Execute antes de iniciar uma retrospective e deixe rodando durante a execução.

---

### 2. `watch-all-logs.sh`
**Monitora TODOS os logs do Cloud Run em tempo real**

```bash
./scripts/shell/watch-all-logs.sh
```

- Mostra todos os logs do serviço
- Útil para debug geral
- Atualização em tempo real (streaming)

---

### 3. `get-recent-retrospective-logs.sh`
**Busca logs recentes da retrospective**

```bash
# Últimos 10 minutos (padrão)
./scripts/shell/get-recent-retrospective-logs.sh

# Últimos 30 minutos
./scripts/shell/get-recent-retrospective-logs.sh 30

# Últimos 10 minutos, máximo 50 entradas
./scripts/shell/get-recent-retrospective-logs.sh 10 50
```

**Parâmetros:**
- `$1`: Minutos (padrão: 10)
- `$2`: Limite de entradas (padrão: 100)

---

## 🚀 Como Usar Durante uma Retrospective

### Opção 1: Terminal Separado (Recomendado)

1. **Abra um terminal e inicie o monitoramento:**
   ```bash
   cd /home/fsegall/Desktop/New_Projects/google-context-pilot
   ./scripts/shell/watch-retrospective-logs.sh
   ```

2. **Em outro terminal, inicie a retrospective:**
   - Via extensão VS Code, ou
   - Via API:
     ```bash
     curl -X POST "https://YOUR-BACKEND-URL/agents/retrospective/trigger" \
       -H "Content-Type: application/json" \
       -d '{"trigger": "manual", "use_llm": true, "trigger_topic": "Seu tópico aqui"}'
     ```

3. **Observe os logs em tempo real no primeiro terminal**

### Opção 2: Logs Após a Execução

```bash
# Ver logs dos últimos 15 minutos
./scripts/shell/get-recent-retrospective-logs.sh 15
```

---

## 📊 O Que Procurar nos Logs

### ✅ Sinais de Sucesso

- `[API] Gemini API key found, will generate LLM summary`
- `[RetrospectiveAgent] ✅ LLM summary generated successfully`
- `[RetrospectiveAgent] Saved retrospective to ...`
- `[API] Retrospective completed: retro-XXXXXX`

### ⚠️ Sinais de Problemas

- `[API] LLM synthesis requested (use_llm=True) but no API key found`
- `[RetrospectiveAgent] ❌ Gemini API error`
- `[API] Retrospective timeout`
- `ERROR` ou `WARNING` com mensagens relacionadas

---

## 🔧 Troubleshooting

### Script não funciona

1. **Verifique se o projeto está configurado:**
   ```bash
   gcloud config get-value project
   ```

2. **Verifique se está autenticado:**
   ```bash
   gcloud auth list
   ```

3. **Verifique permissões:**
   ```bash
   gcloud projects get-iam-policy $(gcloud config get-value project)
   ```

### Comando `tail` não disponível

Os scripts tentam usar `gcloud beta logging tail` primeiro, depois `gcloud alpha logging tail`, e se nenhum estiver disponível, usam um modo de polling (verifica logs a cada 5 segundos).

**Se você receber erro sobre `tail` não estar disponível:**
- O script automaticamente usará o modo de polling
- Ou instale o componente beta: `gcloud components install beta`
- Ou use o modo de polling manualmente verificando logs recentes:
  ```bash
  ./scripts/shell/get-recent-retrospective-logs.sh 5
  ```

### Logs não aparecem

- Aguarde alguns segundos (pode haver delay)
- Verifique se o serviço está rodando:
  ```bash
  gcloud run services describe contextpilot-backend --region us-central1
  ```

### Filtro muito restritivo

Use `watch-all-logs.sh` para ver todos os logs e filtrar manualmente.

---

## 📝 Exemplo de Saída

```
🔍 Watching Retrospective Logs
Project: gen-lang-client-0805532064
Service: contextpilot-backend
Region: us-central1

Press Ctrl+C to stop watching

[2025-11-10T21:00:10Z] [INFO] [API] Starting retrospective process...
[2025-11-10T21:00:10Z] [INFO] [RetrospectiveAgent] Starting retrospective (trigger: manual, topic: ...)
[2025-11-10T21:00:16Z] [INFO] [RetrospectiveAgent] Calling Gemini for agent discussion...
[2025-11-10T21:00:21Z] [INFO] [RetrospectiveAgent] Got 6 perspectives from LLM
[2025-11-10T21:00:34Z] [INFO] [RetrospectiveAgent] Saved retrospective to /app/.contextpilot/workspaces/contextpilot/retrospectives
[2025-11-10T21:00:49Z] [INFO] [API] Retrospective completed: retro-20251110-210034
```

---

## 🎯 Dicas

1. **Deixe o script rodando em um terminal separado** enquanto trabalha
2. **Use cores** para identificar rapidamente erros (vermelho) e warnings (amarelo)
3. **Procure por timestamps** para rastrear o progresso da retrospective
4. **Se a retrospective travar**, os logs mostrarão onde parou

