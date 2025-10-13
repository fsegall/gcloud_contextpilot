# utils/create_workspace.py

import sys
from utils.workspace_manager import create_workspace, list_workspaces

def main():
    if len(sys.argv) < 2:
        print("Uso: python create_workspace.py <nome_do_workspace>")
        print("\n📂 Workspaces existentes:")
        for ws in list_workspaces():
            print(f"- {ws['name']} ({ws['id']})")
        return

    name = " ".join(sys.argv[1:])
    workspace_id = create_workspace(name)
    print(f"✅ Workspace criado: {name} (ID: {workspace_id})")

if __name__ == "__main__":
    main()
