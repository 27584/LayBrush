"""Show all arcade.uicolors in a grid.

Click on a color to select
it and copy the Arcade reference to the clipboard.

If Arcade and Python are properly installed, you can run this example with:
python -m arcade.examples.gui.5_uicolor_picker

"""

from dataclasses import dataclass

import arcade
from arcade.gui import (
    UIAnchorLayout,
    UIBoxLayout,
    UIEvent,
    UIGridLayout,
    UIInteractiveWidget,
    UILabel,
    UITextWidget,
    UIView, UIFlatButton,
)
from arcade.types import Color

from src.style import COMMON_BUTTON_STYLE
from src.utils.client import client


@dataclass
class ChooseColorEvent(UIEvent):
    """Custom event, which is dispatched when a color button is clicked."""

    color_name: str
    color: arcade.color.Color



class ColorButton(UITextWidget, UIInteractiveWidget):
    """Button which shows a color and color name and
    emits a ChooseColorEvent event when clicked."""

    def __init__(
        self,
        color_name: str,
        color: arcade.color.Color,
        **kwargs,
    ):
        super().__init__(text="", **kwargs)
        # set color and place text on the bottom
        self.with_background(color=color)
        self.place_text(anchor_y="bottom")

        # set font color based on background color
       # f = 2 if color_name.startswith("DARK") else 0.5
      #  self.ui_label.update_font(
      #      font_color=arcade.color.Color(int(color[0] * f), int(color[1] * f), int(color[2] * f))
       # )

        # store color name and color for later reference
        self._color_name = color_name
        self._color = color

        # register custom event
        self.register_event_type("on_choose_color")

    def on_update(self, dt):
        """Update the button state.

        UIInteractiveWidget provides properties like hovered and pressed,
        which can be used to highlight the button."""
        if self.pressed:
            self.with_border(color=arcade.uicolor.WHITE_CLOUDS, width=3)
        elif self.hovered:
            self.with_border(color=arcade.uicolor.WHITE_CLOUDS, width=2)
        else:
            self.with_border(color=arcade.color.BLACK, width=1)

    def on_click(self, event) -> bool:
        """Emit a ChooseColorEvent event when clicked."""
        self.dispatch_event(
            "on_choose_color", ChooseColorEvent(self, self._color_name, self._color)
        )
        return True

    def on_choose_color(self, event: ChooseColorEvent):
        """ChooseColorEvent event handler, which can be overridden."""
        pass


class ColorBox(UIBoxLayout):
    """Uses the arcade.gui.UIView which takes care about the UIManager setup."""

    def __init__(self,room_view: arcade.gui.UIView):
        super().__init__(size_hint=(0.5, 1))
        # Create an anchor layout, which can be used to position widgets on screen
        self.root = self.add(UIAnchorLayout())
        self.room_view = room_view

        # Define colors in grid order
        self.colors = {
            # row 0
            "GREEN_TURQUOISE": arcade.uicolor.GREEN_TURQUOISE,
            "GREEN_EMERALD": arcade.uicolor.GREEN_EMERALD,
            "BLUE_PETER_RIVER": arcade.uicolor.BLUE_PETER_RIVER,
            "PURPLE_AMETHYST": arcade.uicolor.PURPLE_AMETHYST,
            "DARK_BLUE_WET_ASPHALT": arcade.uicolor.DARK_BLUE_WET_ASPHALT,
            # row 1
            "GREEN_GREEN_SEA": arcade.uicolor.GREEN_GREEN_SEA,
            "GREEN_NEPHRITIS": arcade.uicolor.GREEN_NEPHRITIS,
            "BLUE_BELIZE_HOLE": arcade.uicolor.BLUE_BELIZE_HOLE,
            "PURPLE_WISTERIA": arcade.uicolor.PURPLE_WISTERIA,
            "DARK_BLUE_MIDNIGHT_BLUE": arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
            # row 2
            "YELLOW_SUN_FLOWER": arcade.uicolor.YELLOW_SUN_FLOWER,
            "ORANGE_CARROT": arcade.uicolor.ORANGE_CARROT,
            "RED_ALIZARIN": arcade.uicolor.RED_ALIZARIN,
            "WHITE_CLOUDS": arcade.uicolor.WHITE_CLOUDS,
            "GRAY_CONCRETE": arcade.uicolor.GRAY_CONCRETE,
            # row 3
            "YELLOW_ORANGE": arcade.uicolor.YELLOW_ORANGE,
            "ORANGE_PUMPKIN": arcade.uicolor.ORANGE_PUMPKIN,
            "RED_POMEGRANATE": arcade.uicolor.RED_POMEGRANATE,
            "WHITE_SILVER": arcade.uicolor.WHITE_SILVER,
            "GRAY_ASBESTOS": arcade.uicolor.GRAY_ASBESTOS,
        }
        self.colors = {
            # 第0行（ROW0）：基础原色（10列）
            "ROW0_COL0": Color(0, 0, 0, 255),  # 黑色
            "ROW0_COL1": Color(255, 255, 255, 255),  # 白色
            "ROW0_COL2": Color(255, 0, 0, 255),  # 纯红
            "ROW0_COL3": Color(0, 255, 0, 255),  # 纯绿
            "ROW0_COL4": Color(0, 0, 255, 255),  # 纯蓝
            "ROW0_COL5": Color(255, 255, 0, 255),  # 纯黄
            "ROW0_COL6": Color(0, 255, 255, 255),  # 纯青
            "ROW0_COL7": Color(255, 0, 255, 255),  # 纯品红
            "ROW0_COL8": Color(128, 128, 128, 255),  # 纯灰
            "ROW0_COL9": Color(255, 165, 0, 255),  # 纯橙

            # 第1行（ROW1）：红系渐变（10列：从深到浅）
            "ROW1_COL0": Color(80, 0, 0, 255),  # 最深红
            "ROW1_COL1": Color(120, 0, 0, 255),  # 深暗红
            "ROW1_COL2": Color(160, 0, 0, 255),  # 暗红
            "ROW1_COL3": Color(200, 0, 0, 255),  # 中红
            "ROW1_COL4": Color(230, 0, 0, 255),  # 浅红
            "ROW1_COL5": Color(255, 50, 50, 255),  # 淡红
            "ROW1_COL6": Color(255, 100, 100, 255),  # 粉红
            "ROW1_COL7": Color(255, 150, 150, 255),  # 嫩红
            "ROW1_COL8": Color(255, 200, 200, 255),  # 极浅红
            "ROW1_COL9": Color(255, 230, 230, 255),  # 近乎白红

            # 第2行（ROW2）：绿系渐变（10列：从深到浅）
            "ROW2_COL0": Color(0, 80, 0, 255),  # 最深绿
            "ROW2_COL1": Color(0, 120, 0, 255),  # 深暗绿
            "ROW2_COL2": Color(0, 160, 0, 255),  # 暗绿
            "ROW2_COL3": Color(0, 200, 0, 255),  # 中绿
            "ROW2_COL4": Color(0, 230, 0, 255),  # 浅绿
            "ROW2_COL5": Color(50, 255, 50, 255),  # 淡绿
            "ROW2_COL6": Color(100, 255, 100, 255),  # 薄荷绿
            "ROW2_COL7": Color(150, 255, 150, 255),  # 嫩绿
            "ROW2_COL8": Color(200, 255, 200, 255),  # 极浅绿
            "ROW2_COL9": Color(230, 255, 230, 255),  # 近乎白绿

            # 第3行（ROW3）：蓝系渐变（10列：从深到浅）
            "ROW3_COL0": Color(0, 0, 80, 255),  # 最深蓝
            "ROW3_COL1": Color(0, 0, 120, 255),  # 深暗蓝
            "ROW3_COL2": Color(0, 0, 160, 255),  # 暗蓝
            "ROW3_COL3": Color(0, 0, 200, 255),  # 中蓝
            "ROW3_COL4": Color(0, 0, 230, 255),  # 浅蓝
            "ROW3_COL5": Color(50, 50, 255),  # 淡蓝
            "ROW3_COL6": Color(100, 100, 255),  # 天蓝
            "ROW3_COL7": Color(150, 150, 255),  # 嫩蓝
            "ROW3_COL8": Color(200, 200, 255),  # 极浅蓝
            "ROW3_COL9": Color(230, 230, 255),  # 近乎白蓝

            # 第4行（ROW4）：黄橙系渐变（10列：从深到浅）
            "ROW4_COL0": Color(120, 80, 0, 255),  # 最深橙
            "ROW4_COL1": Color(160, 110, 0, 255),  # 深暗橙
            "ROW4_COL2": Color(200, 140, 0, 255),  # 暗橙
            "ROW4_COL3": Color(230, 170, 0, 255),  # 中橙
            "ROW4_COL4": Color(255, 200, 0, 255),  # 浅橙
            "ROW4_COL5": Color(255, 220, 50, 255),  # 深黄
            "ROW4_COL6": Color(255, 240, 100, 255),  # 中黄
            "ROW4_COL7": Color(255, 250, 150, 255),  # 浅黄
            "ROW4_COL8": Color(255, 255, 200, 255),  # 淡黄
            "ROW4_COL9": Color(255, 255, 230, 255),  # 近乎白黄

            # 第5行（ROW5）：紫系渐变（10列：从深到浅）
            "ROW5_COL0": Color(80, 0, 80, 255),  # 最深紫
            "ROW5_COL1": Color(120, 0, 120, 255),  # 深暗紫
            "ROW5_COL2": Color(160, 0, 160, 255),  # 暗紫
            "ROW5_COL3": Color(200, 0, 200, 255),  # 中紫
            "ROW5_COL4": Color(230, 0, 230, 255),  # 浅紫
            "ROW5_COL5": Color(255, 50, 255),  # 淡紫
            "ROW5_COL6": Color(255, 100, 255),  # 粉紫
            "ROW5_COL7": Color(255, 150, 255),  # 嫩紫
            "ROW5_COL8": Color(255, 200, 255),  # 极浅紫
            "ROW5_COL9": Color(255, 230, 255),  # 近乎白紫

            # 第6行（ROW6）：灰阶渐变（10列：从黑到白）
            "ROW6_COL0": Color(0, 0, 0, 255),  # 纯黑
            "ROW6_COL1": Color(30, 30, 30, 255),  # 极深灰
            "ROW6_COL2": Color(60, 60, 60, 255),  # 深灰
            "ROW6_COL3": Color(90, 90, 90, 255),  # 中深灰
            "ROW6_COL4": Color(128, 128, 128, 255),  # 纯灰
            "ROW6_COL5": Color(160, 160, 160, 255),  # 中浅灰
            "ROW6_COL6": Color(190, 190, 190, 255),  # 浅灰
            "ROW6_COL7": Color(220, 220, 220, 255),  # 极浅灰
            "ROW6_COL8": Color(240, 240, 240, 255),  # 近乎白灰
            "ROW6_COL9": Color(255, 255, 255, 255),  # 纯白

            # 第7行（ROW7）：棕/青/粉混合系（10列：实用色）
            "ROW7_COL0": Color(100, 50, 0, 255),  # 深棕
            "ROW7_COL1": Color(150, 80, 30, 255),  # 中棕
            "ROW7_COL2": Color(200, 120, 60, 255),  # 浅棕
            "ROW7_COL3": Color(0, 120, 120, 255),  # 深青
            "ROW7_COL4": Color(0, 180, 180, 255),  # 中青
            "ROW7_COL5": Color(100, 255, 255),  # 浅青
            "ROW7_COL6": Color(255, 80, 130, 255),  # 深粉
            "ROW7_COL7": Color(255, 130, 180, 255),  # 中粉
            "ROW7_COL8": Color(255, 180, 230, 255),  # 浅粉
            "ROW7_COL9": Color(255, 220, 240, 255),  # 嫩粉
        }

        # setup grid with colors
        self.grid = self.root.add(
            UIGridLayout(
                column_count=10,
                row_count=8,
                size_hint=(1, 1),
            )
        )
        for i, (name, color) in enumerate(self.colors.items()):
            button = ColorButton(
                color_name=name,
                color=color,
                size_hint=(1, 1),
            )
            self.grid.add(button, row=i // 10, column=i % 10)

            # connect event handler
            button.on_choose_color = self.on_color_button_choose_color



    def on_color_button_choose_color(self, event: ChooseColorEvent) -> bool:
        """Color button click event handler, which copies the color name to the clipboard.

        And shows a temporary message."""
        self.room_view.pen_color = event.color

        return True

    def on_draw_before_ui(self):
        # Add draw commands that should be below the UI
        pass

    def on_draw_after_ui(self):
        # Add draw commands that should be on top of the UI (uncommon)
        pass


class DrawingBox(UIBoxLayout):
    def __init__(self,room_view: arcade.gui.UIView):
        super().__init__(size_hint=(0.9, 0.15),vertical=False)
       # self.root = self.add(UIAnchorLayout())
       #     self.color_box = self.root.add(ColorBox())
        self.room_view = room_view
        self.color_box = self.add(ColorBox(room_view))

        self.size_box = UIBoxLayout(vertical=True)
        self.add(self.size_box)
        self.size_box.add(UIFlatButton(text=" 2px ",style=COMMON_BUTTON_STYLE)).on_click = self.set_size_2
        self.size_box.add(UIFlatButton(text=" 4px ",style=COMMON_BUTTON_STYLE)).on_click = self.set_size_4
        self.size_box.add(UIFlatButton(text=" 8px ",style=COMMON_BUTTON_STYLE)).on_click = self.set_size_8
        self.size_box.add(UIFlatButton(text=" 16px ",style=COMMON_BUTTON_STYLE)).on_click = self.set_size_16
        self.size_box.add(UIFlatButton(text=" 32px ",style=COMMON_BUTTON_STYLE)).on_click = self.set_size_32

        self.add(UIFlatButton(text=" 橡皮 ",style=COMMON_BUTTON_STYLE)).on_click = self.set_eraser
        self.add(UIFlatButton(text=" 清屏 ",style=COMMON_BUTTON_STYLE,width=180)).on_click = self.clear_
        self.add(UIFlatButton(text=" 创作完毕 ",style=COMMON_BUTTON_STYLE,width=180)).on_click = self.ok
    def set_eraser(self,event):
        self.room_view.pen_color =    arcade.uicolor.WHITE_CLOUDS
    def set_size_2(self,event):
        self.room_view.pen_size = 2
    def set_size_4(self,event):
        self.room_view.pen_size = 4
    def set_size_8(self,event):
        self.room_view.pen_size = 8
    def set_size_16(self,event):
        self.room_view.pen_size = 16
    def set_size_32(self,event):
        self.room_view.pen_size = 32
    def ok(self,event):
        data = {"type":"end_draw"}
        client.tcp_send("room",data)
    def clear_(self,event):
        data = {"type":"clear"}
        client.tcp_send("room",data)
        self.room_view.need_clear = True