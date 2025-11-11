from fastapi import FastAPI, Body, Query, HTTPException, Request
from typing import Optional
from app.git_context_manager import Git_Context_Manager
from datetime import datetime
from dotenv import load_dotenv
import os
from app.llm_request_model import LLMRequest
from pydantic import BaseModel
from typing import List
import httpx
from datetime import datetime, timezone
from fastapi import Body, Query
import logging
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from time import time

# Temporarily commented - install dependencies later
# from app.routers import rewards, proposals, events
from app.agents.spec_agent import SpecAgent
from app.middleware.abuse_detection import abuse_detector
from app.utils.workspace_manager import get_workspace_path
from app.repositories.proposal_repository import get_proposal_repository
import os
from typing import List, Dict
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("server.log", mode="w"), logging.StreamHandler()],
    force=True,
)
logger = logging.getLogger(__name__)

CONTEXT_PILOT_URL = "http://localhost:8000"

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(
    title="ContextPilot API",
    description="Manage long-term project scope using Git + LLMs + Web3 incentives. Stay aligned and intentional.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Simple in-memory rate limiter
rate_limit_store = defaultdict(list)


def check_rate_limit(
    client_ip: str, max_requests: int = 100, window_seconds: int = 3600
) -> bool:
    """
    Rate limiting: max_requests per window_seconds per IP.
    Default: 100 requests/hour per IP
    """
    now = time()
    cutoff = now - window_seconds

    # Clean old requests
    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip] if timestamp > cutoff
    ]

    # Check limit
    if len(rate_limit_store[client_ip]) >= max_requests:
        return False

    # Add current request
    rate_limit_store[client_ip].append(now)
    return True


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting and abuse detection to all requests"""
    client_ip = request.client.host if request.client else "unknown"

    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)

    # Check for abuse patterns
    abuse_check = abuse_detector.check_request(request)
    if abuse_check["should_block"]:
        logger.error(f"🚫 Blocking request from {client_ip}: {abuse_check['reason']}")
        raise HTTPException(
            status_code=403, detail="Access denied due to suspicious activity."
        )

    if abuse_check["suspicious"]:
        logger.warning(
            f"⚠️ Suspicious request from {client_ip}: {abuse_check['reason']}"
        )

    # Check rate limit (100 req/hour per IP)
    if not check_rate_limit(client_ip, max_requests=100, window_seconds=3600):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        abuse_detector.record_error(client_ip, 429)
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Try again later."
        )

    response = await call_next(request)

    # Record errors for abuse detection
    if response.status_code >= 400:
        abuse_detector.record_error(client_ip, response.status_code)

    return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (temporarily commented - install dependencies later)
# app.include_router(rewards.router)
# app.include_router(proposals.router)
# app.include_router(events.router)


def get_manager(workspace_id: str = "default"):
    return Git_Context_Manager(workspace_id=workspace_id)


@app.get("/context")
def get_context(workspace_id: str = Query("default")):
    logger.info(f"GET /context called with workspace_id: {workspace_id}")

    try:
        logger.info(f"Creating Git_Context_Manager for workspace: {workspace_id}")
        manager = get_manager(workspace_id)

        logger.info("Getting project context...")
        context = manager.get_project_context()
        logger.info("Context retrieved successfully")

        return context

    except Exception as e:
        logger.error(f"Error in context endpoint: {str(e)}")
        return {"error": f"Failed to get context: {str(e)}"}


@app.get("/context/milestones")
def get_milestones(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    print("context", manager.get_project_context())
    context = manager.get_project_context()
    checkpoint = context.get("checkpoint", {})
    milestones = checkpoint.get("milestones", [])
    print("milestones", milestones)
    return {"milestones": milestones}


@app.post("/commit")
def manual_commit(
    message: str = "Manual context update",
    agent: str = "manual",
    workspace_id: str = Query("default"),
):
    manager = get_manager(workspace_id)
    commit = manager.commit_changes(message=message, agent=agent)
    return {"status": "success", "commit": commit}


@app.post("/commit/llm")
def llm_commit(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    diff = manager.show_diff()
    try:
        summary = manager.summarize_diff_for_commit(diff)
    except Exception as e:
        summary = f"Error calling OpenAI: {str(e)}"
    commit = manager.commit_changes(message=summary, agent="llm")
    return {"status": "success", "commit": commit, "summary": summary}


@app.get("/log")
def get_log(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    return manager.get_project_context()["history"]


@app.get("/coach")
def get_coach_tip(workspace_id: str = Query("default")):
    logger.info(f"GET /coach called with workspace_id: {workspace_id}")

    try:
        logger.info(f"Creating Git_Context_Manager for workspace: {workspace_id}")
        manager = get_manager(workspace_id)

        logger.info("Getting project context...")
        state = manager.get_project_context()
        checkpoint = state.get("checkpoint")
        history = state.get("history", [])

        if not checkpoint:
            logger.info("No checkpoint data available")
            return {"tip": "No checkpoint data available yet."}

        today = datetime.today().date()
        milestones = checkpoint.get("milestones", [])
        status = checkpoint.get("current_status", "No current status recorded.")

        logger.info(f"Current status: {status}")
        logger.info(f"Number of milestones: {len(milestones)}")
        logger.info(f"Number of history entries: {len(history)}")

        if history:
            last_entry = history[-1]
            last_time = datetime.fromisoformat(last_entry["timestamp"]).date()
            days_inactive = (today - last_time).days
            logger.info(f"Days since last activity: {days_inactive}")

            if days_inactive >= 3:
                tip = (
                    f"You haven't made updates in {days_inactive} days.\n"
                    f"🔄 Review your current status: '{status}' and consider logging progress today!"
                )
                logger.info("Generated inactivity tip")
                return {"tip": tip}
            elif days_inactive == 0:
                logger.info("Generated momentum tip")
                return {"tip": "You're on a roll! Keep the momentum going 💪"}

        if milestones:
            next_milestone = sorted(milestones, key=lambda m: m["due"])[0]
            due_date = datetime.strptime(next_milestone["due"], "%Y-%m-%d").date()
            days_left = (due_date - today).days
            name = next_milestone["name"]
            logger.info(f"Next milestone: {name}, days left: {days_left}")

            if days_left < 0:
                tip = f"The milestone '{name}' was due {abs(days_left)} days ago. Consider updating your checkpoint."
                logger.info("Generated overdue milestone tip")
                return {"tip": tip}
            elif days_left == 0:
                logger.info("Generated deadline tip")
                return {
                    "tip": f"Today is the deadline for '{name}'! Time to wrap it up 🎯"
                }
            else:
                logger.info("Generated milestone reminder tip")
                return {
                    "tip": f"{days_left} day(s) left until the milestone '{name}'. Stay focused and make progress today!"
                }

        logger.info("No milestones found, generating default tip")
        return {
            "tip": "No milestones found. You can add one to help guide your progress!"
        }

    except Exception as e:
        logger.error(f"Error in coach endpoint: {str(e)}")
        return {"tip": f"Error generating coach tip: {str(e)}"}


@app.post("/update")
def update_checkpoint(
    project_name: str = Body(...),
    goal: str = Body(...),
    current_status: str = Body(...),
    milestones: list[dict] = Body(...),
    workspace_id: str = Query("default"),
):
    logger.info(f"POST /update called with workspace_id: {workspace_id}")
    logger.info(f"Project name: {project_name}")
    logger.info(f"Goal: {goal}")
    logger.info(f"Current status: {current_status}")
    logger.info(f"Number of milestones: {len(milestones)}")

    try:
        logger.info(f"Creating Git_Context_Manager for workspace: {workspace_id}")
        manager = get_manager(workspace_id)

        logger.info("Getting current project context...")
        state = manager.get_project_context()

        logger.info("Updating checkpoint data...")
        state["checkpoint"].update(
            {
                "project_name": project_name,
                "goal": goal,
                "current_status": current_status,
                "milestones": milestones,
            }
        )

        logger.info("Writing updated context to files...")
        manager.write_context(state)

        logger.info("Committing changes...")
        commit = manager.commit_changes(
            message="Checkpoint updated via API", agent="update"
        )
        logger.info(f"Commit successful with hash: {commit}")

        response = {"status": "updated", "commit": commit}
        logger.info("Update endpoint completed successfully")
        return response

    except Exception as e:
        logger.error(f"Error in update endpoint: {str(e)}")
        return {"status": "error", "message": f"Failed to update checkpoint: {str(e)}"}


@app.post("/push-to-llm")
def push_context_to_llm(request: LLMRequest, workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    try:
        context = manager.get_project_context()
        result = manager.query_llm(prompt=request.prompt, context=context)
        return {"response": result}
    except Exception as e:
        return {"error": str(e)}


@app.get("/summary")
def get_summary(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    context = manager.get_project_context()
    checkpoint = context.get("checkpoint", {})
    milestones = checkpoint.get("milestones", [])
    remaining = [m["name"] for m in milestones if "due" in m]

    return {
        "project_name": checkpoint.get("project_name"),
        "goal": checkpoint.get("goal"),
        "status": checkpoint.get("current_status"),
        "milestones": remaining,
    }


@app.post("/reflect")
def reflect(
    style: LLMRequest = Body(default="motivational"),
    workspace_id: str = Query("default"),
):
    manager = get_manager(workspace_id)
    prompt = (
        f"Gere uma reflexão de coaching no estilo '{style}' com base no contexto atual."
    )
    context = manager.get_project_context()
    try:
        result = manager.query_llm(prompt=prompt, context=context)
        return {"reflection": result}
    except Exception as e:
        return {"error": f"Erro ao gerar reflexão: {str(e)}"}


@app.post("/plan")
def plan(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    prompt = "Com base no contexto atual e nos marcos definidos, gere um plano de ação prático com etapas claras."
    context = manager.get_project_context()
    try:
        result = manager.query_llm(prompt=prompt, context=context)
        return {"plan": result}
    except Exception as e:
        return {"error": f"Erro ao gerar plano: {str(e)}"}


@app.get("/llm-history")
def llm_history(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    context = manager.get_project_context()
    llm_commits = [
        entry for entry in context.get("history", []) if entry.get("agent") == "llm"
    ]
    return {"llm_commits": llm_commits}


@app.post("/validate-goal")
def validate_goal(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    context = manager.get_project_context()
    goal = context.get("checkpoint", {}).get("goal", "")
    if not goal:
        return {
            "valid": False,
            "feedback": "Nenhum objetivo encontrado no contexto atual.",
        }

    prompt = f"Avalie se este objetivo é claro, mensurável e realista: '{goal}'"
    try:
        result = manager.query_llm(prompt=prompt, context=context)
        return {"valid": True, "feedback": result}
    except Exception as e:
        return {"valid": False, "feedback": f"Erro ao consultar LLM: {str(e)}"}


class Milestone(BaseModel):
    name: str
    due: str  # Format: YYYY-MM-DD


class ContextPayload(BaseModel):
    project_name: str
    goal: str
    initial_status: str
    milestones: List[Milestone]


@app.post("/generate-context")
async def generate_context(payload: ContextPayload, workspace_id: str = "default"):
    logger.info(f"POST /generate-context called with workspace_id: {workspace_id}")
    logger.info(f"Project name: {payload.project_name}")
    logger.info(f"Goal: {payload.goal}")
    logger.info(f"Initial status: {payload.initial_status}")
    logger.info(f"Number of milestones: {len(payload.milestones)}")

    try:
        logger.info(f"Creating Git_Context_Manager for workspace: {workspace_id}")
        manager = get_manager(workspace_id)

        # Create initial context structure
        context = {
            "checkpoint": {
                "project_name": payload.project_name,
                "goal": payload.goal,
                "current_status": payload.initial_status,
                "milestones": [milestone.dict() for milestone in payload.milestones],
            },
            "history": [],
        }
        logger.info("Context structure created successfully")

        # Write the context to files
        logger.info("Writing context to files...")
        manager.write_context(context)
        logger.info("Context written to files successfully")

        # Commit the changes
        commit_message = (
            f"Initial context generated for project: {payload.project_name}"
        )
        logger.info(f"Committing changes with message: {commit_message}")
        commit = manager.commit_changes(
            message=commit_message, agent="generate-context"
        )
        logger.info(f"Commit successful with hash: {commit}")

        response = {
            "status": "success",
            "message": f"Context generated successfully for project: {payload.project_name}",
            "commit": commit,
            "context": context,
        }
        logger.info("Generate context endpoint completed successfully")
        return response

    except Exception as e:
        logger.error(f"Error in generate-context endpoint: {str(e)}")
        return {"status": "error", "message": f"Failed to generate context: {str(e)}"}


@app.post("/context/commit-task")
def commit_task(
    task_name: str = Body(...),
    agent: str = Body(...),
    notes: str = Body(...),
    workspace_id: str = Query("default"),
):
    logger.info(f"POST /context/commit-task called with workspace_id: {workspace_id}")
    logger.info(f"Task name: {task_name}")
    logger.info(f"Agent: {agent}")
    logger.info(f"Notes: {notes}")

    try:
        logger.info(f"Creating Git_Context_Manager for workspace: {workspace_id}")
        manager = get_manager(workspace_id)

        # Log to history
        logger.info("Logging task history...")
        manager.log_history(message=notes, agent=agent)

        # ✅ Criar commit
        logger.info("Checking if there are changes to commit...")
        if not manager.repo.is_dirty(untracked_files=True):
            logger.warning("No changes detected. Skipping commit.")
            return {"status": "error", "message": "No changes detected to commit."}

        commit_message = f"Agent {agent} updated task: {task_name}"
        logger.info(f"Committing changes with message: {commit_message}")
        commit = manager.commit_changes(message=commit_message, agent=agent)
        logger.info(f"Commit successful with hash: {commit}")

        response = {"status": "success", "commit": commit}
        logger.info("Commit task endpoint completed successfully")
        return response

    except Exception as e:
        logger.error(f"Error in commit-task endpoint: {str(e)}")
        return {"status": "error", "message": f"Failed to commit task: {str(e)}"}


@app.post("/context/push")
def push_context(
    workspace_id: str = Query("default"),
    remote_name: str = Query("origin"),
    branch: str = Query("main"),
    auto_commit: bool = Query(False),
    commit_message: str = Query("Auto final sync"),
    agent: str = Query("manual"),
):
    logger.info(f"POST /context/push called for workspace_id: {workspace_id}")
    try:
        manager = get_manager(workspace_id)

        if auto_commit:
            final_commit_hash = manager.commit_changes(
                message=commit_message, agent=agent
            )
            logger.info(f"Final commit hash before push: {final_commit_hash}")

            # 🔒 Safety check extra
            if manager.repo.is_dirty(untracked_files=True):
                logger.info(
                    "Extra changes detected even after final commit. Forcing last safety commit..."
                )
                manager.repo.git.add(A=True)
                extra_message = f"Final safety auto-commit before push by {agent}"
                extra_commit = manager.repo.index.commit(extra_message)
                logger.info(
                    f"✅ Safety commit created with hash: {extra_commit.hexsha}"
                )

        res = manager.push_changes(remote_name=remote_name, branch=branch)

        if res["status"] == "success":
            return {
                "status": "success",
                "message": "Changes pushed successfully",
                "push_details": res["details"],
                "commit": final_commit_hash,
            }
        else:
            return {"status": "error", "message": res["message"]}
    except Exception as e:
        logger.error(f"Error in push endpoint: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.post("/context/close-cycle")
def close_cycle(workspace_id: str = Query("default")):
    logger.info(f"POST /context/close-cycle called for workspace_id: {workspace_id}")
    try:
        manager = get_manager(workspace_id)
        success = manager.close_cycle()
        if success:
            return {"status": "success", "message": "Cycle closed successfully."}
        else:
            return {"status": "error", "message": "Failed to close cycle."}
    except Exception as e:
        logger.error(f"Error closing cycle: {str(e)}")
        return {"status": "error", "message": str(e)}


# ===== ENDPOINTS FOR EXTENSION (MOCK FOR TESTING) =====


@app.get("/health")
def health_check():
    """Health check for extension connectivity"""
    logger.info("Health check called")
    return {
        "status": "ok",
        "version": "2.0.0",
        "agents": ["context", "spec", "strategy", "milestone", "git", "coach"],
    }


@app.get("/admin/abuse-stats")
def get_abuse_stats():
    """
    Get abuse detection statistics (admin endpoint)

    In production, this should require authentication!
    """
    logger.info("GET /admin/abuse-stats called")
    return abuse_detector.get_stats()


@app.get("/agents/status")
def get_agents_status():
    """Get status of all agents (mock for now)"""
    logger.info("GET /agents/status called")
    return [
        {
            "agent_id": "context",
            "name": "Context Agent",
            "status": "active",
            "last_activity": "Just now",
        },
        {
            "agent_id": "spec",
            "name": "Spec Agent",
            "status": "active",
            "last_activity": "5 minutes ago",
        },
        {
            "agent_id": "strategy",
            "name": "Strategy Agent",
            "status": "idle",
            "last_activity": "1 hour ago",
        },
        {
            "agent_id": "milestone",
            "name": "Milestone Agent",
            "status": "active",
            "last_activity": "10 minutes ago",
        },
        {
            "agent_id": "git",
            "name": "Git Agent",
            "status": "active",
            "last_activity": "2 minutes ago",
        },
        {
            "agent_id": "coach",
            "name": "Coach Agent",
            "status": "active",
            "last_activity": "Just now",
        },
    ]


@app.post("/agents/coach/ask")
def coach_ask(user_id: str = Body(...), question: str = Body(...)):
    """Ask the coach agent a question (mock for now)"""
    logger.info(f"POST /agents/coach/ask - user: {user_id}, question: {question}")
    # TODO: Integrate with actual coach agent
    mock_answer = f"Great question! For '{question}', I recommend: 1) Break it into smaller tasks, 2) Write tests first, 3) Document as you go. Let me know if you need more specific guidance!"
    return {"answer": mock_answer}


@app.get("/proposals/mock")
def get_mock_proposals():
    """Get mock proposals for testing"""
    logger.info("GET /proposals/mock called")
    return [
        {
            "id": "prop-001",
            "agent_id": "strategy",
            "title": "Add error handling to API calls",
            "description": "Found 3 API calls without proper error handling. This could cause silent failures.",
            "proposed_changes": [
                {
                    "file_path": "src/api.ts",
                    "change_type": "update",
                    "description": "Wrap fetch calls in try-catch blocks",
                }
            ],
            "status": "pending",
            "created_at": "2025-10-14T10:30:00Z",
        },
        {
            "id": "prop-002",
            "agent_id": "spec",
            "title": "Update API documentation",
            "description": "API endpoints in api.ts need documentation with examples.",
            "proposed_changes": [
                {
                    "file_path": "src/api.ts",
                    "change_type": "update",
                    "description": "Add JSDoc comments with examples",
                }
            ],
            "status": "pending",
            "created_at": "2025-10-14T10:45:00Z",
        },
    ]


@app.get("/rewards/balance/mock")
def get_mock_balance(user_id: str = Query("test")):
    """Get mock rewards balance for testing"""
    logger.info(f"GET /rewards/balance/mock called for user: {user_id}")
    return {"balance": 150, "total_earned": 300, "pending_rewards": 50}


# ===== GIT AGENT ENDPOINTS =====


@app.post("/git/event")
async def trigger_git_event(
    workspace_id: str = Query("default"),
    event_type: str = Body(...),
    data: dict = Body(...),
    source: str = Body("manual"),
):
    """
    Trigger Git Agent to handle an event

    Example:
    ```json
    {
        "event_type": "spec.created",
        "data": {
            "file_name": "git_agent.py",
            "description": "Created Git Agent MVP"
        },
        "source": "developer"
    }
    ```
    """
    from app.agents.git_agent import commit_via_agent

    logger.info(f"POST /git/event - workspace: {workspace_id}, type: {event_type}")

    try:
        commit_hash = await commit_via_agent(
            workspace_id=workspace_id, event_type=event_type, data=data, source=source
        )

        if commit_hash:
            return {
                "status": "success",
                "message": "Git Agent processed event and created commit",
                "commit_hash": commit_hash,
            }
        else:
            return {
                "status": "skipped",
                "message": "Git Agent decided not to commit (changes not significant)",
            }
    except Exception as e:
        logger.error(f"Error processing git event: {str(e)}")
        return {"status": "error", "message": str(e)}


# ===== SPEC AGENT ENDPOINTS =====


@app.post("/agents/spec/analyze")
async def spec_analyze(workspace_id: str = Query("default")):
    """Analyze documentation consistency and return issues (Spec Agent)."""
    logger.info(f"POST /agents/spec/analyze - workspace: {workspace_id}")
    try:
        workspace_path = str(get_workspace_path(workspace_id))
        project_id = os.getenv(
            "GCP_PROJECT_ID",
            os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
        )
        agent = SpecAgent(workspace_path=workspace_path, project_id=project_id)
        issues = await agent.validate_docs()
        return {"issues": issues, "count": len(issues)}
    except Exception as e:
        logger.error(f"Error analyzing docs: {str(e)}")
        return {"issues": [], "count": 0, "error": str(e)}


@app.get("/agents/spec/proposals")
async def spec_get_proposals(workspace_id: str = Query("default")):
    """Create in-memory change proposals from SpecAgent issues (no commit).

    The approval will be a separate step that triggers the Git Agent.
    """
    logger.info(f"GET /agents/spec/proposals - workspace: {workspace_id}")
    try:
        workspace_path = str(get_workspace_path(workspace_id))
        project_id = os.getenv(
            "GCP_PROJECT_ID",
            os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
        )
        agent = SpecAgent(workspace_path=workspace_path, project_id=project_id)
        issues: List[Dict] = await agent.validate_docs()

        # Map issues -> lightweight proposals (not persisted)
        proposals: List[Dict] = []
        for idx, issue in enumerate(issues, start=1):
            title = f"Docs issue: {issue.get('file', 'unknown')}"
            description = issue.get("message", issue.get("type", "issue"))
            proposals.append(
                {
                    "id": f"spec-{idx}",
                    "agent_id": "spec",
                    "title": title,
                    "description": description,
                    "proposed_changes": [
                        {
                            "file_path": issue.get("file", "docs/"),
                            "change_type": "update",
                            "description": description,
                        }
                    ],
                    "status": "pending",
                }
            )

        return {"proposals": proposals, "count": len(proposals)}
    except Exception as e:
        logger.error(f"Error generating spec proposals: {str(e)}")
        return {"proposals": [], "count": 0, "error": str(e)}


@app.post("/proposals/approve-mvp")
async def approve_proposal_mvp(
    workspace_id: str = Query("default"),
    proposal_id: str = Body(...),
    summary: str = Body(...),
):
    """Approval trigger that calls the Git Agent (MVP, no persistence)."""
    logger.info(
        f"POST /proposals/approve-mvp - {proposal_id} (workspace: {workspace_id})"
    )
    try:
        from app.agents.git_agent import commit_via_agent

        commit_hash = await commit_via_agent(
            workspace_id=workspace_id,
            event_type="proposal.approved",
            data={"proposal_id": proposal_id, "changes_summary": summary},
            source="spec-agent",
        )
        return {"status": "approved", "commit_hash": commit_hash}
    except Exception as e:
        logger.error(f"Error approving proposal: {str(e)}")
        return {"status": "error", "error": str(e)}


# ===== PROPOSALS PERSISTENCE (MVP - JSON + MD in workspace) =====


def _proposals_paths(workspace_id: str) -> Dict[str, Path]:
    ws = Path(get_workspace_path(workspace_id))
    proposals_dir = ws / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    return {
        "json": ws / "proposals.json",
        "dir": proposals_dir,
    }


def _read_proposals(json_path: Path) -> List[Dict]:
    """Read proposals from proposals.json (legacy)"""
    if json_path.exists():
        try:
            return json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _read_proposals_from_dir(proposals_dir: Path) -> List[Dict]:
    """Read all proposals from proposals/ directory (new format with diffs)"""
    if not proposals_dir.exists():
        return []

    proposals = []
    for json_file in proposals_dir.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                proposal = json.load(f)
                proposals.append(proposal)
        except Exception as e:
            logger.error(f"Error reading proposal {json_file}: {e}")

    # Sort by created_at (newest first)
    proposals.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return proposals


def _write_proposals(json_path: Path, proposals: List[Dict]):
    json_path.write_text(json.dumps(proposals, indent=2), encoding="utf-8")


def _auto_approve_enabled() -> bool:
    val = os.getenv(
        "CONTEXTPILOT_AUTO_APPROVE_PROPOSALS",
        os.getenv("CP_AUTO_APPROVE_PROPOSALS", "false"),
    )
    return str(val).lower() in ("1", "true", "yes", "on")


async def _trigger_github_workflow(proposal_id: str, proposal: Dict) -> bool:
    """
    Trigger GitHub Actions workflow to apply proposal.

    Uses repository_dispatch event to trigger the workflow.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv(
        "GITHUB_REPO", "fsegall/google-context-pilot"
    )  # Format: owner/repo

    if not github_token:
        logger.warning("[API] GITHUB_TOKEN not set, skipping GitHub trigger")
        return False

    url = f"https://api.github.com/repos/{github_repo}/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    payload = {
        "event_type": "proposal-approved",
        "client_payload": {
            "proposal_id": proposal_id,
            "title": proposal.get("title", ""),
            "description": proposal.get("description", ""),
            "workspace_id": proposal.get("workspace_id", "contextpilot"),
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=10.0
            )
            response.raise_for_status()
            logger.info(
                f"[API] GitHub Actions triggered successfully for {proposal_id}"
            )
            return True
    except Exception as e:
        logger.error(f"[API] Failed to trigger GitHub Actions: {e}")
        return False


@app.get("/proposals")
async def list_proposals(workspace_id: str = Query("default")):
    """List all proposals with diffs"""

    # Try Firestore first (if enabled)
    if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
        try:
            from app.repositories.proposal_repository import get_proposal_repository

            repo = get_proposal_repository()
            proposals = repo.list(workspace_id=workspace_id)
            logger.info(f"[API] Listed {len(proposals)} proposals from Firestore")
            return {"proposals": proposals, "count": len(proposals)}
        except Exception as e:
            logger.error(f"[API] Firestore error, falling back to local: {e}")

    # Fallback to local file storage
    paths = _proposals_paths(workspace_id)

    # Try new format first (individual JSON files with diffs)
    proposals = _read_proposals_from_dir(paths["dir"])

    # Fallback to legacy format if no proposals in dir
    if not proposals:
        proposals = _read_proposals(paths["json"])

    return {"proposals": proposals, "count": len(proposals)}


@app.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str, workspace_id: str = Query("default")):
    """Get a single proposal by ID with full diff"""

    # Try Firestore first (if enabled)
    if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
        try:
            from app.repositories.proposal_repository import get_proposal_repository

            repo = get_proposal_repository()
            proposal = repo.get(proposal_id)
            if proposal:
                logger.info(f"[API] Found proposal in Firestore: {proposal_id}")
                return proposal
        except Exception as e:
            logger.error(f"[API] Firestore error, falling back to local: {e}")

    # Fallback to local file storage
    paths = _proposals_paths(workspace_id)

    # Try to read from individual file
    proposal_file = paths["dir"] / f"{proposal_id}.json"
    if proposal_file.exists():
        try:
            with open(proposal_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading proposal {proposal_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to read proposal: {e}")

    # Fallback: search in proposals.json
    proposals = _read_proposals(paths["json"])
    for p in proposals:
        if p.get("id") == proposal_id:
            return p

    raise HTTPException(status_code=404, detail="Proposal not found")


@app.post("/proposals/create")
async def create_proposals_from_spec(workspace_id: str = Query("default")):
    """Generate proposals from SpecAgent with diffs, persist to Firestore."""
    logger.info(f"POST /proposals/create - workspace: {workspace_id}")

    try:
        workspace_path = str(get_workspace_path(workspace_id))
        project_id = os.getenv(
            "GCP_PROJECT_ID",
            os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
        )
        agent = SpecAgent(
            workspace_path=workspace_path,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        issues: List[Dict] = await agent.validate_docs()

        # Create proposals with actual diffs using agent's method
        new_proposals = []
        for issue in issues:
            proposal_id = await agent._create_proposal_for_issue(issue)
            if proposal_id:
                new_proposals.append(proposal_id)

        # Count total proposals in Firestore
        if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
            repo = get_proposal_repository()
            all_proposals = repo.list(workspace_id=workspace_id)
            total = len(all_proposals)
        else:
            # Fallback to local file storage
            paths = _proposals_paths(workspace_id)
            proposals = _read_proposals_from_dir(paths["dir"])
            if not proposals:
                proposals = _read_proposals(paths["json"])
            total = len(proposals)

        return {"created": len(new_proposals), "total": total}
    except Exception as e:
        logger.error(f"Error creating proposals: {str(e)}")
        return {"created": 0, "error": str(e)}


@app.get("/context/summary")
async def get_context_summary(
    proposal_type: str = Query("general"), workspace_id: str = Query("default")
):
    """Generate intelligent context summary for new chat sessions."""
    try:
        from app.agents.spec_agent import SpecAgent

        # Get workspace path
        workspace_path = get_workspace_path(workspace_id)
        if not workspace_path:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Initialize Spec Agent
        spec_agent = SpecAgent(
            workspace_path=workspace_path,
            workspace_id=workspace_id,
            project_id=os.getenv("GCP_PROJECT_ID"),
        )

        # Generate context summary
        context = spec_agent.generate_context_summary(proposal_type)

        return {
            "context": context,
            "proposal_type": proposal_type,
            "workspace_id": workspace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating context summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, workspace_id: str = Query("default")):
    # Try Firestore first (if enabled)
    if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
        try:
            from app.repositories.proposal_repository import get_proposal_repository

            repo = get_proposal_repository()
            prop = repo.get(proposal_id)

            if not prop:
                return {"status": "not_found"}

            summary = prop.get("description", "")
            commit_hash = None

            if _auto_approve_enabled():
                try:
                    from app.agents.git_agent import commit_via_agent

                    commit_hash = await commit_via_agent(
                        workspace_id=workspace_id,
                        event_type="proposal.approved",
                        data={
                            "proposal_id": proposal_id,
                            "workspace_id": workspace_id,
                            "changes_summary": summary,
                        },
                        source="spec-agent",
                    )
                except Exception as git_error:
                    logger.warning(f"[API] Git commit failed (non-fatal): {git_error}")
                    # Continue with approval even if Git fails

            # Update status in Firestore
            repo.approve(proposal_id, commit_hash)

            # Trigger GitHub Actions workflow for cloud deployment
            github_triggered = False
            if os.getenv("ENVIRONMENT") == "production" and not commit_hash:
                try:
                    github_triggered = await _trigger_github_workflow(proposal_id, prop)
                    logger.info(
                        f"[API] GitHub Actions triggered for proposal {proposal_id}"
                    )
                except Exception as gh_error:
                    logger.warning(f"[API] GitHub trigger failed: {gh_error}")

            return {
                "status": "approved",
                "commit_hash": commit_hash,
                "auto_committed": bool(commit_hash),
                "github_triggered": github_triggered,
            }
        except Exception as e:
            logger.error(f"[API] Firestore approve error: {e}")
            return {"status": "error", "error": str(e)}

    # Fallback to local file storage
    paths = _proposals_paths(workspace_id)

    # Try to read from individual file first (new format)
    proposal_file = paths["dir"] / f"{proposal_id}.json"
    if proposal_file.exists():
        with open(proposal_file, "r") as f:
            prop = json.load(f)
    else:
        # Fallback to proposals.json (legacy)
        proposals = _read_proposals(paths["json"])
        prop = next((p for p in proposals if p.get("id") == proposal_id), None)

    if not prop:
        return {"status": "not_found"}

    summary = prop.get("description", "")
    try:
        commit_hash = None
        if _auto_approve_enabled():
            try:
                from app.agents.git_agent import commit_via_agent

                commit_hash = await commit_via_agent(
                    workspace_id=workspace_id,
                    event_type="proposal.approved",
                    data={"proposal_id": proposal_id, "changes_summary": summary},
                    source="spec-agent",
                )
            except Exception as git_error:
                logger.warning(f"[API] Git commit failed (non-fatal): {git_error}")
                # Continue with approval even if Git fails
        # Update proposal status
        prop["status"] = "approved"
        if commit_hash:
            prop["commit_hash"] = commit_hash

        # Save to individual file if it exists
        if proposal_file.exists():
            with open(proposal_file, "w") as f:
                json.dump(prop, f, indent=2)
        else:
            # Save to proposals.json (legacy)
            _write_proposals(paths["json"], proposals)

        # Update MD file
        md_path = paths["dir"] / f"{proposal_id}.md"
        if md_path.exists():
            md_content = md_path.read_text(encoding="utf-8")
            md_content += f"\n\n---\n**Status:** approved\n"
            if commit_hash:
                md_content += f"**Commit:** {commit_hash}\n"
            md_path.write_text(md_content, encoding="utf-8")

        return {
            "status": "approved",
            "commit_hash": commit_hash,
            "auto_committed": bool(commit_hash),
        }
    except Exception as e:
        logger.error(f"Error approving proposal: {str(e)}")
        return {"status": "error", "error": str(e)}


@app.post("/proposals/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: str, workspace_id: str = Query("default"), reason: str = Body("")
):
    paths = _proposals_paths(workspace_id)
    proposals = _read_proposals(paths["json"])
    prop = next((p for p in proposals if p.get("id") == proposal_id), None)
    if not prop:
        return {"status": "not_found"}
    prop["status"] = "rejected"
    prop["reason"] = reason
    _write_proposals(paths["json"], proposals)

    md_path = paths["dir"] / f"{proposal_id}.md"
    if md_path.exists():
        md_content = md_path.read_text(encoding="utf-8")
        md_content += f"\nStatus: rejected\nReason: {reason}\n"
        md_path.write_text(md_content, encoding="utf-8")
    return {"status": "rejected"}


# ===== RETROSPECTIVE AGENT ENDPOINTS =====


@app.post("/agents/retrospective/trigger")
async def trigger_agent_retrospective(
    workspace_id: str = Query("default"),
    trigger: str = Body("manual"),
    use_llm: bool = Body(False),
    trigger_topic: Optional[str] = Body(None),
):
    """
    Trigger a retrospective meeting between agents.

    This endpoint facilitates cross-agent learning by:
    - Collecting metrics from all agents
    - Analyzing event history
    - Generating insights and action items
    - (Optional) Synthesizing with LLM

    Args:
        workspace_id: Workspace identifier
        trigger: What triggered the retrospective (e.g., "manual", "milestone_complete", "cycle_end")
        use_llm: Whether to use Gemini LLM for narrative synthesis
        trigger_topic: Optional topic for agent discussion

    Returns:
        Retrospective summary with agent insights
    """
    logger.info(f"POST /agents/retrospective/trigger - workspace: {workspace_id}, trigger: {trigger}, topic: {trigger_topic}")

    try:
        from app.agents.retrospective_agent import trigger_retrospective
        import asyncio

        # Get Gemini API key if LLM synthesis requested
        gemini_api_key = None
        if use_llm:
            gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not gemini_api_key:
                logger.warning("[API] LLM synthesis requested but no API key found")

        # Add timeout to prevent 503 errors (max 840 seconds to stay under Cloud Run 900s limit)
        try:
            retrospective = await asyncio.wait_for(
                trigger_retrospective(
                    workspace_id=workspace_id,
                    trigger=trigger,
                    gemini_api_key=gemini_api_key,
                    trigger_topic=trigger_topic
                ),
                timeout=840.0  # 14 minutes max (leaving 60s buffer for Cloud Run 900s limit)
            )
        except asyncio.TimeoutError:
            logger.error(f"[API] Retrospective timeout after 840 seconds for workspace: {workspace_id}")
            raise HTTPException(
                status_code=504,
                detail="Retrospective processing timed out. Try again with use_llm=false or check agent logs."
            )

        return {
            "status": "success",
            "retrospective": retrospective
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retrospective: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger retrospective: {str(e)}"
        )


@app.get("/agents/development/diagnostic")
async def get_development_agent_diagnostic(workspace_id: str = Query("default")):
    """
    Get detailed diagnostic information about Development Agent and Codespaces configuration.
    
    This endpoint provides visibility into:
    - Codespaces configuration status
    - Token availability and scopes
    - Authentication test results
    - Last error messages
    - Current mode being used
    """
    logger.info(f"GET /agents/development/diagnostic - workspace: {workspace_id}")
    
    try:
        # Ensure workspace exists before getting path
        from app.utils.workspace_manager import ensure_workspace_exists
        ensure_workspace_exists(workspace_id)
        
        workspace_path = get_workspace_path(workspace_id)
        project_id = os.getenv(
            "GCP_PROJECT_ID",
            os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
        )
        
        from app.agents.development_agent import DevelopmentAgent
        import requests
        
        # Initialize agent to get configuration
        try:
            agent = DevelopmentAgent(
                workspace_path=str(workspace_path),
                workspace_id=workspace_id,
                project_id=project_id,
            )
        except Exception as agent_error:
            logger.error(f"Error initializing DevelopmentAgent: {agent_error}", exc_info=True)
            return {
                "error": f"Failed to initialize DevelopmentAgent: {str(agent_error)}",
                "workspace_id": workspace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        diagnostic = {
            "workspace_id": workspace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "codespaces": {
                "enabled": agent.codespaces_enabled,
                "repo": agent.codespaces_repo,
                "machine": agent.codespaces_machine,
            },
            "sandbox": {
                "enabled": agent.sandbox_enabled,
                "repo_url": agent.sandbox_repo_url if agent.sandbox_enabled else None,
            },
            "github_token": {
                "available": agent.github_token is not None,
                "source": None,
                "preview": None,
                "length": len(agent.github_token) if agent.github_token else 0,
            },
            "authentication": {
                "tested": False,
                "status": "not_tested",
                "message": None,
                "scopes": [],
                "missing_scopes": [],
                "error": None,
            },
            "processed_retrospectives": list(agent.processed_retrospectives),
        }
        
        # Determine token source
        if os.getenv("PERSONAL_GITHUB_TOKEN"):
            diagnostic["github_token"]["source"] = "PERSONAL_GITHUB_TOKEN"
        elif os.getenv("GITHUB_TOKEN"):
            diagnostic["github_token"]["source"] = "GITHUB_TOKEN"
        elif os.getenv("GH_TOKEN"):
            diagnostic["github_token"]["source"] = "GH_TOKEN"
        else:
            diagnostic["github_token"]["source"] = "none"
        
        if agent.github_token:
            diagnostic["github_token"]["preview"] = f"{agent.github_token[:10]}...{agent.github_token[-4:]}" if len(agent.github_token) > 14 else "***"
        
        # Test authentication if token is available
        if agent.github_token and agent.codespaces_enabled:
            try:
                # Test 1: Check token scopes
                url = "https://api.github.com/user"
                headers = {
                    "Authorization": f"Bearer {agent.github_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    scopes_header = response.headers.get("X-OAuth-Scopes", "")
                    if scopes_header:
                        scopes = [s.strip() for s in scopes_header.split(",")]
                        diagnostic["authentication"]["scopes"] = scopes
                        
                        required_scopes = ["repo", "codespace"]
                        missing = [s for s in required_scopes if s not in scopes]
                        diagnostic["authentication"]["missing_scopes"] = missing
                        
                        if missing:
                            diagnostic["authentication"]["status"] = "missing_scopes"
                            diagnostic["authentication"]["message"] = f"Token missing scopes: {', '.join(missing)}"
                        else:
                            diagnostic["authentication"]["status"] = "scopes_ok"
                            diagnostic["authentication"]["message"] = "Token has required scopes"
                    
                    # Test 2: Try to list codespaces
                    codespaces_url = "https://api.github.com/user/codespaces"
                    codespaces_response = requests.get(codespaces_url, headers=headers, timeout=10)
                    
                    if codespaces_response.status_code == 200:
                        diagnostic["authentication"]["status"] = "authenticated"
                        diagnostic["authentication"]["message"] = "Authentication successful - Codespaces API accessible"
                        codespaces_data = codespaces_response.json()
                        diagnostic["codespaces"]["active_count"] = len(codespaces_data.get("codespaces", []))
                    elif codespaces_response.status_code in [401, 403]:
                        diagnostic["authentication"]["status"] = "authentication_failed"
                        try:
                            error_data = codespaces_response.json()
                            error_msg = error_data.get("message", "Unknown error")
                            diagnostic["authentication"]["message"] = f"Authentication failed: {error_msg}"
                            diagnostic["authentication"]["error"] = error_data
                        except:
                            diagnostic["authentication"]["message"] = f"Authentication failed: {codespaces_response.status_code}"
                    else:
                        diagnostic["authentication"]["status"] = "api_error"
                        diagnostic["authentication"]["message"] = f"API returned status {codespaces_response.status_code}"
                else:
                    diagnostic["authentication"]["status"] = "token_invalid"
                    diagnostic["authentication"]["message"] = f"Token validation failed: {response.status_code}"
                
                diagnostic["authentication"]["tested"] = True
                
            except Exception as e:
                diagnostic["authentication"]["status"] = "test_error"
                diagnostic["authentication"]["message"] = f"Error testing authentication: {str(e)}"
                diagnostic["authentication"]["error"] = str(e)
        
        # Determine current mode
        if agent.codespaces_enabled and diagnostic["authentication"]["status"] == "authenticated":
            diagnostic["current_mode"] = "codespaces"
            diagnostic["current_mode_reason"] = "Codespaces enabled and authenticated"
        elif agent.sandbox_enabled:
            diagnostic["current_mode"] = "sandbox"
            diagnostic["current_mode_reason"] = "Sandbox mode enabled (Codespaces not available or not authenticated)"
        else:
            diagnostic["current_mode"] = "proposal"
            diagnostic["current_mode_reason"] = "Proposal mode (Codespaces and Sandbox not available)"
        
        return diagnostic
        
    except Exception as e:
        logger.error(f"Error getting development agent diagnostic: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "workspace_id": workspace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@app.get("/agents/retrospective/list")
async def list_retrospectives(workspace_id: str = Query("default")):
    """
    List all retrospectives for a workspace.

    Returns:
        List of retrospective summaries
    """
    logger.info(f"GET /agents/retrospective/list - workspace: {workspace_id}")

    try:
        workspace_path = get_workspace_path(workspace_id)
        retro_dir = Path(workspace_path) / "retrospectives"

        if not retro_dir.exists():
            return {"retrospectives": [], "count": 0}

        retrospectives = []
        for json_file in sorted(retro_dir.glob("*.json"), reverse=True):
            try:
                with open(json_file, "r") as f:
                    retro = json.load(f)
                    # Return summary only (not full data)
                    retrospectives.append({
                        "retrospective_id": retro.get("retrospective_id"),
                        "timestamp": retro.get("timestamp"),
                        "trigger": retro.get("trigger"),
                        "insights_count": len(retro.get("insights", [])),
                        "action_items_count": len(retro.get("action_items", []))
                    })
            except Exception as e:
                logger.error(f"Error reading retrospective {json_file}: {e}")

        return {"retrospectives": retrospectives, "count": len(retrospectives)}

    except Exception as e:
        logger.error(f"Error listing retrospectives: {str(e)}")
        return {"retrospectives": [], "count": 0, "error": str(e)}


@app.get("/agents/retrospective/{retrospective_id}")
async def get_retrospective(retrospective_id: str, workspace_id: str = Query("default")):
    """
    Get a specific retrospective by ID.

    Returns:
        Full retrospective data
    """
    logger.info(f"GET /agents/retrospective/{retrospective_id} - workspace: {workspace_id}")

    try:
        workspace_path = get_workspace_path(workspace_id)
        retro_file = Path(workspace_path) / "retrospectives" / f"{retrospective_id}.json"

        if not retro_file.exists():
            raise HTTPException(status_code=404, detail="Retrospective not found")

        with open(retro_file, "r") as f:
            retrospective = json.load(f)

        return retrospective

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading retrospective: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/log")
async def get_event_log(
    workspace_id: str = Query("default"),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
):
    """
    Get event log from EventBus (inspect event stack).
    
    Returns all events published through the event bus.
    Works with both InMemoryEventBus (development) and PubSubEventBus (production).
    
    Args:
        workspace_id: Workspace identifier
        limit: Maximum number of events to return (1-1000)
        event_type: Optional filter by event type
    
    Returns:
        List of events with full payload
    """
    logger.info(f"GET /events/log - workspace: {workspace_id}, limit: {limit}, event_type: {event_type}")
    
    try:
        from app.services.event_bus import get_event_bus
        
        project_id = os.getenv(
            "GCP_PROJECT_ID",
            os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
        )
        
        event_bus = get_event_bus(project_id=project_id)
        
        # Get event log
        if hasattr(event_bus, "get_event_log"):
            events = event_bus.get_event_log(limit=limit)
            
            # Filter by event type if specified
            if event_type:
                events = [e for e in events if e.get("event_type") == event_type]
            
            # Sort by timestamp (most recent first)
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {
                "events": events,
                "count": len(events),
                "event_bus_type": type(event_bus).__name__,
                "workspace_id": workspace_id,
            }
        else:
            return {
                "error": "Event bus does not support get_event_log()",
                "event_bus_type": type(event_bus).__name__,
                "workspace_id": workspace_id,
            }
    
    except Exception as e:
        logger.error(f"Error getting event log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get event log: {str(e)}")


@app.get("/events/stats")
async def get_event_stats(workspace_id: str = Query("default")):
    """
    Get event statistics (counts by type, source, topic).
    
    Returns:
        Statistics about events in the event log
    """
    logger.info(f"GET /events/stats - workspace: {workspace_id}")
    
    try:
        from app.services.event_bus import get_event_bus
        
        project_id = os.getenv(
            "GCP_PROJECT_ID",
            os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
        )
        
        event_bus = get_event_bus(project_id=project_id)
        
        if hasattr(event_bus, "get_event_log"):
            events = event_bus.get_event_log(limit=1000)
            
            # Calculate statistics
            by_type = defaultdict(int)
            by_source = defaultdict(int)
            by_topic = defaultdict(int)
            
            for event in events:
                event_type = event.get("event_type", "unknown")
                source = event.get("source", "unknown")
                topic = event.get("topic", "unknown")
                
                by_type[event_type] += 1
                by_source[source] += 1
                by_topic[topic] += 1
            
            return {
                "total_events": len(events),
                "by_type": dict(by_type),
                "by_source": dict(by_source),
                "by_topic": dict(by_topic),
                "event_bus_type": type(event_bus).__name__,
                "workspace_id": workspace_id,
            }
        else:
            return {
                "error": "Event bus does not support get_event_log()",
                "event_bus_type": type(event_bus).__name__,
            }
    
    except Exception as e:
        logger.error(f"Error getting event stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get event stats: {str(e)}")
