# Pub/Sub Push Subscriptions Setup

Este guia explica como configurar as push subscriptions do Google Cloud Pub/Sub para o ContextPilot.

## Visão Geral

O ContextPilot usa Google Cloud Pub/Sub para comunicação entre agentes. Quando um agente publica um evento, ele é enviado para um tópico do Pub/Sub. As push subscriptions configuram o Pub/Sub para enviar esses eventos automaticamente para o endpoint `/events` do Cloud Run.

## Pré-requisitos

1. Google Cloud Project configurado
2. Cloud Run service deployado
3. `gcloud` CLI instalado e autenticado
4. Permissões necessárias no projeto

## Configuração Automática

Execute o script de setup:

```bash
cd back-end
./setup-pubsub-push.sh
```

O script irá:
1. ✅ Habilitar a API do Pub/Sub
2. ✅ Criar todos os tópicos necessários
3. ✅ Criar push subscriptions apontando para o Cloud Run
4. ✅ Configurar permissões (Pub/Sub → Cloud Run)
5. ✅ Exibir resumo da configuração

## Configuração Manual

Se preferir configurar manualmente:

### 1. Criar Tópicos

```bash
PROJECT_ID="gen-lang-client-0805532064"
gcloud pubsub topics create git-events --project=$PROJECT_ID
gcloud pubsub topics create proposal-events --project=$PROJECT_ID
gcloud pubsub topics create spec-events --project=$PROJECT_ID
# ... (outros tópicos)
```

### 2. Obter URL do Cloud Run

```bash
SERVICE_URL=$(gcloud run services describe contextpilot-backend \
  --region us-central1 \
  --project $PROJECT_ID \
  --format='value(status.url)')
PUSH_ENDPOINT="${SERVICE_URL}/events"
```

### 3. Criar Push Subscription

```bash
gcloud pubsub subscriptions create git-events-sub \
  --topic=git-events \
  --project=$PROJECT_ID \
  --push-endpoint=$PUSH_ENDPOINT \
  --ack-deadline=60 \
  --message-retention-duration=7d
```

### 4. Configurar Permissões

O Pub/Sub precisa de permissão para invocar o Cloud Run:

```bash
gcloud run services add-iam-policy-binding contextpilot-backend \
  --region us-central1 \
  --project $PROJECT_ID \
  --member="serviceAccount:service-$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

## Testando

### 1. Publicar um evento de teste

```bash
echo '{"event_type":"git.commit.v1","data":{"workspace_id":"contextpilot","commit_hash":"test123"}}' | \
gcloud pubsub topics publish git-events --message-file=- --project=$PROJECT_ID
```

### 2. Verificar logs do Cloud Run

```bash
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=contextpilot-backend' \
  --limit 20 \
  --project=$PROJECT_ID
```

Você deve ver logs como:
- `[route_event] Routing git.commit.v1 to agents...`
- `[Spec Agent] Received event: git.commit.v1`
- `[Spec Agent] Processing commit test123`

## Troubleshooting

### Eventos não estão chegando aos agentes

1. **Verificar se as subscriptions existem:**
   ```bash
   gcloud pubsub subscriptions list --project=$PROJECT_ID
   ```

2. **Verificar se o push endpoint está correto:**
   ```bash
   gcloud pubsub subscriptions describe git-events-sub --project=$PROJECT_ID
   ```

3. **Verificar permissões:**
   ```bash
   gcloud run services get-iam-policy contextpilot-backend \
     --region us-central1 \
     --project $PROJECT_ID
   ```

4. **Verificar logs do Pub/Sub:**
   ```bash
   gcloud logging read 'resource.type=pubsub_subscription' --limit 20 --project=$PROJECT_ID
   ```

### Erro 403 ao criar subscription

Certifique-se de que:
- O serviço do Cloud Run está deployado
- A URL do push endpoint está correta
- As permissões do Pub/Sub estão configuradas

### Eventos chegam mas agentes não processam

1. Verificar se o `route_event` está funcionando (logs do Cloud Run)
2. Verificar se os agentes estão inicializados corretamente
3. Verificar se os agentes têm subscriptions corretas para o tipo de evento

## Arquitetura

```
Agent publica evento → Pub/Sub Topic → Push Subscription → Cloud Run /events → route_event → Agents.handle_event
```

## Subscriptions Criadas

O script cria uma subscription por tópico:

- `git-events-sub` → `git-events`
- `proposal-events-sub` → `proposal-events`
- `spec-events-sub` → `spec-events`
- `strategy-events-sub` → `strategy-events`
- `coach-events-sub` → `coach-events`
- `retrospective-events-sub` → `retrospective-events`
- `milestone-events-sub` → `milestone-events`
- `context-events-sub` → `context-events`
- `artifact-events-sub` → `artifact-events`
- `reward-events-sub` → `reward-events`

Todas as subscriptions enviam eventos para o mesmo endpoint: `https://contextpilot-backend-.../events`

O `route_event` então roteia os eventos para os agentes apropriados baseado no tipo de evento.

