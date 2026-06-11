

import arcade
import arcade.gui

import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.gui import UILabel, UIInputText, UIButtonRow, UISpace, UIOnActionEvent, UITextArea

from src.views.room import RoomView
from src.views.rooms import RoomsView
from src.config import FONT_PATH, GAME_NAME, FONT_NAME, CLIENT_VERSION  
from src.style import COMMON_BUTTON_STYLE, QUIT_BUTTON_STYLE
from src.utils.client import client
from src.widgets.message_box import UIMessageBox


class MainMenuView(arcade.gui.UIView):
    def __init__(self):
        super().__init__()

        self.ui = arcade.gui.UIManager()
        self.need_update_room = False
        self.player_name = "Player"
        self.coin = 0
        self.uid_text = "未连接至服务器"
        self.need_update_user_info = False


        root = self.add_widget(arcade.gui.UIAnchorLayout())

        # Setup side navigation
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
        nav_side.add_button(" 开始 ", style=COMMON_BUTTON_STYLE, size_hint=(1, 0.1))
        nav_side.add_button(" 设置 ", style=COMMON_BUTTON_STYLE, size_hint=(1, 0.1))
        nav_side.add_button(" 结束 ", style=QUIT_BUTTON_STYLE, size_hint=(1, 0.1))
        root.add(nav_side, anchor_x="left", anchor_y="top")

        @nav_side.event("on_action")
        def on_action(event: UIOnActionEvent):
            if event.action == " 开始 ":
                self._show_start_page()
            elif event.action == " 结束 ":
                arcade.exit()


        # Setup content to show widgets in

        self._body = arcade.gui.UIAnchorLayout(size_hint=(0.7, 1))
        self._body.with_padding(all=20)
        root.add(self._body, anchor_x="right", anchor_y="top")
        self.root = root
        # init start widgets
        self._show_start_page()

    def _show_start_page(self):

        self._body.clear()


        # 创建左上角的水平布局，用于放置玩家名称文本、输入框和修改按钮
        self.top_h_box = arcade.gui.widgets.layout.UIBoxLayout(vertical=False, space_between=10)

        # 添加玩家名称文本标签
        self.player_label = UILabel("名称:", font_name=FONT_NAME, font_size=16)
        self.top_h_box.add(self.player_label)

        # 添加玩家名称输入框
        if not hasattr(self,"player_input"):
            self.player_input = UIInputText(text="Player", width=150, font_name=FONT_NAME, font_size=16)
        self.top_h_box.add(self.player_input)

        # 添加修改按钮
        self.edit_button = arcade.gui.widgets.buttons.UIFlatButton(
            text=" 修改 ", width=80, style=COMMON_BUTTON_STYLE
        )
        self.top_h_box.add(self.edit_button)

        # 正确绑定修改按钮的点击事件
        @self.edit_button.event("on_click")
        def on_click_edit(event):
            self.on_click_edit(event)

        # 创建左上角锚点布局
        top_anchor = arcade.gui.widgets.layout.UIAnchorLayout()
        top_anchor.add(child=self.top_h_box, anchor_x="left", anchor_y="top", align_x=20, align_y=-20)

        # 创建左下角锚点布局，用于显示版本信息
        left_bottom_anchor = arcade.gui.widgets.layout.UIAnchorLayout()
        self.version_label = UILabel(f"版本: {CLIENT_VERSION}", font_name=FONT_NAME, font_size=20)
        left_bottom_anchor.add(child=self.version_label, anchor_x="left", anchor_y="bottom", align_x=20, align_y=20)

        # 创建右下角锚点布局，用于显示UID
        right_bottom_anchor = arcade.gui.widgets.layout.UIAnchorLayout()
        if not hasattr(self,"uid_label"):
            self.uid_label = UILabel("未连接至服务器！", font_name=FONT_NAME, font_size=16)
        right_bottom_anchor.add(child=self.uid_label, anchor_x="right", anchor_y="bottom", align_x=-20, align_y=20)

        # 创建中央垂直布局
        self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

        # 创建中央锚点布局，用于放置中央垂直布局
        center_anchor = arcade.gui.widgets.layout.UIAnchorLayout()
        center_anchor.add(child=self.v_box, anchor_x="center", anchor_y="center", align_x=0, align_y=0)

        # 添加匹配按钮
        self.start_button = arcade.gui.widgets.buttons.UIFlatButton(
            text=" 开房 ", width=200, height=60, style=COMMON_BUTTON_STYLE
        )
        # 添加匹配按钮
        self.join_button = arcade.gui.widgets.buttons.UIFlatButton(
            text=" 加入 ", width=200, height=60, style=COMMON_BUTTON_STYLE
        )
        self.v_box.add(self.start_button)
        self.v_box.add(self.join_button)
        
        # 绑定匹配按钮事件
        @self.start_button.event("on_click")
        def on_click_start(event):
            self.on_click_start(event)

        @self.join_button.event("on_click")
        def on_click_join(event):
            self.on_click_join(event)

        # 将所有布局都添加到UI管理器中
        self._body.add(top_anchor)
        self._body.add(center_anchor)
        self._body.add(left_bottom_anchor)
        self._body.add(right_bottom_anchor)




    def send_get_user_info(self):
        from src.game import game
        data = {"phcathub_uid": client.phcathub_uid}
        client.tcp_callbacks["get_user_info"] = self.update_user_info
        client.tcp_send("get_user_info", data)

    def update_user_info(self,data):
        self.need_update_user_info = True
        client.uid = data.get('uid')


        self.player_name = data['name']
        self.uid_text =  f"UID: {data['uid']}({data['phcathub_uid']})"
        self.coin = data['coin']

    def on_hide_view(self):
        self.ui.disable()

    def on_show_view(self):
        self.window.background_color = arcade.color.DARK_BLUE_GRAY
        self.ui.enable()
        self.send_get_user_info()


    def on_click_start(self, event):
        print("Start:", event)
        # 进入游戏界面

        data = {
        }
        def callback(data):
            if data['code'] == 1:
                self.need_update_room = True
            else:
                print("匹配失败")

        client.tcp_callbacks['start'] = callback
        client.tcp_send("start",data)

    def on_click_join(self, event):
        self.window.show_view(RoomsView())


    def on_click_edit(self, event):
        from src.game import game
        # 获取输入框中的玩家名称
        player_name = self.player_input.text.strip()
         # 检查名称是否为空
        if player_name:

            data = {
               "name": player_name,
            }
            client.tcp_send("edit_user_name",data)

            data = {"phcathub_uid": client.phcathub_uid}
            client.tcp_callbacks["get_user_info"] = self.update_user_info
            client.tcp_send("get_user_info", data)

        else:
            message_box = UIMessageBox(
                width=600,
                height=200,
                message_text=(
                    "玩家名称不能为空"
                ), title="提示",
                buttons=[" 好吧 "],
            )
            # 可以设置默认名称
            self.player_input.text = "player"
            self.root.add(message_box)


    def on_update(self, delta_time: float) -> bool | None:
        if self.need_update_user_info:
            self.need_update_user_info = False
            self.player_input.text = self.player_name
            self.uid_label.text =  self.uid_text

        if self.need_update_room:
            self.window.show_view(RoomView())




    def on_draw(self):
        self.clear()
        self.ui.draw()
