from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Vertical, Horizontal
from git_context_manager import Git_Context_Manager
import datetime

class MilestonesScreen(Screen):
    BINDINGS = [("q", "app.pop_screen", "Back")]

    def __init__(self, workspace_id: str = "default"):
        super().__init__()
        self.workspace_id = workspace_id
        self.manager = Git_Context_Manager(workspace_id)
        self.inputs = []

    def compose(self):
        yield Header()
        yield Static("📆 Edit Milestones", id="title")

        cp = self.manager.get_project_context().get("checkpoint", {})
        milestones = cp.get("milestones", [])

        for m in milestones:
            name_input = Input(value=m.get("name", ""), placeholder="Milestone Name")
            date_input = Input(value=m.get("due", ""), placeholder="YYYY-MM-DD")
            self.inputs.append((name_input, date_input))
            yield Horizontal(name_input, date_input)

        # Inputs vazios para novos marcos
        for _ in range(2):
            name_input = Input(placeholder="New Milestone Name")
            date_input = Input(placeholder="YYYY-MM-DD")
            self.inputs.append((name_input, date_input))
            yield Horizontal(name_input, date_input)

        yield Horizontal(
            Button("💾 Save", id="save"),
            Button("↩️ Back", id="back"),
            id="actions"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            new_milestones = []
            for name_input, date_input in self.inputs:
                name = name_input.value.strip()
                due = date_input.value.strip()
                if name and due:
                    try:
                        datetime.datetime.strptime(due, "%Y-%m-%d")  # valida formato
                        new_milestones.append({"name": name, "due": due})
                    except ValueError:
                        continue  # ignora datas inválidas

            cp = self.manager.get_project_context()
            cp["checkpoint"]["milestones"] = new_milestones
            self.manager.write_context(cp)
            self.manager.commit_changes(message="Updated milestones", agent="ui")
            await self.app.pop_screen()

        elif event.button.id == "back":
            await self.app.pop_screen()
