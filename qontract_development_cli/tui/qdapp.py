from textual.app import App, ComposeResult, log
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header

from ..models import DEFAULT_PROFILE, Env, Profile
from .widgets import Body, DockerLog, EnvList, Notification, ProfileList, Sidebar


class QdApp(App):
    CSS_PATH = "qdapp.css"
    TITLE = "Qontract Development CLI"
    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
        ("ctrl+t", "app.toggle_dark", "Toggle Dark mode"),
        ("ctrl+s", "app.screenshot()", "Screenshot"),
        Binding("ctrl+c,ctrl+q", "app.quit", "Quit", show=True),
    ]

    show_sidebar = reactive(False)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def action_screenshot(self, filename: str | None = None, path: str = "./") -> None:
        """Save an SVG "screenshot". This action will save an SVG file containing the current contents of the screen.
        Args:
            filename (str | None, optional): Filename of screenshot, or None to auto-generate. Defaults to None.
            path (str, optional): Path to directory. Defaults to "./".
        """
        self.bell()
        path = self.save_screenshot(path=path)
        # message = Text.assemble("Screenshot saved to ", (f"'{path}'", "bold green"))
        # self.add_note(message)
        self.screen.mount(Notification("message"))

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        yield Body(
            Horizontal(
                Sidebar(),
                DockerLog(wrap=False, highlight=True, markup=True),
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        docker_log = self.query_one(DockerLog)
        docker_log.write("text " * 100)
        docker_log.write("text")
        docker_log.write("text")
        envs_list = self.query_one("#envs", EnvList)
        envs_list.add_items(sorted([e.name for e in Env.list_all()]))
        self.set_focus(envs_list)
        profiles_list = self.query_one("#profiles", ProfileList)
        profiles_list.add_items(
            [e.name for e in Profile.list_all() if e.name != DEFAULT_PROFILE.name] * 10
        )
        profiles_list.add_items(
            [e.name + "2" for e in Profile.list_all() if e.name != DEFAULT_PROFILE.name]
        )
        profiles_list.add_items(
            [e.name + "3" for e in Profile.list_all() if e.name != DEFAULT_PROFILE.name]
        )

    # def on_item_control_item_selected(self, event: EnvList.ItemSelected):
    #     log("here")

    # def on_env_list_item_selected(self, event: EnvList.ItemSelected):
    #     self.set_focus(self.query_one("#profiles", ProfileList))

    # def on_profile_list_item_selected(self, event: ProfileList.ItemSelected):
    #     self.set_focus(self.query_one("#btn-start", Button))

    # def on_button_pressed(self, event: Button.Pressed) -> None:
    #     """Called when a button is pressed."""

    #     button_id = event.button.id
    #     assert button_id is not None

    #     envs_list = self.query_one("#envs", EnvList)
    #     envs_list.can_focus = not envs_list.can_focus
    #     envs_list.toggle_class("-disabled")
    #     profiles_list = self.query_one("#profiles", ProfileList)
    #     profiles_list.can_focus = not profiles_list.can_focus
    #     profiles_list.toggle_class("-disabled")

    #     btn_start = self.query_one("#btn-start", Button)
    #     btn_start.toggle_class("-hidden")
    #     btn_stop = self.query_one("#btn-stop", Button)
    #     btn_stop.toggle_class("-hidden")
    #     if button_id == "btn-start":
    #         self.set_focus(btn_stop)
    #     else:
    #         self.set_focus(btn_start)
