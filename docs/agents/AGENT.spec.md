---
id: spec-agent
version: 1.0.0
owner: "@contextpilot-team"
category: ai-agents
gemini_model: gemini-1.5-flash
cloud_run_type: Service
events_in:
  - context.delta.v1
  - spec.request.v1
  - git.commit.v1
  - milestone.created.v1
events_out:
  - spec.update.v1
  - spec.validation.v1
  - spec.template.created.v1
resources:
  firestore:
    - spec_history
    - spec_templates
  pubsub:
    - topics: [spec-updates]
    - subs: [spec-from-context, spec-from-git]
prompts:
  ai_studio: "https://aistudio.google.com/prompts/SPEC-001"
  local: "./prompts/spec/base.prompt.md"
contracts:
  inputs_schema: "schemas/spec_events_v1.json"
  outputs_schema: "schemas/spec_update_v1.json"
slos:
  doc_freshness_hours: 24
  validation_accuracy: 0.85
  template_generation_time_ms: 3000
---

# 📄 Spec Agent

## Purpose

Spec Agent é o **curador de artefatos de documentação** do projeto. Ele gerencia, valida e atualiza arquivos Markdown que servem como **fonte única de verdade** para especificações técnicas.

**Core Principle:** Documentação como código - versionada, validada e evoluída junto com o projeto.

---

## 🎯 Responsibilities

### 1. **Markdown Artifact Management**

Spec Agent gerencia um conjunto padronizado de arquivos `.md` como artefatos de desenvolvimento:

#### Standard Templates (Built-in)

| Arquivo | Propósito | Atualização |
|---------|-----------|-------------|
| `README.md` | Overview do projeto, setup, uso | Manual + Agent suggestions |
| `ARCHITECTURE.md` | Design de sistema, componentes | Agent-assisted |
| `scope.md` | Escopo do projeto, o que entra/não entra | Manual + Agent validation |
| `project_checklist.md` | Checklist de tarefas do projeto | Agent-synced com milestones |
| `daily_checklist.md` | Checklist diário (standup, review) | Agent-generated daily |
| `API.md` | Documentação de endpoints | Auto-generated from code |
| `CHANGELOG.md` | Histórico de mudanças | Auto-generated from commits |
| `CONTRIBUTING.md` | Guidelines de contribuição | Manual |
| `DECISIONS.md` | ADRs (Architecture Decision Records) | Manual + Agent suggestions |

#### User-Defined Templates

Devs podem criar templates customizados:

```yaml
# .contextpilot/templates/custom.yml
templates:
  - name: "sprint_planning.md"
    schema:
      sections:
        - Goals
        - Tasks
        - Blockers
    frequency: "weekly"
    auto_update: true
  
  - name: "technical_debt.md"
    schema:
      sections:
        - Current Debt
        - Priority
        - Plan to Address
    frequency: "monthly"
    auto_update: false
```

### 2. **Documentation Generation**

Spec Agent gera/atualiza docs baseado em:

**From Code:**
```python
# Detecta docstrings e gera API.md
@spec_agent.on_event("context.delta.v1")
async def generate_api_docs(event):
    if event.files_changed contains ".py":
        # Parse docstrings
        api_docs = parse_docstrings(event.files)
        # Generate markdown
        update_file("API.md", api_docs)
```

**From Git:**
```python
# Gera CHANGELOG.md de commits
@spec_agent.on_event("git.commit.v1")
async def update_changelog(event):
    if is_semantic_commit(event.message):
        entry = format_changelog_entry(event)
        append_to_changelog(entry)
```

**From Milestones:**
```python
# Atualiza project_checklist.md
@spec_agent.on_event("milestone.created.v1")
async def sync_checklist(event):
    checklist = generate_checklist(event.milestone)
    update_file("project_checklist.md", checklist)
```

### 3. **Validation & Consistency**

Spec Agent valida que docs estão sincronizados com código:

```python
@spec_agent.daily_job
async def validate_docs():
    issues = []
    
    # Check API docs vs actual endpoints
    documented_endpoints = parse_api_md()
    actual_endpoints = scan_code_for_routes()
    
    missing = actual_endpoints - documented_endpoints
    if missing:
        issues.append({
            "type": "missing_docs",
            "endpoints": missing,
            "action": "Add to API.md"
        })
    
    # Check architecture diagram vs actual structure
    documented_structure = parse_architecture_md()
    actual_structure = scan_project_structure()
    
    if documented_structure != actual_structure:
        issues.append({
            "type": "outdated_architecture",
            "action": "Update ARCHITECTURE.md"
        })
    
    if issues:
        emit_event("spec.validation.v1", issues)
```

### 4. **Template System**

Spec Agent fornece templates prontos e aceita customizações:

**Standard Template: scope.md**
```markdown
# 📋 Project Scope

## ✅ In Scope
<!-- What this project WILL do -->

- Feature A: Description
- Feature B: Description

## ❌ Out of Scope
<!-- What this project will NOT do -->

- Feature X: Reason why not
- Feature Y: Maybe in v2.0

## 🤔 To Be Decided
<!-- Features under consideration -->

- Feature Z: Needs stakeholder approval

## 📊 Scope Metrics
<!-- Auto-updated by Spec Agent -->

- Total features: 15
- Completed: 8 (53%)
- In progress: 4 (27%)
- Not started: 3 (20%)

Last updated: 2025-10-14 by Spec Agent
```

**Standard Template: daily_checklist.md**
```markdown
# 📅 Daily Checklist - {{date}}

## 🌅 Morning
- [ ] Review yesterday's progress
- [ ] Check Slack/email for blockers
- [ ] Prioritize today's tasks (top 3)

## 💻 Development
- [ ] Pull latest from main
- [ ] Run tests before starting
- [ ] Commit frequently (small chunks)
- [ ] Update relevant docs

## 🧪 Testing
- [ ] Run unit tests
- [ ] Manual testing of changes
- [ ] Check CI pipeline status

## 📝 End of Day
- [ ] Push all commits
- [ ] Update project_checklist.md
- [ ] Note any blockers for tomorrow
- [ ] Quick standup note (what done, what next)

## 🧘 Coach Suggestions
<!-- Auto-populated by Coach Agent -->
{{coach_nudges}}
```

### 5. **User-Initiated Templates**

Dev pode pedir para criar novo template:

```bash
# Via CLI
contextpilot spec create-template \
  --name="retrospective.md" \
  --sections="What Went Well,What To Improve,Action Items" \
  --frequency="sprint"

# Via UI
# Click "New Template" → Fill form → Spec Agent generates
```

Spec Agent usa Gemini para gerar estrutura:

**Prompt para Gemini:**
```
User wants a template for: "retrospective.md"
Sections: What Went Well, What To Improve, Action Items
Frequency: End of sprint

Generate a markdown template that:
- Has clear section headers
- Includes helpful prompts/questions
- Has a standard footer with metadata
- Follows our template style guide
```

---

## 📋 Standard Artifacts

### Core Documentation Set

```
docs/
├── README.md                   # Project overview
├── ARCHITECTURE.md             # System design
├── scope.md                    # Project scope
├── project_checklist.md        # Master checklist
├── daily_checklist.md          # Daily template
├── API.md                      # API documentation
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # How to contribute
├── DECISIONS.md                # ADRs
├── TOKENOMICS.md              # (Project-specific)
└── templates/                  # User templates
    ├── sprint_planning.md
    ├── retrospective.md
    └── technical_debt.md
```

### Metadata in Frontmatter

Todos os .md gerenciados têm frontmatter:

```markdown
---
managed_by: spec-agent
template: daily_checklist
version: 1.2.0
last_updated: 2025-10-14T08:00:00Z
auto_update: true
frequency: daily
next_update: 2025-10-15T08:00:00Z
---

# 📅 Daily Checklist
...
```

---

## 🔄 Event Flows

### Flow 1: Code Change → Doc Update

```
1. Dev commits code (new API endpoint)
   ↓
2. Git Agent emits "git.commit.v1"
   ↓
3. Context Agent detects API change → "context.delta.v1"
   ↓
4. Spec Agent receives both events
   ↓
5. Parses new endpoint from code
   ↓
6. Generates API doc entry
   ↓
7. Creates Change Proposal for API.md
   ↓
8. Dev approves → API.md updated
   ↓
9. Spec Agent emits "spec.update.v1"
   ↓
10. CHANGELOG.md auto-updated
```

### Flow 2: User Creates Custom Template

```
1. Dev: "contextpilot spec create-template sprint_planning"
   ↓
2. Spec Agent receives "spec.request.v1"
   ↓
3. Asks Gemini to generate template structure
   ↓
4. Creates docs/templates/sprint_planning.md
   ↓
5. Registers in .contextpilot/templates.yml
   ↓
6. Emits "spec.template.created.v1"
   ↓
7. Coach Agent notified → creates nudge:
   "New template available, want to fill it out?"
```

### Flow 3: Daily Checklist Auto-Generation

```
1. Cloud Scheduler: Every day 8 AM
   ↓
2. Triggers Spec Agent daily job
   ↓
3. Generates fresh daily_checklist.md
   ↓
4. Populates with:
   - Date
   - Yesterday's uncompleted items
   - Coach suggestions
   - Upcoming milestones (from Milestone Agent)
   ↓
5. Commits to Git (via Git Agent)
   ↓
6. Notifies dev: "Today's checklist ready"
```

---

## 🛡️ Validation Rules

### 1. Consistency Checks

```python
class SpecValidator:
    async def validate_api_docs(self):
        # Check: All @app.route() documented
        routes = scan_fastapi_routes()
        documented = parse_api_md()
        
        missing = [r for r in routes if r not in documented]
        return ValidationResult(
            valid=len(missing) == 0,
            issues=missing,
            fix_suggestion="Add to API.md"
        )
    
    async def validate_architecture(self):
        # Check: Diagram matches actual structure
        documented_services = parse_mermaid_diagram()
        actual_services = scan_docker_compose()
        
        return ValidationResult(
            valid=documented_services == actual_services,
            issues=set(actual_services) - set(documented_services),
            fix_suggestion="Update ARCHITECTURE.md diagram"
        )
```

### 2. Freshness Checks

```python
@spec_agent.daily_job
async def check_freshness():
    for doc in managed_docs:
        last_updated = get_frontmatter(doc)["last_updated"]
        code_changed_since = git.last_change_in_related_code(doc)
        
        if code_changed_since > last_updated:
            age_days = (now() - last_updated).days
            
            if age_days > 7:
                emit_alert(
                    f"{doc} is stale (last updated {age_days} days ago)",
                    severity="high"
                )
```

---

## 📊 Metrics & SLOs

### SLOs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Doc Freshness | < 24h after code change | Timestamp comparison |
| Validation Accuracy | > 85% issues caught | Manual review sample |
| Template Generation | < 3s | Time to generate |
| Update Latency | < 5min (event → proposal) | Pub/Sub timestamp |

### Dashboards

**Cloud Monitoring:**
- Doc staleness distribution
- Validation errors over time
- Template usage (which templates most used)
- Approval rate for doc proposals

---

## 🧪 Test Vectors

### Vector 1: API Endpoint Added

**Input:**
```json
{
  "event": "context.delta.v1",
  "type": "feature",
  "files_changed": ["src/api/rewards.py"],
  "new_endpoints": [
    {
      "path": "/rewards/track",
      "method": "POST",
      "description": "Track reward action"
    }
  ]
}
```

**Expected Output:**
```json
{
  "event": "spec.update.v1",
  "file": "API.md",
  "action": "proposal_created",
  "proposal_id": "cp_042",
  "changes": {
    "section": "Rewards API",
    "content": "### POST /rewards/track\n\nTrack a reward-earning action..."
  }
}
```

**Checks:**
- ✅ Proposal created (not auto-applied)
- ✅ Correct section in API.md
- ✅ Includes method, path, description
- ✅ Links to related code

### Vector 2: User Creates Template

**Input:**
```json
{
  "event": "spec.request.v1",
  "action": "create_template",
  "template_name": "retrospective.md",
  "sections": ["What Went Well", "What To Improve", "Action Items"],
  "frequency": "sprint"
}
```

**Expected Output:**
```json
{
  "event": "spec.template.created.v1",
  "template_name": "retrospective.md",
  "path": "docs/templates/retrospective.md",
  "registered": true
}
```

**Checks:**
- ✅ File created at correct path
- ✅ Has frontmatter with metadata
- ✅ Sections properly formatted
- ✅ Registered in templates.yml

---

## 🚀 Deployment

### Cloud Run Service

```yaml
service: spec-agent
runtime: python311
env_variables:
  GEMINI_MODEL: gemini-1.5-flash
  TEMPLATES_PATH: /workspace/docs/templates
  AUTO_GENERATE_DAILY: true
resources:
  cpu: 1
  memory: 512Mi
scaling:
  min_instances: 0  # Scale to zero
  max_instances: 5
```

### Cloud Scheduler (Daily Jobs)

```bash
# Generate daily checklist
gcloud scheduler jobs create http spec-daily-checklist \
  --location=us-central1 \
  --schedule="0 8 * * *" \
  --uri="https://spec-agent-HASH.run.app/jobs/daily-checklist" \
  --http-method=POST

# Validate all docs
gcloud scheduler jobs create http spec-validate-docs \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://spec-agent-HASH.run.app/jobs/validate" \
  --http-method=POST
```

---

## 🎯 API Endpoints

### Generate Template

```http
POST /spec/templates/create
Authorization: Bearer <token>

{
  "name": "retrospective.md",
  "sections": ["What Went Well", "What To Improve", "Action Items"],
  "frequency": "sprint",
  "auto_update": false
}

Response:
{
  "template_id": "tpl_001",
  "path": "docs/templates/retrospective.md",
  "status": "created"
}
```

### Validate Docs

```http
POST /spec/validate
Authorization: Bearer <token>

Response:
{
  "valid": false,
  "issues": [
    {
      "file": "API.md",
      "type": "missing_endpoint",
      "endpoint": "/rewards/track",
      "fix": "Add documentation for this endpoint"
    }
  ],
  "last_validated": "2025-10-14T10:00:00Z"
}
```

### Get Doc Status

```http
GET /spec/docs/status

Response:
{
  "docs": [
    {
      "file": "API.md",
      "last_updated": "2025-10-13T15:00:00Z",
      "stale": false,
      "managed_by": "spec-agent"
    },
    {
      "file": "ARCHITECTURE.md",
      "last_updated": "2025-10-01T10:00:00Z",
      "stale": true,
      "age_days": 13
    }
  ]
}
```

---

## 🔮 Future Enhancements

### Phase 2
- [ ] Visual diagram generation (Mermaid auto-gen)
- [ ] Doc diff tracking (what changed?)
- [ ] Multi-language support (i18n docs)
- [ ] Doc search (full-text)

### Phase 3
- [ ] Doc versioning (per release)
- [ ] Doc analytics (most viewed, least updated)
- [ ] Collaborative editing (multiple devs)
- [ ] Doc templates marketplace

---

**Status**: 📐 **Architecture defined**  
**Next**: Implement template system + validation  
**Owner**: Spec Agent Team

