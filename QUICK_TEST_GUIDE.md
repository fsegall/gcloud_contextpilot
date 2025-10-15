# Quick Test Guide - AI-Assisted Review

**Date:** October 15, 2025  
**Time:** 5 minutes

## Prerequisites

- ✅ Backend running on `localhost:8000`
- ✅ Extension installed in Cursor

## Test Flow

### 1. Start Backend (if not running)

```bash
cd back-end
source .venv/bin/activate
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000
```

### 2. Create Test Proposal with Diff

```bash
cd back-end
python test_proposal_diffs.py
```

**Expected Output:**
```
✅ Created proposal: spec-missing_doc-XXXXXXXXXX
✅ Diff format: unified
✅ Diff length: 298 chars
```

### 3. Verify API Returns Diff

```bash
curl -s "http://localhost:8000/proposals?workspace_id=contextpilot" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); p=d['proposals'][0]; print(f'Has diff: {\"diff\" in p}')"
```

**Expected:** `Has diff: True`

### 4. Test Extension (Manual)

#### A. Open Extension Development Host
```
Press F5 in Cursor (or Ctrl+F5 if already open)
```

#### B. Connect to Backend
```
1. Cmd+Shift+P
2. Type: "ContextPilot: Connect"
3. Should show: "✅ Connected to ContextPilot!"
```

#### C. View Proposals
```
1. Open ContextPilot sidebar (left panel)
2. Expand "Change Proposals" section
3. Should see: "Docs issue: README.md"
```

#### D. View Diff
```
1. Click on proposal
2. Diff viewer opens with syntax highlighting
3. Should see:
   --- a/README.md
   +++ b/README.md
   @@ -0,0 +1,21 @@
   +# Readme
   ...
```

#### E. Ask Claude to Review
```
1. Quick pick menu appears
2. Select: "🤖 Ask Claude to Review"
3. Message: "Review context copied to clipboard!"
4. Click "Open Chat"
5. Cursor Chat opens
6. Paste (Cmd+V)
7. Claude analyzes the diff
8. Claude responds with recommendation
```

#### F. Approve Proposal
```
1. Based on Claude's feedback, decide
2. If approve: Select "✅ Approve"
3. Should show: "✅ Proposal approved (pending commit)"
4. Check git log to see commit
```

### 5. Verify Git Commit

```bash
cd back-end/.contextpilot/workspaces/contextpilot
git log --oneline -3
```

**Expected:**
```
xxxxxxx agent(proposal): Apply proposal spec-missing_doc-XXXXXXXXXX
```

---

## Expected Claude Response (Example)

When you paste the review context, Claude might respond:

> "I've analyzed the proposed changes to README.md. Here's my assessment:
> 
> **Verdict: ✅ Approve**
> 
> **Reasoning:**
> 1. **Structure:** The README follows standard markdown conventions with clear sections (Overview, Purpose, Usage, Examples, References)
> 2. **Completeness:** Includes placeholders for user to fill in project-specific details
> 3. **Quality:** Clean, well-organized, and easy to read
> 4. **No Concerns:** No security issues, breaking changes, or code quality problems
> 
> **Recommendation:** I recommend approving this proposal. It creates a solid foundation for project documentation that you can build upon."

---

## Troubleshooting

### Backend not responding
```bash
pkill -f uvicorn
cd back-end && source .venv/bin/activate
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000
```

### Extension not connecting
```
1. Check backend is running: curl http://localhost:8000/health
2. Check extension settings: Cmd+, → search "contextpilot"
3. Verify API URL: http://localhost:8000
```

### No proposals showing
```bash
# Generate new proposals
curl -X POST "http://localhost:8000/proposals/create?workspace_id=contextpilot"
```

### Diff not showing
```
1. Check proposal has diff: curl http://localhost:8000/proposals/PROPOSAL_ID
2. Look for "diff" field in JSON
3. If missing, regenerate proposal with test_proposal_diffs.py
```

---

## Success Criteria

- ✅ Backend returns proposals with diffs
- ✅ Extension shows diff viewer
- ✅ Claude integration copies context
- ✅ Cursor Chat opens
- ✅ User can paste and get AI review
- ✅ Approval triggers Git Agent
- ✅ Commit appears in git log

---

## Next Steps After Testing

1. Fix any bugs found
2. Improve UI/UX
3. Add Gemini integration
4. Deploy to GCP
5. Beta test with friends

---

**Status:** ✅ Ready for testing!  
**Time to test:** ~5 minutes  
**Confidence:** 🔥 High - all components tested individually

**Let's test it! 🚀**

