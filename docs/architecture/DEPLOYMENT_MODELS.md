# 🏗️ ContextPilot Deployment Models

Como os usuários acessam os recursos do GCP e qual modelo de deployment usar.

---

## 🎯 Visão Geral

Existem **3 modelos** principais de deployment para ContextPilot:

1. **SaaS Model** (Recomendado) - Instância central hospedada
2. **Self-Hosted** - Cada usuário/empresa deploys sua instância
3. **Hybrid** - Freemium SaaS + Self-hosted enterprise

---

## 📊 Comparação de Modelos

| Aspecto | SaaS | Self-Hosted | Hybrid |
|---------|------|-------------|--------|
| **Usuário precisa conta GCP?** | ❌ Não | ✅ Sim | Depende |
| **Setup complexity** | Muito fácil | Complexo | Médio |
| **Custo para usuário** | Subscription | GCP + Manutenção | Variado |
| **Privacidade de código** | Central | Total | Configurável |
| **Escala** | Gerenciada | Manual | Mista |
| **Ideal para** | Indie devs | Enterprises | Todos |

---

## 🌐 Modelo 1: SaaS (RECOMENDADO)

### Arquitetura

```
┌─────────────────────────────────────────────┐
│         Usuários (Sem conta GCP)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ VSCode   │  │ VSCode   │  │ VSCode   │  │
│  │Extension │  │Extension │  │Extension │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼─────────┘
        │             │             │
        │   HTTPS (Autenticado)     │
        ▼             ▼             ▼
┌─────────────────────────────────────────────┐
│      ContextPilot SaaS (Cloud Run)          │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  API Gateway (Load Balanced)         │  │
│  │  contextpilot.io/api                 │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Backend Services (Cloud Run)        │  │
│  │  - Multi-tenant                      │  │
│  │  - Isolated workspaces per user     │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │  Shared Infrastructure               │  │
│  │  - Pub/Sub (multi-tenant)            │  │
│  │  - Firestore (per-user collections)  │  │
│  │  - Cloud Storage (isolated buckets)  │  │
│  └──────────────────────────────────────┘  │
│                                             │
│        Operado por: ContextPilot Inc.       │
│        GCP Project: contextpilot-prod       │
└─────────────────────────────────────────────┘
```

### Como Funciona

1. **Usuário instala extensão** do VSCode Marketplace
2. **Primeiro uso**: Sign up em `contextpilot.io`
   - Email + senha OU
   - OAuth (GitHub, Google, etc.)
3. **Extensão se conecta** via API key
4. **Backend gerencia** toda infraestrutura GCP
5. **Usuário não precisa** de conta GCP

### Autenticação

```typescript
// Na extensão
const apiKey = await context.secrets.get('contextpilot.apiKey');
const client = new ContextPilotClient(apiKey);

// No backend (FastAPI)
@app.get("/proposals")
async def get_proposals(
    api_key: str = Header(..., alias="X-API-Key")
):
    user = await verify_api_key(api_key)
    # Retorna dados isolados do usuário
```

### Vantagens
- ✅ **Zero setup** - Funciona imediatamente
- ✅ **Sem custos GCP** para usuário
- ✅ **Manutenção centralizada**
- ✅ **Escalabilidade automática**
- ✅ **Updates instantâneos**

### Desvantagens
- ❌ Código passa pelo servidor central
- ❌ Depende de conectividade
- ❌ Custo recorrente (subscription)

### Pricing Sugerido
```
Free Tier:
  - 100 proposals/mês
  - 1,000 CPT tokens
  - Community support

Pro: $9/mês
  - Unlimited proposals
  - 10,000 CPT/mês
  - Priority support

Team: $49/mês (até 10 devs)
  - Everything in Pro
  - Team analytics
  - Shared context

Enterprise: Custom
  - Self-hosted option
  - SLA garantido
  - White-label
```

---

## 🏠 Modelo 2: Self-Hosted

### Arquitetura

```
┌──────────────────────────────────────┐
│    Empresa XYZ (Com conta GCP)       │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  VSCode Extensions (Team)      │ │
│  │  ├─ Dev 1                       │ │
│  │  ├─ Dev 2                       │ │
│  │  └─ Dev 3                       │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│           │ Private Network/VPN      │
│           ▼                          │
│  ┌────────────────────────────────┐ │
│  │  GCP Project: xyz-contextpilot │ │
│  │                                │ │
│  │  - Cloud Run Services          │ │
│  │  - Pub/Sub                     │ │
│  │  - Firestore                   │ │
│  │  - Cloud Storage               │ │
│  │  - Secret Manager              │ │
│  │                                │ │
│  │  Gerenciado por: Empresa XYZ   │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### Setup

1. **Create GCP Project**
```bash
gcloud projects create xyz-contextpilot
gcloud config set project xyz-contextpilot
```

2. **Enable APIs**
```bash
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com
```

3. **Deploy Backend**
```bash
cd infra
bash setup-all.sh

cd ../back-end
gcloud run deploy contextpilot-api \
  --source . \
  --region us-central1
```

4. **Configure Extension**
```json
// settings.json
{
  "contextpilot.apiUrl": "https://contextpilot-api-xxx.run.app",
  "contextpilot.userId": "dev@company.com"
}
```

### Vantagens
- ✅ **Privacidade total** - Código nunca sai da empresa
- ✅ **Controle completo** - Customização ilimitada
- ✅ **Compliance** - HIPAA, SOC2, etc.
- ✅ **Integração interna** - VPN, SSO, etc.

### Desvantagens
- ❌ Requer expertise GCP
- ❌ Custos de infraestrutura
- ❌ Manutenção manual
- ❌ Setup complexo

---

## 🔄 Modelo 3: Hybrid (Freemium + Enterprise)

### Arquitetura

```
┌─────────────────────────────────────────────┐
│          Free/Pro Users                     │
│  Conectam a: contextpilot.io                │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│       SaaS Instance (Multi-tenant)          │
│  - Free tier: 100 proposals/mês             │
│  - Pro tier: Unlimited                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│          Enterprise Customers               │
│  Cada um com sua instância                  │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│    Self-Hosted Instances (Isolated)         │
│  ├─ Company A (GCP Project A)               │
│  ├─ Company B (GCP Project B)               │
│  └─ Company C (GCP Project C)               │
└─────────────────────────────────────────────┘
```

### Como Funciona

1. **Usuário começa no Free Tier** (SaaS)
2. **Upgrade para Pro** se precisar mais recursos
3. **Enterprise pode migrar** para self-hosted mantendo dados
4. **White-label option** para enterprises

### Migration Path
```
Free (SaaS)
   ↓ $9/mês
Pro (SaaS)
   ↓ Custom pricing
Enterprise (Self-hosted)
   ↓ Custom
White-label (Self-hosted + Rebrand)
```

---

## 🔐 Autenticação e Segurança

### SaaS Model

#### User Authentication
```python
# Backend: FastAPI + Supabase Auth
from fastapi import Depends, HTTPException
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_current_user(token: str = Header(...)):
    user = supabase.auth.get_user(token)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user
```

#### API Keys
```python
# Gerado no primeiro login
api_key = secrets.token_urlsafe(32)
await db.api_keys.insert({
    "user_id": user.id,
    "key": hash_api_key(api_key),
    "created_at": datetime.now()
})
```

#### Extension → Backend
```typescript
// Extension armazena token de forma segura
await context.secrets.store('contextpilot.token', token);

// Todas requests incluem token
const response = await axios.get('/api/proposals', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Self-Hosted Model

#### IAM Authentication
```python
# Backend verifica IAM do GCP
from google.auth.transport import requests
from google.oauth2 import id_token

def verify_gcp_token(token: str):
    request = requests.Request()
    id_info = id_token.verify_oauth2_token(
        token, request
    )
    return id_info['email']
```

#### Service Accounts
```bash
# Criar service account para extensão
gcloud iam service-accounts create contextpilot-extension
gcloud iam service-accounts keys create key.json \
  --iam-account=contextpilot-extension@project.iam.gserviceaccount.com
```

---

## 💰 Custos (Estimativas)

### SaaS Model (Para o operador)

**Por 1,000 usuários ativos:**
- Cloud Run: ~$50/mês (autoscale)
- Pub/Sub: ~$10/mês
- Firestore: ~$30/mês
- Cloud Storage: ~$5/mês
- Load Balancer: ~$20/mês
- **Total**: ~$115/mês = $0.12/usuário

**Receita potencial:**
- 800 Free users: $0
- 150 Pro users ($9): $1,350
- 50 Team users ($49): $2,450
- **Total**: $3,800/mês
- **Margem**: $3,685/mês (~97%)

### Self-Hosted (Para empresa)

**Empresa com 50 devs:**
- Cloud Run: ~$30/mês
- Pub/Sub: ~$5/mês
- Firestore: ~$10/mês
- Cloud Storage: ~$3/mês
- **Total**: ~$48/mês = $0.96/dev

**vs Subscriptions:**
- Pro tier: $9 × 50 = $450/mês
- **Economia**: $402/mês (~89%)

---

## 🚀 Recomendação para Hackathon

### Fase 1: Demo (Agora)
```
✅ Deploy SaaS instance no GCP
✅ URL pública: demo.contextpilot.io
✅ Free tier ilimitado (temporário)
✅ Sem autenticação (API aberta)
✅ Foco: demonstrar funcionalidade
```

### Fase 2: Beta (Pós-hackathon)
```
✅ Implementar autenticação (Supabase)
✅ API keys
✅ Free tier: 100 proposals/mês
✅ Coletar feedback
```

### Fase 3: Launch (Production)
```
✅ Pro tier ($9/mês)
✅ Self-hosted docs completos
✅ Enterprise offering
✅ Marketplace listing
```

---

## 📋 Checklist de Deployment

### SaaS Setup
- [ ] Create production GCP project
- [ ] Setup custom domain (contextpilot.io)
- [ ] Configure Cloud Run services
- [ ] Setup Supabase for auth
- [ ] Implement API key system
- [ ] Configure rate limiting
- [ ] Setup monitoring (Cloud Logging)
- [ ] Create pricing page
- [ ] Implement billing (Stripe)

### Self-Hosted Docs
- [ ] Write deployment guide
- [ ] Create Terraform templates
- [ ] Document IAM setup
- [ ] Provide cost calculator
- [ ] Create troubleshooting guide
- [ ] Setup support channel

---

## 🔗 Próximos Passos

1. **Hackathon Demo**: Deploy SaaS simples
2. **Documentar**: Criar guias para ambos modelos
3. **Decidir**: Qual modelo priorizar
4. **Implementar**: Auth + API keys
5. **Testar**: Com beta users

---

**Recomendação Final**: 
- 🎯 **Para hackathon**: SaaS simples (demo.contextpilot.io)
- 🚀 **Para lançamento**: Hybrid (Free SaaS + Paid self-hosted)
- 💼 **Para enterprise**: Self-hosted com suporte

---

**Last Updated**: 2025-10-14  
**Status**: Architecture defined, ready to implement

