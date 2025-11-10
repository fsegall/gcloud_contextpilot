# Retrospective → Code Generation Flow

## 🎯 Feature: Auto-Generated Code Proposals

The **Retrospective Agent** now automatically triggers the **Development Agent** to generate **real code implementations** (not just documentation) when action items require code changes!

---

## 🔄 How It Works

### 1️⃣ **Retrospective Analysis**
- User triggers retrospective via extension
- Agents discuss and identify improvement areas
- System generates **action items** with priorities

### 2️⃣ **Code Action Detection** ✨ NEW
```python
def _identify_code_actions(action_items: List[Dict]) -> List[Dict]:
    """
    Identifies action items that need code implementation.
    
    Looks for keywords:
    - implement, add, create, fix, refactor, update
    - error handling, validation, endpoint, api
    - function, method, class, component, service
    - schema, protocol, message, event handler
    
    Excludes:
    - Pure documentation tasks
    """
```

**Example action items that trigger code generation:**
- ✅ "Fix agent error handling" → **Code generated**
- ✅ "Add validation to event handlers" → **Code generated**
- ✅ "Implement message queue" → **Code generated**
- ❌ "Update README documentation" → **No code, just markdown**

### 3️⃣ **Development Agent Triggered** ✨ NEW
```python
async def _trigger_development_agent(retrospective, code_actions):
    """
    For each code action:
    1. Initialize DevelopmentAgent with project context
    2. Build comprehensive description with retrospective context
    3. Call implement_feature() to generate actual code
    4. Create proposal with real diffs
    """
```

### 4️⃣ **Code Generation with AI**
The Development Agent uses **Gemini 2.5 Flash** to:
- 📖 Load full project context (like Claude does)
- 🎯 Infer which files need changes
- 📝 Read existing code
- ✨ Generate production-ready implementations
- 📊 Create unified diffs

### 5️⃣ **Proposals Created**
You'll see **TWO types of proposals**:

#### A) **Documentation Proposal** (from Retrospective Agent)
```
ID: retro-proposal-retro-20251022-024959
Title: "Can you identify any code... - Recommendations"
Content: Markdown with action items and guidance
Files: docs/agent_improvements_*.md
```

#### B) **Code Implementation Proposal** (from Development Agent) ✨ NEW
```
ID: dev-1729566234
Title: "💻 Fix agent error handling"
Content: Real Python/TypeScript code
Files: back-end/app/agents/*.py, extension/src/*.ts
Diff: Unified diff showing exact code changes
```

---

## 📊 Complete Flow Diagram

```
User triggers retrospective
         ↓
┌────────────────────────┐
│  Retrospective Agent   │
│  - Collects metrics    │
│  - Runs agent meeting  │
│  - Generates insights  │
│  - Extracts actions    │
└────────┬───────────────┘
         ↓
    [Action Items]
         ↓
    ┌────────┴────────┐
    ↓                 ↓
[Doc Actions]   [Code Actions] ✨ NEW
    ↓                 ↓
Creates MD      Triggers Dev Agent
Proposal             ↓
                ┌────────────────────┐
                │ Development Agent  │
                │ - Loads context    │
                │ - Infers files     │
                │ - Generates code   │
                │ - Creates diffs    │
                └────────┬───────────┘
                         ↓
                  Code Proposal
                         ↓
                  User Approves
                         ↓
                   GitHub Action
                         ↓
                  Code Applied! 🎉
```

---

## 🧪 Testing

### Test 1: Trigger retrospective with code-related topic
```
Topic: "Can you identify any code that could be improved for agents?"

Expected:
- Retrospective completes ✅
- Documentation proposal created ✅
- Code implementation proposal created ✅ NEW
- Proposal has real code diffs ✅ NEW
```

### Test 2: Review generated code
```
1. Open VS Code extension
2. View "Proposals" in sidebar
3. See TWO proposals:
   - retro-proposal-* (markdown)
   - dev-* (code) ✨ NEW
4. Right-click dev-* → "View Proposal Diff"
5. See actual code changes!
```

### Test 3: Approve and apply
```
1. Right-click dev-* → "Approve Proposal"
2. GitHub Action runs
3. Code is committed to repository
4. Changes appear in git log
```

---

## 🎛️ Configuration

### Backend Environment Variables
```bash
GEMINI_API_KEY=your_key_here  # Required for code generation
FIRESTORE_ENABLED=true        # Required for Cloud mode
STORAGE_MODE=cloud            # Required for proposals
```

### Agent Behavior

**When does Development Agent run?**
- ✅ When retrospective identifies code actions
- ✅ When manually triggered via API
- ❌ NOT on every retrospective (only when needed)

**Keyword Detection:**
The system looks for these patterns in action items:
```python
code_keywords = [
    "implement", "add", "create", "fix", "refactor", "update",
    "error handling", "validation", "endpoint", "api",
    "function", "method", "class", "component", "service",
    "agent code", "schema", "protocol", "message", "event handler"
]
```

---

## 🔧 Technical Details

### Files Modified
1. **back-end/app/agents/retrospective_agent.py**
   - Added `_identify_code_actions()` method
   - Added `_trigger_development_agent()` method
   - Integrated into `_create_improvement_proposal()`

2. **back-end/app/agents/development_agent.py**
   - Already had `implement_feature()` (no changes needed)
   - Already had AI code generation (no changes needed)
   - Already created proposals with diffs (no changes needed)

### Dependencies
- `app.agents.development_agent.DevelopmentAgent`
- `app.agents.diff_generator.generate_unified_diff`
- `google.generativeai` (Gemini API)

### Error Handling
- If `GEMINI_API_KEY` is missing, logs warning and skips code generation
- If Development Agent fails, logs error but retrospective continues
- If file inference fails, fallback mechanisms exist

---

## 🎉 Benefits

### For Users
- 🤖 **AI writes the code for you!**
- 📝 See actual implementation before applying
- ✅ One-click approval to apply changes
- 🔍 Full diff review in extension

### For Development
- 🔄 Closes the feedback loop completely
- 📊 Retrospective → Insights → Code → Commit
- 🧠 AI understands full project context
- 🛡️ Safe: user approval required before applying

### For System
- 📈 Continuous self-improvement
- 🤝 True agent collaboration
- 🎯 Actionable outcomes from retrospectives
- 💡 Code reflects learnings automatically

---

## 🚀 Next Steps

1. **Deploy backend** with new integration
2. **Test retrospective** with code-focused topic
3. **Review generated proposals** in extension
4. **Approve and verify** code is applied correctly
5. **Monitor metrics** for code generation success rate

---

## 📝 Example Output

### Example Retrospective Topic
```
"Can you identify any code that could be improved for the agents to interact and make good decisions?"
```

### Example Generated Proposals

#### 1. Documentation (Retrospective Agent)
```markdown
# Can you identify any code... - Recommendations

**Generated from Retrospective:** retro-20251022-024959

## Proposed Changes

### 1. Review error logs and fix agent error handling
**Priority:** HIGH
**Implementation:**
- Review error logs in `.agent_state/` files
- Add try-catch blocks around agent operations
- Improve error reporting to event bus
```

#### 2. Code Implementation (Development Agent) ✨ NEW
```python
# back-end/app/agents/base_agent.py

@@ -45,7 +45,18 @@ class BaseAgent:
     async def handle_event(self, event_type: str, data: Dict) -> None:
-        # Process event
-        self.process(data)
+        try:
+            # Process event with error handling
+            logger.info(f"[{self.agent_id}] Processing {event_type}")
+            await self.process(data)
+            self.increment_metric("events_processed")
+        except ValidationError as e:
+            logger.error(f"[{self.agent_id}] Validation error: {e}")
+            self.increment_metric("errors")
+            await self.publish_error_event(event_type, str(e))
+        except Exception as e:
+            logger.error(f"[{self.agent_id}] Unexpected error: {e}")
+            self.increment_metric("errors")
+            await self.publish_error_event(event_type, str(e))
```

---

**Status:** ✅ Implemented, ready for deployment
**Date:** October 22, 2025
**Version:** 0.4.5 (next)


