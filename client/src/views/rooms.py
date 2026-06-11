

import arcade
import arcade.gui
from arcade.gui.experimental import UIScrollArea
from arcade.gui.experimental.scroll_area import UIScrollBar
from arcade.gui import UIAnchorLayout, UIBoxLayout, UIFlatButton, UIView


import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.gui import UILabel, UIInputText, UIButtonRow, UISpace, UIOnActionEvent, UITextArea

from src.views.room import RoomView
from src.config import FONT_PATH, GAME_NAME, FONT_NAME, CLIENT_VERSION, MODE
from src.style import COMMON_BUTTON_STYLE, QUIT_BUTTON_STYLE
from src.utils.client import client
from src.widgets.message_box import UIMessageBox


class RoomsView(arcade.gui.UIView):
    def __init__(self):
        super().__init__()

        self.rooms = []
        self.need_update_rooms = False
        self.need_update_room = False
        self.ui = arcade.gui.UIManager()


        root = self.add_widget(arcade.gui.UIAnchorLayout())


        nav_side = UIButtonRow(vertical=True, size_hint=(0.3, 1))
        nav_side.add(
            UILabel(
                GAME_NAME,
                font_name=FONT_NAME,
                font_size=32,
                text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
                size_hint=(1, 0.1),
                align="center",
            )
        )
        
        nav_side.add(UISpace(size_hint=(1, 0.01), color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE))

        nav_side.with_padding(all=10)
        nav_side.with_background(color=arcade.uicolor.WHITE_CLOUDS)
        nav_side.add_button(" 房间列表 ", style=COMMON_BUTTON_STYLE, size_hint=(1, 0.1))
        nav_side.add_button(" 返回 ", style=QUIT_BUTTON_STYLE, size_hint=(1, 0.1))
        root.add(nav_side, anchor_x="left", anchor_y="top")

        @nav_side.event("on_action")
        def on_action(event: UIOnActionEvent):
            if event.action == " 房间列表 ":
                self._show_start_page()
            elif event.action == " 返回 ":
                from src.views.main_menu import MainMenuView
                self.window.show_view(MainMenuView())



        # Setup content to show widgets in

        self._body = arcade.gui.UIAnchorLayout(size_hint=(0.7, 1))
        self._body.with_padding(all=20)
        root.add(self._body, anchor_x="right", anchor_y="top")
        self.root = root
        # init start widgets
        self._show_start_page()

    def _show_start_page(self):

        self._body.clear()

        # 创建左上角锚点布局
        top_anchor = arcade.gui.widgets.layout.UIAnchorLayout()

        self.refresh_button = arcade.gui.widgets.buttons.UIFlatButton(
            text=" 刷新 ", width=200, height=60, style=COMMON_BUTTON_STYLE
        )

        @self.refresh_button.event("on_click")
        def on_click_refresh_(event):
            self.on_click_refresh(event)

        top_anchor.add(child=self.refresh_button, anchor_x="left", anchor_y="top", align_x=20, align_y=-20)
        v_scroll_area =UIBoxLayout(vertical=False, size_hint=(0.8, 0.8))
        scroll_layout = v_scroll_area.add(UIScrollArea(size_hint=(1, 1)))
        scroll_layout.with_border(color=arcade.uicolor.WHITE_CLOUDS)

        self.rooms_list = UIBoxLayout(size_hint=(1, 0), space_between=1)

        scroll_layout.add(self.rooms_list)
        v_scroll_area.add(UIScrollBar(scroll_layout))



        # 将所有布局都添加到UI管理器中
        self._body.add(top_anchor)
        self._body.add(v_scroll_area, anchor_x="center", anchor_y="center")

    def send_get_rooms(self):
        from src.game import game
        data = {}
        client.tcp_callbacks["get_rooms"] = self.get_rooms_callback
        client.tcp_send("get_rooms", data)

    def get_rooms_callback(self, data):
        self.rooms = data["rooms"]
        self.need_update_rooms = True

    def on_hide_view(self):
        self.ui.disable()

    def on_show_view(self):
        self.window.background_color = arcade.color.DARK_BLUE_GRAY
        self.ui.enable()
        self.send_get_rooms()

    def on_click_refresh(self, event):
        self.send_get_rooms()


    def on_click_join(self, event):
        print("Start:", event)
        # 进入游戏界面
        self.window.show_view(RoomsView)

    def send_join(self,room_id):
        data = {
            "room_id": room_id,
        }
        client.tcp_callbacks["join"] = self.join_callback
        client.tcp_send("join", data)

    def join_callback(self, data):
        if data['code'] == 1:
            self.need_update_room = True
        else:
            message_box = UIMessageBox(
                width=600,
                height=200,
                message_text=(
                    data.get("msg")
                ), title="提示",
                buttons=[" 好吧 "],
            )



            self.root.add(message_box)


    def update_rooms(self):
        self.rooms_list.clear()
        for room in self.rooms:
            mode = MODE[room["mode"]]
            text = f"【{mode}】{room['owner_name']}的房间 人数：{room['player_number']} { '（等待中）' if room['status'] == 0 else '（已开始）'}"
            button = UIFlatButton(height=150, size_hint=(1, None), text=text,style=COMMON_BUTTON_STYLE)

            button.on_click = lambda *args, rid=room['room_id'], **kwargs: self.send_join(rid)

            self.rooms_list.add(button)



    def on_update(self, delta_time: float) -> bool | None:
        if self.need_update_rooms:
            self.need_update_rooms = False
            self.update_rooms()

        if self.need_update_room:
            self.window.show_view(RoomView())


    def on_draw(self):
        self.clear()
        self.ui.draw()
