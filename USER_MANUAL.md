# 📘 ContextPilot User Manual

**Complete Guide to Starting a New Project with ContextPilot**

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Creating Your First Project](#creating-your-first-project)
6. [Using ContextPilot Features](#using-contextpilot-features)
7. [Working with Proposals](#working-with-proposals)
8. [Agent Retrospectives](#agent-retrospectives)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## 🎯 Introduction

**ContextPilot** is an AI-powered development assistant that helps you manage project context, automate documentation, and coordinate multiple AI agents to improve your development workflow.

### Key Features

- **Multi-Agent System**: 6 specialized AI agents working together
  - **Spec Agent**: Automatically generates and maintains documentation
  - **Git Agent**: Intelligent semantic commits
  - **Context Agent**: Real-time project analysis
  - **Coach Agent**: Personalized development tips
  - **Milestone Agent**: Progress tracking
  - **Development Agent**: Code implementation
  - **Retrospective Agent**: Agent coordination and learning

- **Proposal System**: Review and approve AI-generated improvements
- **Agent Retrospectives**: Periodic agent meetings to improve coordination
- **Gamification**: Earn CPT tokens for productive actions

---

## 📋 Prerequisites

Before you begin, ensure you have:

### Required

- **VS Code or Cursor** (latest version)
- **Git** installed and configured
- **Node.js** 18+ (for extension development, if building from source)
- **Python 3.11+** (if running backend locally)
- **Google Cloud Account** (for production/cloud features)

### Optional (for local development)

- **Docker** (for containerized backend)
- **Google Cloud SDK** (`gcloud` CLI)

---

## 🚀 Installation

### Step 1: Install the VS Code Extension

#### Option A: From VS Code Marketplace (Recommended)

1. Open VS Code or Cursor
2. Press `Ctrl+Shift+X` (or `Cmd+Shift+X` on Mac) to open Extensions
3. Search for **"ContextPilot"**
4. Click **Install**
5. Reload the window when prompted

#### Option B: From VSIX File

```bash
code --install-extension contextpilot-0.1.0.vsix
```

### Step 2: Verify Installation

1. Look for the **🚀 ContextPilot** icon in the sidebar
2. Check the status bar (bottom right) - it should show connection status
3. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) and type "ContextPilot" to see available commands

### Step 3: Configure Backend Connection

The extension connects to the ContextPilot backend API. By default, it uses the production Cloud Run instance:

```
https://contextpilot-backend-581368740395.us-central1.run.app
```

**To use a local backend** (for development):

1. Open VS Code Settings (`Ctrl+,` or `Cmd+,`)
2. Search for "ContextPilot"
3. Set `ContextPilot: API URL` to `http://localhost:8000`
4. Make sure your local backend is running (see [Local Backend Setup](#local-backend-setup-optional))

---

## 🏁 Getting Started

### First Launch

1. **Open a Project Folder**
   - Open VS Code/Cursor
   - Open any folder containing a Git repository (or create a new one)
   - The extension will automatically detect the project

2. **Check Connection Status**
   - Look at the status bar (bottom right)
   - You should see: `⭐ 0 CPT | ContextPilot: Connected`
   - If it shows "Disconnected", check your internet connection and backend URL

3. **Explore the Sidebar**
   - Click the **🚀 ContextPilot** icon in the sidebar
   - You'll see several sections:
     - **Change Proposals**: AI-generated improvement suggestions
     - **Agents**: Status of all AI agents
     - **Context**: Project context files
     - **Coach**: Development tips
     - **Rewards**: Your CPT token balance

---

## 🆕 Creating Your First Project

### Method 1: Using the Extension (Recommended)

1. **Open Your Project Folder**
   ```bash
   # Navigate to your project directory
   cd /path/to/your/project
   
   # Open in VS Code
   code .
   ```

2. **Initialize Git Repository** (if not already initialized)
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

3. **Create Initial Context via API**

   The extension will automatically create a workspace when you first use it. However, you can also create a workspace manually via the API:

   **Using cURL:**
   ```bash
   curl -X POST "http://localhost:8000/generate-context?workspace_id=my-project" \
     -H "Content-Type: application/json" \
     -d '{
       "project_name": "My Awesome Project",
       "goal": "Build a modern web application with React and Node.js",
       "initial_status": "Project initialization. Setting up development environment.",
       "milestones": [
         {
           "name": "Setup development environment",
           "due": "2025-02-01"
         },
         {
           "name": "Implement core features",
           "due": "2025-02-15"
         },
         {
           "name": "Testing and deployment",
           "due": "2025-03-01"
         }
       ]
     }'
   ```

   **Using Swagger UI:**
   1. Start your backend (if running locally)
   2. Open `http://localhost:8000/docs` in your browser
   3. Find `POST /generate-context`
   4. Click "Try it out"
   5. Fill in the form:
      - `workspace_id`: Your project identifier (e.g., `my-project`)
      - `project_name`: Display name for your project
      - `goal`: High-level project goal
      - `initial_status`: Current project status
      - `milestones`: Array of milestone objects with `name` and `due` date
   6. Click "Execute"

4. **Verify Workspace Creation**

   The workspace is created at:
   - **Local**: `.contextpilot/workspaces/{workspace_id}/`
   - **Cloud**: Stored in Firestore

   Check that the following files were created:
   - `checkpoint.yaml` - Project state and milestones
   - `history.json` - Project history log
   - `meta.json` - Workspace metadata

### Method 2: Using the Script (For ContextPilot Development)

If you're working on the ContextPilot project itself:

```bash
# Make sure backend is running first!
bash scripts/shell/create-contextpilot-workspace.sh
```

---

## 🎨 Using ContextPilot Features

### 1. Viewing Change Proposals

**Change Proposals** are AI-generated suggestions for improving your codebase.

1. Open the **Change Proposals** section in the sidebar
2. Click on any proposal to see details:
   - **Description**: What the change does
   - **Files Affected**: Which files will be modified
   - **Diff Preview**: Visual diff of the changes
3. Review the proposal carefully

### 2. Approving Proposals

When you approve a proposal:

1. Click the **✓ Approve** button next to the proposal
2. The changes are automatically applied to your codebase
3. A Git commit is created with a semantic commit message
4. You earn **CPT tokens** (shown in a notification)
5. The proposal moves to "Approved" status

**Note**: In Cloud Run mode, approved proposals trigger GitHub Actions for automated deployment.

### 3. Rejecting Proposals

If you don't want to apply a proposal:

1. Click the **✗ Reject** button
2. Optionally provide a reason for rejection
3. The proposal is marked as rejected and archived

### 4. Asking the Coach

Get personalized development tips:

1. Open the **Coach** section in the sidebar
2. Click **"Ask Coach"** or use Command Palette: `ContextPilot: Ask Coach`
3. Enter your question or select from suggested topics
4. The Coach Agent will provide tailored advice

### 5. Viewing Agent Status

Monitor your AI agents:

1. Open the **Agents** section in the sidebar
2. See real-time status of each agent:
   - **Active**: Agent is processing events
   - **Idle**: Agent is waiting for events
   - **Error**: Agent encountered an issue (check logs)
3. View event bus mode (Pub/Sub or In-Memory)

### 6. Exploring Project Context

View project documentation and context:

1. Open the **Context** section in the sidebar
2. Browse generated documentation:
   - `context.md` - Project overview
   - `milestones.md` - Milestone tracking
   - `task_history.md` - Activity log
   - `timeline.md` - Project timeline

---

## 🔄 Working with Proposals

### Understanding Proposals

Proposals are AI-generated suggestions that can include:

- **Code improvements**: Refactoring, bug fixes, optimizations
- **Documentation updates**: Missing docs, outdated information
- **Architecture changes**: Better patterns, structure improvements
- **Dependency updates**: Security patches, version upgrades

### Proposal Workflow

```
1. Agent generates proposal
   ↓
2. Proposal appears in "Change Proposals" view
   ↓
3. You review the proposal
   ↓
4. Approve or Reject
   ↓
5. If approved:
   - Changes applied to codebase
   - Git commit created
   - CPT tokens earned
   - GitHub Action triggered (if in Cloud Run)
```

### Proposal States

- **Pending**: Waiting for your review
- **Approved**: Changes have been applied
- **Rejected**: You declined the proposal
- **In Progress**: Agent is implementing the changes

### Filtering Proposals

You can filter proposals by:
- **Status**: Pending, Approved, Rejected
- **Agent**: Which agent created the proposal
- **Priority**: High, Medium, Low
- **Date**: Recent, Oldest first

---

## 🤖 Agent Retrospectives

**Agent Retrospectives** are periodic "meetings" where all agents share metrics, insights, and generate action items for improvement.

### Triggering a Retrospective

1. **Via Command Palette:**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P`)
   - Type: `ContextPilot: Trigger Retrospective`
   - Press Enter

2. **Via Extension:**
   - Open the **Agents** section
   - Click **"Trigger Retrospective"** button

3. **Via API:**
   ```bash
   curl -X POST "http://localhost:8000/agents/retrospective/trigger" \
     -H "Content-Type: application/json" \
     -d '{
       "trigger": "manual",
       "use_llm": true,
       "trigger_topic": "Improve agent coordination"
     }'
   ```

### What Happens During a Retrospective

1. **Data Collection**: Agents share their metrics:
   - Events processed
   - Errors encountered
   - Learnings and insights
   - Collaboration patterns

2. **Analysis**: The Retrospective Agent analyzes:
   - Agent activity levels
   - Event bus patterns
   - Workflow efficiency
   - Bottlenecks and issues

3. **Insights Generation**: Key insights are identified:
   - What's working well
   - What needs improvement
   - Coordination opportunities

4. **Action Items**: Specific, prioritized actions are created:
   - High priority: Critical improvements
   - Medium priority: Important enhancements
   - Low priority: Nice-to-have optimizations

5. **Proposal Creation** (Optional): High-priority action items may automatically generate improvement proposals

### Viewing Retrospective Results

After a retrospective completes:

1. A **webview** opens automatically showing:
   - Agent metrics
   - Insights
   - Action items
   - LLM summary (if `use_llm=true`)

2. The retrospective is saved to:
   ```
   .contextpilot/workspaces/{workspace_id}/retrospectives/{retrospective_id}.md
   ```

3. If a proposal was created, it appears in the **Change Proposals** view

### Retrospective Parameters

- **`trigger`**: How the retrospective was triggered
  - `"manual"`: User-initiated
  - `"milestone"`: Triggered on milestone completion
  - `"cycle"`: Triggered on cycle closure

- **`use_llm`**: Whether to generate an LLM-synthesized narrative
  - `true`: Generate detailed AI summary
  - `false`: Return raw metrics and insights only

- **`trigger_topic`**: Optional discussion topic for the retrospective

---

## 🔧 Troubleshooting

### Extension Not Connecting

**Symptoms**: Status bar shows "Disconnected"

**Solutions**:
1. Check your internet connection
2. Verify backend URL in settings:
   - Settings → Search "ContextPilot: API URL"
   - For production: `https://contextpilot-backend-581368740395.us-central1.run.app`
   - For local: `http://localhost:8000`
3. Test backend health:
   ```bash
   curl http://localhost:8000/health
   ```
4. Check backend logs for errors

### Proposals Not Appearing

**Symptoms**: No proposals in the "Change Proposals" view

**Solutions**:
1. Check workspace ID matches where proposals are stored
2. Verify agents are active (check Agents view)
3. Check backend logs for agent errors
4. Try triggering a retrospective to generate proposals
5. Verify Firestore/local storage is accessible

### Retrospective Webview Empty

**Symptoms**: Retrospective completes but webview is blank

**Solutions**:
1. Check browser console for JavaScript errors (F12)
2. Verify retrospective data structure in API response
3. Check extension logs:
   - View → Output → Select "ContextPilot" from dropdown
4. Try triggering another retrospective

### Git Agent Not Triggering GitHub Actions

**Symptoms**: Proposals approved but no GitHub Actions triggered

**Solutions**:
1. Verify you're in Cloud Run mode (not local)
2. Check `GITHUB_TOKEN` environment variable is set
3. Verify `GITHUB_REPO` matches your repository
4. Check Git Agent logs:
   ```bash
   # View Cloud Run logs
   gcloud logging read "resource.type=cloud_run_revision AND textPayload:\"GitAgent\"" --limit 50
   ```
5. Verify GitHub Actions workflow file exists in `.github/workflows/`

### Development Agent Codespaces Issues

**Symptoms**: Development Agent fails to create Codespaces

**Solutions**:
1. Check `PERSONAL_GITHUB_TOKEN` has `codespace` scope:
   - Go to: https://github.com/settings/tokens
   - Create token with `repo` and `codespace` scopes
2. Verify token is stored in Secret Manager (Cloud Run) or `.env` (local)
3. Check diagnostic endpoint:
   ```bash
   curl "http://localhost:8000/agents/development/diagnostic?workspace_id=default"
   ```
4. Review Development Agent logs for authentication errors

### Workspace Not Found

**Symptoms**: Error: "Workspace 'xxx' not found"

**Solutions**:
1. Verify workspace exists:
   ```bash
   ls .contextpilot/workspaces/
   ```
2. Create workspace if missing:
   ```bash
   curl -X POST "http://localhost:8000/generate-context?workspace_id=my-project" ...
   ```
3. Check workspace ID matches in all API calls

---

## 🚀 Next Steps

### After Creating Your Project

1. **Review Initial Context**
   - Open `.contextpilot/workspaces/{workspace_id}/checkpoint.yaml`
   - Verify project name, goal, and milestones are correct
   - Update as needed

2. **Start Development**
   - Make code changes as usual
   - Agents will automatically analyze your work
   - Proposals will appear in the sidebar

3. **Review Proposals Regularly**
   - Check the "Change Proposals" view daily
   - Approve improvements that make sense
   - Reject proposals that don't fit your vision

4. **Trigger Retrospectives Periodically**
   - Weekly retrospectives help agents learn and improve
   - Use retrospectives to identify bottlenecks
   - Review action items and prioritize improvements

5. **Monitor Agent Status**
   - Keep an eye on agent health
   - Address any errors promptly
   - Check event bus mode (should be Pub/Sub in production)

### Advanced Usage

- **Custom Agent Configuration**: Modify agent behavior via environment variables
- **Multiple Workspaces**: Manage multiple projects with different workspace IDs
- **CI/CD Integration**: Set up GitHub Actions for automated deployments
- **Team Collaboration**: Share workspaces with team members (future feature)

### Getting Help

- **Documentation**: Check `back-end/README.md` and `extension/README.md`
- **API Docs**: Visit `http://localhost:8000/docs` (Swagger UI)
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord (link in extension README)

---

## 📚 Additional Resources

### Documentation Files

- **Backend README**: `back-end/README.md` - Backend architecture and API
- **Extension README**: `extension/README.md` - Extension features and commands
- **Architecture**: `ARCHITECTURE.md` - System design overview
- **Deployment**: `docs/deployment/` - Deployment guides

### API Endpoints

Key endpoints for project management:

- `POST /generate-context` - Create new workspace
- `GET /proposals` - List all proposals
- `POST /proposals/{id}/approve` - Approve a proposal
- `POST /agents/retrospective/trigger` - Trigger retrospective
- `GET /health` - Check backend health and configuration

### Scripts

- `scripts/shell/create-contextpilot-workspace.sh` - Create workspace for ContextPilot project
- `scripts/shell/deploy-cloud-run.sh` - Deploy backend to Cloud Run
- `scripts/shell/watch-git-agent-logs.sh` - Monitor Git Agent logs

---

## 🎉 Congratulations!

You're now ready to use ContextPilot! Start by creating your first project workspace and exploring the features. The AI agents will learn from your project and provide increasingly relevant suggestions over time.

**Happy coding! 🚀**

---

*Last updated: January 2025*
*ContextPilot v2.0.0*

