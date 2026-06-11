

import arcade
import arcade.gui
from arcade.gui.events import UIControllerButtonPressEvent
from arcade.gui.experimental import UIScrollArea
from arcade.gui.experimental.focus import UIFocusGroup
from arcade.gui.experimental.scroll_area import UIScrollBar
from arcade.gui import UIAnchorLayout, UIBoxLayout, UIFlatButton, UIView, UIMouseFilterMixin, UIDropdown

import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.gui import UILabel, UIInputText, UIButtonRow, UISpace, UIOnActionEvent, UITextArea
from arcade.types import Color

from src.config import FONT_PATH, GAME_NAME, FONT_NAME, CLIENT_VERSION, MODE
from src.style import COMMON_BUTTON_STYLE, QUIT_BUTTON_STYLE
from src.utils.client import client, split_list
from src.utils.voice import AudioHandler
from src.widgets.drawing import DrawingBox
from src.widgets.message_box import UIMessageBox
from src.widgets.toast import Toast


class RoomView(arcade.gui.UIView):
    def __init__(self):
        super().__init__()

        self.mouse_position = (0,0)
        self.need_del_room = False
        self.guessing_box = None
        self.drawing_box = None
        self.setting_box = None

        self.need_clear = False

        self.audio_handler = AudioHandler(
            sample_rate=16000,
            channels=1,
            dtype="int16",
            blocksize=256,
            udp_send_func=self.send_voice,
            on_audio_recv=None
        )


        self.new_chat = []
        self.players_ = []
        self.players = []
        self.room_info = None
        self.ui = arcade.gui.UIManager()

        self.open_voice = False
        self.open_sound = True


        self.root = self.add_widget(arcade.gui.UIAnchorLayout())

        self.pen_color = arcade.color.BLACK
        self.pen_size = 8
        self.points = []
        self.current_points = []
        self.is_eraser = False

        # Setup side navigation
        nav_side = UIButtonRow(vertical=True, size_hint=(0.3, 1))

        mode_row = UIBoxLayout(vertical=False, size_hint=(1, 0.1), space_between=10)
        nav_side.add(mode_row)


        self.mode_title = mode_row.add(
            UILabel(
                GAME_NAME,
                font_name=FONT_NAME,
                font_size=32,
                text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
                size_hint=(1, 0.1),
                align="center",
            )
        )

        self.mode_dropdown = mode_row.add(
            UIDropdown(
                default=f" {MODE[1]} ",
                options= [f" {m} " for m in MODE.values()],primary_style=COMMON_BUTTON_STYLE,dropdown_style=COMMON_BUTTON_STYLE,active_style=COMMON_BUTTON_STYLE

            )
        )
        self.mode_dropdown.disabled = True
        nav_side.add(UISpace(size_hint=(1, 0.01), color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE))

        nav_side.with_padding(all=10)
        nav_side.with_background(color=arcade.uicolor.WHITE_CLOUDS)
        # players

        v_scroll_area = UIBoxLayout(vertical=False, size_hint=(0.95, 0.8))
        scroll_layout = v_scroll_area.add(UIScrollArea(size_hint=(1, 1)))
        scroll_layout.with_border(color=arcade.uicolor.WHITE_CLOUDS)

        self.players_list = UIBoxLayout(size_hint=(1, 0), space_between=1)

        scroll_layout.add(self.players_list)
        v_scroll_area.add(UIScrollBar(scroll_layout))
        nav_side.add(v_scroll_area)

        # chat
        v_scroll_area =UIBoxLayout(vertical=False, size_hint=(0.95, 0.8))
        scroll_layout = v_scroll_area.add(UIScrollArea(size_hint=(1, 1)))
        scroll_layout.with_border(color=arcade.uicolor.WHITE_CLOUDS)

        self.chat_list = UIBoxLayout(size_hint=(1, 0), space_between=1)

        scroll_layout.add(self.chat_list)
        v_scroll_area.add(UIScrollBar(scroll_layout))
        nav_side.add(v_scroll_area)

        self.chat_input = UIInputText(
            text="",height = 48,size_hint=(0.95,None), font_name=FONT_NAME, font_size=20,
            text_color= arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,border_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
            caret_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
        )
        nav_side.add(self.chat_input)


        self.start_button = nav_side.add_button(" 开始 ", style=COMMON_BUTTON_STYLE, size_hint=(1, 0.1))
        self.start_button.disabled = True

        nav_side.add_button(" 退出 ", style=QUIT_BUTTON_STYLE, size_hint=(1, 0.1))
        self.root.add(nav_side, anchor_x="left", anchor_y="top")
        @nav_side.event("on_action")
        def on_action(event: UIOnActionEvent):
            if event.action == " 开始 ":
                self.send_start()
            if event.action == " 退出 ":
                data = {"type": "exit"}
                client.tcp_send("room", data)
                from src.views.main_menu import MainMenuView
                self.window.show_view(MainMenuView())

        # Setup content to show widgets in

        self._body = arcade.gui.UIAnchorLayout(size_hint=(0.7, 1))
        self._body.with_padding(all=20)
        self.root.add(self._body, anchor_x="right", anchor_y="top")

        # init start widgets
        self._show_start_page()

        self.toasts = self._body.add(UIBoxLayout(space_between=2), anchor_x="right", anchor_y="top")
        self.toasts.with_padding(all=10)
    def tip(self,text,duration = 3):
        # prepare and show toast
        try:
            toast = Toast(text, width=300, size_hint=(None, 0),duration=duration)
            toast.update_font(
                font_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
                font_size=12,font_name=FONT_NAME,

            )
            toast.with_background(color=arcade.color.WHITE_SMOKE)
            toast.with_padding(all=10)

            self.toasts.add(toast)
        except IndexError:
            print("这个问题还没解决！！！！！！！！！！！！！！！！")
    def send_voice(self,data):
        data = {
            "type": "voice","voice_data":data
        }
        client.udp_send("room",data)
       # client.udp_send("room", {})

    def send_start(self):
        data = {
            "type":"start"
        }
        client.tcp_send("room",data)

    def chat(self,text,name = ""):
        self.tip(f"【{name}】{text}" if name!= ""  else text)
        self.chat_list.add( UILabel(
            f"【{name}】{text}" if name!= ""  else text,
            font_name=FONT_NAME,align='left',
            font_size=12,multiline=True,
            text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
            size_hint=(1, None)
        ))

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.ESCAPE:
            if self.chat_input.focused:
                self.chat_input.focused = False
            return True
        elif symbol == arcade.key.ENTER:
            if self.chat_input.focused:
                if self.chat_input.text.replace(" ", "").replace("\n","") == "":
                    self.chat_input.focused = False
                else:
                    # 发送
                    self.chat(self.chat_input.text.replace("\n",""),"我")
                    self.send_text(self.chat_input.text.replace("\n",""))
                    self.chat_input.text = ""
                    self.chat_input.focused = False
            else:
                self.chat_input.focused = True
            return True
        elif symbol == arcade.key.T:
            self.open_voice = not self.open_voice

        elif symbol == arcade.key.S:
            self.open_sound = not self.open_sound
        return False

    def is_drawing(self):
        if self.room_info:
            my_index = self.get_my_index()
            if self.room_info['status'] == 2 and self.room_info['current_player'] == my_index and self.room_info['mode'] == 0:
                return True
            if self.room_info['status'] == 2 and self.room_info['mode'] == 1:
                return True
        return False
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if self.is_drawing():
            if (int(x), int(y)) not in self.current_points and y > 80:
                self.current_points.append((int(x), int(y)))
    def on_mouse_drag(
        self, x: int, y: int, dx: int, dy: int, _buttons: int, _modifiers: int
    ) -> bool | None:
        if self.is_drawing():
            if (int(x), int(y)) not in self.current_points and y > 80:
                self.current_points.append((int(x), int(y)))
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        self.mouse_position = (int(x), int(y))
    def clear_points(self):
        self.points = []


    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:

        if self.current_points != []:

            self.points.append((self.current_points,self.pen_color,self.pen_size))

            # 分包发送
            for l in split_list(self.current_points,30):
                data = {
                    "type":"draw",
                    "points":(l,self.pen_color,self.pen_size)
                }
                client.tcp_send("room",data)

            self.current_points = []


    def send_text(self,text):
        data = {
            "type":"chat","text":text
        }
        client.tcp_send("room",data)
    def _show_start_page(self):

        self._body.clear()


        # 顶端信息容器
        top_panel = arcade.gui.widgets.layout.UIAnchorLayout(
            vertical=True,
            space_between=5
        )

        # 第一行：时间和房间ID
        first_row = arcade.gui.widgets.layout.UIBoxLayout(
            vertical=False,
            space_between=30
        )

        self.time_label = UILabel(
            text="时间: 00:00",
            font_name=FONT_NAME,
            font_size=20,
            text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE
        )

        self.room_label = UILabel(
            text="正在载入房间",
            font_name=FONT_NAME,
            font_size=20,
            text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE
        )

        first_row.add(self.time_label)
        first_row.add(self.room_label)

        second_row = arcade.gui.widgets.layout.UIBoxLayout(
            vertical=False,
            space_between=30
        )

        self.draw_label = UILabel(
            text="",
            font_name=FONT_NAME,
            font_size=20,
            text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE
        )

        second_row.add(self.draw_label)

        third_row = arcade.gui.widgets.layout.UIBoxLayout(
            vertical=False,
            space_between=30
        )

        self.guess_label = UILabel(
            text="",
            font_name=FONT_NAME,
            font_size=20,
            text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE
        )


        third_row.add(self.guess_label)


        top_panel.add(first_row, anchor_x="center", anchor_y="top", align_x=0, align_y=-20)
        top_panel.add(second_row, anchor_x="center", anchor_y="top", align_x=0, align_y=-50)
        top_panel.add(third_row, anchor_x="center", anchor_y="bottom", align_x=0, align_y= 20)

        # 添加到主布局
        self._body.add(top_panel)


    def on_hide_view(self):
        self.ui.disable()
        self.audio_handler.stop()

    def on_show_view(self):
        self.ui.enable()
        self.window.background_color = arcade.uicolor.WHITE_CLOUDS

        #self.drawing_box = self._body.add(DrawingBox(self), anchor_y='bottom', align_y=5)
        client.udp_callbacks['room'] = self.room_udp
        client.tcp_callbacks['room'] = self.room_tcp

        self.audio_handler.start()

    def room_udp(self, data,address):
        """处理房间信息更新"""
        self.room_info = data.get('room_info', self.room_info)
        self.players = data.get('players', self.players)

        if data.get('type') == "voice":
            self.audio_handler.handle_recv_json(data['voice_data'])

    def room_tcp(self, data):

        self.room_info = data.get('room_info', self.room_info)
        self.players = data.get('players', self.players)

        if data.get('type') == "chat":
            self.new_chat.append((data['name'],data['text']))
        elif data.get('type') == "draw":
            self.points.append(data['points'])
        elif data.get('type') == "clear":
            self.need_clear = True
        elif data.get('type') == "del_room":
            self.need_del_room = True

    def update_players(self):
        self.players_list.clear()
        i = 0
        for player in self.players:
            p = UIBoxLayout(size_hint=(1, None),space_between=1,height=80,vertical=False)
            a = ""
            my_index = self.get_my_index()
            if  self.room_info['current_player'] >= my_index:
                a = f"{player['answer']}"
            p.add(UILabel(
            f"{player['name']}{'（房主）'if player['is_owner'] else ''}{'（我）'if i == my_index else '（退出）' if not player['online'] else ''}"+a,
            font_name=FONT_NAME,align='left',
            font_size=20,
                text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
            size_hint=(1, None)
            )
                  )
            self.players_list.add(p)
            i+=1
    def get_my_index(self):
        my_index = 0
        for player in self.players:
            if player['uid'] == client.uid:
                break
            my_index += 1
        return my_index
    def is_owner(self):
        for player in self.players:
            if player['is_owner'] and player['uid'] == client.uid:
                return True
        return False

    def on_update(self, delta_time: float) -> bool | None:
        # 语音
        self.audio_handler.enable_send(self.open_voice)
        self.audio_handler.enable_recv(self.open_sound)

        if self.players != self.players_:
            self.players_ = self.players
            self.update_players()
        my_index = self.get_my_index()
        if self.need_clear:
            self.clear_points()
            self.need_clear = False
        if self.need_del_room:
            self.need_del_room = False

            message_box = UIMessageBox(
                width=600,
                height=200,
                message_text=(
                    "由于房主退出或人数小于2，房间已摧毁" if self.room_info['mode'] == 0 else "中途有玩家退出，房间已摧毁（后面会优化）"
                ),title="提示",
                buttons=[" 好吧 "],
            )

            @message_box.event("on_action")
            def on_message_box_close(e: UIOnActionEvent):
                from src.views.main_menu import MainMenuView
                self.window.show_view(MainMenuView())
            self.root.add(message_box)
        if self.room_info:
            if self.mode_dropdown.value != f" {MODE[self.room_info['mode']]} ":
                if self.is_owner():
                    mode = 0
                    for i in MODE.keys():
                        if ' '+MODE[i]+' ' == self.mode_dropdown.value:
                            mode = i
                    data = {
                        "type":"set_mode","mode":mode
                    }
                    client.tcp_send("room",data)
                else:
                    self.mode_dropdown.value = f" {MODE[self.room_info['mode']]} "

            self.mode_title.text = MODE[self.room_info['mode']]
            if self.room_info['status'] == 0:
                self.room_label.text = "等待中"

                self.draw_label.text = ''
                self.guess_label.text = ''

                if self.is_owner() and len(self.players)>=2:
                    self.start_button.disabled = False
                    self.mode_dropdown.disabled = False

                else:
                    self.start_button.disabled = True
                    self.mode_dropdown.disabled = True
            else:

                self.start_button.disabled = True
                self.mode_dropdown.disabled = True


                if self.room_info['mode'] == 0:
                    # 单线接龙
                    current_player = self.players[self.room_info['current_player']]

                    if self.room_info['status'] == 1:
                        self.room_label.text = f"{current_player['name']}正在出题"

                        if self.setting_box is None and self.room_info['current_player'] == my_index:
                            self.setting_box = self._body.add(SettingBox(),anchor_y='bottom',align_y=5)

                    elif self.room_info['status'] == 2:
                        self.room_label.text = f"{current_player['name']}正在创作TA的伟大作品"

                        if self.drawing_box is None and self.room_info['current_player'] == my_index:
                            self.drawing_box = self._body.add(DrawingBox(self),anchor_y='bottom',align_y=5)

                    elif self.room_info['status'] == 3:
                        self.room_label.text = f"{current_player['name']}正在思考这玩意是什么"
                        if self.guessing_box is None and self.room_info['current_player'] == my_index:
                            self.guessing_box = self._body.add(GuessingBox(),anchor_y='bottom',align_y=5)
                    elif self.room_info['status'] == 4:
                        # 回放
                        if self.room_info['current_player'] == 0:
                            i = 0
                        else :
                            i = self.room_info['current_player'] - 1

                        self.room_label.text = f"回放中"
                        if self.guessing_box is not None :
                            self.guessing_box.close(None)
                            self.guessing_box = None

                        self.draw_label.text = f"{current_player['name']}正在画 {current_player['answer']}"
                        if self.room_info['draw_over']:
                            if (self.room_info['current_player']+2) <= len(self.players):
                                next_player = self.players[self.room_info['current_player']+1]
                                self.guess_label.text = f"{next_player['name']}猜这是 {next_player['answer']}"
                        else:
                            self.guess_label.text = ''
                    if self.setting_box is not None and self.room_info['status'] != 1:
                        self.setting_box.close(None)
                        self.setting_box = None

                    if self.drawing_box is not None and self.room_info['status'] != 2:
                        self.drawing_box.clear()
                        self.drawing_box = None

                    if self.guessing_box is not None and self.room_info['status'] != 3:
                        self.guessing_box.close(None)
                        self.guessing_box = None
                elif self.room_info['mode'] == 1:
                    # 多线接龙
                    if self.room_info['status'] == 1:
                        if self.players[self.get_my_index()]['question'] != "":
                            self.room_label.text = f"等待其它玩家出题……"

                        else:
                            self.room_label.text = "正在出题……"

                        if self.setting_box is None and self.players[self.get_my_index()]['question'] == "":
                            self.setting_box = self._body.add(SettingBox(), anchor_y='bottom', align_y=5)

                    elif self.room_info['status'] == 2:

                        if self.get_my_index() in self.room_info['over']:
                            self.room_label.text = f"等待其它玩家创作……"

                        else:
                            setter = self.get_normal_index(self.get_my_index()-self.room_info['round'])
                            last_answer = self.players[self.get_normal_index(self.get_my_index()-1)]['answers'][str(setter)]
                            self.room_label.text = f"请创作：{last_answer}"

                        if self.drawing_box is None and self.get_my_index() not in self.room_info['over']:
                            self.drawing_box = self._body.add(DrawingBox(self), anchor_y='bottom', align_y=5)

                    elif self.room_info['status'] == 3:
                        if self.get_my_index() in self.room_info['over']:
                            self.room_label.text = f"等待其它玩家思考……"

                        else:
                            self.room_label.text = "正在思考这玩意是什么……"

                        if self.guessing_box is None and self.get_my_index() not in self.room_info['over']:
                            self.guessing_box = self._body.add(GuessingBox(), anchor_y='bottom', align_y=5)

                    elif self.room_info['status'] == 4:
                        # 回放
                        self.room_label.text = f"回放中"

                        setter = self.room_info['current_player']
                        round = self.room_info['round']
                        painter = self.get_normal_index(setter + round)

                        current_player = self.players[self.room_info['current_player']]
                        if round == 0:
                            self.draw_label.text = f"{current_player['name']}出题：{current_player['question']}"
                        else:
                            last_answer = self.players[self.get_normal_index(painter-1)]['answers'][str(setter)]
                            self.draw_label.text = f"{current_player['question']}-{self.players[painter]['name']}正在画 {last_answer}"
                            if self.room_info['draw_over']:
                                next_player = self.players[self.get_normal_index(painter + 1)]
                                print(setter,next_player)
                                self.guess_label.text = f"{next_player['name']}猜这是 {next_player['answers'][str(setter)]}"
                            else:
                                self.guess_label.text = ''
                    if self.setting_box and self.players[self.get_my_index()]['question'] != "":
                        self.setting_box.close(None)
                        self.setting_box = None
                    if self.drawing_box:
                        if self.room_info['status'] != 2 or self.get_my_index() in self.room_info['over']:
                            self.drawing_box.clear()
                            self.drawing_box = None
                    if self.guessing_box:
                        if self.room_info['status'] != 3 or self.get_my_index() in self.room_info['over']:
                            self.guessing_box.close(None)
                            self.guessing_box = None

            """格式化显示时间"""

            elapsed = self.room_info['ticks']
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.time_label.text =  f"麦克风（T）{'开' if self.open_voice else '关'}  听筒（S）{'开' if self.open_sound else '关'}  {minutes:02d}:{seconds:02d}"


        for c in self.new_chat:
            self.chat(c[1],c[0])
            self.new_chat.remove(c)
    def get_normal_index(self,i):
        if i >= 0 and i < len(self.players) :
            return i
        elif i >= len(self.players) :
            return i - len(self.players)
        else:
            return len(self.players) + i
    def on_draw(self):
        self.clear()

        for ps in self.points:
            arcade.draw_points(ps[0], ps[1], ps[2])

        arcade.draw_points(self.current_points, self.pen_color, self.pen_size)
        if self.is_drawing():
            arcade.draw_point(self.mouse_position[0],self.mouse_position[1], self.pen_color, self.pen_size)

        self.ui.draw()

class Box(UIMouseFilterMixin, UIFocusGroup):
    def __init__(self):
        super().__init__(size_hint=(0.7, 0.2))
        self.with_background(color=arcade.uicolor.GRAY_ASBESTOS)
        self.root = self.add(UIBoxLayout(space_between=10,size_hint=(0.8, 1)))
       # self.detect_focusable_widgets()
      #  self.set_focus()

    def on_event(self, event):
        if super().on_event(event):
            return True

        if isinstance(event, UIControllerButtonPressEvent):
            if event.button == "b":
                pass
                return False

        return False

    def close(self, event):
        print("Close")
        # self.trigger_full_render()
        self.trigger_full_render()
        self.parent.remove(self)


class SettingBox(Box):
    def __init__(self):
        super().__init__()
        self.root.add(UILabel(
            "请出题",
            font_name=FONT_NAME,
            font_size=32,
            text_color=Color(44, 62, 80, 155),
            align="center",
        )
        )
        self.input = self.root.add(UIInputText(
            text="", height=48, size_hint=(1, None), font_name=FONT_NAME, font_size=20,
            text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE, border_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
            caret_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
        ))

        self.root.add(UIFlatButton(text=" 确定 ",style=COMMON_BUTTON_STYLE)).on_click = self.ok

    def ok(self,event):
        if self.input.text != "":
            data = {"type":"setting","answer":self.input.text}
            client.tcp_send("room",data)

class GuessingBox(Box):
    def __init__(self):
        super().__init__()
        self.root.add(UILabel(
            "请猜",
            font_name=FONT_NAME,
            font_size=32,
            text_color=Color(44, 62, 80, 155),
            align="center",
        )
        )
        self.input = self.root.add(UIInputText(
            text="", height=48, size_hint=(1, None), font_name=FONT_NAME, font_size=20,
            text_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE, border_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
            caret_color=arcade.uicolor.DARK_BLUE_MIDNIGHT_BLUE,
        ))

        self.root.add(UIFlatButton(text=" 确定 ",style=COMMON_BUTTON_STYLE)).on_click = self.ok

    def ok(self,event):
        if self.input.text != "":
            data = {"type":"guess","answer":self.input.text}
            client.tcp_send("room",data)