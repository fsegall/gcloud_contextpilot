# Git & GitHub Architecture

## Overview

ContextPilot uses a **hybrid git architecture** that combines local git operations with GitHub Actions automation. This document explains how git operations work in different deployment modes and how they integrate with the multi-agent system.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Components](#components)
3. [Deployment Modes](#deployment-modes)
4. [Git Flow (Cloud Mode)](#git-flow-cloud-mode)
5. [Git Flow (Local Mode)](#git-flow-local-mode)
6. [Git Agent Enhancements](#git-agent-enhancements)
7. [Configuration](#configuration)
8. [Monitoring & Debugging](#monitoring--debugging)

> Full documentation catalog (architecture deep dives, deployment guides, retrospectives) now lives in `docs/INDEX.md`.

---

## Architecture Overview

### Two-Layer System

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: Internal                        │
│                   Event Bus + Git Agent                     │
│                                                              │
│  • Metadata tracking                                        │
│  • Markdown documentation updates                           │
│  • Commit history logging                                   │
│  • CPT rewards tracking                                     │
│  • LLM-enhanced commit messages (optional)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 2: External                        │
│                    GitHub Actions                           │
│                                                              │
│  • Real git commits to repository                           │
│  • CI/CD pipeline execution                                 │
│  • Automated testing                                        │
│  • Code review & audit trail                                │
└─────────────────────────────────────────────────────────────┘
```

### Key Principle

- **Internal Layer (Git Agent)**: Handles metadata, tracking, and documentation
- **External Layer (GitHub Actions)**: Handles actual repository commits in production

This separation ensures:
- ✅ Safe multi-user collaboration
- ✅ Complete audit trail in GitHub
- ✅ Automated testing before merge
- ✅ No conflicts from concurrent local commits

---

## Components

### 1. Git_Context_Manager (Low-Level)

**File:** `back-end/app/git_context_manager.py`

**Purpose:** Core git operations and workspace management

**Responsibilities:**
- Git repository initialization and management
- Commit operations with metadata tracking
- Workspace context file management (checkpoint.yaml, history.json)
- Markdown template initialization (context.md, milestones.md, timeline.md)
- Push operations to remote repositories

**Used By:**
- GitAgent (primary consumer)
- Legacy server endpoints (backward compatibility)

**Key Methods:**
```python
commit_changes(message: str, agent: str) -> str
get_project_context() -> dict
write_context(state: dict)
log_history(message: str, agent: str, commit: str)
push_changes(remote_name: str, branch: str)
initialize_markdown_files()
```

---

### 2. GitAgent (High-Level)

**File:** `back-end/app/agents/git_agent.py`

**Purpose:** Intelligent git operations orchestrator

**Responsibilities:**
- Event-driven commit decisions (reacts to proposals, milestones)
- Conventional Commits message generation
- Smart commit filtering (decides what's worth committing)
- **NEW:** Markdown file management (context.md, timeline.md, task_history.md)
- **NEW:** Rich history tracking (JSON + Markdown)
- **NEW:** CPT rewards tracking after commits
- **NEW:** LLM-enhanced commit messages (optional, uses Gemini)

**Event Subscriptions:**
- `PROPOSAL_APPROVED` → Apply changes from proposals
- `MILESTONE_COMPLETE` → Create milestone commits + tags

**Enhanced Features (v2.0):**

1. **Markdown Management**
   - Auto-updates `context.md` with recent activity
   - Maintains `timeline.md` organized by date
   - Logs full commit history in `task_history.md`

2. **Rewards Integration**
   - Calls `/rewards/track` API after each commit
   - Tracks metadata: agent, commit hash, message
   - Fire-and-forget async (doesn't block commits)

3. **Rich History**
   - Logs to 4 places: history.json, task_history.md, context.md, timeline.md
   - Automatic message summarization
   - Complete audit trail

4. **LLM Commit Messages** (Optional)
   - Uses Gemini API for intelligent commit messages
   - Follows Conventional Commits format
   - Automatic fallback to templates
   - Enable with: `USE_LLM_COMMITS=true`

---

### 3. Proposals Router Integration

**File:** `back-end/app/routers/proposals.py`

**Function:** `approve_proposal()` (Line 322)

**Dual Responsibility:**

1. **Internal Processing:**
   ```python
   # Publish event for Git Agent (Layer 1)
   event_bus.publish(
       topic="proposals-events",
       event_type="proposal.approved.v1",
       data={...}
   )
   ```

2. **External Trigger:**
   ```python
   # Trigger GitHub Actions (Layer 2)
   await trigger_github_action(proposal_id)
   ```

---

### 4. GitHub Actions Trigger

**File:** `back-end/app/routers/proposals.py`

**Function:** `trigger_github_action()` (Line 38-76)

**Purpose:** Bridge to GitHub Actions via repository_dispatch webhook

**Implementation:**
```python
async def trigger_github_action(proposal_id: str):
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "owner/repo")
    
    url = f"https://api.github.com/repos/{github_repo}/dispatches"
    
    payload = {
        "event_type": "proposal-approved",
        "client_payload": {"proposal_id": proposal_id}
    }
    
    # POST to GitHub API
    await client.post(url, json=payload, headers={...})
```

**GitHub API Response:**
- `204 No Content`: Success, workflow triggered
- `404 Not Found`: Repository or token invalid
- `422 Unprocessable Entity`: Workflow not configured

---

### 5. GitHub Actions Workflow

**File:** `.github/workflows/apply-proposal.yml`

**Trigger:**
```yaml
on:
  repository_dispatch:
    types: [proposal-approved]
```

**Workflow Steps:**

1. **Checkout Repository**
   ```yaml
   - uses: actions/checkout@v3
   ```

2. **Fetch Proposal**
   ```bash
   curl -X GET "${{ secrets.BACKEND_URL }}/proposals/${{ github.event.client_payload.proposal_id }}"
   ```

3. **Apply Changes**
   - Parse proposed_changes from proposal
   - Apply diffs to files
   - Create/update/delete files as needed

4. **Commit Changes**
   ```bash
   git config user.name "ContextPilot Bot"
   git config user.email "bot@contextpilot.dev"
   git add .
   git commit -m "feat(proposal): Apply proposal $PROPOSAL_ID"
   git push
   ```

5. **Update Proposal**
   ```bash
   curl -X POST "${{ secrets.BACKEND_URL }}/proposals/$PROPOSAL_ID/update" \
     -d '{"commit_hash": "$COMMIT_HASH"}'
   ```

---

## Deployment Modes

### Local Mode

**Configuration:**
```bash
STORAGE_MODE=local
REWARDS_MODE=local
EVENT_BUS_MODE=in_memory
```

**Git Flow:**
```
Developer → Extension → Backend → Git Agent
                                      ↓
                             Git_Context_Manager
                                      ↓
                            LOCAL REPOSITORY
                              (direct commit)
```

**Characteristics:**
- ✅ Fast (no network round-trip)
- ✅ Works offline
- ✅ Good for development & testing
- ❌ Not safe for multi-user
- ❌ Requires local git setup

**Use Cases:**
- Developing ContextPilot itself
- Testing new agent features
- Working on documentation
- Offline development

---

### Cloud Mode

**Configuration:**
```bash
STORAGE_MODE=cloud
REWARDS_MODE=firestore
EVENT_BUS_MODE=pubsub
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPO=owner/repo
```

**Git Flow:**
```
Developer → Extension → Cloud Run → Proposals Router
                                           ↓
                    ┌──────────────────────┴──────────────────────┐
                    ↓                                              ↓
              Event Bus                                  GitHub API
                    ↓                                              ↓
              Git Agent                               GitHub Actions
            (metadata only)                                        ↓
                                                        REMOTE REPOSITORY
                                                          (real commit)
```

**Characteristics:**
- ✅ Multi-user safe
- ✅ Complete audit trail in GitHub
- ✅ Automated CI/CD
- ✅ No local git required
- ❌ Slight delay (GitHub Actions startup)
- ❌ Requires GITHUB_TOKEN setup

**Use Cases:**
- Production deployments
- Team collaboration
- Projects with CI/CD requirements
- Automated testing before merge

---

## Git Flow (Cloud Mode)

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. VS CODE EXTENSION                                        │
│    Developer clicks "Approve Proposal"                      │
│    → POST /proposals/{id}/approve                           │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CLOUD RUN (proposals.py)                                │
│    ✅ Update Firestore: status = "approved"                │
│    ✅ Publish event: proposal.approved.v1                  │
│    ✅ Track CPT rewards (+25 CPT)                          │
│    ✅ trigger_github_action(proposal_id)                   │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
┌────────────────────────────┐  ┌────────────────────────────────────────┐
│ 2a. EVENT BUS              │  │ 2b. GITHUB API                         │
│  (In-memory / Pub/Sub-ready)│ │  POST /repos/{owner}/{repo}/dispatches│
│                            │ │  {                                      │
│ Git Agent receives:        │ │    "event_type": "proposal-approved",  │
│ - proposal_id              │ │    "client_payload": {                 │
│ - changes                  │ │      "proposal_id": "..."              │
│                            │ │    }                                    │
│ Does:                      │ │  }                                      │
│ • Log history              │ └──────────────┬─────────────────────────┘
│ • Update MDs               │                ↓
│ • Track CPT (async)        │  ┌─────────────────────────────────────────┐
│ • No commit!               │  │ 3. GITHUB ACTIONS                       │
└────────────────────────────┘  │   (.github/workflows/apply-proposal.yml)│
└────────────────┘   │                                          │
                     │   1. Checkout repository                 │
                     │   2. GET /proposals/{id}                 │
                     │   3. Apply changes to files              │
                     │   4. git add .                           │
                     │   5. git commit -m "feat: Apply..."      │
                     │   6. git push                            │
                     │   7. POST /proposals/{id}/update         │
                     │      {commit_hash: "abc123"}             │
                     └─────────────────────────────────────────┘
```

### Step-by-Step

1. **User Approval** (Extension)
   - User reviews proposal in VS Code
   - Clicks "Approve" button
   - Extension sends: `POST /proposals/{id}/approve`

2. **Backend Processing** (Cloud Run)
   - Updates proposal status in Firestore
   - Publishes internal event to Event Bus
   - Awards CPT rewards (+25 for approval)
   - Calls `trigger_github_action()`

3. **Dual Path Execution**

   **Path A - Internal (Git Agent):**
   - Receives `proposal.approved.v1` event
   - Logs to history.json
   - Updates markdown files
   - Tracks rewards metadata
   - **Does NOT commit to git**

   **Path B - External (GitHub Actions):**
   - Receives `repository_dispatch` webhook
   - Fetches proposal details from backend
   - Applies file changes
   - Creates real git commit
   - Pushes to repository
   - Updates proposal with commit hash

4. **Result**
   - Changes appear in GitHub repository
   - Full audit trail available
   - CI/CD tests run automatically
   - Metadata tracked internally

---

## Git Flow (Local Mode)

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. VS CODE EXTENSION                                        │
│    Developer clicks "Approve Proposal"                      │
│    → POST /proposals/{id}/approve                           │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. LOCAL BACKEND (proposals.py)                            │
│    ✅ Update local storage (JSON file)                     │
│    ✅ Publish event: proposal.approved.v1                  │
│    ✅ Track rewards (local JSON)                           │
│    ❌ NO GitHub Actions trigger                            │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. GIT AGENT (Event Handler)                               │
│    Receives: proposal.approved.v1                          │
│                                                              │
│    Does:                                                    │
│    1. Load proposal from local storage                      │
│    2. Apply changes to files                                │
│    3. _commit() → Git_Context_Manager                      │
│    4. Log history.json                                      │
│    5. Update markdown files                                 │
│    6. Track rewards                                         │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. GIT_CONTEXT_MANAGER                                     │
│    commit_changes(message, agent)                          │
│                                                              │
│    1. git add --all                                         │
│    2. git commit -m "agent(proposal): ..."                  │
│    3. Log to history.json                                   │
│    4. Update task_history.md                                │
│    5. Return commit hash                                    │
└─────────────────────────────────────────────────────────────┘
```

### Differences from Cloud Mode

| Aspect | Cloud Mode | Local Mode |
|--------|-----------|-----------|
| **Storage** | Firestore | JSON files |
| **Event Bus** | Pub/Sub (planned toggle) | In-Memory (default in current build) |
| **Git Commits** | GitHub Actions | Direct (Git Agent) |
| **Speed** | ~30s delay | Instant |
| **Multi-user** | ✅ Safe | ❌ Conflicts possible |
| **Audit Trail** | GitHub | Local only |
| **CI/CD** | ✅ Automatic | ❌ Manual |

---

## Git Agent Enhancements

### Version 2.0 Features

#### 1. Markdown File Management

**Purpose:** Keep documentation automatically synchronized with git activity

**Files Managed:**

1. **context.md**
   - Section: "🚀 Recent Activity"
   - Updates: Every commit adds entry with agent name and summary
   - Format: `- **{agent}**: {message_summary}`

2. **timeline.md**
   - Organized by date (## YYYY-MM-DD)
   - Updates: Commits grouped by date
   - Format: `- {agent}: {message_summary}`

3. **task_history.md**
   - Complete commit log with full details
   - Updates: Every commit appends full entry
   - Format:
     ```markdown
     ### 2025-10-22T19:30:00Z
     - **Agent**: git-agent
     - **Message**: feat(proposal): Apply proposal...
     - **Commit**: a1b2c3d
     ```

**Implementation:**
```python
def _update_markdown_files(self, message: str, agent: str, commit_hash: str):
    """Update all markdown documentation files"""
    self._update_context_md(...)
    self._update_timeline_md(...)
    self._update_task_history_md(...)
```

---

#### 2. Rich History Tracking

**Purpose:** Comprehensive audit trail in multiple formats

**Logged To:**

1. **history.json** (Structured data)
   ```json
   {
     "timestamp": "2025-10-22T19:30:00Z",
     "message": "feat(proposal): Apply changes",
     "agent": "git-agent",
     "commit": "a1b2c3d4e5f",
     "summary": "feat(proposal): Apply changes"
   }
   ```

2. **task_history.md** (Human-readable)
3. **context.md** (Recent activity)
4. **timeline.md** (Date-organized)

**Benefits:**
- Complete audit trail
- Multiple views of same data
- Easy debugging and reporting
- Historical analysis support

---

#### 3. CPT Rewards Tracking

**Purpose:** Gamification through automatic reward tracking

**Implementation:**
```python
async def _track_reward(self, agent: str, commit_hash: str, message: str):
    """Track reward action via API"""
    await client.post(
        f"{self.api_base_url}/rewards/track",
        json={
            "user_id": self.workspace_id,
            "action_type": "git_commit",
            "metadata": {
                "agent": agent,
                "commit": commit_hash,
                "message": message[:100]
            }
        }
    )
```

**Rewards:**
- Git commit: Variable (based on action type)
- Proposal approval: +25 CPT
- Milestone completion: Variable

**Features:**
- Async fire-and-forget (doesn't block commits)
- Automatic retry on failure
- Detailed metadata logging

---

#### 4. LLM-Enhanced Commit Messages

**Purpose:** Generate intelligent, context-aware commit messages

**Configuration:**
```bash
USE_LLM_COMMITS=true        # Enable LLM messages
GEMINI_API_KEY=AIza...      # Required for LLM
```

**How It Works:**

1. **Attempt LLM Generation:**
   ```python
   llm_message = await _generate_llm_commit_message(
       commit_type=CommitType.FEAT,
       scope="proposal",
       changes_context="Applied 3 file changes..."
   )
   ```

2. **LLM Prompt:**
   ```
   Generate a concise git commit message following Conventional Commits.
   
   Type: feat
   Scope: proposal
   Context: Applied 3 file changes...
   
   Requirements:
   - Format: <type>(<scope>): <subject>
   - Subject: imperative mood, lowercase, no period
   - Max 50 chars for subject
   - Be specific and actionable
   ```

3. **Fallback to Template:**
   - If LLM fails or unavailable
   - Uses conventional commit templates
   - Always ensures valid format

**Example Output:**
```
LLM:      feat(proposal): apply user authentication changes
Template: feat(proposal): Apply proposal spec-20251022-001

Generated-by: git-agent (LLM-enhanced)
```

---

### Post-Commit Workflow

**Every commit triggers:**

```python
def _commit(self, message: str, agent: str) -> Optional[str]:
    # 1. Execute commit via Git_Context_Manager
    result = self.git_manager.commit_changes(message, agent)
    
    if result and result != "SKIPPED_NO_CHANGES":
        # 2. Log to history
        self._log_history(message, agent, result)
        
        # 3. Update markdown docs
        self._update_markdown_files(message, agent, result)
        
        # 4. Track rewards (async)
        asyncio.create_task(self._track_reward(agent, result, message))
    
    return result
```

**Benefits:**
- Automatic documentation
- Complete audit trail
- Gamification active
- No manual intervention needed

---

## Configuration

### Environment Variables

#### Required (Both Modes)

```bash
# Storage configuration
STORAGE_MODE=local|cloud              # Deployment mode
REWARDS_MODE=local|firestore          # Rewards storage
EVENT_BUS_MODE=in_memory|pubsub       # Event system

# GCP (if cloud mode)
GCP_PROJECT_ID=your-project-id        # Google Cloud project
ENVIRONMENT=development|production     # Environment

# API Keys
GEMINI_API_KEY=AIza...                # For LLM features (optional)
```

#### Cloud Mode Additional

```bash
# GitHub Integration
GITHUB_TOKEN=ghp_xxxxx                # Personal Access Token
GITHUB_REPO=owner/repo-name           # Target repository

# Firestore
FIRESTORE_ENABLED=true                # Enable Firestore storage

# Pub/Sub (planned)
USE_PUBSUB=true                       # Route event bus through Pub/Sub (toggle returns after hardening)
```

#### Optional Features

```bash
# LLM Commit Messages
USE_LLM_COMMITS=true|false            # Enable AI commit messages (default: false)

# Auto-approval
CONTEXTPILOT_AUTO_APPROVE_PROPOSALS=true|false   # Auto-commit approved proposals
```

---

### GitHub Token Setup

**Requirements:**
- Personal Access Token (PAT) or GitHub App
- Permissions: `repo` (full repository access)
- Scopes needed:
  - `repo:status` - Access commit status
  - `repo_deployment` - Access deployments
  - `public_repo` - Access public repositories
  - Or `repo` - Full control (includes all above)

**Create Token:**

1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`
4. Copy token: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Configure in Cloud Run:**

```bash
# Via gcloud
gcloud run services update contextpilot-backend \
  --region us-central1 \
  --update-env-vars="GITHUB_TOKEN=ghp_xxxxx,GITHUB_REPO=owner/repo"

# Or via Google Secret Manager (recommended)
echo -n "ghp_xxxxx" | gcloud secrets create github-token --data-file=-

# Then reference in Cloud Run
--set-secrets=GITHUB_TOKEN=github-token:latest
```

---

### GitHub Actions Workflow Setup

**Required File:** `.github/workflows/apply-proposal.yml`

**Minimal Configuration:**

```yaml
name: Apply ContextPilot Proposals

on:
  repository_dispatch:
    types: [proposal-approved]

jobs:
  apply-changes:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Fetch Proposal
        id: fetch
        run: |
          PROPOSAL=$(curl -s "${{ secrets.BACKEND_URL }}/proposals/${{ github.event.client_payload.proposal_id }}")
          echo "proposal=$PROPOSAL" >> $GITHUB_OUTPUT
      
      - name: Apply Changes
        run: |
          # Parse and apply changes from proposal
          # (implementation depends on your needs)
      
      - name: Commit and Push
        run: |
          git config user.name "ContextPilot Bot"
          git config user.email "bot@contextpilot.dev"
          git add .
          git commit -m "feat: Apply proposal ${{ github.event.client_payload.proposal_id }}"
          git push
      
      - name: Update Proposal
        run: |
          COMMIT_HASH=$(git rev-parse HEAD)
          curl -X POST "${{ secrets.BACKEND_URL }}/proposals/${{ github.event.client_payload.proposal_id }}/update" \
            -H "Content-Type: application/json" \
            -d "{\"commit_hash\": \"$COMMIT_HASH\"}"
```

**Required Secrets:**

- `BACKEND_URL`: Your Cloud Run service URL
- (GitHub token is automatic via `${{ secrets.GITHUB_TOKEN }}`)

---

## Monitoring & Debugging

### Log Locations

#### Cloud Run Logs

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=contextpilot-backend" \
  --limit 50 --format json

# Filter for git operations
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'GitAgent'" \
  --limit 20

# Filter for GitHub triggers
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'GitHub Action triggered'" \
  --limit 10
```

#### GitHub Actions Logs

```bash
# Via GitHub CLI
gh run list --limit 10

# View specific run
gh run view <run-id> --log

# Or in browser
https://github.com/{owner}/{repo}/actions
```

#### Local Logs

```bash
# Git Agent logs
tail -f back-end/git_context_manager.log

# Server logs
tail -f back-end/server.log

# History tracking
cat workspaces/default/history.json | jq .
```

---

### Common Issues

#### 1. GitHub Actions Not Triggering

**Symptoms:**
- Proposal approved but no workflow run
- No commit appears in GitHub

**Debug:**
```bash
# Check Cloud Run logs for trigger
gcloud logging read "textPayload=~'GitHub Action triggered'" --limit 5

# Check GitHub webhook deliveries
gh api repos/{owner}/{repo}/hooks/{hook-id}/deliveries
```

**Common Causes:**
- Missing or invalid `GITHUB_TOKEN`
- Wrong `GITHUB_REPO` format (should be `owner/repo`)
- Workflow file not on main branch
- Workflow trigger type mismatch

**Solution:**
```bash
# Verify env vars
gcloud run services describe contextpilot-backend --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# Test GitHub API
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/{owner}/{repo}
```

---

#### 2. Git Agent Not Processing Events

**Symptoms:**
- Markdown files not updated
- History.json not updated
- No reward tracking logs

**Debug:**
```python
# Check agent initialization
grep "GitAgent.*Initialized" server.log

# Check event subscriptions
grep "Subscribed to event" server.log

# Check event reception
grep "GitAgent.*Received event" server.log
```

**Common Causes:**
- Event bus misconfiguration
- Agent not registered in orchestrator
- Event type mismatch

**Solution:**
```bash
# Verify event bus mode
echo $EVENT_BUS_MODE  # Should be "pubsub" or "in_memory"

# Check orchestrator logs
grep "AgentOrchestrator" server.log
```

---

#### 3. Commit Message Generation Fails

**Symptoms:**
- Commits with default messages
- LLM errors in logs

**Debug:**
```bash
# Check LLM configuration
echo $USE_LLM_COMMITS    # Should be "true"
echo $GEMINI_API_KEY     # Should be set

# Check logs for LLM errors
grep "LLM.*failed" git_context_manager.log
```

**Solution:**
- Verify Gemini API key is valid
- Check API quota limits
- Fallback to templates (automatic)

---

#### 4. Markdown Files Not Updating

**Symptoms:**
- context.md not showing recent activity
- timeline.md missing entries

**Debug:**
```python
# Check file existence
ls -la workspaces/default/*.md

# Check permissions
stat workspaces/default/context.md

# Check update logs
grep "Updated.*md" git_context_manager.log
```

**Solution:**
- Ensure markdown files exist (created by initialize_markdown_files)
- Check file permissions (should be writable)
- Verify _update_markdown_files() is called in _commit()

---

### Performance Monitoring

#### Commit Latency

```bash
# Cloud Mode (via GitHub Actions)
# Expected: 20-60 seconds
# - API call: ~1s
# - Workflow startup: 10-30s
# - Commit + push: 5-20s

# Local Mode (via Git Agent)
# Expected: 1-5 seconds
# - Event processing: <1s
# - File operations: 1-3s
# - Git commit: <1s
```

#### Resource Usage

```bash
# Cloud Run metrics
gcloud monitoring timeseries list \
  --filter='metric.type="run.googleapis.com/request_count"' \
  --interval-start-time="2025-10-22T00:00:00Z"

# Git Agent memory usage (local)
ps aux | grep git_agent
```

---

## Best Practices

### 1. Commit Message Quality

✅ **Do:**
- Use Conventional Commits format
- Keep subject line under 50 characters
- Use imperative mood ("Add feature" not "Added feature")
- Be specific about changes

❌ **Don't:**
- Use vague messages ("Fix stuff", "Update code")
- Include ticket numbers in subject (put in body)
- Use past tense
- Write novels in subject line

### 2. GitHub Actions Security

✅ **Do:**
- Store tokens in Google Secret Manager
- Use minimal required permissions
- Rotate tokens regularly (90 days)
- Monitor webhook deliveries

❌ **Don't:**
- Commit tokens to repository
- Use tokens with admin access
- Share tokens between services
- Leave unused tokens active

### 3. Event Bus Usage

✅ **Do:**
- Default to the in-memory event bus while Pub/Sub hardening is underway.
- Flip `USE_PUBSUB=true` only after validating the managed bus in staging.
- Subscribe to specific event types and keep handlers asynchronous.
- Treat event handlers as idempotent (replays will happen once Pub/Sub returns).

❌ **Don't:**
- Assume Pub/Sub is active in current builds.
- Subscribe to all events or block inside event handlers.
- Ignore event processing errors—surface them in agent metrics for tracing.

### 4. Markdown Documentation

✅ **Do:**
- Let Git Agent update automatically
- Review generated documentation periodically
- Use markdown for human-readable logs
- Keep history.json for structured queries

❌ **Don't:**
- Manually edit auto-generated sections
- Delete markdown files (will break updates)
- Rely only on markdown (use JSON too)
- Ignore documentation drift

---

## Migration Guide

### From Local to Cloud Mode

**Prerequisites:**
1. GitHub repository with write access
2. GitHub token with `repo` permissions
3. GCP project with Cloud Run enabled

**Steps:**

1. **Configure GitHub Actions**
   ```bash
   # Create workflow file (paste the snippet from "GitHub Actions Workflow Setup")
   mkdir -p .github/workflows
   cat <<'YAML' > .github/workflows/apply-proposal.yml
   # Paste minimal workflow from the documentation here
   YAML

   # Commit and push
   git add .github/workflows/apply-proposal.yml
   git commit -m "chore: add ContextPilot workflow"
   git push
   ```

2. **Update Environment Variables**
   ```bash
   gcloud run services update contextpilot-backend \
     --region us-central1 \
     --update-env-vars="
       STORAGE_MODE=cloud,
       REWARDS_MODE=firestore,
       EVENT_BUS_MODE=pubsub,
       GITHUB_TOKEN=ghp_xxxxx,
       GITHUB_REPO=owner/repo
     "
   ```

3. **Test Integration**
   ```bash
   # Approve a test proposal
   # Check GitHub Actions runs
   gh run list --limit 5
   ```

4. **Monitor Initial Runs**
   - Watch Cloud Run logs for trigger confirmations
   - Check GitHub Actions logs for successful commits
   - Verify proposals are updated with commit hashes

---

## Troubleshooting Decision Tree

```
Proposal approved but no changes?
├─ Is STORAGE_MODE=cloud?
│  ├─ Yes → Check GitHub Actions
│  │  ├─ Workflow triggered?
│  │  │  ├─ Yes → Check workflow logs
│  │  │  └─ No → Check GITHUB_TOKEN/REPO
│  │  └─ Workflow failed?
│  │     └─ Check apply-proposal.yml configuration
│  └─ No (local) → Check Git Agent
│     ├─ Event received?
│     │  ├─ Yes → Check _commit() logs
│     │  └─ No → Check event bus configuration
│     └─ Commit failed?
│        └─ Check git_context_manager.log
│
Markdown files not updating?
├─ Files exist?
│  ├─ Yes → Check _update_markdown_files() logs
│  └─ No → Run initialize_markdown_files()
├─ Permissions OK?
│  ├─ Yes → Check _commit() called _update_markdown_files()
│  └─ No → Fix file permissions
└─ Check context.md manually for test entry
│
Rewards not tracking?
├─ Backend reachable?
│  ├─ Yes → Check /rewards/track endpoint
│  └─ No → Check API_BASE_URL
├─ Check reward adapter configuration
└─ Verify user_id in request
```

---

## Future Enhancements

### Planned Features

1. **Branch Management**
   - Automatic feature branch creation
   - Smart branch naming (feat/proposal-123)
   - Auto-merge on approval

2. **Git Tags**
   - Milestone tagging
   - Version bumping
   - Semantic release integration

3. **Rollback Support**
   - Undo proposal commits
   - Cherry-pick specific changes
   - Conflict resolution automation

4. **Advanced LLM Features**
   - Context-aware commit messages (include recent history)
   - Multi-file change summaries
   - Breaking change detection

5. **Analytics**
   - Commit velocity tracking
   - Agent productivity metrics
   - Code quality trends

---

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions: repository_dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub/docs)

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/fsegall/google-context-pilot/issues
- Documentation: /docs/
- Architecture Diagrams: /docs/architecture/

---

**Last Updated:** 2025-10-22  
**Version:** 2.0 (with Git Agent enhancements)

