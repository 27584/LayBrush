"""Constructs, are prepared widget combinations, you can use for common use-cases"""

from typing import Any

import arcade
from arcade import uicolor
from arcade.gui.events import UIOnActionEvent, UIOnClickEvent
from arcade.gui.mixins import UIMouseFilterMixin
from arcade.gui.nine_patch import NinePatchTexture
from arcade.gui.widgets.buttons import UIFlatButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from arcade.gui.widgets.text import UILabel, UITextArea

from src.config import FONT_NAME
from src.style import COMMON_BUTTON_STYLE


class UIMessageBox(UIMouseFilterMixin, UIAnchorLayout):
    """A simple dialog box that pops up a message with buttons to close.
    Subclass this class or overwrite the 'on_action' event handler with

    .. code-block:: python

        box = UIMessageBox(...)
        @box.event("on_action")
        def on_action(event: UIOnActionEvent):
            pass

    Args:
      width: Width of the message box
      height: Height of the message box
      message_text: Text to show as message to the user
      title: Title of the message box, displayed on the top
      buttons: List of strings, which are shown as buttons

    """

    def __init__(
        self,
        *,
        width: float,
        height: float,
        message_text: str,
        title: str | None = None,
        buttons=("Ok",),
    ):
        if not buttons:
            raise ValueError("At least a single value has to be available for `buttons`")

        super().__init__(size_hint=(1, 1))
        self.register_event_type("on_action")
        self.with_background(color=uicolor.GRAY_CONCRETE.replace(a=150))

        space = 20

        # setup frame which will act like the window
        frame = self.add(UIAnchorLayout(width=width, height=height, size_hint=None))

        frame.with_background(
            texture=NinePatchTexture(
                left=7,
                right=7,
                bottom=7,
                top=7,
                texture=arcade.load_texture(":resources:gui_basic_assets/window/panel_gray.png"),
            )
        )

        # setup title
        if title:
            title_label = frame.add(
                child=UILabel(
                    text=title,font_name=FONT_NAME,
                    font_size=16,
                    size_hint=(1, 0),
                    align="center",
                ),
                anchor_y="top",
            )
            title_label.with_padding(all=2, bottom=5)
            title_label.with_background(color=uicolor.DARK_BLUE_MIDNIGHT_BLUE)
            title_offset = title_label.height
        else:
            title_offset = 0

        # Setup text
        text_area = frame.add(
            child=UITextArea(
                text=message_text,font_name=FONT_NAME,
                width=width - space,
                height=height - space,
                text_color=arcade.color.BLACK,
            ),
            anchor_x="center",
            anchor_y="top",
            align_y=-(title_offset + space),
        )
        text_area.with_padding(all=10)

        # setup buttons
        button_group = UIBoxLayout(vertical=False, space_between=10)
        for button_text in buttons:
            button = UIFlatButton(text=button_text,style=COMMON_BUTTON_STYLE)
            button_group.add(button)
            button.on_click = self._on_choice  # type: ignore

        frame.add(
            child=button_group, anchor_x="right", anchor_y="bottom", align_x=-space, align_y=space
        )

    def _on_choice(self, event):
        if self.parent:
            self.parent.remove(self)
        self.dispatch_event("on_action", UIOnActionEvent(self, event.source.text))

    def on_action(self, event: UIOnActionEvent):
        """Called when button was pressed"""
        pass


