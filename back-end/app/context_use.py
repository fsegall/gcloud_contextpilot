from GitContextManager import GitContextManager

manager = GitContextManager()
state = manager.get_project_context()
print(state)  # → conteúdo de checkpoint.yaml + history.json