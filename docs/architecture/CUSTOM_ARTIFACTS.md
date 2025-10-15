# Custom Artifacts & Agent Rules System

**Date:** October 15, 2025  
**Status:** 🚧 Design Document

## Concept

Allow users to:
1. **Create custom `.md` artifacts** (e.g., `project_scope.md`, `daily_checklist.md`)
2. **Define agent rules** via prompts (when/how agents should use each artifact)
3. **Configure producer/consumer relationships** dynamically

## Architecture

### 1. Artifact Registry (Firestore)

```json
{
  "workspace_id": "contextpilot",
  "custom_artifacts": {
    "project_scope.md": {
      "created_by": "user",
      "created_at": "2025-10-15T12:00:00Z",
      "description": "High-level project scope and boundaries",
      "rules": {
        "producer": "user",
        "consumers": ["spec", "strategy"],
        "update_frequency": "weekly",
        "agent_prompts": {
          "spec": "Read project_scope.md before creating proposals. Reject any proposal that violates scope boundaries.",
          "strategy": "Use project_scope.md to validate milestones align with project goals."
        }
      },
      "metadata": {
        "template": false,
        "required": true,
        "priority": "high"
      }
    },
    
    "daily_checklist.md": {
      "created_by": "user",
      "description": "Daily tasks and reminders",
      "rules": {
        "producer": "user",
        "consumers": ["coach", "retrospective"],
        "update_frequency": "daily",
        "agent_prompts": {
          "coach": "Check daily_checklist.md each morning. Remind user of incomplete tasks. Provide motivation.",
          "retrospective": "Analyze daily_checklist.md completion rate. Identify patterns in missed tasks."
        }
      }
    },
    
    "project_checklist.md": {
      "created_by": "user",
      "description": "Master checklist for project completion",
      "rules": {
        "producer": "user",
        "consumers": ["strategy", "milestone", "coach"],
        "update_frequency": "on_milestone",
        "agent_prompts": {
          "strategy": "Before updating milestones, check project_checklist.md. Ensure milestones map to checklist items.",
          "milestone": "When a checklist item is completed, trigger milestone.progress event.",
          "coach": "Celebrate checklist completions. Suggest next steps based on remaining items."
        }
      }
    }
  }
}
```

### 2. Artifact Configuration File

**Location:** `.contextpilot/workspaces/{workspace_id}/artifacts.yaml`

```yaml
# User-defined custom artifacts
custom_artifacts:
  
  project_scope.md:
    description: "Project scope and boundaries"
    producer: user
    consumers:
      - spec
      - strategy
    update_frequency: weekly
    required: true
    priority: high
    
    # Agent-specific rules (natural language prompts)
    agent_rules:
      spec: |
        Before creating any proposal:
        1. Read project_scope.md
        2. Verify the proposal aligns with defined scope
        3. Reject proposals that add features outside scope
        4. Flag scope violations in proposal metadata
        
      strategy: |
        When updating strategy or milestones:
        1. Consult project_scope.md for project boundaries
        2. Ensure all milestones contribute to scope goals
        3. Alert if current progress diverges from scope
  
  daily_checklist.md:
    description: "Daily tasks and todos"
    producer: user
    consumers:
      - coach
      - retrospective
    update_frequency: daily
    
    agent_rules:
      coach: |
        Every morning (9am):
        1. Read daily_checklist.md
        2. Identify incomplete tasks from yesterday
        3. Send friendly reminder to user
        4. Provide motivation and estimate time to complete
        
        Every evening (6pm):
        1. Review completed tasks
        2. Celebrate wins
        3. Suggest priorities for tomorrow
        
      retrospective: |
        During weekly retrospective:
        1. Analyze daily_checklist.md completion rates
        2. Identify patterns (e.g., "user never completes testing tasks")
        3. Recommend process improvements
        4. Track completion trends over time
  
  project_checklist.md:
    description: "Master project completion checklist"
    producer: user
    consumers:
      - strategy
      - milestone
      - coach
    update_frequency: on_milestone
    
    agent_rules:
      strategy: |
        Before updating milestones:
        1. Load project_checklist.md
        2. Map milestones to checklist sections
        3. Ensure milestones cover all checklist items
        4. Identify checklist items without milestones
        
      milestone: |
        On milestone completion:
        1. Find corresponding project_checklist.md item
        2. Mark as [x] completed
        3. Update completion percentage
        4. Trigger celebration if section completed
        
      coach: |
        When user completes checklist item:
        1. Send congratulations message
        2. Show progress (e.g., "23/50 items done - 46%")
        3. Suggest next logical item to tackle
        4. Estimate project completion date

  # System artifacts (pre-defined)
  context.md:
    description: "Project context and current status"
    producer: git
    consumers: [spec, strategy, coach]
    system: true
    
  proposals.md:
    description: "Active and historical proposals"
    producer: spec
    consumers: [git, user]
    system: true
```

### 3. BaseAgent Integration

```python
# back-end/app/agents/base_agent.py

class BaseAgent(ABC):
    def __init__(self, workspace_id: str, agent_id: str):
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self.artifacts_config = self._load_artifacts_config()
        self.agent_rules = self._get_my_rules()
        
    def _load_artifacts_config(self) -> Dict:
        """Load artifacts.yaml configuration"""
        config_path = self._get_workspace_path('artifacts.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_my_rules(self) -> Dict[str, str]:
        """Get all agent rules that apply to this agent"""
        rules = {}
        for artifact_name, config in self.artifacts_config.get('custom_artifacts', {}).items():
            if self.agent_id in config.get('consumers', []):
                prompt = config.get('agent_rules', {}).get(self.agent_id)
                if prompt:
                    rules[artifact_name] = prompt
        return rules
    
    def consume_artifact(self, artifact_name: str) -> str:
        """Read artifact content with rule awareness"""
        # 1. Read the artifact
        artifact_path = self._get_workspace_path(artifact_name)
        with open(artifact_path, 'r') as f:
            content = f.read()
        
        # 2. Get the agent rule for this artifact
        rule = self.agent_rules.get(artifact_name)
        
        # 3. Log consumption
        logger.info(f"[{self.agent_id}] Reading {artifact_name}")
        if rule:
            logger.info(f"[{self.agent_id}] Applying rule: {rule[:100]}...")
        
        return content
    
    def apply_artifact_rules(self, artifact_name: str, context: Dict) -> Dict:
        """Apply agent rules from artifact to decision-making context"""
        rule = self.agent_rules.get(artifact_name)
        if not rule:
            return context
        
        # Inject rule into LLM prompt context
        context['artifact_rules'] = context.get('artifact_rules', [])
        context['artifact_rules'].append({
            'artifact': artifact_name,
            'rule': rule
        })
        
        return context
```

### 4. Spec Agent with Custom Rules

```python
# back-end/app/agents/spec_agent.py

class SpecAgent(BaseAgent):
    async def create_proposal(self, issue: Dict) -> str:
        """Create proposal - respecting custom artifact rules"""
        
        # 1. Gather artifacts I'm supposed to consume
        context = {}
        for artifact_name in self.agent_rules.keys():
            content = self.consume_artifact(artifact_name)
            context[artifact_name] = content
        
        # 2. Build LLM prompt with artifact rules
        prompt = self._build_prompt_with_rules(issue, context)
        
        # 3. Call LLM
        response = await self.llm.generate(prompt)
        
        # 4. Validate against artifact rules
        if not self._validate_against_rules(response, context):
            logger.warning(f"Proposal violates artifact rules: {response}")
            return None
        
        # 5. Create proposal
        return self._persist_proposal(response)
    
    def _build_prompt_with_rules(self, issue: Dict, artifacts: Dict) -> str:
        """Build LLM prompt that includes artifact rules"""
        prompt = f"""You are the Spec Agent. You found this issue:
{issue['description']}

Before creating a proposal, you must follow these rules:

"""
        # Inject artifact rules into prompt
        for artifact_name, rule in self.agent_rules.items():
            artifact_content = artifacts.get(artifact_name, '')
            prompt += f"""
### Rule from {artifact_name}:
{rule}

### Current {artifact_name} content:
{artifact_content}

"""
        
        prompt += f"""
Now, create a proposal to fix the issue. Ensure it follows all rules above.
If the proposal violates any rule, explain why and suggest an alternative.

Output format:
{{
  "compliant": true/false,
  "proposal": "...",
  "rule_violations": []
}}
"""
        return prompt
```

### 5. User Interface for Custom Artifacts

#### CLI Command

```bash
# Create custom artifact
contextpilot artifact create project_scope.md \
  --description "Project scope and boundaries" \
  --producer user \
  --consumers spec,strategy \
  --rule spec:"Reject proposals outside scope" \
  --rule strategy:"Align milestones with scope"

# Update artifact rules
contextpilot artifact rule project_scope.md spec \
  --prompt "Before creating proposals, read project_scope.md and ensure alignment"

# List artifacts
contextpilot artifact list

# Show artifact details
contextpilot artifact show project_scope.md
```

#### Extension UI

```typescript
// extension/src/commands/artifacts.ts

export async function createCustomArtifact(): Promise<void> {
  // 1. Ask for artifact name
  const name = await vscode.window.showInputBox({
    prompt: 'Artifact name (e.g., project_scope.md)',
    placeHolder: 'my_artifact.md'
  });
  
  // 2. Ask for description
  const description = await vscode.window.showInputBox({
    prompt: 'Description',
    placeHolder: 'What is this artifact for?'
  });
  
  // 3. Select consumers (multi-select)
  const agents = ['spec', 'strategy', 'git', 'coach', 'milestone'];
  const consumers = await vscode.window.showQuickPick(agents, {
    canPickMany: true,
    placeHolder: 'Which agents should read this artifact?'
  });
  
  // 4. Define rules for each consumer
  const rules: Record<string, string> = {};
  for (const agent of consumers || []) {
    const rule = await vscode.window.showInputBox({
      prompt: `Rule for ${agent} agent`,
      placeHolder: `When should ${agent} read this? What should it do?`,
      value: `Read ${name} before making decisions. Ensure actions align with content.`
    });
    if (rule) {
      rules[agent] = rule;
    }
  }
  
  // 5. Create artifact
  await service.createCustomArtifact({
    name,
    description,
    consumers: consumers || [],
    rules
  });
  
  vscode.window.showInformationMessage(`✅ Created ${name} with rules for ${consumers?.join(', ')}`);
}
```

### 6. Backend Endpoint

```python
# back-end/app/server.py

@app.post("/artifacts/create")
async def create_custom_artifact(
    workspace_id: str = Query(...),
    name: str = Body(...),
    description: str = Body(...),
    consumers: List[str] = Body(...),
    rules: Dict[str, str] = Body(...)
):
    """Create custom artifact with agent rules"""
    
    # 1. Load artifacts.yaml
    config_path = get_workspace_path(workspace_id, 'artifacts.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 2. Add custom artifact
    config['custom_artifacts'][name] = {
        'description': description,
        'producer': 'user',
        'consumers': consumers,
        'created_at': datetime.utcnow().isoformat(),
        'agent_rules': rules
    }
    
    # 3. Save config
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # 4. Create empty artifact file
    artifact_path = get_workspace_path(workspace_id, name)
    if not os.path.exists(artifact_path):
        with open(artifact_path, 'w') as f:
            f.write(f"# {name}\n\n{description}\n\n<!-- User content here -->\n")
    
    # 5. Publish event
    event_bus.publish('artifact.created.v1', {
        'artifact_name': name,
        'consumers': consumers
    })
    
    return {"status": "created", "artifact": name}

@app.get("/artifacts")
async def list_artifacts(workspace_id: str = Query(...)):
    """List all artifacts (system + custom)"""
    config_path = get_workspace_path(workspace_id, 'artifacts.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return {
        'system': config.get('system_artifacts', {}),
        'custom': config.get('custom_artifacts', {})
    }

@app.post("/artifacts/{artifact_name}/rules")
async def update_artifact_rules(
    artifact_name: str,
    workspace_id: str = Query(...),
    agent_id: str = Body(...),
    rule: str = Body(...)
):
    """Update agent rule for specific artifact"""
    config_path = get_workspace_path(workspace_id, 'artifacts.yaml')
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update rule
    if artifact_name not in config['custom_artifacts']:
        raise HTTPException(404, "Artifact not found")
    
    config['custom_artifacts'][artifact_name]['agent_rules'][agent_id] = rule
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    return {"status": "updated", "artifact": artifact_name, "agent": agent_id}
```

## Example Workflow

### 1. User Creates Custom Artifact

```bash
# Via CLI
contextpilot artifact create project_scope.md \
  --description "Project scope document" \
  --consumers spec,strategy \
  --rule spec:"Read project_scope.md before creating proposals. Reject any feature outside defined scope." \
  --rule strategy:"Ensure milestones align with scope boundaries defined in project_scope.md"
```

**Result:**
- `project_scope.md` created in workspace
- `artifacts.yaml` updated with rules
- Event `artifact.created.v1` published

### 2. User Edits Artifact

```markdown
# project_scope.md

## In Scope
- ✅ Multi-agent AI system
- ✅ VSCode extension
- ✅ Git integration
- ✅ Proposal approval flow

## Out of Scope
- ❌ Mobile app
- ❌ Real-time collaboration
- ❌ Video calls
- ❌ Blockchain beyond token rewards

## Success Criteria
- Launch before hackathon (Oct 20)
- At least 3 agents working
- Extension published to marketplace
```

### 3. Spec Agent Uses Artifact

```python
# Spec Agent runs
async def create_proposal(self, issue: Dict):
    # Load project_scope.md (configured as consumer)
    scope = self.consume_artifact('project_scope.md')
    
    # Build prompt with rule
    prompt = f"""
    You found this issue: {issue['description']}
    
    RULE: {self.agent_rules['project_scope.md']}
    
    PROJECT SCOPE:
    {scope}
    
    Create a proposal. If it violates scope, explain why and suggest alternative.
    """
    
    response = await llm.generate(prompt)
    
    # If proposal adds "mobile app" feature, LLM will reject it
    # because project_scope.md says mobile is out of scope
```

### 4. Strategy Agent Uses Same Artifact

```python
# Strategy Agent runs
async def update_milestones(self):
    # Load project_scope.md (also configured as consumer)
    scope = self.consume_artifact('project_scope.md')
    
    # Apply rule
    prompt = f"""
    RULE: {self.agent_rules['project_scope.md']}
    
    PROJECT SCOPE:
    {scope}
    
    Current milestones:
    {self.current_milestones}
    
    Ensure milestones align with scope. Flag any that don't.
    """
    
    updated_milestones = await llm.generate(prompt)
```

## Benefits

1. **Flexibility**: Users define custom workflows without code changes
2. **Natural Language Rules**: No need to learn complex configuration syntax
3. **Multi-Agent Coordination**: Same artifact guides multiple agents
4. **Auditable**: All rules stored in `artifacts.yaml` (version controlled)
5. **Extensible**: Easy to add new artifacts as project evolves

## Implementation Plan

### Phase 1: Core System (Week 1)
- [ ] Create `artifacts.yaml` schema
- [ ] Update `BaseAgent` to load artifact rules
- [ ] Implement `consume_artifact()` method
- [ ] Test with Spec Agent + `project_scope.md`

### Phase 2: User Interface (Week 2)
- [ ] CLI commands for artifact management
- [ ] Extension UI for creating artifacts
- [ ] Artifact list view in sidebar
- [ ] Rule editor

### Phase 3: Advanced Features (Week 3)
- [ ] Artifact templates (pre-defined common artifacts)
- [ ] Rule validation (ensure rules are actionable)
- [ ] Artifact dependency graph
- [ ] Conflict detection (if rules contradict)

### Phase 4: LLM Integration (Week 4)
- [ ] Inject artifact rules into all agent prompts
- [ ] Track rule compliance in proposals
- [ ] Generate "rule violation" reports
- [ ] Auto-suggest rules based on usage patterns

## Pre-defined Artifact Templates

```yaml
templates:
  project_scope:
    file: project_scope.md
    description: "Define what's in/out of scope"
    suggested_rules:
      spec: "Reject proposals outside scope"
      strategy: "Align milestones with scope"
  
  daily_checklist:
    file: daily_checklist.md
    description: "Daily tasks and reminders"
    suggested_rules:
      coach: "Remind user of incomplete tasks each morning"
      retrospective: "Analyze completion patterns"
  
  project_checklist:
    file: project_checklist.md
    description: "Master project checklist"
    suggested_rules:
      strategy: "Map milestones to checklist items"
      milestone: "Mark items complete on milestone finish"
```

---

**Next:** Implement Phase 1 alongside BaseAgent state management

