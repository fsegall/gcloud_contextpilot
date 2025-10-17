# 🧪 Manual Test - Local Backend + Extension

## ✅ Prerequisites

- [x] Docker Compose running (`docker-compose up -d`)
- [x] Backend healthy (`curl http://localhost:8000/health`)
- [x] Extension compiled (`cd extension && npm run compile`)
- [x] Settings updated (`.vscode/settings.json` → `"apiUrl": "http://localhost:8000"`)

---

## 🎯 Test Sequence

### Test 1: Extension Connects to Local Backend

**Steps:**
1. Open Extension Development Host (F5)
2. Open project folder in Extension Host
3. Check sidebar for ContextPilot icon 🚀
4. Expand Proposals section

**Expected Result:**
- ✅ Extension shows "Connected to http://localhost:8000"
- ✅ 2 proposals appear:
  - "Docs issue: ARCHITECTURE.md"
  - "Docs issue: README.md"
- ✅ No connection errors in console

**Debug Console:**
```
[ContextPilot] Connected to http://localhost:8000
[ContextPilot] Fetched 2 proposals
```

---

### Test 2: View Proposal Details

**Steps:**
1. Click on first proposal (README.md)
2. Expand to see details

**Expected Result:**
- ✅ Shows proposal title
- ✅ Shows description
- ✅ Shows file path
- ✅ Shows status: "pending"

---

### Test 3: Approve Proposal Flow (MAIN TEST)

**Steps:**
1. Right-click on "Docs issue: README.md"
2. Select "Approve Proposal"
3. Confirm in dialog: "Yes"
4. Wait for processing (~2-3 seconds)

**Expected Result:**
- ✅ Toast notification: "✅ Proposal approved (+10 CPT)"
- ✅ Proposal disappears from pending list (or status changes)
- ✅ Rewards section updates: 110 CPT
- ✅ Achievement notification (if first approval)

**In Terminal:**
```bash
# Check git log
git log --oneline -1

# Should show semantic commit:
# abc1234 docs(contextpilot): Update README.md documentation
```

**In Docker logs:**
```bash
docker-compose logs backend | tail -20

# Should show:
# INFO: POST /proposals/{id}/approve - 200 OK
```

---

### Test 4: Verify File Changes

**Steps:**
1. Check if README.md was updated
2. `git status` should show changes
3. `git diff` should show the proposal changes applied

**Expected Result:**
- ✅ README.md modified (or created)
- ✅ Git commit created automatically
- ✅ Commit message is semantic (feat/docs/fix...)

---

### Test 5: Rewards System

**Steps:**
1. Expand Rewards section in sidebar
2. Check CPT balance
3. Check achievements

**Expected Result:**
- ✅ CPT Balance: 110 (started at 100, +10 for approval)
- ✅ Achievement: "First Approval" unlocked
- ✅ Weekly Streak: 0 (or 1 if you approve daily)

---

### Test 6: Reject Proposal

**Steps:**
1. Right-click on second proposal (ARCHITECTURE.md)
2. Select "Reject Proposal"
3. Confirm

**Expected Result:**
- ✅ Proposal removed from pending list
- ✅ Status changed to "rejected" in backend
- ✅ No file changes
- ✅ No git commit

---

### Test 7: Backend API Health

**In terminal:**
```bash
# List proposals after approval
curl -s "http://localhost:8000/proposals?workspace_id=default" | jq '.count'
# Should show 2 (1 approved, 1 pending or rejected)

# Check agents status
curl -s "http://localhost:8000/agents/status" | jq

# Check abuse stats
curl -s "http://localhost:8000/admin/abuse-stats" | jq
```

**Expected Result:**
- ✅ All endpoints return 200
- ✅ Agents status shows all 6 agents
- ✅ Abuse stats show request counts

---

## 🐛 Common Issues & Solutions

### Issue 1: Extension shows "Connection failed"
**Solution:**
- Check `.vscode/settings.json` has `"apiUrl": "http://localhost:8000"`
- Run `npm run compile` in extension folder
- Reload Extension Development Host (Ctrl+R)

### Issue 2: No proposals appear
**Solution:**
```bash
# Create test proposal
curl -X POST "http://localhost:8000/proposals/create" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "default",
    "agent_id": "spec",
    "title": "Test Proposal",
    "description": "Testing approval flow",
    "proposed_changes": [{
      "file_path": "test.md",
      "change_type": "create",
      "after": "# Test\n\nThis is a test."
    }]
  }'
```

### Issue 3: Git commit fails
**Solution:**
```bash
# Configure git
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Issue 4: Docker container stopped
**Solution:**
```bash
docker-compose up -d
docker-compose logs backend | tail -50
```

---

## 📊 Success Criteria

Test is successful if:
- [x] Extension connects to local backend
- [x] Proposals load correctly
- [x] Approve creates git commit
- [x] Rewards system updates
- [x] No errors in console
- [x] Backend logs show successful requests

---

## 🎬 After Testing

Once all tests pass:
1. **Revert to Cloud Run:**
   - Update `.vscode/settings.json`:
     ```json
     "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app"
     ```
   - Recompile: `npm run compile`

2. **Prepare for video recording:**
   - Follow `VIDEO_DEMO_SCRIPT.md`
   - Use Cloud Run backend (production)
   - Clean terminal history
   - Disable notifications

3. **Create release v0.1.2**

4. **Make repo public**

5. **Submit to Devpost!**

---

**Ready? Let's test! 🚀**
