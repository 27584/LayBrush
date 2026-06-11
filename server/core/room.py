"""
房间逻辑
"""

import random
import time
import uuid
from copy import deepcopy

from utils.json_helper import Json
from utils.server import split_list

# 游戏状态常量
WAITTING = 0
SETTING = 1 #出题中
DRAWING = 2 #绘画中
GUESSING = 3 #猜
END = 4 # 复盘

# 模式常量
RELAY_1 = 0 #单线接龙
RELAY_2 = 1 #多线接龙
QUIZ = 2 #竞猜 （没做）
PAINTING = 3 #茶绘模式 （没做）

# 同步时间
SYNC_TIME = 1



class Room:
    """
    房间处理
    """
    def __init__(self,manager):
        self.draw_over = False # 用于回放时判断回放过程是否画完
        self.name = "" #未使用
        self.type = "draw" #未使用

        self.mode =RELAY_2

        self.room_id = uuid.uuid4().hex # 房间唯一ID
        self.status = WAITTING
        self.manager = manager # 上层管理器
        self.answer = "" # 用于单线接龙 正确答案
        self.ticks = 0 # 绝对时间
        self.last_sync_time = 0
        self.start_player = 0 # 用于单线接龙
        self.current_player = 0 #在单线接龙中为当前轮到的玩家

        #如果是多线接龙，则current_player代表以玩家0为基准的出题者开始的顺序
        # 在回放中则代表当前回放的进行玩家

        self.current_status_time = 0
        self.need_del = False # 为真时主进程会删除房间
        self.points = {

        } # 单线接龙的画作

        # m_ 为多线接龙专用属性

        self.m_points = {} #多线接龙的画作，用于回放
        self.m_points_2 = {} # 用于实时展示


        self.current_points = []

        self.m_current_points = {} # 多线接龙 {0:[],1:[]}

        self.m_round = 0 # 多线接龙的回合数
        self.m_over = [] # 当前回合完成的玩家index



        self.players = [

        ]

        self.words = None

    def m_get_setter(self,i):
        """根据当前画家获取出题者"""
        return self.get_normal_index( i - self.m_round)

    def get_normal_index(self,i):
        """
        用于多线接龙正常化玩家index

        """
        if i >= 0 and i < len(self.players) :
            return i
        elif i >= len(self.players) :
            return i - len(self.players)
        else:
            return len(self.players) + i

    def add_player(self,tcp_address,is_owner = False):
        uid = self.manager.server.get_client_info_by_address(tcp_address)['user_info']['uid']
        name = self.manager.get_user_info({'uid':uid},tcp_address)['name']
        player = {
            "tcp_address": tcp_address,
            "is_owner" : is_owner,
            "online":True,
            'name':name,
            'uid':uid,
            "answer":"",
            "question":"",
            "answers":{},
            'phcathub_id':None
        }
        self.players.append(player)

    def get_player_number(self):
        return len(self.players)

    def get_owner(self):
        for i in self.players:
            if i['is_owner']:
                return i
        return None

    def get_owner_name(self):
        if self.get_owner() is None:
            return ""
        return self.get_owner()['name']

    def tcp_send(self,player_index,data):
        message = self.manager.server.build_message("room",data)
        uid = self.players[player_index]['uid']
        self.manager.server.send_to_client_by_uid(uid,message,1)
    def udp_send(self,player_index,data):

        message = self.manager.server.build_message("room",data)
        uid = self.players[player_index]['uid']
        self.manager.server.send_to_client_by_uid(uid,message,0)
    def init_game(self):

        for p in self.players:
            p['answer'] = ""
            p['question'] = ""
            p['answers'] = {}
        self.answer = ""
        self.current_status_time = deepcopy(self.ticks)
        self.points = {}
        self.current_player = 0
        self.start_player = 0
        self.m_round = 0
        self.m_over = []
        self.m_points = {}
        self.m_points_2 = {}
        self.m_current_points = {}
        self.clear_all()


        self.words = Json(path =  "./words_lib/default.json")
        self.words.load()

    def get_random_word(self):
        l = []

        return l
    def handle(self,data,client_address):
        # 处理逻辑回调函数
        player_index = self.get_player_index_by_tcp_address(tcp_address=client_address)

        if data['type'] == 'chat':
            for i in self.get_online_players_index():
                if i != player_index:
                    data = {
                        "type":"chat","text":data['text'],"name":self.players[player_index]['name']
                    }
                    self.tcp_send(i,data)
                i+=1
        elif data['type'] == 'start':
            if self.players[player_index]['is_owner'] and self.status == WAITTING:
                if len(self.players) >=2 and  self.mode in [RELAY_1]:

                    self.status = SETTING
                    self.init_game()
                if self.mode in [RELAY_2]:
                    if  len(self.players) >= 3 :
                        self.status = SETTING
                        self.init_game()
                    else:
                        self.chat(player_index,"该模式需要至少三人开局，3-4人一轮，5-6人两轮，7-8人三轮……因此建议7人以上开局。")
                if self.mode not in [RELAY_1,RELAY_2]:
                    self.chat(player_index,'该模式暂未开放！')

        elif data['type'] == 'set_mode':
            if self.players[player_index]['is_owner'] and self.status == WAITTING:

                self.mode = data['mode']

        elif data['type'] == 'setting':

            if self.status == SETTING :
                if self.mode in [RELAY_1,QUIZ] and self.current_player == player_index:
                    self.status = DRAWING
                    self.answer = data['answer']
                    self.players[player_index]['answer'] = data['answer']
                elif self.mode == RELAY_2:
                    self.players[player_index]['question'] = data['answer']
                    self.players[player_index]['answers'][player_index] = data['answer']

        elif data['type'] == 'draw':
            if self.status == DRAWING:
                if self.mode == RELAY_1:
                    self.current_points.append(data['points'])
                    for i in self.get_online_players_index():
                        if i != player_index :
                            if (self.mode == RELAY_1 and i <= self.current_player +1) or self.mode == QUIZ:
                                data = {
                                    "type": "draw", "points":data['points'],
                                }
                                self.tcp_send(i, data)

                        i += 1
                elif self.mode == RELAY_2:
                    # 多线接龙模式，先存
                    # 比如 [0,1,2,3,4,5]
                    #
                    # player_index 当前画的玩家
                    # player_index - current_player 即为出题者
                    if player_index not in self.m_current_points.keys():
                        self.m_current_points[player_index] = []
                    self.m_current_points[player_index].append(data['points'])

        elif data['type'] == 'end_draw':
            if self.status == DRAWING:
                if self.mode == RELAY_1:
                    self.points[player_index] = deepcopy(self.current_points)

                    self.current_points = []
                    self.status = GUESSING
                    self.current_player += 1
                elif self.mode == RELAY_2:
                    self.m_over.append(player_index)
                    setter = self.m_get_setter(player_index)
                    if setter not in self.m_points.keys():
                        self.m_points[setter] = {}
                        self.m_points_2[setter] = {}
                    if player_index not in self.m_points[setter].keys():
                        self.m_points[setter][player_index] = []
                        self.m_points_2[setter][player_index] = []

                    self.m_points[setter][player_index] = deepcopy(self.m_current_points[player_index])
                    self.m_points_2[setter][player_index] = deepcopy(self.m_current_points[player_index])

        elif data['type'] == 'guess':
            if self.status == GUESSING:
                if self.mode == RELAY_1:
                    name = self.players[self.current_player]['name']
                    self.players[self.current_player]['answer'] = data['answer']
                    for i in self.get_online_players_index():
                        if i <= self.current_player:
                            self.chat(i,f"{name}猜：{data['answer']}")
                    if (self.current_player == len(self.players)-1) or self.current_player >= max(self.get_online_players_index()):

                        self.chat_to_all(f"游戏结束 ，正确答案是：{self.answer}，最终猜出：{data['answer']}")

                        self.clear_all()
                        self.status = END
                        self.current_status_time = deepcopy(self.ticks)
                        self.current_player =0
                        self.start_player = 0
                    else:
                        self.status = DRAWING
                        self.clear_all()
                elif self.mode == RELAY_2:

                    setter = self.m_get_setter(player_index)
                    self.players[player_index]['answers'][setter] = data['answer']
                    self.m_over.append(player_index)
        elif data['type'] == 'clear':
            if self.mode == RELAY_1:
                self.clear_all()
            elif self.mode == RELAY_2:
                self.clear(player_index)

        elif data['type'] == 'exit':
            if self.players[player_index]['is_owner']:
                self.del_room()
            self.players[player_index]['online'] = False
        elif data['type'] == 'voice':
            for i in self.get_online_players_index():
                if i != player_index:
                    data = {
                        "type": "voice", "voice_data": data['voice_data'],
                    }
                    self.udp_send(i, data)
                i += 1

    def get_online_players(self):
        l = []
        for i in self.players:
            if i['online']:
                l.append(i)
        return l
    def get_online_players_index(self):
        l = []
        i =0
        for p in self.players:
            if p['online']:
                l.append(i)
            i+=1
        return l
    def get_online_players_number(self):
        return len(self.get_online_players_index())
    def del_room(self):
        # 销毁房间
        for i in self.get_online_players_index():

            data = {
                "type": "del_room",
            }
            self.tcp_send(i, data)
        self.need_del = True
    def clear_all(self):
        # 清除所有人的画布
        self.current_points = []
        for i in self.get_online_players_index():

            data = {
                "type": "clear",
            }
            self.tcp_send(i, data)
    def clear(self,i):
        # 根据index清除玩家画布
        if i in self.m_current_points.keys():
            self.m_current_points[i] = []
        data = {
            "type": "clear",
        }
        self.tcp_send(i, data)
    def chat(self,i,text,name='',):
        # 根据玩家Index发送聊天 name为""则为系统消息
        data = {
            "type": "chat", "text": text, "name": name
        }
        self.tcp_send(i, data)

    def chat_to_all(self,text,name=''):
        for i in self.get_online_players_index():

            data = {
                "type": "chat", "text": text, "name": name
            }
            self.tcp_send(i, data)
            i += 1

    def get_player_index_by_tcp_address(self, tcp_address):
        i = 0
        for p in self.players:
            if p['tcp_address'] == tcp_address:
                return i
            i+=1
        return None



    def get_players_tcp_address(self):
        l = []
        for p in self.players:
            l.append(p['tcp_address'])
        return l
    def get_room_info(self):
        return {
            "room_id": self.room_id,
            "room_name": self.name,
            "owner_name": self.get_owner_name(),
            "player_number": self.get_player_number(),
            "status":self.status,
             "ticks":self.ticks,
            "current_player": self.current_player,
            "start_player": self.start_player,
            "mode":self.mode,"draw_over":self.draw_over,
            "round":self.m_round,"over":self.m_over,
            "words_name":self.words
        }

    def sync(self):
        # 同步
        for i in self.get_online_players_index():

            data = {
                "room_info":self.get_room_info(),
                "players": self.players
            }
          #  self.udp_send(i,data)
            self.tcp_send(i, data)

    def update(self,dt :float):

        self.ticks += dt
        if self.current_player not in self.get_online_players_index() and self.status not in  [WAITTING,END]:
            if self.current_player >= len(self.players)-1:
                answer = ""
                for p in self.get_online_players():
                    if p['answer'] != "":
                        answer += p['answer']

                self.chat_to_all(f"游戏结束 ，正确答案是：{self.answer}，最终猜出：{answer}","")
                self.clear_all()
                self.status = END
                self.current_player =0
                self.start_player = 0
            else:
                self.current_player += 1

        if self.ticks - self.last_sync_time >= SYNC_TIME:
            self.sync()
            self.last_sync_time = self.ticks
        if self.mode == RELAY_2 and self.get_online_players_number() != len(self.players):
            self.del_room()
        if self.status != WAITTING and self.get_online_players_number() <= 1:
            self.del_room()
        if self.status  == WAITTING:
            for p in self.players:
                if not p['online']:
                    if p['is_owner']:
                        self.del_room()
                    self.players.remove(p)
        if self.get_owner() and not self.get_owner()['online']:
            self.del_room()


        if self.status == SETTING:
            if self.mode == RELAY_2:
                ok =  True
                for p in self.players:
                    if p['question'] == "":
                        ok = False
                if ok:
                    self.status = DRAWING
                    self.m_round +=1

        if self.status == DRAWING:
            if self.mode == RELAY_2:
                if  all(element in self.m_over for element in self.get_online_players_index()):
                    self.m_over = []
                    self.status = GUESSING
                    self.m_current_points = {}
                    self.m_round += 1
                    self.clear_all()
                    time.sleep(0.1)

        if self.status == GUESSING:
            if self.mode == RELAY_2:

                #
                # 绘制给下一位玩家

                for setter in self.m_points.keys():
                    painter = self.get_normal_index(setter + self.m_round -1)
                    guesser = self.get_normal_index(setter + self.m_round )

                    if self.m_points_2[setter][painter]:
                        points = self.m_points_2[setter][painter][0]

                        for p in split_list(points, 5):

                            data = {
                                "type": "draw", "points": p,
                            }
                            self.tcp_send(guesser, data)


                        self.m_points_2[setter][painter].pop(0)

                    #painters = self.m_points[setter].keys()
                    #painters[self]

                if  all(element in self.m_over for element in self.get_online_players_index()):
                    self.m_over = []
                    self.m_round += 1
                    self.clear_all()
                    # 判断是否游戏结束
                    if (len(self.players) % 2 == 1 and self.m_round == len(self.players)) or (len(self.players) % 2 == 0 and self.m_round == len(self.players)-1 ):

                        self.status = END
                        self.m_round = 0
                        self.current_status_time = deepcopy(self.ticks)


                    else:
                        self.status = DRAWING
     #   print(self.current_player)

        # 回放
        if self.status == END:
            if self.mode == RELAY_1:
                if self.current_player <= len(self.players)-1:
                    if  self.current_player in self.points.keys():
                        time.sleep(0.08)

                        if self.points[self.current_player]:

                            points = self.points[self.current_player][0]

                            for p in split_list(points,5):
                                for i in self.get_online_players_index():
                                    data = {
                                        "type": "draw", "points": p,
                                    }
                                    self.tcp_send(i, data)


                                    i += 1
                            self.points[self.current_player].pop(0)
                        else:
                            if not self.draw_over:
                                self.draw_over = True
                                self.current_status_time = deepcopy(self.ticks)
                            else:
                                if self.ticks - self.current_status_time >= 5:
                                    self.current_player += 1
                                    self.clear_all()
                                    self.draw_over = False
                    else:
                        self.current_player += 1
                        self.draw_over = False
                else:
                    self.status = WAITTING
                    self.init_game()

            elif self.mode == RELAY_2:
                # 此时current_player代表出题者index
                if self.m_round == 0:
                    # 出题

                    if self.ticks - self.current_status_time >= 3:
                        self.m_round += 1
                        self.draw_over = False


                else:
                    current_painter = self.get_normal_index(self.current_player+self.m_round)

                    if self.current_player <= len(self.players) - 1:
                        if self.current_player in self.m_points.keys():
                            time.sleep(0.08) # 此处给其它线程处理的清屏指令预留一点时间，避免提前绘制后再清屏导致笔画丢失

                            # print(self.m_round,self.current_player,current_painter)

                            if self.m_points[self.current_player][current_painter]:
                                points = self.m_points[self.current_player][current_painter][0]

                                for p in split_list(points, 5):
                                    for i in self.get_online_players_index():
                                        data = {
                                            "type": "draw", "points": p,
                                        }
                                        self.tcp_send(i, data)

                                        i += 1
                                self.m_points[self.current_player][current_painter].pop(0)
                            else:
                                if not self.draw_over:
                                    self.draw_over = True
                                    self.current_status_time = deepcopy(self.ticks)
                                else:
                                    if self.ticks - self.current_status_time >= 5:
                                        self.m_round += 2
                                        self.clear_all()
                                        time.sleep(0.5)# 此处给其它线程处理的清屏指令预留一点时间，避免提前绘制后再清屏导致笔画丢失
                                        self.draw_over = False
                                        if len(self.players) % 2 == 1:
                                            if self.m_round == len(self.players) :
                                                self.current_player += 1
                                                self.draw_over = False
                                                self.m_round = 0
                                                self.current_status_time = deepcopy(self.ticks)

                                        else:
                                            if self.m_round == len(self.players)-1 :
                                                self.current_player += 1
                                                self.draw_over = False
                                                self.m_round = 0
                                                self.current_status_time = deepcopy(self.ticks)

                                        if self.current_player >= len(self.players) :
                                            self.status = WAITTING
                                            self.init_game()

                    else:
                        self.status = WAITTING
                        self.init_game()
    
