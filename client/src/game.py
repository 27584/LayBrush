import random
import time

import arcade
import arcade.gui

import arcade.gui.widgets.buttons
import arcade.gui.widgets.layout
from arcade.gui import UIOnActionEvent, UIView

from src.utils.json_helper import Json
from src.views.main_menu import MainMenuView
from src.config import *
from src.utils.client import client


import pyglet

from src.widgets.message_box import UIMessageBox


class Game:
    def __init__(self):
        self.config = Json(path="./config.json")
        self.config.load()



        pyglet.font.add_file(FONT_PATH)


    def run(self):
        self.window = GameWindow()
        try:
            client.connect(self.config.content['server_host'],self.config.content['server_tcp_port'],self.config.content['server_udp_port'])
            if self.config.content['phcathub_uid'] == 0:
                self.config.content['phcathub_uid'] = random.randint(1,10000)

                self.config.save()
            u =self.config.content['phcathub_uid'] if not DEBUG else random.randint(1,10000)
          #  u = random.randint(1,1000)
            client.phcathub_uid = u

            client.login(u)
            #time.sleep(3)
            self.window.show_view(MainMenuView())
            self.window.run()
        finally:
            # 确保在游戏结束时关闭套接字连接
            client.disconnect()

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(1600, 800, GAME_NAME, resizable=True)
        self.set_minimum_size(1600,800)
        self.maximize()
        self.shader_program = self._load_shader_program()

        self.shader_program["u_texture"] = 0



    def _load_shader_program(self):
        """从文件加载着色器代码并创建程序"""
        # 读取顶点着色器
        with open(SHADERS_PATH / 'damage_vertex.glsl', "r", encoding="utf-8") as f:
            vertex_shader = f.read()

        # 读取片段着色器
        with open(SHADERS_PATH / 'damage_fragment.glsl', "r", encoding="utf-8") as f:
            fragment_shader = f.read()

        # 创建并返回着色器程序（arcade.gl.Program）
        return self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )

    def on_update(self, delta_time: float) -> bool | None:
        if not client.tcp_connected and not hasattr(self, 'message_box'):

            self.message_box = UIMessageBox(
                width=600,
                height=200,
                message_text=(
                    "未连接至服务器……"
                ),title="提示",
                buttons=[" 好吧 "],
            )

            @self.message_box.event("on_action")
            def on_message_box_close(e: UIOnActionEvent):
                arcade.exit()

            v = UIView()
            v.add_widget(self.message_box)
            self.show_view(v)
        if client.need_update and not hasattr(self, 'message_box'):

            self.message_box = UIMessageBox(
                width=600,
                height=200,
                message_text=(
                    "需要更新！"
                ),title="提示",
                buttons=[" 好吧 "],
            )

            @self.message_box.event("on_action")
            def on_message_box_close(e: UIOnActionEvent):
                arcade.exit()

            v = UIView()
            v.add_widget(self.message_box)
            self.show_view(v)

game = Game()
