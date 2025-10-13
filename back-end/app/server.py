from fastapi import FastAPI, Body, Query
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
from app.routers import rewards, proposals, events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log', mode='w'),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger(__name__)

CONTEXT_PILOT_URL = "http://localhost:8000"

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI(
    title="ContextPilot API",
    description="Manage long-term project scope using Git + LLMs + Web3 incentives. Stay aligned and intentional.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rewards.router)
app.include_router(proposals.router)
app.include_router(events.router)


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
    print('context', manager.get_project_context())
    context = manager.get_project_context()
    checkpoint = context.get("checkpoint", {})
    milestones = checkpoint.get("milestones", [])
    print('milestones', milestones)
    return {"milestones": milestones}


@app.post("/commit")
def manual_commit(message: str = "Manual context update", agent: str = "manual", workspace_id: str = Query("default")):
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
                return {"tip": f"Today is the deadline for '{name}'! Time to wrap it up 🎯"}
            else:
                logger.info("Generated milestone reminder tip")
                return {"tip": f"{days_left} day(s) left until the milestone '{name}'. Stay focused and make progress today!"}

        logger.info("No milestones found, generating default tip")
        return {"tip": "No milestones found. You can add one to help guide your progress!"}
        
    except Exception as e:
        logger.error(f"Error in coach endpoint: {str(e)}")
        return {"tip": f"Error generating coach tip: {str(e)}"}


@app.post("/update")
def update_checkpoint(
    project_name: str = Body(...),
    goal: str = Body(...),
    current_status: str = Body(...),
    milestones: list[dict] = Body(...),
    workspace_id: str = Query("default")
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
        state["checkpoint"].update({
            "project_name": project_name,
            "goal": goal,
            "current_status": current_status,
            "milestones": milestones,
        })
        
        logger.info("Writing updated context to files...")
        manager.write_context(state)
        
        logger.info("Committing changes...")
        commit = manager.commit_changes(message="Checkpoint updated via API", agent="update")
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
        "milestones": remaining
    }


@app.post("/reflect")
def reflect(style: LLMRequest = Body(default="motivational"), workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    prompt = f"Gere uma reflexão de coaching no estilo '{style}' com base no contexto atual."
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
        entry for entry in context.get("history", [])
        if entry.get("agent") == "llm"
    ]
    return {"llm_commits": llm_commits}


@app.post("/validate-goal")
def validate_goal(workspace_id: str = Query("default")):
    manager = get_manager(workspace_id)
    context = manager.get_project_context()
    goal = context.get("checkpoint", {}).get("goal", "")
    if not goal:
        return {"valid": False, "feedback": "Nenhum objetivo encontrado no contexto atual."}

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
                "milestones": [milestone.dict() for milestone in payload.milestones]
            },
            "history": []
        }
        logger.info("Context structure created successfully")
        
        # Write the context to files
        logger.info("Writing context to files...")
        manager.write_context(context)
        logger.info("Context written to files successfully")
        
        # Commit the changes
        commit_message = f"Initial context generated for project: {payload.project_name}"
        logger.info(f"Committing changes with message: {commit_message}")
        commit = manager.commit_changes(message=commit_message, agent="generate-context")
        logger.info(f"Commit successful with hash: {commit}")
        
        response = {
            "status": "success",
            "message": f"Context generated successfully for project: {payload.project_name}",
            "commit": commit,
            "context": context
        }
        logger.info("Generate context endpoint completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate-context endpoint: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to generate context: {str(e)}"
        }
    
@app.post("/context/commit-task")
def commit_task(
    task_name: str = Body(...),
    agent: str = Body(...),
    notes: str = Body(...),
    workspace_id: str = Query("default")
):
    logger.info(f"POST /context/commit-task called with workspace_id: {workspace_id}")
    logger.info(f"Task name: {task_name}")
    logger.info(f"Agent: {agent}")
    logger.info(f"Notes: {notes}")
    
    try:
        logger.info(f"Creating Git_Context_Manager for workspace: {workspace_id}")
        manager = get_manager(workspace_id)

        # ✅ Logar histórico
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
    agent: str = Query("manual")
):
    logger.info(f"POST /context/push called for workspace_id: {workspace_id}")
    try:
        manager = get_manager(workspace_id)

        if auto_commit:
            final_commit_hash = manager.commit_changes(message=commit_message, agent=agent)
            logger.info(f"Final commit hash before push: {final_commit_hash}")

            # 🔒 Safety check extra
            if manager.repo.is_dirty(untracked_files=True):
                logger.info("Extra changes detected even after final commit. Forcing last safety commit...")
                manager.repo.git.add(A=True)
                extra_message = f"Final safety auto-commit before push by {agent}"
                extra_commit = manager.repo.index.commit(extra_message)
                logger.info(f"✅ Safety commit created with hash: {extra_commit.hexsha}")

        res = manager.push_changes(remote_name=remote_name, branch=branch)

        if res["status"] == "success":
            return {
                "status": "success",
                "message": "Changes pushed successfully",
                "push_details": res["details"],
                "commit": final_commit_hash
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