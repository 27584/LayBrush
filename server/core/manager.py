import os
import threading
import time

from peewee import SqliteDatabase

from config import SERVER_VERSION, SERVER_VERSION_, LATEST_CLIENT_VERSION, NEED_CLIENT_VERSION_, LATEST_CLIENT_VERSION_
from core.room import Room
from models.user import User
from datetime import datetime

from models.user_card import UserCard
from models.user_deck import UserDeck
from utils.json_helper import Json

class Manager:
    def __init__(self):
        self.db = None

        self.rooms = []
        self.rooms_thread =  threading.Thread(target=self.rooms_handle,
                    daemon=True)
        self.rooms_thread.start()



        self.callbacks = {
            "login":self.login,
            'get_user_info':self.get_user_info,
            'start':self.start,
            "room":self.room,
            'join':self.join,
            "edit_user_name":self.edit_user_name,
            'get_rooms':self.get_rooms,
        }
        from utils import server
        self.server = server.server




    def rooms_handle(self):
        last_time = time.time()
        while True:
            dt = time.time() - last_time
            last_time = time.time()
            for room in self.rooms:
                room.update(dt)
                if room.need_del:
                    self.rooms.remove(room)


    def connect_db(self):
        """连接数据库"""
        self.db = SqliteDatabase("game.db")
        self.db.bind([User,UserCard, UserDeck])

        self.db.create_tables([User,UserCard,UserDeck],safe = True)
       # self.db.connect()

    def no_callback(self,data,client_address):
        return {
            "code":114
        }
    def start(self, data,client_address):
        """处理玩家匹配请求

        Args:
            data: 包含客户端信息的数据字典，应包含client_id或tcp_thread_name

        Returns:
            dict: 匹配操作结果
        """
        room = Room(self)
        self.rooms.append(room)
        room.add_player(client_address,True)
        return {
            "code": 1,
            "msg": "创建成功"
        }
    def room(self, data,client_address):
        for room in self.rooms:
            if client_address in room.get_players_tcp_address():
                room.handle(data,client_address)


    def join(self,data,client_address):
        room = self.get_room(data['room_id'])
        if room is None:
            return{
                "code": 0,
                "msg": "房间不存在"
            }
        if room.status != 0:
            return {
                "code": 0,
                "msg": "游戏已开始"
            }
        room.add_player(client_address,False)
        return {
            "code": 1,

        }
    def get_room(self,room_id):
        for room in self.rooms:
            if room.room_id == room_id:
                return room
        return None

    def get_rooms(self,data,client_address):
        rooms = []
        for room in self.rooms:
            rooms.append(room.get_room_info())
        return {
            "code": 1,
            "rooms": rooms
        }


    def edit_user_name(self,data,client_address):
        """编辑用户昵称"""
        data['uid'] = self.server.get_client_info_by_address(client_address)['user_info']['uid']
        user_info = self.get_user_info(data,client_address)
        uid = user_info.get("uid",None)
        phcathub_uid = user_info.get("phcathub_uid",None)
        name = data.get("name",None)
        if uid:
            user = User.get_or_none(User.id==uid)
        elif phcathub_uid:
            user = User.get_or_none(User.phcathub_uid==phcathub_uid)
        else:
            user = None
        if user:
            user.name = name
            user.save()
            return {
                "code":1 
            }
        else:
            return {
                "code":0,
                "msg":"用户不存在"
            }
    def get_server_info(self):
        return {
            "server_version":SERVER_VERSION,
            "server_version_":SERVER_VERSION_,
            "latest_client_version":LATEST_CLIENT_VERSION,
            "latest_client_version_":LATEST_CLIENT_VERSION_,
            "need_client_version_":NEED_CLIENT_VERSION_,
        }
    def login(self,data,client_address):
        user = User.get_or_none(User.phcathub_uid==data["phcathub_uid"])
        if user:
            return {
                "code": 2 ,#登录成功
                'msg': "登录成功",
                "uid":user.id,"server_info":self.get_server_info(),
                "phcathub_uid": user.phcathub_uid,

            }
        else:
            user = User.new_user(phcathub_uid=data["phcathub_uid"])
            return {
                "code":1, #注册成功
                'msg': "注册成功",
                "uid":user.id,"server_info":self.get_server_info(),
                "phcathub_uid": user.phcathub_uid,

            }




    def get_user_info(self,data,client_address):
        uid = data.get("uid",None)
        phcathub_uid = data.get("phcathub_uid",None)
        if uid:
            user = User.get_or_none(User.id==uid)
        elif phcathub_uid:
            user = User.get_or_none(User.phcathub_uid==phcathub_uid)
        else:
            user = None
        if user:
            return {
                "code":1 ,
                "phcathub_uid":user.phcathub_uid,
                "uid":user.id,
                "name": user.name,
                "coin": user.coin,
            }
        else:
            return {
                "code":0,
                "error_msg":"用户不存在"
            }
    def handle_message(self, message,client_address):
        # 构建JSON响应
        if message.get("action"):
            response = self.callbacks.get(message["action"],self.no_callback)(message['data'],client_address)
        else:
            # 这里有问题！！！！！！！
            response = self.callbacks.get('room',self.no_callback)(message,client_address)
            print(message)
        return response

    def outline(self,address):
        for room in self.rooms:
            if room:
                for player in room.players:
                    if player['tcp_address'] == address:
                        player['online'] = False
            
# 全局实例
manager = Manager()