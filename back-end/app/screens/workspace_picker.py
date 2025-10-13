from textual.screen import Screen
from textual.widgets import Static, Input, Button, ListView, ListItem
from textual.containers import Vertical
from textual import events
from utils.workspace_manager import list_workspaces, create_workspace


class WorkspacePickerScreen(Screen):
    BINDINGS = [("q", "app.quit", "Quit")]

    def compose(self):
        yield Static("\n🚀 Select a Workspace or Create a New One:\n", classes="title")
        self.workspace_list = ListView(id="workspace-list")
        yield self.workspace_list

        yield Static("\nCreate New Workspace:", classes="subtitle")
        self.name_input = Input(placeholder="Project name...", id="workspace-name")
        yield self.name_input
        yield Button("Create Workspace", id="create-workspace")

    def on_mount(self):
        self.refresh_list()

    def refresh_list(self):
        self.workspace_list.clear()
        for ws in list_workspaces():
            self.workspace_list.append(
                ListItem(Static(f"📦 {ws['name']} ({ws['id']})"), id=ws["id"])
            )

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create-workspace":
            name = self.name_input.value.strip()
            if name:
                new_id = create_workspace(name)
                self.refresh_list()
                await self.app.push_screen("home", workspace_id=new_id)

    async def on_list_view_selected(self, event: ListView.Selected):
        selected_id = event.item.id
        await self.app.push_screen("home", workspace_id=selected_id)
