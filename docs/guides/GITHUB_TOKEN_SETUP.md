# GitHub Token Setup for ContextPilot

This guide explains how to create a GitHub Personal Access Token (PAT) so that ContextPilot can trigger GitHub Actions when proposals are approved.

## 1. Create GitHub Personal Access Token

### Step 1: Go to GitHub Settings
1. Navigate to: https://github.com/settings/tokens
2. Or: Click your profile → Settings → Developer settings → Personal access tokens → Tokens (classic)

### Step 2: Generate New Token
1. Click **"Generate new token"** → **"Generate new token (classic)"**
2. Give it a descriptive name: `ContextPilot Automation`
3. Select expiration: `No expiration` (or `90 days` for security)

### Step 3: Select Scopes
Select **ONLY** these permissions:
- ✅ **`repo`** (Full control of private repositories)
  - This includes:
    - `repo:status` (Access commit status)
    - `repo_deployment` (Access deployment status)
    - `public_repo` (Access public repositories)
    - `repo:invite` (Access repository invitations)

That's it! Just the `repo` scope is sufficient.

### Step 4: Generate and Copy
1. Click **"Generate token"** at the bottom
2. **IMPORTANT:** Copy the token immediately! You won't be able to see it again.
3. Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 2. Add Token to Google Cloud Run

### Option A: Using gcloud CLI (Recommended)

```bash
# Navigate to backend directory
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/back-end

# Update Cloud Run service with GitHub token
gcloud run services update contextpilot-backend \
  --region us-central1 \
  --update-env-vars="GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE,GITHUB_REPO=fsegall/gcloud_contextpilot"
```

### Option B: Using Google Cloud Console

1. Go to: https://console.cloud.google.com/run
2. Find and click: `contextpilot-backend`
3. Click: **"EDIT & DEPLOY NEW REVISION"**
4. Under **"Variables & Secrets"**, click **"+ ADD VARIABLE"**
5. Add:
   - Name: `GITHUB_TOKEN`
   - Value: `ghp_YOUR_TOKEN_HERE`
6. Add another:
   - Name: `GITHUB_REPO`
   - Value: `fsegall/gcloud_contextpilot`
7. Click **"DEPLOY"**

---

## 3. Test the Integration

### Step 1: Approve a Proposal in ContextPilot Extension
1. Open VS Code/Cursor with ContextPilot extension
2. Go to ContextPilot sidebar → **Change Proposals**
3. Click on a pending proposal → **"Approve"**

### Step 2: Check GitHub Actions
```bash
# Check recent workflow runs
cd /home/fsegall/Desktop/New_Projects/google-context-pilot
gh run list --limit 5

# Watch a specific run
gh run watch
```

### Step 3: Verify in Cloud Run Logs
```bash
# View recent logs
gcloud run services logs read contextpilot-backend \
  --region us-central1 \
  --limit 50
```

Look for:
- ✅ `✅ GitHub Action triggered for proposal: retro-proposal-xxx`
- ❌ `❌ GitHub Action trigger failed: ...` (if there's an error)

---

## 4. Security Notes

⚠️ **Important Security Considerations:**

1. **Token Security:**
   - Never commit the token to Git
   - Use environment variables only
   - Rotate tokens periodically

2. **Least Privilege:**
   - The token only has `repo` scope
   - It can only dispatch workflows, not push code directly
   - GitHub Actions still need to pass all checks

3. **Token Expiration:**
   - If you set an expiration, you'll need to regenerate and update Cloud Run before it expires
   - Set a calendar reminder!

4. **Revoke if Compromised:**
   - Go to: https://github.com/settings/tokens
   - Click **"Revoke"** next to the token
   - Generate a new one and update Cloud Run

---

## 5. Troubleshooting

### "GITHUB_TOKEN not set" in logs
- Token is missing from Cloud Run environment variables
- Follow "Add Token to Google Cloud Run" steps above

### "404 Not Found" when triggering webhook
- Check `GITHUB_REPO` format: `owner/repo` (no `https://`)
- Verify repository exists and token has access

### "401 Unauthorized"
- Token may be invalid or expired
- Regenerate token with correct `repo` scope

### "422 Unprocessable Entity"
- GitHub Action workflow may not have `repository_dispatch` trigger
- Check `.github/workflows/apply-proposal.yml` has:
  ```yaml
  on:
    repository_dispatch:
      types: [proposal-approved]
  ```

### Workflow doesn't run
- Check GitHub Actions are enabled: Settings → Actions → General
- Ensure workflow file is on `main` branch
- Verify `types: [proposal-approved]` matches payload event type

---

## 6. How It Works

```mermaid
sequenceDiagram
    participant User as Developer
    participant Ext as VS Code Extension
    participant API as Cloud Run Backend
    participant GH as GitHub API
    participant Action as GitHub Actions

    User->>Ext: Click "Approve Proposal"
    Ext->>API: POST /proposals/{id}/approve
    API->>API: Update Firestore (status=approved)
    API->>GH: POST /repos/{owner}/{repo}/dispatches
    Note over API,GH: Event: proposal-approved<br/>Payload: {proposal_id}
    GH->>Action: Trigger workflow
    Action->>API: GET /proposals/{id}
    Action->>Action: Apply changes to code
    Action->>GH: git push
    Action->>API: Update proposal with commit hash
```

---

## Complete Example

```bash
# 1. Generate token (done in browser)
# Copy: ghp_1234567890abcdefghijklmnopqrstuvwxyzABCD

# 2. Update Cloud Run
gcloud run services update contextpilot-backend \
  --region us-central1 \
  --update-env-vars="GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyzABCD"

# 3. Test by approving a proposal in extension

# 4. Check workflow triggered
gh run list --limit 3
# Should show: "Apply ContextPilot Proposals" with status "in_progress" or "completed"
```

---

**That's it!** 🎉 Your ContextPilot system is now fully automated from approval to code deployment!

