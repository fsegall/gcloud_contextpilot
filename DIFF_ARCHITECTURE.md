# Diff Architecture: Como os Diffs São Gerados e Usados

## 🎯 Objetivo

**Toda proposta DEVE ter diff para o usuário poder revisar antes de aprovar!**

---

## 📊 Fluxo Completo: Retrospective → Código

```
┌─────────────────────────────────────────────────────────────┐
│                    USER TRIGGERS RETROSPECTIVE               │
│                "Can you identify code to improve?"           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              RETROSPECTIVE AGENT                             │
│  1. Collects agent metrics                                   │
│  2. Runs agent meeting (real or LLM)                        │
│  3. Generates insights & action items                        │
│  4. Identifies CODE vs DOC actions                          │
└─────────┬───────────────────────────┬───────────────────────┘
          ↓                           ↓
    [DOC ACTIONS]              [CODE ACTIONS] ✨
          ↓                           ↓
          │                  ┌────────────────────────┐
          │                  │  DEVELOPMENT AGENT     │
          │                  │  - Loads full context  │
          │                  │  - Infers target files │
          │                  │  - Calls Gemini AI     │
          │                  │  - Generates code      │
          │                  └────────┬───────────────┘
          ↓                           ↓
┌─────────────────────┐      ┌────────────────────────┐
│  PROPOSAL #1        │      │  PROPOSAL #2           │
│  (Documentation)    │      │  (Code Implementation) │
│                     │      │                        │
│ 📄 MD file          │      │ 💻 PY/TS files         │
│ ✅ HAS DIFF         │      │ ✅ HAS DIFF            │
└─────────┬───────────┘      └────────┬───────────────┘
          │                           │
          └───────────┬───────────────┘
                      ↓
           ┌────────────────────┐
           │  USER REVIEWS      │
           │  in VS Code        │
           │  - View Diff       │
           │  - See Changes     │
           │  - Approve/Reject  │
           └─────────┬──────────┘
                     ↓
              [User Approves]
                     ↓
           ┌────────────────────┐
           │  GITHUB ACTION     │
           │  - Applies changes │
           │  - Commits code    │
           │  - Pushes to repo  │
           └─────────┬──────────┘
                     ↓
                CODE LIVE! 🎉
```

---

## 🔧 Implementação Técnica

### 1. Diff Generator (Shared Utility)

**File:** `back-end/app/agents/diff_generator.py`

```python
def generate_unified_diff(
    file_path: str,
    old_content: str,
    new_content: str
) -> str:
    """
    Generate unified diff between old and new content.
    
    Returns:
        Unified diff string (Git patch format)
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    )
    
    return "".join(diff)
```

### 2. Agent Implementations

#### A) **Retrospective Agent** (Documentation)

**When:** Creates markdown documentation from retrospective
**Files:** `docs/agent_improvements_*.md`

```python
# Generate diff for new markdown file
file_path = f"docs/agent_improvements_{retro_id}.md"
diff_content = generate_unified_diff(
    file_path=file_path,
    old_content="",  # New file
    new_content=proposal_description
)

proposal_data = {
    "diff": {
        "format": "unified",
        "content": diff_content  # ✅ Diff included
    },
    "proposed_changes": [{
        "file_path": file_path,
        "diff": diff_content,  # ✅ Per-file diff too
        "after": proposal_description
    }]
}
```

#### B) **Development Agent** (Code Implementation) ✨

**When:** Generates real code from action items
**Files:** Python, TypeScript, any code file

```python
# For each file to modify
for file_path, new_content in implementations.items():
    old_content = file_contents.get(file_path) or ""
    
    # Generate diff per file
    diff = generate_unified_diff(
        file_path=file_path,
        old_content=old_content,
        new_content=new_content
    )
    
    proposed_changes.append(
        ProposedChange(
            file_path=file_path,
            diff=diff,  # ✅ Per-file diff
            after=new_content
        )
    )

# Generate overall diff (all files combined)
overall_diff = self._generate_overall_diff(proposed_changes)

proposal = ChangeProposal(
    diff=overall_diff,  # ✅ Overall diff
    proposed_changes=proposed_changes
)
```

#### C) **Spec Agent** (Documentation Issues)

**When:** Detects documentation issues
**Files:** `*.md` files

```python
# Generate diff for documentation fix
diff_content = generate_unified_diff(
    file_path=file_path,
    old_content=current_content,
    new_content=fixed_content
)

proposal_data = {
    "diff": {
        "format": "unified",
        "content": diff_content  # ✅ Diff included
    }
}
```

---

## 📦 Proposal Data Structure

### Complete Proposal Object

```typescript
{
  id: "dev-1729566234",
  workspace_id: "contextpilot",
  user_id: "system",
  agent_id: "development",
  title: "💻 Fix agent error handling",
  description: "...",
  
  // ✅ OVERALL DIFF (all changes combined)
  diff: {
    format: "unified",
    content: `
--- a/back-end/app/agents/base_agent.py
+++ b/back-end/app/agents/base_agent.py
@@ -45,7 +45,18 @@ class BaseAgent:
     async def handle_event(self, event_type: str, data: Dict):
-        self.process(data)
+        try:
+            await self.process(data)
+        except Exception as e:
+            logger.error(f"Error: {e}")
    `
  },
  
  // ✅ PER-FILE CHANGES
  proposed_changes: [
    {
      file_path: "back-end/app/agents/base_agent.py",
      change_type: "modify",
      description: "Add error handling",
      before: "... old code ...",
      after: "... new code ...",
      
      // ✅ PER-FILE DIFF
      diff: "--- a/back-end/app/agents/base_agent.py\n+++ ..."
    },
    {
      file_path: "back-end/app/agents/git_agent.py",
      // ... another file
    }
  ],
  
  status: "pending",
  created_at: "2025-10-22T02:49:59+00:00"
}
```

---

## 🎨 VS Code Extension Display

### 1. **Proposals View (Tree)**

```
📋 Proposals (2)
  ├─ 📝 retro-proposal-retro-20251022-024959
  │   by retrospective • 1 file
  │   💡 Right-click for actions
  │   └─ 📄 docs/agent_improvements_retro-20251022-024959.md
  │
  └─ 💻 dev-1729566234
      by development • 2 files
      💡 Right-click for actions
      ├─ 📄 back-end/app/agents/base_agent.py
      └─ 📄 back-end/app/agents/git_agent.py
```

### 2. **View Diff Command**

**Right-click → "View Proposal Diff"**

Opens document showing:

```diff
# Proposal: Fix agent error handling

## Description
From Retrospective: retro-20251022-024959
Priority: HIGH

Action Item: Fix agent error handling

## Changes (2 files)

### File: back-end/app/agents/base_agent.py

--- a/back-end/app/agents/base_agent.py
+++ b/back-end/app/agents/base_agent.py
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
+        except Exception as e:
+            logger.error(f"[{self.agent_id}] Unexpected error: {e}")
+            self.increment_metric("errors")

### File: back-end/app/agents/git_agent.py
...
```

---

## ⚙️ GitHub Action Application

### When User Approves

**File:** `.github/workflows/apply-proposal.yml`

```yaml
- name: Apply Changes
  run: |
    # For each proposed_change in proposal
    for change in proposal.proposed_changes:
      file_path = change.file_path
      new_content = change.after
      
      # Write file
      mkdir -p $(dirname $file_path)
      echo "$new_content" > $file_path
      
      # Stage
      git add $file_path

- name: Commit
  run: |
    git commit -m "Apply proposal: $PROPOSAL_TITLE
    
    Generated by: $AGENT_ID
    Proposal ID: $PROPOSAL_ID
    
    Changes:
    - $FILE1
    - $FILE2"

- name: Push
  run: git push origin main
```

---

## ✅ Validation Checklist

### Before Deployment
- [ ] All 3 agents import `generate_unified_diff` ✅
- [ ] All 3 agents call `generate_unified_diff` ✅
- [ ] All proposals include `diff` field ✅
- [ ] All `proposed_changes` include per-file `diff` ✅

### After Deployment
- [ ] Retrospective creates documentation proposal with diff
- [ ] Development Agent generates code proposal with diff
- [ ] Extension shows both proposals
- [ ] "View Diff" command displays changes
- [ ] Approval triggers GitHub Action
- [ ] Code is committed to repository

---

## 🐛 Debugging

### If diff is missing:

**1. Check Backend Logs**
```bash
# Look for diff generation
grep "generate_unified_diff" backend.log

# Check proposal creation
grep "Proposal created" backend.log
```

**2. Check Firestore**
```bash
# Query proposal
gcloud firestore read proposals/$PROPOSAL_ID

# Should have:
{
  "diff": {
    "format": "unified",
    "content": "--- a/...\n+++ b/..."
  }
}
```

**3. Check Extension**
```typescript
// In contextpilot.ts
const proposal = await getProposal(id);
console.log("Diff content:", proposal.diff?.content);

// Should NOT be null or empty
```

---

## 🎯 Summary

### What Changed Today

✅ **Retrospective Agent** now:
- Identifies code vs doc actions
- Triggers Development Agent for code
- Still creates its own doc proposals

✅ **Development Agent** now:
- Generates REAL CODE implementations
- Creates proposals with full diffs
- Uses AI to understand context

✅ **All proposals** have:
- Overall diff (all files)
- Per-file diffs
- Before/after content
- Full context

### Result
**Users can now:**
1. 🤖 Trigger retrospective
2. 👀 See AI-generated code proposals
3. 📊 Review diffs in extension
4. ✅ Approve with confidence
5. 🚀 Code auto-commits via GitHub Action

---

**Status:** ✅ Deployed
**Date:** October 22, 2025
**Files Modified:** 1 (retrospective_agent.py)
**Lines Added:** ~100
**Feature:** Auto-code-generation from retrospectives


