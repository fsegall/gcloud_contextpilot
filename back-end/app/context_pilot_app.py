from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Horizontal, Container
from textual.reactive import reactive

from screens.home import HomeScreen
from screens.workspace_picker import WorkspacePickerScreen
from screens.milestones import MilestonesScreen
from screens.logs import LogsScreen
from screens.coach import CoachScreen
from screens.checkpoint_editor import CheckpointEditorScreen
import os

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")


class Menu(Static):
    class Navigate(Button.Pressed):
        def __init__(self, sender: "Menu", button_id: str) -> None:
            super().__init__(button_id)
            self.sender = sender
            self.screen_id = button_id

    def compose(self) -> ComposeResult:
        yield Button("🏠 Home", id="home", variant="primary")
        yield Button("📂 Workspaces", id="workspaces")
        yield Button("🗓️ Milestones", id="milestones")
        yield Button("📝 Checkpoint", id="checkpoint")
        yield Button("📋 Logs", id="logs")
        yield Button("🧠 Coach", id="coach")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        await self.emit(self.Navigate(self, event.button.id))


class ContextPilotApp(App):
    CSS_PATH = "styles/app.css"
    TITLE = "ContextPilot — Terminal UI"
    SUB_TITLE = "Manage long-term project scope with Git + LLMs"

    current_screen = reactive("home")

    SCREENS = {
        "home": HomeScreen,
        "workspaces": WorkspacePickerScreen,
        "milestones": MilestonesScreen,
        "checkpoint": CheckpointEditorScreen,
        "logs": LogsScreen,
        "coach": CoachScreen,
    }

    def mount_screen(self, screen_id: str):
        container = self.query_one("#main_container", Container)
        container.remove_children()
        screen_cls = self.SCREENS.get(screen_id)
        if screen_cls:
            container.mount(screen_cls())
            self.current_screen = screen_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Menu(id="sidebar")
            yield Container(id="main_container")
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen("home")  # Instala e ativa a tela home
        self.query_one(Menu).focus()

    def on_menu_navigate(self, message: Menu.Navigate) -> None:
        self.mount_screen(message.screen_id)



if __name__ == "__main__":
    print("\U0001F511 API KEY carregada?", bool(os.getenv("OPENAI_API_KEY")))
    app = ContextPilotApp()
    app.run()
