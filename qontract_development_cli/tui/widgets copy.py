from typing import ClassVar, NewType

import rich
from importlib_metadata import PackageNotFoundError, version
from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.measure import Measurement
from rich.text import Text
from textual import events, log
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.geometry import Region
from textual.message import Message
from textual.messages import ScrollToRegion
from textual.reactive import Reactive
from textual.scroll_view import ScrollView
from textual.widgets import Button, Static, TextLog


class Body(Container):
    ...


class Notification(Static):
    def on_mount(self) -> None:
        self.set_timer(3, self.remove)

    def on_click(self) -> None:
        self.remove()


class Title(Static):
    pass


class DockerLog(TextLog):
    pass


class Version(Static):
    def render(self) -> RenderableType:
        try:
            return f"Version [b]v{version('qontract-development-cli')}"
        except PackageNotFoundError:
            return "Version [b]dev"


ItemId = NewType("ItemId", int)


@rich.repr.auto
class ItemNode:
    def __init__(
        self, item_id: ItemId, label: RenderableType, control: "ItemControl"
    ) -> None:
        self.id = item_id
        self._control = control
        self.label = label

    def __rich_repr__(self) -> rich.repr.Result:
        yield "id", self.id
        yield "label", self.label

    @property
    def control(self) -> "ItemControl":
        return self._control

    @property
    def is_cursor(self) -> bool:
        return self.control.cursor == self.id

    def __rich__(self) -> RenderableType:
        return self._control.render_item(self)


class ItemList(list):
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        for item in self:
            yield item

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        return Measurement(0, len(self))


class ItemControl(Static, ScrollView, can_focus=True):
    DEFAULT_CSS = """
    ItemControl {
        color: $text;
        height: auto;
        width: 100%;
        link-style: ;
    }
    ItemControl > .item--labels {
        color: $text;
    }
    ItemControl > .item--cursor {
        link-background: $secondary;
        link-color: $text;
        background: $secondary;
        color: $text;
    }

    """
    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "item--labels",
        "item--cursor",
    }

    cursor: Reactive[ItemId | None] = Reactive(None)
    cursor_line: Reactive[int] = Reactive(0)

    def __init__(
        self,
        renderable: RenderableType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        super().__init__(
            renderable=renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
        )
        self._item_list = ItemList()
        # do not style "@click" links automatically
        self.auto_links = False

    def watch_cursor_line(self, value: int) -> None:
        line_region = Region(0, value, self.size.width, 1)
        self.emit_no_wait(ScrollToRegion(self, line_region))

    def key_enter(self, event: events.Key) -> None:
        event.stop()
        self.post_message_no_wait(
            self.ItemSelected(self, self._item_list[self.cursor_line])
        )

    def key_down(self, event: events.Key) -> None:
        event.stop()
        self.cursor_down()

    def key_up(self, event: events.Key) -> None:
        event.stop()
        self.cursor_up()

    def cursor_down(self) -> None:
        self.cursor_line += 1
        try:
            self.cursor = self._item_list[self.cursor_line].id
        except IndexError:
            self.cursor_line = 0
            self.cursor = self._item_list[self.cursor_line].id

    def cursor_up(self) -> None:
        self.cursor_line -= 1
        if self.cursor_line < 0:
            self.cursor_line = len(self._item_list) - 1
            self.cursor = self._item_list[self.cursor_line].id
        else:
            self.cursor = self._item_list[self.cursor_line].id

    def render(self) -> RenderableType:
        return self._item_list

    def render_item(self, item: ItemNode) -> RenderableType:
        meta = {
            "@click": f"click_item({item.id})",
            "item": item.id,
            "cursor": item.is_cursor,
        }
        label = (
            Text(item.label, no_wrap=True, overflow="ellipsis")
            if isinstance(item.label, str)
            else item.label.copy()  # type: ignore
        )
        label.highlight_regex(r"\..*$", "italic")
        label.stylize(self.get_component_rich_style("item--labels"))
        if item.is_cursor:
            label = Text("→ ") + label
            label.stylize(self.get_component_rich_style("item--cursor"))
        label.apply_meta(meta)
        return label

    def add_items(self, items: list[str]):
        for i, item in enumerate(items, len(self._item_list)):
            item_id = ItemId(i)
            if i == 0:
                self.cursor = item_id
            self._item_list.append(
                ItemNode(
                    item_id=item_id,
                    label=Text(item, no_wrap=True, overflow="ellipsis"),
                    control=self,
                )
            )

    def action_click_item(self, item_id: ItemId) -> None:
        self.cursor = item_id
        self.cursor_line = item_id
        # self.post_message_no_wait(self.ItemSelected(self, self._item_list[item_id]))

    @rich.repr.auto
    class ItemSelected(Message, bubble=True):
        def __init__(self, sender: "ItemControl", item: ItemNode) -> None:
            super().__init__(sender)
            self.item = item


class EnvList(ItemControl):
    @rich.repr.auto
    class ItemSelected(Message, bubble=True):
        def __init__(self, sender: "EnvList", item: ItemNode) -> None:
            super().__init__(sender)
            self.item = item


class ProfileList(ItemControl):
    @rich.repr.auto
    class ItemSelected(Message, bubble=True):
        def __init__(self, sender: "ProfileList", item: ItemNode) -> None:
            super().__init__(sender)
            self.item = item


class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Title("Textual Demo")
        yield EnvList(id="envs")
        yield ProfileList(id="profiles")
        yield Button("Start", id="btn-start")
        yield Button("Stop", classes="-hidden", id="btn-stop")
        yield Version()
