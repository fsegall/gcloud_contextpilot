# 🤝 Agent Autonomy & Developer Control

## Philosophy

**"Agents suggest, developers approve. Always."**

ContextPilot não é um sistema autônomo que modifica código sem permissão. É um **assistente inteligente** que propõe mudanças, explica o porquê, e aguarda aprovação humana.

---

## 🎯 Níveis de Autonomia

### ✅ Nível 0: Full Control (Default)
**Agentes podem:**
- ✅ Ler código
- ✅ Analisar arquitetura
- ✅ Gerar sugestões
- ✅ Atualizar documentação (markdown)
- ✅ Criar checkpoints

**Agentes NÃO podem:**
- ❌ Modificar código `.py`, `.ts`, `.js`
- ❌ Fazer commits automáticos
- ❌ Deletar arquivos
- ❌ Mudar configurações críticas

### ⚠️ Nível 1: Assisted (Opt-in)
**Com aprovação explícita:**
- ⚠️ Aplicar refactorings sugeridos
- ⚠️ Adicionar testes gerados
- ⚠️ Atualizar dependencies

**Requer:**
- Preview completo do diff
- Confirmação do dev
- Possibilidade de editar antes de aplicar

### 🔒 Nível 2: Watched (Futuro)
**Para casos específicos:**
- 🔒 Auto-fix de linting
- 🔒 Format code
- 🔒 Update docs após commit

**Requer:**
- Whitelist de ações permitidas
- Rollback automático se CI falha
- Notificação sempre

---

## 📋 Change Proposal System

### Conceito

Quando Strategy ou Spec Agent identifica uma melhoria, em vez de modificar código diretamente, cria um **Change Proposal**.

### Estrutura

```json
{
  "proposal_id": "cp_001",
  "created_at": "2025-10-13T15:00:00Z",
  "agent": "strategy-agent",
  "type": "refactor",
  "title": "Extract AuthService",
  "description": "Auth logic is duplicated across 3 files. Extracting to a service improves maintainability.",
  "impact": {
    "files_affected": 4,
    "lines_added": 50,
    "lines_removed": 120,
    "test_coverage": "maintained",
    "breaking_changes": false
  },
  "changes": [
    {
      "file": "src/auth/login.py",
      "action": "modify",
      "diff": "@@ -10,30 +10,8 @@ ...",
      "reason": "Remove duplicated auth logic"
    },
    {
      "file": "src/services/auth_service.py",
      "action": "create",
      "content": "class AuthService:\n    def authenticate...",
      "reason": "Centralize auth logic"
    }
  ],
  "benefits": [
    "Reduce duplication from 3x to 1x",
    "Easier to test (mock single service)",
    "Single source of truth for auth"
  ],
  "risks": [
    "Need to update imports in 8 files",
    "Potential merge conflicts if auth code changes"
  ],
  "estimated_time": "45 minutes",
  "status": "pending_approval",
  "preview_branch": "agent/refactor-auth-service"
}
```

### Workflow

```
1. Strategy Agent analisa código
   ↓
2. Identifica oportunidade de melhoria
   ↓
3. Cria Change Proposal (não altera código)
   ↓
4. Envia para IDE Extension
   ↓
5. Dev recebe notificação no VSCode/Cursor
   ↓
6. Dev abre preview side-by-side
   ↓
7. Dev pode: Approve | Edit | Reject
   ↓
8. Se aprovado: Agent cria branch + commit
   ↓
9. Dev revisa PR normalmente
```

---

## 🔌 IDE Integration

### VSCode/Cursor Extension

**Nome:** `contextpilot-ide`

**Features:**

#### 1. Change Proposals Panel
```
┌─ CONTEXTPILOT PROPOSALS ──────┐
│                               │
│ 🟢 Extract AuthService        │
│    Strategy Agent • 45min     │
│    └─ 4 files • +50 -120     │
│    [Preview] [Apply] [Reject] │
│                               │
│ 🟡 Update API docs            │
│    Spec Agent • 15min         │
│    └─ 1 file • +30 -5        │
│    [Preview] [Apply] [Reject] │
│                               │
│ 🔴 Security: Validate input   │
│    Strategy Agent • 30min     │
│    └─ 2 files • +15 -0       │
│    [Preview] [Apply] [Reject] │
└───────────────────────────────┘
```

#### 2. Inline Suggestions
```python
# src/auth/login.py

def login(username, password):
    # [💡 Strategy Agent suggests: Extract to AuthService]
    # [Click to preview]
    if not username or not password:
        return False
    ...
```

#### 3. Diff Preview
Quando dev clica "Preview":
```
┌─ PREVIEW: Extract AuthService ────────────────┐
│                                                │
│ src/auth/login.py                             │
│ ─────────────────                             │
│ - def login(username, password):              │
│ -     if not username or not password:        │
│ -         return False                        │
│ +     return AuthService.authenticate(        │
│ +         username, password                  │
│ +     )                                       │
│                                                │
│ src/services/auth_service.py (NEW)           │
│ ──────────────────────────────                │
│ + class AuthService:                          │
│ +     @staticmethod                           │
│ +     def authenticate(username, password):   │
│ +         if not username or not password:    │
│ +             return False                    │
│ +         ...                                 │
│                                                │
│ [✓ Apply All] [Edit First] [✗ Reject]        │
└────────────────────────────────────────────────┘
```

#### 4. Coach Nudges
```
┌─ 🧘 COACH ────────────────────┐
│                               │
│ Validate refactor de auth     │
│                               │
│ Why: Mudança grande + deadline│
│                               │
│ Next:                         │
│ • Run auth tests (8 min)      │
│ • Check endpoints (5 min)     │
│                               │
│ [Start 25min Focus]           │
└───────────────────────────────┘
```

### Extension Architecture

```typescript
// Extension connects to Cloud Run API
class ContextPilotExtension {
  private apiClient: ContextPilotAPI;
  
  // Poll for new proposals
  async pollProposals() {
    const proposals = await this.apiClient.getProposals();
    this.updateProposalsPanel(proposals);
  }
  
  // Preview proposal
  async previewProposal(proposalId: string) {
    const proposal = await this.apiClient.getProposal(proposalId);
    const diffs = proposal.changes.map(c => this.createDiff(c));
    this.showDiffEditor(diffs);
  }
  
  // Apply proposal
  async applyProposal(proposalId: string) {
    // Create branch
    await this.git.checkout('-b', proposal.preview_branch);
    
    // Apply changes
    for (const change of proposal.changes) {
      if (change.action === 'create') {
        await this.fs.writeFile(change.file, change.content);
      } else if (change.action === 'modify') {
        await this.applyDiff(change.file, change.diff);
      }
    }
    
    // Commit
    await this.git.commit(proposal.title);
    
    // Notify backend
    await this.apiClient.markApplied(proposalId);
  }
}
```

---

## 🛡️ Safety Mechanisms

### 1. Sandbox Preview
Proposals são aplicados em **branch temporário** primeiro:
```bash
agent/proposal-<id>-preview
```

Dev pode testar antes de merge.

### 2. Rollback Automático
Se CI falha após aplicar proposal:
```python
@on_ci_failure
async def rollback_proposal(proposal_id):
    # Revert commit
    git.revert(proposal.commit_hash)
    # Notify dev
    notify(f"Proposal {proposal_id} reverted due to CI failure")
    # Mark as failed
    mark_proposal_failed(proposal_id)
```

### 3. Approval Chain
Para mudanças críticas:
```json
{
  "approval_required": {
    "code_owner": true,
    "senior_dev": true,
    "security_review": true
  }
}
```

### 4. Blast Radius Limit
Agentes **não** podem propor mudanças que afetem:
- Mais de 10 arquivos
- Mais de 500 linhas
- Arquivos de config críticos (`.env`, `secrets`)
- Deployment scripts

Se ultrapassar, quebra em proposals menores.

---

## 📊 Developer Experience

### Notification Flow

**Low Priority (Spec updates):**
- Badge no ícone da extensão
- Não interrompe trabalho

**Medium Priority (Strategy suggestions):**
- Toast notification
- "X new suggestions available"

**High Priority (Security issues):**
- Modal alert
- Requires acknowledgment

### Batch Approval
Dev pode aprovar múltiplos proposals de uma vez:
```
[✓] Extract AuthService
[✓] Update API docs
[ ] Add rate limiting (want to review)

[Apply Selected (2)]
```

### Custom Rules
Dev pode configurar:
```json
{
  "auto_approve": {
    "doc_updates": true,
    "formatting": true,
    "linting": false
  },
  "require_review": {
    "security_changes": true,
    "api_changes": true,
    "database_migrations": true
  },
  "ignore_suggestions_for": [
    "legacy/",
    "third_party/"
  ]
}
```

---

## 🔄 Integration with Existing Tools

### GitHub/GitLab
Proposals podem virar PRs automaticamente:
```yaml
# .contextpilot.yml
proposals:
  create_pr: true
  pr_template: |
    🤖 **Agent Proposal**: {{proposal.title}}
    
    **Agent**: {{proposal.agent}}
    **Impact**: {{proposal.impact.files_affected}} files
    
    ## Description
    {{proposal.description}}
    
    ## Benefits
    {{#each proposal.benefits}}
    - {{this}}
    {{/each}}
    
    ## Changes
    {{proposal.changes}}
```

### Linear/Jira
Link proposals to tickets:
```json
{
  "proposal_id": "cp_001",
  "linked_tickets": ["ENG-123"],
  "created_from_requirement": true
}
```

### Slack/Discord
Notify team:
```
🤖 Strategy Agent
New proposal: Extract AuthService
Impact: 4 files, ~45min
👉 Review in VSCode
```

---

## 🎯 Implementation Plan

### Phase 1: Basic Proposals (Week 1-2)
- [x] Change Proposal data model
- [ ] API endpoints: `/proposals/create`, `/proposals/list`
- [ ] Strategy Agent generates proposals (not applies)
- [ ] Simple CLI for review (`contextpilot proposals list`)

### Phase 2: IDE Extension (Week 3-4)
- [ ] VSCode extension scaffolding
- [ ] Proposals panel
- [ ] Diff preview
- [ ] Apply/Reject actions

### Phase 3: Advanced Features (Month 2)
- [ ] Batch approval
- [ ] Auto-approve rules
- [ ] PR integration
- [ ] Rollback automation

### Phase 4: Polish (Month 3)
- [ ] Cursor integration
- [ ] JetBrains support
- [ ] Mobile app (view proposals)
- [ ] Team collaboration features

---

## 📝 API Endpoints

### Create Proposal
```http
POST /proposals
Authorization: Bearer <token>

{
  "agent": "strategy-agent",
  "type": "refactor",
  "title": "Extract AuthService",
  "changes": [...],
  "user_id": "dev_123"
}
```

### List Proposals
```http
GET /proposals?status=pending&user_id=dev_123

Response:
{
  "proposals": [
    {
      "id": "cp_001",
      "title": "Extract AuthService",
      "status": "pending_approval",
      "created_at": "2025-10-13T15:00:00Z"
    }
  ]
}
```

### Approve Proposal
```http
POST /proposals/cp_001/approve

Response:
{
  "status": "approved",
  "branch_created": "agent/refactor-auth-service",
  "commit_hash": "abc123"
}
```

### Reject Proposal
```http
POST /proposals/cp_001/reject
{
  "reason": "Not aligned with current architecture"
}

Response:
{
  "status": "rejected",
  "feedback_recorded": true
}
```

---

## 🏆 Success Metrics

### Developer Satisfaction
- **Approval Rate**: > 60% proposals approved
- **Time to Review**: < 5 min average
- **False Positive Rate**: < 10% (irrelevant suggestions)

### Productivity
- **Time Saved**: > 2 hours/week per dev
- **Code Quality**: Maintainability index +15%
- **Bug Prevention**: Security issues caught +40%

### Trust
- **Rollback Rate**: < 5% (proposals break CI)
- **Override Rate**: < 15% (dev edits before apply)
- **Adoption**: > 70% devs use weekly

---

## 🎬 Demo Scenario (Hackathon Video)

**Narrator:**
> "Traditional AI code assistants make changes for you. ContextPilot works **with** you."

**Screen:**
1. Strategy Agent analyzes code
2. Finds duplication in auth logic
3. Creates Change Proposal (not applies)
4. VSCode extension shows notification
5. Dev clicks "Preview"
6. Side-by-side diff appears
7. Dev reviews, edits one line
8. Clicks "Apply"
9. Agent creates branch + commit
10. Dev pushes PR

**Narrator:**
> "You're always in control. Agents suggest, you decide."

---

**Philosophy**: 🤝 **Human-in-the-Loop AI**

**Trust**: Built through transparency and control

**Adoption**: Natural integration into existing workflows

---

*Document created: 2025-10-13*  
*Status: Architecture defined*  
*Next: Build VSCode extension MVP*

