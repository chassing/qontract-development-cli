from typing import ClassVar, NewType

import rich
from importlib_metadata import PackageNotFoundError, version
from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.style import Style
from rich.table import Table
from rich.text import Text
from textual import events, log
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.geometry import clamp, Size
from textual.message import Message

from textual.widget import Widget
from textual.widgets import Button, Static, TextLog


class Body(Container):
    ...


class Scrollable(Container):
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


class ItemListRenderable:
    def __init__(
        self,
        items: list[str],
        selected_index: int | None,
        item_column_style: Style,
        highlight_item_column_style: Style,
        icon_column_style: Style | None = None,
        highlight_icon_column_style: Style | None = None,
    ) -> None:
        self.items = items
        self.selected_index = selected_index
        self.item_column_style = item_column_style
        self.highlight_item_column_style = highlight_item_column_style
        self.icon_column_style = icon_column_style
        self.highlight_icon_column_style = highlight_icon_column_style

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        table = Table.grid(expand=True)
        table.add_column()
        # table.add_column(justify="right", max_width=8)

        for i, item in enumerate(self.items):
            label = Text(item, no_wrap=True, overflow="ellipsis")
            label.highlight_regex(r"\..*$", "italic")
            label.stylize(self.item_column_style)
            if i == self.selected_index:
                label.stylize(self.highlight_item_column_style)
            table.add_row(label)

        yield table


class ItemControl(Widget, can_focus=True):
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

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._items: list[str] = []
        # brauch ich das noch? do not style "@click" links automatically
        # self.auto_links = False

    @property
    def selected_index(self):
        return self._selected_index

    @selected_index.setter
    def selected_index(self, new_value: int | None):
        if new_value is not None:
            self._selected_index = self._clamp_index(new_value)
            if self._selected_index is not None:
                selected_item = self._items[self._selected_index]
                self.emit_no_wait(self.ItemSelected(self, selected_item))
        # If we're scrolled such that the selected index is not on screen.
        # That is, if the selected index does not lie between scroll_y and scroll_y+content_region.height,
        # Then update the scrolling
        self.refresh(layout=True)

    def _on_mount(self, event: events.Mount) -> None:
        # This is in place to trigger the FilePreviewChanged
        self.selected_index = 0

    def _clamp_index(self, new_index: int) -> int | None:
        """Ensure the selected index stays within range"""
        if not self._items:
            return None
        return clamp(new_index, 0, len(self._items) - 1)

    def render(self) -> RenderableType:
        return ItemListRenderable(
            items=self._items,
            selected_index=self.selected_index,
            item_column_style=self.get_component_rich_style("item--labels"),
            highlight_item_column_style=self.get_component_rich_style("item--cursor"),
        )

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return max(len(self._items), container.height)

    def add_items(self, items: list[str]):
        self._items += items
        if self.selected_index is None:
            self.selected_index = 0

    # def key_enter(self, event: events.Key) -> None:
    #     event.stop()
    #     self.post_message_no_wait(
    #         self.ItemSelected(self, self._item_list[self.cursor_line])
    #     )

    def key_down(self, event: events.Key) -> None:
        event.stop()
        self.selected_index += 1
        content_size = self.parent.content_size if self.parent else self.container_size  # type: ignore
        log((self.selected_index - self.parent.scroll_offset.y) % content_size.height)
        if (
            self.selected_index - self.parent.scroll_offset.y
        ) % content_size.height == 0 and self.parent:
            self.parent.scroll_down(animate=False)
        log(self.parent.scroll_offset.y)

    def key_up(self, event: events.Key) -> None:
        event.stop()
        self.selected_index -= 1
        content_size = self.parent.content_size if self.parent else self.container_size  # type: ignore
        log(
            (self.selected_index + 1 - self.parent.scroll_offset.y)
            % content_size.height
        )
        if (
            self.selected_index + 1 - self.parent.scroll_offset.y
        ) % content_size.height == 0 and self.parent:
            self.parent.scroll_up(animate=False)

    # def cursor_down(self) -> None:
    #     self.cursor_line += 1
    #     try:
    #         self.cursor = self._item_list[self.cursor_line].id
    #     except IndexError:
    #         self.cursor_line = 0
    #         self.cursor = self._item_list[self.cursor_line].id

    # def cursor_up(self) -> None:
    #     self.cursor_line -= 1
    #     if self.cursor_line < 0:
    #         self.cursor_line = len(self._item_list) - 1
    #         self.cursor = self._item_list[self.cursor_line].id
    #     else:
    #         self.cursor = self._item_list[self.cursor_line].id

    # def render(self) -> RenderableType:
    #     return self._item_list

    # def add_items(self, items: list[str]):
    #     for i, item in enumerate(items, len(self._item_list)):
    #         item_id = ItemId(i)
    #         if i == 0:
    #             self.cursor = item_id
    #         self._item_list.append(
    #             ItemNode(
    #                 item_id=item_id,
    #                 label=Text(item, no_wrap=True, overflow="ellipsis"),
    #                 control=self,
    #             )
    #         )

    # def action_click_item(self, item_id: ItemId) -> None:
    #     self.cursor = item_id
    #     self.cursor_line = item_id
    #     # self.post_message_no_wait(self.ItemSelected(self, self._item_list[item_id]))

    @rich.repr.auto
    class ItemSelected(Message, bubble=True):
        def __init__(self, sender: "ItemControl", item: str) -> None:
            super().__init__(sender)
            self.item = item


class EnvList(ItemControl):
    @rich.repr.auto
    class ItemSelected(Message, bubble=True):
        def __init__(self, sender: "EnvList", item: str) -> None:
            super().__init__(sender)
            self.item = item


class ProfileList(ItemControl):
    @rich.repr.auto
    class ItemSelected(Message, bubble=True):
        def __init__(self, sender: "ProfileList", item: str) -> None:
            super().__init__(sender)
            self.item = item


class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Title("Textual Demo")
        yield Scrollable(EnvList(id="envs"), id="envs-wrapper")
        yield Scrollable(ProfileList(id="profiles"), id="profiles-wrapper")
        yield Button("Start", id="btn-start")
        yield Button("Stop", classes="-hidden", id="btn-stop")
        yield Horizontal(Version(), id="test")
