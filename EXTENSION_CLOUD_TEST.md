# Extension Cloud Test - Quick Guide

**Testing ContextPilot Extension with Google Cloud Backend**

---

## 🎯 What We're Testing

Extension → Cloud Run → Pub/Sub → Agents → Results

**Service URL:** `https://contextpilot-backend-898848898667.us-central1.run.app`

---

## 🚀 How to Test

### Step 1: Open Extension Development Host

**In Cursor:**
1. Open the `extension` folder in Cursor
2. Press **F5** (or **Ctrl+F5**)
3. Extension Development Host window will open

**Or via Terminal:**
```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension
code --extensionDevelopmentPath=. /tmp/test-workspace
```

---

### Step 2: Open ContextPilot Sidebar

In the Extension Development Host window:
1. Look for the **rocket icon** (🚀) in the Activity Bar (left side)
2. Click it to open ContextPilot sidebar
3. You should see sections:
   - **CHANGE PROPOSALS**
   - **AGENTS**
   - **REWARDS**
   - **PROJECT CONTEXT**

---

### Step 3: Check Connection

**Look at the bottom status bar:**
- Should show: **ContextPilot** with token balance
- If it says "Disconnected", click "Connect to ContextPilot"

**Check Developer Console:**
1. Open Dev Tools: **Ctrl+Shift+I** (Linux) or **Cmd+Option+I** (Mac)
2. Go to **Console** tab
3. Look for logs:
   ```
   [ContextPilot] Extension activated - API: https://contextpilot-backend-898848898667.us-central1.run.app
   [ContextPilot] Auto-connect completed, refreshing providers...
   ```

---

### Step 4: View Proposals

**In the CHANGE PROPOSALS section:**
1. Expand the section
2. You should see existing proposals:
   - "Docs issue: README.md"
   - "Docs issue: API_SPEC.md"
   - etc.

**Click on a proposal to:**
- View the diff
- Ask Claude to review
- Approve or reject

---

### Step 5: Test Cloud Connection

**Open Terminal in Extension Dev Host:**

```bash
# Test health endpoint
curl https://contextpilot-backend-898848898667.us-central1.run.app/health

# Expected: {"status":"ok","version":"2.0.0"...}
```

**Or test from extension:**
1. Click on any proposal
2. Extension should load the diff from Cloud Run
3. If it works = CONNECTION SUCCESS! 🎉

---

## 🧪 What to Check

### ✅ Success Indicators

1. **Sidebar loads** - Shows proposals, agents, rewards
2. **Proposals clickable** - Can view diffs
3. **No 404 errors** - Cloud Run responding
4. **Console logs clean** - No red errors
5. **Claude integration works** - Can ask for review

### ❌ Failure Indicators

1. **"Failed to fetch proposals"** - Backend not responding
2. **404 errors** - Wrong URL
3. **CORS errors** - Need to enable CORS in backend
4. **Timeout errors** - Cloud Run cold start (wait 5s, retry)

---

## 🐛 Troubleshooting

### Extension Shows "No Proposals"

**Check 1: Backend is running**
```bash
curl https://contextpilot-backend-898848898667.us-central1.run.app/health
```

**Check 2: Proposals exist**
```bash
curl "https://contextpilot-backend-898848898667.us-central1.run.app/proposals?workspace_id=contextpilot"
```

**Check 3: Extension logs**
- Open Console (Ctrl+Shift+I)
- Look for errors
- Should see: `[ContextPilot] Fetched X proposals`

### CORS Errors

If you see: `Access to fetch ... has been blocked by CORS policy`

**Fix:** Add CORS middleware to backend (already should be OK with FastAPI default)

### Connection Timeout

**Cause:** Cloud Run cold start (first request takes ~5s)

**Fix:** Wait 5 seconds and click "Refresh" or retry

---

## 📊 Test Checklist

### Basic Connection
- [ ] Extension sidebar appears
- [ ] Status bar shows "ContextPilot"
- [ ] Console shows connection logs
- [ ] No red errors in console

### Proposals
- [ ] Proposals load in sidebar
- [ ] Can click on a proposal
- [ ] Diff viewer opens
- [ ] Can see proposal details

### Cloud Integration
- [ ] Backend responds to /health
- [ ] Backend responds to /proposals
- [ ] Extension shows real data (not mocks)
- [ ] No 404/500 errors

### Advanced Features
- [ ] Can ask Claude to review
- [ ] Can approve proposal
- [ ] Can reject proposal
- [ ] Status updates correctly

---

## 🎥 For Demo Video

### Recording Checklist

1. **Show extension in action:**
   - Open sidebar
   - Show proposals
   - Click on proposal

2. **Show diff viewer:**
   - Clean, readable diff
   - Before/after clear

3. **Show Claude integration:**
   - Click "Ask Claude to Review"
   - Show AI feedback
   - Show decision process

4. **Show approval flow:**
   - Approve proposal
   - Show success message
   - Show that proposal status updated

5. **Show Cloud Console (parallel window):**
   - Cloud Run service running
   - Pub/Sub messages flowing
   - Logs showing requests

---

## 🎯 Success Criteria

**Minimum for Hackathon:**
- ✅ Extension connects to Cloud Run
- ✅ Proposals load from cloud
- ✅ Diff viewer works
- ✅ Basic approve/reject works

**Nice to Have:**
- ✅ Claude integration smooth
- ✅ No errors or crashes
- ✅ Fast response times (< 1s)
- ✅ Beautiful UI

---

## 📝 What to Record for Demo

### Opening (10 sec)
> "Here's ContextPilot running in VSCode, connected to our production backend on Google Cloud Run."

### Show Proposals (20 sec)
> "The Spec Agent detected missing documentation and created these proposals. Each proposal includes a full diff showing exactly what will change."

### Show Diff (20 sec)
> "Here's the diff for this proposal. Before approving, I can ask Claude to review it."

### Show Claude Review (20 sec)
> "Claude analyzes the changes and provides feedback. Based on this, I can approve or reject."

### Show Approval (10 sec)
> "When I approve, the Git Agent automatically applies the changes and commits them."

### Show Cloud (10 sec)
> "Behind the scenes, this all runs on Google Cloud - Cloud Run for the backend, Pub/Sub for events, Firestore for storage."

**Total:** 90 seconds = perfect for demo!

---

## 🚀 Quick Start Commands

```bash
# Terminal 1: Ensure backend is running
curl https://contextpilot-backend-898848898667.us-central1.run.app/health

# Terminal 2: Open Extension Dev
cd extension
code --extensionDevelopmentPath=. /tmp/test-workspace

# Or just press F5 in Cursor!
```

---

**Ready? Press F5 and let's test!** 🚀

**Service URL:** https://contextpilot-backend-898848898667.us-central1.run.app  
**Status:** 🟢 READY TO TEST

