# Custom Artifacts Guide

**How to use custom artifacts to control AI agents**

---

## 🎯 What Are Custom Artifacts?

Custom artifacts are `.md` files that you create to **teach agents how to work**:

- **Spec-Driven Development:** Templates for feature specs
- **Coding Standards:** Patterns and conventions to follow
- **Project Scope:** What's in/out of scope
- **Roadmaps:** Detailed plans for future features

**Key Benefit:** Agents read these files and follow the rules you define **in natural language**.

---

## 📚 Available Templates

### 1. **Feature Spec Template**
**File:** `feature_spec_template.md`  
**Purpose:** Complete specification for new features

**Use Case:**
```
You want to implement "Multi-workspace support"
→ Copy feature_spec_template.md to features/multi_workspace_spec.md
→ Fill in all sections
→ Tell Spec Agent to implement it
→ Spec Agent generates code following YOUR spec
```

**Agents That Use It:**
- **Spec Agent:** Generates code from spec
- **Git Agent:** Commits with proper references
- **Strategy Agent:** Validates against architecture

### 2. **Coding Standards**
**File:** `coding_standards.md`  
**Purpose:** Define patterns, conventions, architecture

**Use Case:**
```
You want all agents to follow Repository pattern
→ Add Repository pattern to coding_standards.md
→ Spec Agent automatically generates code using that pattern
→ Git Agent validates commits against standards
```

**Agents That Use It:**
- **Spec Agent:** Generates code following standards
- **Git Agent:** Validates commits
- **Strategy Agent:** Suggests refactorings to align

### 3. **Project Scope**
**File:** `project_scope.md`  
**Purpose:** Define what's in/out of scope

**Use Case:**
```
You want to focus on MVP, no mobile app yet
→ Create project_scope.md with "Out of Scope: Mobile app"
→ Spec Agent rejects proposals for mobile features
→ Strategy Agent keeps milestones focused on MVP
```

**Agents That Use It:**
- **Spec Agent:** Rejects out-of-scope proposals
- **Strategy Agent:** Aligns milestones with scope
- **Coach Agent:** Keeps you focused

### 4. **Feature Roadmap**
**File:** `q4_2025_roadmap.md`  
**Purpose:** Detailed plan with specs for future features

**Use Case:**
```
You have 10 features planned for Q4
→ Create roadmap with specs for each
→ Spec Agent implements features following roadmap specs
→ Strategy Agent tracks progress
→ Milestone Agent celebrates when Q4 goal hit
```

**Agents That Use It:**
- **Spec Agent:** Implements roadmap features
- **Strategy Agent:** Tracks progress vs plan
- **Milestone Agent:** Marks features complete

---

## 🚀 Quick Start

### Step 1: Create Artifact

```bash
# Copy template
cp back-end/app/templates/feature_spec_template.md \
   back-end/.contextpilot/workspaces/my-workspace/features/my_feature_spec.md

# Edit it
code back-end/.contextpilot/workspaces/my-workspace/features/my_feature_spec.md
```

### Step 2: Configure Agents

Edit `artifacts.yaml`:

```yaml
custom_artifacts:
  features/my_feature_spec.md:
    description: "Spec for my awesome feature"
    producer: user
    consumers:
      - spec
      - git
    agent_rules:
      spec: |
        When implementing this feature:
        1. Read features/my_feature_spec.md
        2. Follow the Technical Design section exactly
        3. Implement all Acceptance Criteria
        4. Generate tests from Test Plan section
        
      git: |
        When committing changes for this feature:
        1. Reference feature spec in commit message
        2. Validate commit includes all components listed in spec
```

### Step 3: Use It

```bash
# Via API
curl -X POST http://localhost:8000/proposals/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "my-workspace",
    "feature_spec": "features/my_feature_spec.md"
  }'

# Or via Extension
# 1. Open ContextPilot sidebar
# 2. Right-click "Proposals"
# 3. Select "Create from Feature Spec"
# 4. Choose "features/my_feature_spec.md"
```

---

## 💡 Real-World Examples

### Example 1: Enforce Architecture Pattern

**Goal:** All new features must use Repository pattern

**Solution:**

1. **Edit `coding_standards.md`:**
```markdown
## Repository Pattern (MANDATORY)

All database access MUST go through Repository classes:

```python
# ✅ CORRECT
class ProposalRepository:
    async def get(self, id: str) -> Proposal:
        return await db.proposals.find_one({'id': id})

class ProposalService:
    def __init__(self, repo: ProposalRepository):
        self.repo = repo
    
    async def fetch(self, id: str):
        return await self.repo.get(id)

# ❌ WRONG - Direct DB access in service
class ProposalService:
    async def fetch(self, id: str):
        return await db.proposals.find_one({'id': id})
```
\```

2. **Configure in `artifacts.yaml`:**
```yaml
custom_artifacts:
  coding_standards.md:
    consumers: [spec, git]
    agent_rules:
      spec: |
        When generating code:
        1. Read coding_standards.md
        2. Use Repository pattern for ALL database access
        3. Never access database directly from services
        4. If you see direct DB access, refactor it
```

3. **Result:**
- Spec Agent generates code with Repository pattern
- Git Agent rejects commits with direct DB access
- Consistent architecture across codebase

---

### Example 2: Spec-Driven Feature Development

**Goal:** Implement "Rate Limiting" feature with full spec

**Solution:**

1. **Create `features/rate_limiting_spec.md`:**
```markdown
# Rate Limiting Feature Spec

## User Story
As a developer, I want API rate limiting so that costs are controlled.

## Acceptance Criteria
- [ ] Limit: 100 requests/minute per user
- [ ] Return 429 status when exceeded
- [ ] Include Retry-After header
- [ ] Store limits in Redis

## Technical Design
### Components
1. **Middleware:** `RateLimitMiddleware` in `app/middleware/rate_limit.py`
2. **Storage:** Redis with key pattern `ratelimit:user:{user_id}`
3. **Configuration:** Environment variable `RATE_LIMIT_RPM`

### API Response
```json
{
  "error": "Rate limit exceeded",
  "limit": 100,
  "remaining": 0,
  "reset_at": "2025-10-15T14:30:00Z"
}
```
\```

2. **Configure:**
```yaml
custom_artifacts:
  features/rate_limiting_spec.md:
    consumers: [spec]
    agent_rules:
      spec: |
        Implement rate limiting following the spec:
        1. Create RateLimitMiddleware exactly as designed
        2. Use Redis with the key pattern specified
        3. Return the exact JSON response format
        4. Write tests covering all acceptance criteria
```

3. **Trigger:**
```bash
# Spec Agent creates proposal with full implementation
curl -X POST http://localhost:8000/proposals/create \
  -d '{"feature_spec": "features/rate_limiting_spec.md"}'
```

4. **Result:**
- Proposal includes middleware, tests, docs
- All acceptance criteria implemented
- Redis integration as specified
- Ready to review and approve

---

### Example 3: Keep Project Focused

**Goal:** Prevent scope creep before hackathon

**Solution:**

1. **Create `project_scope.md`:**
```markdown
# ContextPilot - Pre-Hackathon Scope

## In Scope (Must Have for Launch)
- ✅ Spec Agent (docs automation)
- ✅ Git Agent (auto-commits)
- ✅ Coach Agent (nudges)
- ✅ VSCode Extension
- ✅ Basic rewards (CPT tokens)

## Out of Scope (Post-Hackathon)
- ❌ Mobile app
- ❌ Real-time collaboration
- ❌ Video calls
- ❌ Advanced analytics dashboard
- ❌ Multi-language support (only Python/TS for now)

## Success Criteria
- [ ] Extension published to marketplace
- [ ] 3 agents working end-to-end
- [ ] Demo ready for hackathon judges
- [ ] Docs complete

## Deadline
**October 20, 2025** - Hackathon submission
```

2. **Configure:**
```yaml
custom_artifacts:
  project_scope.md:
    consumers: [spec, strategy, coach]
    agent_rules:
      spec: |
        Before creating ANY proposal:
        1. Check if feature is in "In Scope" section
        2. REJECT proposals for "Out of Scope" features
        3. Explain: "This is out of scope for pre-hackathon launch"
      
      strategy: |
        When planning milestones:
        1. Only include "In Scope" features
        2. Prioritize "Success Criteria" items
        3. Alert if deadline at risk
      
      coach: |
        When user suggests new feature:
        1. Check project_scope.md
        2. If out of scope, say: "Great idea! Let's add it post-hackathon"
        3. Redirect focus to "Success Criteria"
```

3. **Result:**
- User tries: "Let's add mobile app"
- Spec Agent: "Mobile app is out of scope. Focus on marketplace launch first."
- Coach: "You have 5 days until deadline. Priority: Complete Success Criteria."
- Project stays on track!

---

## 🎨 Best Practices

### 1. **Be Specific**
```markdown
# ❌ BAD: Vague rule
"Generate good code"

# ✅ GOOD: Specific rule
"Use async/await for all I/O operations. Add type hints. Include docstrings."
```

### 2. **Include Examples**
```markdown
# Rule
Use Repository pattern for database access.

# Example
```python
# ✅ CORRECT
class UserRepository:
    async def get(self, id: str) -> User:
        return await db.users.find_one({'id': id})

# ❌ WRONG
async def get_user(id: str):
    return await db.users.find_one({'id': id})
```
\```

### 3. **Make Rules Actionable**
```markdown
# ❌ BAD: Not actionable
"Code should be clean"

# ✅ GOOD: Actionable
"Before committing:
1. Run Black formatter
2. Fix all Ruff warnings
3. Ensure test coverage > 80%
4. Add docstrings to public functions"
```

### 4. **Update Regularly**
- Review artifacts weekly
- Add patterns you want agents to follow
- Remove outdated rules

---

## 🔧 Troubleshooting

### Agent Not Following Rules?

**Check:**
1. Is artifact listed in `artifacts.yaml`?
2. Is agent in `consumers` list?
3. Is `agent_rules` defined for that agent?

**Debug:**
```python
# In agent code
logger.info(f"[{self.agent_id}] My rules: {self.agent_rules}")
```

### Rules Conflicting?

**Solution:** Use priority system
```yaml
custom_artifacts:
  coding_standards.md:
    priority: high  # Always respected
  
  experimental_patterns.md:
    priority: low   # Can be overridden
```

---

## 📊 Measuring Success

Track artifact effectiveness:

```python
# In BaseAgent
self.increment_metric('artifacts_consumed')
self.increment_metric('rules_applied')
self.increment_metric('rules_violated')

# View metrics
GET /agents/{agent_id}/metrics
```

**Good Indicators:**
- `rules_applied` >> `rules_violated`
- Proposals follow standards consistently
- Fewer PR review comments about patterns

---

## 🚀 Advanced: Dynamic Templates

**Goal:** Generate artifact from conversation

**Example:**
```bash
# User: "Create a feature spec for authentication"
# Coach Agent:
curl -X POST /artifacts/generate \
  -d '{
    "template": "feature_spec_template.md",
    "prompt": "Authentication with JWT tokens",
    "output": "features/auth_spec.md"
  }'

# Result: Filled-in spec ready for Spec Agent
```

---

## 📚 Template Library

| Template | Purpose | Agents |
|----------|---------|--------|
| `feature_spec_template.md` | Feature specification | Spec, Git |
| `coding_standards.md` | Code patterns | Spec, Git |
| `project_scope.md` | Scope boundaries | Spec, Strategy, Coach |
| `api_design_guide.md` | API conventions | Spec |
| `test_plan_template.md` | Test specification | Spec |
| `architecture_decision.md` | ADR template | Strategy |

---

## 💡 Pro Tips

1. **Start Small:** Begin with `project_scope.md` only
2. **Iterate:** Add rules as you see patterns
3. **Share:** Team members can add rules too
4. **Version Control:** Commit artifacts to Git
5. **Document:** Explain WHY rules exist

---

**Next Steps:**
1. Copy a template
2. Fill it in for your project
3. Configure in `artifacts.yaml`
4. Watch agents follow your rules!

---

**Created:** 2025-10-15  
**Last Updated:** 2025-10-15  
**Owner:** ContextPilot Team

