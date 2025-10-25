# workspace_manager.py
import os
import uuid
import json
import yaml
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Determine base directory based on environment
if os.getcwd().endswith('/back-end'):
    # Running in Cloud Run - use /app
    BASE_DIR = os.path.join("/app", ".contextpilot", "workspaces")
else:
    # Running locally - use current directory
    BASE_DIR = os.path.join(os.getcwd(), ".contextpilot", "workspaces")
logger.info(f"Base directory for workspaces: {BASE_DIR}")
os.makedirs(BASE_DIR, exist_ok=True)
logger.info(f"Base directory created/verified: {BASE_DIR}")

def create_workspace(workspace_id: str, name: str) -> str:
    """Cria um novo workspace com ID específico e nome."""
    path = os.path.join(BASE_DIR, workspace_id)
    os.makedirs(path, exist_ok=True)

    metadata = {
        "id": workspace_id,
        "name": name,
        "path": path,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }

    with open(os.path.join(path, "meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Adiciona arquivos padrão
    with open(os.path.join(path, "checkpoint.yaml"), "w") as f:
        yaml.dump({
            "project_name": name,
            "goal": "",
            "current_status": "",
            "milestones": [],
            "created_at": datetime.utcnow().isoformat()
        }, f)

    with open(os.path.join(path, "history.json"), "w") as f:
        json.dump([], f, indent=2)

    return workspace_id

def ensure_workspace_exists(workspace_id: str):
    """Cria estrutura padrão se workspace não existir."""
    logger.info(f"Ensuring workspace exists: {workspace_id}")
    path = os.path.join(BASE_DIR, workspace_id)
    logger.info(f"Workspace path: {path}")
    
    if not os.path.exists(path):
        logger.info(f"Workspace does not exist, creating: {path}")
        os.makedirs(path, exist_ok=True)
        logger.info(f"Workspace directory created: {path}")

        meta_file = os.path.join(path, "meta.json")
        logger.info(f"Creating meta file: {meta_file}")
        with open(meta_file, "w") as f:
            json.dump({
                "id": workspace_id,
                "name": workspace_id,
                "path": path
            }, f, indent=2)
        logger.info("Meta file created successfully")

        checkpoint_file = os.path.join(path, "checkpoint.yaml")
        logger.info(f"Creating checkpoint file: {checkpoint_file}")
        with open(checkpoint_file, "w") as f:
            yaml.dump({
                "project_name": workspace_id,
                "goal": "",
                "current_status": "",
                "milestones": [],
                "created_at": datetime.utcnow().isoformat()
            }, f)
        logger.info("Checkpoint file created successfully")

        history_file = os.path.join(path, "history.json")
        logger.info(f"Creating history file: {history_file}")
        with open(history_file, "w") as f:
            json.dump([], f, indent=2)
        logger.info("History file created successfully")
        
        logger.info(f"Workspace '{workspace_id}' created successfully")
    else:
        logger.info(f"Workspace already exists: {path}")

def list_workspaces() -> list:
    """Lista todos os workspaces existentes com seus metadados."""
    workspaces = []
    for entry in os.listdir(BASE_DIR):
        meta_path = os.path.join(BASE_DIR, entry, "meta.json")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                workspaces.append(json.load(f))
    return workspaces

def get_workspace_path(workspace_id: str) -> str:
    """Retorna o caminho completo de um workspace existente."""
    logger.info(f"Getting workspace path for: {workspace_id}")
    path = os.path.join(BASE_DIR, workspace_id)
    logger.info(f"Calculated path: {path}")
    
    if os.path.exists(path):
        logger.info(f"Workspace found: {path}")
        return path
    else:
        logger.error(f"Workspace not found: {path}")
        raise FileNotFoundError(f"❌ Workspace '{workspace_id}' não encontrado.")

def get_workspace_meta(workspace_id: str) -> dict:
    """Retorna os metadados de um workspace específico."""
    meta_path = os.path.join(BASE_DIR, workspace_id, "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            return json.load(f)
    raise FileNotFoundError(f"❌ Metadados não encontrados para '{workspace_id}'.")
