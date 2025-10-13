from app.git_context_manager import Git_Context_Manager
from app.utils.workspace_manager import list_workspaces, create_workspace
from datetime import datetime, date
import argparse
from dotenv import load_dotenv
import json
import sys

load_dotenv(dotenv_path=".env")

def print_context(workspace_id="default"):
    """Print the current context for a workspace"""
    try:
        manager = Git_Context_Manager(workspace_id=workspace_id)
        context = manager.get_project_context()
        cp = context["checkpoint"]
        history = context["history"]

        print(f"\n📦 Projeto: {cp.get('project_name', 'N/A')}")
        print(f"🎯 Meta: {cp.get('goal', 'N/A')}")
        print(f"📅 Criado em: {cp.get('created_at', 'N/A')}")
        print(f"📍 Status atual: {cp.get('current_status', 'N/A')}")

        print("\n🗓️ Marcos futuros:")
        for m in cp.get("milestones", []):
            print(f"  - {m['name']} (🗓️ {m['due']})")

        print("\n🕓 Histórico de contexto:")
        for h in reversed(history[-5:]):
            commit = h.get("commit", "???????")[:7]
            agent = h.get("agent", "unknown")
            summary = h.get("summary", "sem resumo")
            timestamp = h.get("timestamp")
            dt = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M') if timestamp else "sem data"

            print(f"  - [{commit}] ({agent}) {summary} @ {dt}")
    except Exception as e:
        print(f"❌ Erro ao carregar contexto: {str(e)}")
        sys.exit(1)

def suggest_next(workspace_id="default"):
    """Suggest next steps based on milestones"""
    try:
        manager = Git_Context_Manager(workspace_id=workspace_id)
        context = manager.get_project_context()
        cp = context["checkpoint"]
        today = date.today()

        print("\n🧠 Sugestão de próximo passo:")
        milestones = cp.get("milestones", [])
        if not milestones:
            print("- Nenhum marco definido. Considere adicionar marcos ao projeto.")
            return

        for m in milestones:
            due_date = m['due'] if isinstance(m['due'], date) else datetime.strptime(m['due'], "%Y-%m-%d").date()
            delta = (due_date - today).days
            if delta >= 0:
                print(f"- Faltam {delta} dia(s) para o marco: '{m['name']}'")
                print(f"  Sugestão: Revise os requisitos para '{m['name']}' e atualize o progresso no checkpoint.\n")
                return

        print("- Todos os marcos parecem ter sido ultrapassados. Considere atualizar o checkpoint.")
    except Exception as e:
        print(f"❌ Erro ao gerar sugestões: {str(e)}")
        sys.exit(1)

def list_workspaces_cmd():
    """List all available workspaces"""
    try:
        workspaces = list_workspaces()
        print("\n📁 Workspaces disponíveis:")
        for ws in workspaces:
            name = ws.get('name', ws['id'])
            print(f"  - {name} (ID: {ws['id']})")
        if not workspaces:
            print("  Nenhum workspace encontrado.")
    except Exception as e:
        print(f"❌ Erro ao listar workspaces: {str(e)}")
        sys.exit(1)

def create_workspace_cmd(name, goal, status="Planning"):
    """Create a new workspace"""
    try:
        workspace_id = create_workspace(name, goal, status)
        print(f"✅ Workspace '{name}' criado com ID: {workspace_id}")
        print(f"🎯 Meta: {goal}")
        print(f"📍 Status inicial: {status}")
    except Exception as e:
        print(f"❌ Erro ao criar workspace: {str(e)}")
        sys.exit(1)

def commit_task(workspace_id, task_name, agent, notes=""):
    """Commit a task to the workspace"""
    try:
        manager = Git_Context_Manager(workspace_id=workspace_id)
        
        # Combine task name and notes in the message
        message = f"Task: {task_name}"
        if notes:
            message += f" - {notes}"
        
        commit_hash = manager.commit_changes(
            message=message,
            agent=agent
        )
        print(f"✅ Task '{task_name}' commitada com sucesso!")
        print(f"🔗 Commit hash: {commit_hash}")
        print(f"👤 Agent: {agent}")
        if notes:
            print(f"📝 Notes: {notes}")
    except Exception as e:
        print(f"❌ Erro ao fazer commit da task: {str(e)}")
        sys.exit(1)

def show_help():
    """Show detailed help information"""
    print("""
🎯 ContextPilot CLI - Gerenciador de Contexto de Projetos

COMANDOS DISPONÍVEIS:

  context [workspace_id]     Mostra o contexto atual do projeto
  next [workspace_id]        Sugere próximos passos baseado nos marcos
  list                       Lista todos os workspaces disponíveis
  create <name> <goal>       Cria um novo workspace
  commit <task> <agent>      Faz commit de uma task (opcional: --notes, --workspace)
  help                       Mostra esta ajuda

EXEMPLOS:

  python -m app.cli context
  python -m app.cli context my-project
  python -m app.cli next
  python -m app.cli list
  python -m app.cli create "Meu Projeto" "Desenvolver uma API REST"
  python -m app.cli commit "Implementar autenticação" "developer" --notes "JWT tokens"
  python -m app.cli commit "Design da UI" "designer" --workspace "frontend-project"

OPÇÕES GLOBAIS:

  --workspace-id, -w        Especifica o workspace (padrão: default)
  --help, -h                Mostra ajuda para o comando específico
""")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ContextPilot CLI - Gerenciador de Contexto de Projetos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s context
  %(prog)s next
  %(prog)s list
  %(prog)s create "Meu Projeto" "Desenvolver uma API"
  %(prog)s commit "Implementar auth" "developer"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Context command
    context_parser = subparsers.add_parser("context", help="Mostra o contexto atual")
    context_parser.add_argument("workspace_id", nargs="?", default="default", help="ID do workspace")
    
    # Next command
    next_parser = subparsers.add_parser("next", help="Sugere próximos passos")
    next_parser.add_argument("workspace_id", nargs="?", default="default", help="ID do workspace")
    
    # List command
    subparsers.add_parser("list", help="Lista todos os workspaces")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Cria um novo workspace")
    create_parser.add_argument("name", help="Nome do projeto")
    create_parser.add_argument("goal", help="Objetivo do projeto")
    create_parser.add_argument("--status", default="Planning", help="Status inicial")
    
    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Faz commit de uma task")
    commit_parser.add_argument("task_name", help="Nome da task")
    commit_parser.add_argument("agent", help="Agente responsável")
    commit_parser.add_argument("--notes", default="", help="Notas adicionais")
    commit_parser.add_argument("--workspace", default="default", help="ID do workspace")
    
    # Help command
    subparsers.add_parser("help", help="Mostra ajuda detalhada")
    
    args = parser.parse_args()
    
    if not args.command or args.command == "help":
        show_help()
    elif args.command == "context":
        print_context(args.workspace_id)
    elif args.command == "next":
        suggest_next(args.workspace_id)
    elif args.command == "list":
        list_workspaces_cmd()
    elif args.command == "create":
        create_workspace_cmd(args.name, args.goal, args.status)
    elif args.command == "commit":
        commit_task(args.workspace, args.task_name, args.agent, args.notes)
    else:
        parser.print_help()
