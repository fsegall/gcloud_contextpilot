from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Button, ListView, ListItem, Input, TextArea, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from app.utils.workspace_manager import list_workspaces, create_workspace
from app.git_context_manager import Git_Context_Manager
import uuid
import os


class CreateWorkspaceModal(ModalScreen):
    """Modal para criar novo workspace"""
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("📁 Criar Novo Workspace", classes="title"),
            Input(placeholder="Nome do projeto", id="project_name"),
            Input(placeholder="Objetivo do projeto", id="project_goal"),
            Input(placeholder="Status inicial (opcional)", id="project_status", value="Planning"),
            Horizontal(
                Button("✅ Criar", id="create_btn", variant="primary"),
                Button("❌ Cancelar", id="cancel_btn", variant="default"),
            ),
            classes="modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_btn":
            name = self.query_one("#project_name", Input).value
            goal = self.query_one("#project_goal", Input).value
            status = self.query_one("#project_status", Input).value
            
            if name and goal:
                try:
                    workspace_id = create_workspace(name, goal, status)
                    self.app.notify(f"✅ Workspace '{name}' criado com ID: {workspace_id}")
                    self.dismiss()
                    # Refresh the sidebar
                    self.app.refresh_sidebar()
                except Exception as e:
                    self.app.notify(f"❌ Erro ao criar workspace: {str(e)}", severity="error")
            else:
                self.app.notify("❌ Nome e objetivo são obrigatórios", severity="error")
        elif event.button.id == "cancel_btn":
            self.dismiss()


class CommitTaskModal(ModalScreen):
    """Modal para fazer commit de uma task"""
    
    def __init__(self, workspace_id: str, **kwargs):
        super().__init__(**kwargs)
        self.workspace_id = workspace_id

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"📝 Commit Task - Workspace: {self.workspace_id}", classes="title"),
            Input(placeholder="Nome da task", id="task_name"),
            Input(placeholder="Agente responsável", id="task_agent"),
            TextArea(placeholder="Notas adicionais (opcional)", id="task_notes"),
            Horizontal(
                Button("✅ Commit", id="commit_btn", variant="primary"),
                Button("❌ Cancelar", id="cancel_btn", variant="default"),
            ),
            classes="modal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "commit_btn":
            task_name = self.query_one("#task_name", Input).value
            agent = self.query_one("#task_agent", Input).value
            notes = self.query_one("#task_notes", TextArea).text
            
            if task_name and agent:
                try:
                    manager = Git_Context_Manager(workspace_id=self.workspace_id)
                    message = f"Task: {task_name}"
                    if notes:
                        message += f" - {notes}"
                    
                    commit_hash = manager.commit_changes(message=message, agent=agent)
                    self.app.notify(f"✅ Task '{task_name}' commitada! Hash: {commit_hash[:7]}")
                    self.dismiss()
                    # Refresh the main panel
                    self.app.refresh_main_panel()
                except Exception as e:
                    self.app.notify(f"❌ Erro ao fazer commit: {str(e)}", severity="error")
            else:
                self.app.notify("❌ Nome da task e agente são obrigatórios", severity="error")
        elif event.button.id == "cancel_btn":
            self.dismiss()


class Sidebar(Static):
    def compose(self) -> ComposeResult:
        yield Static("📁 Workspaces", classes="title")
        yield Container(id="workspaces_list")
        yield Button(label="[+] Novo Workspace", id="new_workspace", variant="default")

    def on_mount(self):
        self.refresh_workspaces()

    def refresh_workspaces(self):
        """Refresh the workspaces list"""
        workspaces_container = self.query_one("#workspaces_list")
        workspaces_container.remove_children()
        
        try:
            workspaces = list_workspaces()
            for ws in workspaces:
                label = f"{ws.get('name', ws['id'])}"
                workspaces_container.mount(Button(label=label, id=ws["id"], variant="primary"))
        except Exception as e:
            workspaces_container.mount(Static(f"❌ Error loading workspaces: {str(e)}", classes="error"))


class MainPanel(Static):
    workspace_id = reactive("default")
    
    def __init__(self, workspace_id: str = "default", **kwargs):
        super().__init__(**kwargs)
        self.workspace_id = workspace_id

    def on_mount(self):
        self.refresh_context()

    def watch_workspace_id(self, workspace_id: str) -> None:
        """Called when workspace_id changes"""
        # Only refresh if the widget is already mounted
        if self.is_mounted:
            self.refresh_context()

    def refresh_context(self):
        try:
            manager = Git_Context_Manager(workspace_id=self.workspace_id)
            context = manager.get_project_context()
            cp = context.get("checkpoint", {})
            history = context.get("history", [])[-5:]

            content = f"\n📦 Project: {cp.get('project_name', 'N/A')}\n"
            content += f"🎯 Goal: {cp.get('goal', 'N/A')}\n"
            content += f"📍 Status: {cp.get('current_status', 'N/A')}\n"
            content += "\n🗓️ Milestones:\n"
            for m in cp.get("milestones", []):
                content += f"  - {m['name']} (due: {m['due']})\n"
            content += "\n🕓 Last commits:\n"
            for h in reversed(history):
                commit_hash = h.get('commit', '')[:7] if h.get('commit') else 'N/A'
                content += f"  - [{commit_hash}] ({h.get('agent', 'N/A')}) {h.get('summary', 'N/A')}\n"

            # Update the context content widget
            context_widget = self.query_one("#context_content", Static)
            context_widget.update(content)

        except Exception as e:
            error_content = f"❌ Error loading workspace '{self.workspace_id}': {str(e)}"
            try:
                context_widget = self.query_one("#context_content", Static)
                context_widget.update(error_content)
            except:
                # If widget doesn't exist yet, just log the error
                pass

    def compose(self) -> ComposeResult:
        yield Static("📊 Context Panel", classes="title")
        yield Static(id="context_content")
        yield Horizontal(
            Button("📝 Commit Task", id="commit_task", variant="primary"),
            Button("🔄 Refresh", id="refresh", variant="default"),
            Button("📋 Full History", id="full_history", variant="default"),
        )


class ContextPilotApp(App):
    CSS_PATH = "styles/app.css"
    TITLE = "ContextPilot"
    SUB_TITLE = "Project Context Manager"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_workspace = "default"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Sidebar(id="sidebar"),
            MainPanel(workspace_id=self.selected_workspace, id="main"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "new_workspace":
            self.push_screen(CreateWorkspaceModal())
        elif button_id == "commit_task":
            self.push_screen(CommitTaskModal(self.selected_workspace))
        elif button_id == "refresh":
            self.refresh_main_panel()
        elif button_id == "full_history":
            self.show_full_history()
        else:
            # Assume it's a workspace button
            self.selected_workspace = button_id
            main_panel = self.query_one("#main", MainPanel)
            main_panel.workspace_id = self.selected_workspace

    def refresh_sidebar(self):
        """Refresh the sidebar workspaces list"""
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.refresh_workspaces()

    def refresh_main_panel(self):
        """Refresh the main panel content"""
        main_panel = self.query_one("#main", MainPanel)
        main_panel.refresh_context()

    def show_full_history(self):
        """Show full history in a modal"""
        try:
            manager = Git_Context_Manager(workspace_id=self.selected_workspace)
            context = manager.get_project_context()
            history = context.get("history", [])
            
            # Create a simple history display
            history_text = f"📋 Full History - {self.selected_workspace}\n\n"
            for h in reversed(history):
                commit_hash = h.get('commit', '')[:7] if h.get('commit') else 'N/A'
                timestamp = h.get('timestamp', 'N/A')[:19] if h.get('timestamp') else 'N/A'
                history_text += f"[{commit_hash}] ({h.get('agent', 'N/A')}) {h.get('summary', 'N/A')}\n"
                history_text += f"  📅 {timestamp}\n\n"
            
            # For now, just show a notification with the count
            self.notify(f"📋 {len(history)} entries in history. Check logs for full details.")
        except Exception as e:
            self.notify(f"❌ Error loading history: {str(e)}", severity="error")

if __name__ == "__main__":
    ContextPilotApp().run()
