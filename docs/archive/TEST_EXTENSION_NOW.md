# 🚀 Test Extension Now - Quick Guide

**Ready:** ✅ Backend running with Gemini  
**Time:** 5 minutes

---

## 🎯 Complete Flow to Test

### 1. Open Extension Development Host (30 seconds)

```
In Cursor:
- Press F5 (or Ctrl+F5 if already open)
- New window opens: "[Extension Development Host]"
```

### 2. Connect to Backend (10 seconds)

```
In new window:
- Cmd+Shift+P (or Ctrl+Shift+P)
- Type: "ContextPilot: Connect"
- Should show: "✅ Connected to ContextPilot!"
```

### 3. View Proposals (20 seconds)

```
- Click ContextPilot icon in left sidebar (rocket icon)
- Expand "Change Proposals" section
- Should see proposals with AI-generated content
```

### 4. View Diff (30 seconds)

```
- Click on a proposal
- Diff viewer opens with syntax highlighting
- See the AI-generated README content
- Quick actions menu appears:
  • 🤖 Ask Claude to Review
  • ✅ Approve  
  • ❌ Reject
  • 👁️  View Files
```

### 5. Ask Claude to Review (1 minute)

```
- Select "🤖 Ask Claude to Review"
- Review Panel opens (side-by-side)
- Context copied to clipboard
- Click "Open Chat" or press Cmd+L
- Paste (Cmd+V) in Cursor Chat
- Claude analyzes the diff
- Claude responds with recommendation
```

**Example Claude Response:**
> "I've reviewed the AI-generated README. It looks professional with:
> - Clear structure and sections
> - Comprehensive installation instructions
> - Best practices included
> - Proper markdown formatting
> 
> ✅ I recommend approving this proposal."

### 6. Approve Proposal (20 seconds)

```
- Based on Claude's feedback, click "✅ Approve"
- Extension shows: "✅ Proposal approved and committed! (cd5c616)"
- Git Agent applies changes
- README.md created in workspace
- Commit appears in git log
```

### 7. Verify Result (30 seconds)

```
In terminal:
cd back-end/.contextpilot/workspaces/contextpilot
ls -lh README.md
git log --oneline -3
```

**Expected:**
```
-rw-rw-r-- 1 user user 4.3K README.md
cd5c616 agent(proposal): Apply proposal: Docs issue
```

---

## 🎨 What You'll See

### Review Panel (Side-by-Side)

```
┌────────────────────────────────────────────────────────┐
│ 🤖 ContextPilot AI Review Session                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│ 👤 You (Proposal: spec-missing_doc-1760571093)        │
│                                                         │
│ # Review Proposal #spec-missing_doc-1760571093         │
│                                                         │
│ **Title:** Docs issue: README.md                       │
│ **Agent:** spec                                        │
│                                                         │
│ ## Changes                                             │
│ ```diff                                                │
│ --- a/README.md                                        │
│ +++ b/README.md                                        │
│ @@ -0,0 +1,128 @@                                     │
│ +# Project Title                                       │
│ +## Overview                                           │
│ +This document serves as...                            │
│ ```                                                    │
│                                                         │
│ 💡 Context copied to clipboard!                        │
│ Open Cursor Chat (Cmd+L) and paste                     │
└────────────────────────────────────────────────────────┘
```

### Diff Viewer

```
┌────────────────────────────────────────────────────────┐
│ diff ─ README.md (preview)                    ×        │
├────────────────────────────────────────────────────────┤
│  1 | --- a/README.md                                   │
│  2 | +++ b/README.md                                   │
│  3 | @@ -0,0 +1,128 @@                                │
│  4 | +```markdown                                      │
│  5 | +# Project Title                                  │
│  6 | +                                                  │
│  7 | +## Overview                                      │
│  8 | +                                                  │
│  9 | +This document serves as the primary entry...     │
│ 10 | +                                                  │
│ 11 | +## Purpose/Objectives                            │
│ 12 | +                                                  │
│ 13 | +The primary objectives of this project are to:   │
│ 14 | +                                                  │
│ 15 | +*   Develop a multi-agent AI system              │
│    |   ...                                             │
└────────────────────────────────────────────────────────┘
```

---

## 🧪 Test Checklist

- [ ] Extension connects to backend
- [ ] Proposals appear in sidebar
- [ ] Clicking proposal opens diff viewer
- [ ] Diff has syntax highlighting
- [ ] Quick actions menu appears
- [ ] "Ask Claude" copies context to clipboard
- [ ] Review Panel opens (side-by-side)
- [ ] Cursor Chat can be opened
- [ ] Pasting context works
- [ ] Claude provides meaningful review
- [ ] Approve button works
- [ ] Success message shows commit hash
- [ ] File actually created in workspace
- [ ] Commit appears in git log

---

## 🐛 If Something Doesn't Work

### Extension won't connect
```bash
# Check backend is running
curl http://localhost:8000/health

# Should return: {"status":"ok",...}
```

### No proposals showing
```bash
# Generate new proposal
cd back-end
export GOOGLE_API_KEY=AIzaSyBNxMHMiAbuq5Yh63DgcD6obERUb8iD_Pg
python test_proposal_diffs.py
```

### Diff not showing
```
Check: Extension console (Help → Toggle Developer Tools)
Look for errors in console
```

### Claude integration doesn't work
```
- Context should be in clipboard (Cmd+V to verify)
- Cursor Chat: Cmd+L or Ctrl+L
- Paste manually if auto-open doesn't work
```

---

## 🎉 Success Criteria

**You'll know it's working when:**
1. ✅ Proposal appears in sidebar
2. ✅ Diff viewer shows AI-generated content
3. ✅ Claude reviews and recommends
4. ✅ Approval creates README.md
5. ✅ Git log shows agent commit
6. ✅ README has professional content

---

## 🚀 Ready Commands

```bash
# Backend status
curl http://localhost:8000/health

# List proposals
curl "http://localhost:8000/proposals?workspace_id=contextpilot"

# Generate new proposal
cd back-end && python test_proposal_diffs.py
```

---

**STATUS:** 🟢 Ready to test!  
**Backend:** Running on localhost:8000  
**Gemini:** Configured and working  
**Proposals:** Available with AI-generated diffs

**Press F5 and let's go! 🚀**

