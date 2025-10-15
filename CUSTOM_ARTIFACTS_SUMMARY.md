# Custom Artifacts System - Summary

**Date:** October 15, 2025  
**Status:** ✅ Designed and Documented

## What Was Implemented

### 1. **artifacts.yaml** Configuration System

Centralized configuration file that defines:
- Which agents consume which artifacts
- Natural language rules for each agent
- Producer/consumer relationships
- Update frequencies and priorities

**Example:**
```yaml
custom_artifacts:
  project_scope.md:
    consumers: [spec, strategy]
    agent_rules:
      spec: "Reject proposals outside defined scope"
      strategy: "Align milestones with scope goals"
```

### 2. Three New Artifact Templates

#### `project_scope.md`
- **Purpose:** Define project boundaries (in/out of scope)
- **Consumers:** Spec Agent, Strategy Agent
- **Rules:**
  - Spec: Reject proposals that violate scope
  - Strategy: Ensure milestones align with scope

#### `project_checklist.md`
- **Purpose:** Master project completion checklist (10 phases, 43 items)
- **Consumers:** Strategy Agent, Milestone Agent, Coach Agent
- **Rules:**
  - Strategy: Map milestones to checklist items
  - Milestone: Mark items complete when milestones finish
  - Coach: Show progress and celebrate completions

#### `daily_checklist.md`
- **Purpose:** Daily tasks and to-dos
- **Consumers:** Coach Agent, Retrospective Agent
- **Rules:**
  - Coach: Remind user morning and evening
  - Retrospective: Analyze completion patterns weekly

### 3. BaseAgent Integration (Design)

```python
class BaseAgent:
    def consume_artifact(self, artifact_name: str) -> str:
        """Read artifact and get its content"""
        
    def apply_artifact_rules(self, artifact_name: str, context: Dict) -> Dict:
        """Inject artifact rules into LLM prompt context"""
```

**How It Works:**
1. Agent loads `artifacts.yaml` on init
2. Reads artifacts it's configured to consume
3. Injects rules into LLM prompts
4. LLM makes decisions respecting those rules

### 4. User Interface (Planned)

**CLI:**
```bash
# Create custom artifact
contextpilot artifact create my_artifact.md \
  --consumers spec,strategy \
  --rule spec:"Your rule here"

# List artifacts
contextpilot artifact list

# Update rules
contextpilot artifact rule my_artifact.md spec --prompt "New rule"
```

**Extension:**
- Artifact creation wizard
- Rule editor UI
- Artifact list in sidebar
- Visual producer/consumer graph

## Key Benefits

### 1. **No Code Required**
Users define agent behavior with natural language, not Python code:
```yaml
agent_rules:
  spec: "Before creating proposals, check if feature is in scope"
```

### 2. **Multi-Agent Coordination**
Same artifact guides multiple agents differently:
- `project_scope.md` → Spec (reject out-of-scope) + Strategy (align milestones)

### 3. **Flexible & Extensible**
Add new artifacts anytime without changing code:
```bash
contextpilot artifact create coding_standards.md --consumers spec,git
```

### 4. **Version Controlled**
All artifacts and rules stored in workspace Git repo:
- Track changes over time
- Rollback if rules don't work
- Share configurations across teams

### 5. **Context-Aware AI**
Agents make better decisions with artifact context:
```
User: "Add mobile app feature"
Spec Agent: [Reads project_scope.md, sees mobile is out of scope]
Response: "❌ Rejected: Mobile app is out of scope per project_scope.md"
```

## Example Workflow

### 1. User Creates Artifact
```bash
contextpilot artifact create project_scope.md \
  --description "Project scope document" \
  --consumers spec,strategy
```

### 2. User Defines Rules
```yaml
agent_rules:
  spec: |
    Read project_scope.md before creating proposals.
    Reject any feature listed in "Out of Scope".
```

### 3. User Edits Artifact
```markdown
# project_scope.md

## Out of Scope
- ❌ Mobile app
- ❌ Real-time collaboration
```

### 4. Agent Uses Artifact
```python
# Spec Agent creates proposal
scope_content = self.consume_artifact('project_scope.md')
rule = self.agent_rules['project_scope.md']

prompt = f"""
RULE: {rule}
SCOPE: {scope_content}

User suggests: "Add mobile app"
Create proposal or reject with reason.
"""

# LLM responds: "Rejected - mobile app is out of scope"
```

## Architecture Integration

### State Management + Artifacts
```python
class BaseAgent:
    def __init__(self, workspace_id, agent_id):
        # State Management (Phase 1A)
        self.state = self._load_state()  # From Firestore
        
        # Custom Artifacts (Phase 1B)
        self.artifacts_config = self._load_artifacts_config()  # From YAML
        self.agent_rules = self._get_my_rules()  # Rules for this agent
    
    def remember(self, key, value):
        """Persistent memory"""
        
    def consume_artifact(self, name):
        """Read artifact with rules"""
```

### Event-Driven Artifacts
```python
# When artifact is created
event_bus.publish('artifact.created.v1', {'name': 'project_scope.md'})

# When artifact is updated
event_bus.publish('artifact.updated.v1', {'name': 'project_scope.md'})

# Agents subscribed to artifact events refresh their context
```

## Implementation Phases

### Phase 1B: Custom Artifacts (Week 1) 🎯 CURRENT
- [ ] Create `artifacts.yaml` configuration system
- [ ] Add `consume_artifact()` to `BaseAgent`
- [ ] Implement rule loading and injection
- [ ] Create templates (project_scope, project_checklist, daily_checklist)
- [ ] Test with Spec Agent

### Phase 2: User Interface (Week 2)
- [ ] CLI commands (`artifact create`, `artifact list`, `artifact rule`)
- [ ] Extension UI for artifact management
- [ ] Artifact viewer in sidebar
- [ ] Rule editor

### Phase 3: Advanced Features (Week 3)
- [ ] Artifact templates library
- [ ] Rule validation (ensure actionable)
- [ ] Dependency graphs (which artifacts depend on others)
- [ ] Conflict detection (contradictory rules)

### Phase 4: LLM Integration (Week 4)
- [ ] Inject rules into all agent prompts automatically
- [ ] Track rule compliance in proposals
- [ ] Generate "rule violation" reports
- [ ] Auto-suggest rules based on patterns

## Files Created

### Documentation
- `docs/architecture/CUSTOM_ARTIFACTS.md` - Complete design doc (800+ lines)
- `CUSTOM_ARTIFACTS_SUMMARY.md` - This file

### Templates
- `back-end/app/templates/project_scope.md` - Project scope template
- `back-end/app/templates/project_checklist.md` - Master checklist template
- `back-end/app/templates/daily_checklist.md` - Daily tasks template
- `back-end/app/templates/artifacts.yaml` - Configuration schema

### Updated
- `ARCHITECTURE_ROADMAP.md` - Phase 1 now includes artifacts

## Next Steps

1. ✅ Design complete
2. ✅ Templates created
3. ✅ Documentation written
4. 🎯 Implement `BaseAgent` class (Phase 1A + 1B together)
5. 🎯 Test with Spec Agent + `project_scope.md`
6. 🎯 Create CLI commands
7. 🎯 Build Extension UI

## Commits

- `9a09c64` - docs(architecture): design event-driven multi-agent system
- `1045b12` - feat(artifacts): implement custom artifacts system with agent rules

---

**Status:** ✅ Ready for implementation  
**Next:** Start Phase 1 (BaseAgent + State + Artifacts)  
**Timeline:** 1 week for Phase 1, 4 weeks total for full system

**Questions?** See `docs/architecture/CUSTOM_ARTIFACTS.md` for complete details.

