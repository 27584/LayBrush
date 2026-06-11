#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户端套接字管理模块
功能：
1. TCP客户端 - 负责连接到TCP服务器，发送JSON格式的数据并接收响应
2. UDP客户端 - 负责UDP游戏数据传输
3. 统一的客户端管理
使用独立线程处理套接字通信
"""

import socket
import json
import threading
import queue
import time
import uuid
import logging
from typing import List

from src.config import CLIENT_VERSION_

TIMEOUT_THRESHOLD = 15
PING_INTERVAL = 5


def split_list( lst: List, max_size: int = 100) -> List[List]:
    """手动循环分割列表（兼容所有 Python 版本）"""
    split_lists = []
    current_sublist = []

    for item in lst:
        current_sublist.append(item)
        # 当当前子列表长度达到 max_size 时，添加到结果并重置
        if len(current_sublist) == max_size:
            split_lists.append(current_sublist)
            current_sublist = []

    # 添加最后一个未填满的子列表（若有）
    if current_sublist:
        split_lists.append(current_sublist)

    return split_lists
class Client:
    """客户端套接字类，支持TCP和UDP通信"""
    
    def __init__(self):
        self.last_pong_time =  0
        self.tcp_socket = None
        self.udp_socket = None
        self.connected = False
        self.tcp_connected = False
        self.udp_connected = False
        
        # 服务器信息
        self.server_host = None
        self.server_tcp_port = None
        self.server_udp_port = None
        
        # 线程相关
        self.tcp_receive_thread = None
        self.udp_receive_thread = None
        self.running = False
        self.thread_name = None

        self.need_update = False
        # 用户信息
        self.uid = None
        self.phcathub_uid = None

        self.cards = {}
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 回调函数
        self.tcp_callbacks = {}  # TCP动作回调字典
        self.udp_callbacks = {}  # UDP类型回调字典

    def udp_send_ping(self):
        """定期发送Ping消息（每PING_INTERVAL秒一次）"""
        while self.running:


            self.udp_send('ping',{"thread_name":self.thread_name})


            # 检查是否超时（超过TIMEOUT_THRESHOLD秒没收到Pong）
            """
            if time.time() - self.last_pong_time > TIMEOUT_THRESHOLD:
                # 重置socket（重新获取UDP地址）
                self.udp_socket.close()
                self._connect_udp()
             """
            time.sleep(PING_INTERVAL)

    def connect(self, server_host, server_tcp_port, server_udp_port):
        """连接到服务器
        
        Args:
            server_host: 服务器主机地址
            server_tcp_port: TCP端口
            server_udp_port: UDP端口
        """
        self.server_host = server_host
        self.server_tcp_port = server_tcp_port
        self.server_udp_port = server_udp_port
        
        try:
            # 创建TCP连接
            self._connect_tcp()
            
            # 创建UDP套接字
            self._connect_udp()
            
            if self.tcp_connected and self.udp_connected:
                self.connected = True
                self.running = True
                
                # 启动接收线程
                self._start_receive_threads()
                
                self.logger.info(f"已连接到服务器 {server_host}:{server_tcp_port}/{server_udp_port}")
                return True
            else:
                self.logger.error("连接失败")
                return False
                
        except Exception as e:
            self.logger.error(f"连接服务器失败: {e}")
            self.disconnect()
            return False
    
    def _connect_tcp(self):
        """连接TCP服务器"""
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置TCP keep-alive选项
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Windows下的TCP keep-alive设置
            if hasattr(socket, 'TCP_KEEPIDLE'):
                self.tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            if hasattr(socket, 'TCP_KEEPINTVL'):
                self.tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, 'TCP_KEEPCNT'):
                self.tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            
            self.tcp_socket.connect((self.server_host, self.server_tcp_port))
            self.tcp_connected = True
            self.logger.info(f"TCP连接成功 {self.server_host}:{self.server_tcp_port}")
        except Exception as e:
            self.logger.error(f"TCP连接失败: {e}")
            self.tcp_connected = False
            raise
    
    def _connect_udp(self):
        """连接UDP套接字"""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 设置UDP套接字选项，避免Windows下的无效参数错误
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 设置接收超时，避免阻塞
            self.udp_socket.settimeout(1)
            self.udp_connected = True
            self.logger.info(f"UDP套接字创建成功")
        except Exception as e:
            self.logger.error(f"UDP套接字创建失败: {e}")
            self.udp_connected = False
            raise
    
    def _start_receive_threads(self):
        """启动接收线程"""
        # TCP接收线程
        self.tcp_receive_thread = threading.Thread(target=self._tcp_receive_loop, daemon=True)
        self.tcp_receive_thread.start()
        
        # UDP接收线程
        self.udp_receive_thread = threading.Thread(target=self._udp_receive_loop, daemon=True)
        self.udp_receive_thread.start()

        self.send_ping_thread = threading.Thread(target=self.udp_send_ping, daemon=True)
        self.send_ping_thread.start()

    def _tcp_receive_loop(self):
        """TCP接收主循环"""
        while self.running and self.tcp_connected:
            try:
                data = self.tcp_socket.recv(4096*1024)
                if not data:
                    self.logger.warning("TCP连接断开")

                    self.tcp_connected = False
                    break

                # 存储拆分后的完整 JSON 串
                json_list = []
                # 记录当前 JSON 串的起始索引、括号匹配计数器
                start_idx = -1
                brace_count = 0  # 用于处理嵌套 {}

                json_data = data.decode('utf-8')

                # 遍历字符串，按 JSON 语法拆分
                for idx, char in enumerate(json_data):
                    if char == '{':
                        # 找到 JSON 起始符 {
                        if start_idx == -1:  # 首次遇到 {，记录起始位置
                            start_idx = idx
                        brace_count += 1  # 括号计数 +1（处理嵌套）
                    elif char == '}':
                        # 找到 JSON 结束符 }
                        if brace_count > 0:  # 确保有匹配的 {
                            brace_count -= 1
                            # 当括号计数器归 0 时，说明当前 JSON 串完整
                            if brace_count == 0 and start_idx != -1:
                                # 截取完整的 JSON 子串（包含 {}）
                                json_sub = json_data[start_idx:idx + 1].strip()
                                if json_sub:  # 跳过空串（避免纯空白字符）
                                    json_list.append(json_sub)
                                # 重置起始索引，准备下一个 JSON 串
                                start_idx = -1

                # 处理拆分后的每个 JSON 串
                for idx, json_str in enumerate(json_list):
                    try:
                        # 单独解析每个 JSON 串
                        message = json.loads(json_str)

                        self._handle_tcp_message(message)

                        self.logger.debug(f"TCP 解析成功第 {idx + 1} 条消息：{message}")
                    except json.JSONDecodeError as e:
                        # 单个 JSON 解析失败，记录日志但不中断整体流程
                        self.logger.error(f"TCP 第 {idx + 1} 条消息解析失败：{e}，原始数据：{repr(json_str)}")
                    except Exception as e:
                        self.logger.error(f"TCP 第 {idx + 1} 条消息处理异常：{e}")




            except socket.timeout:
                continue

    
    def _udp_receive_loop(self):
        """UDP接收主循环"""
        while self.running and self.udp_connected:
            try:
                # 使用更小的缓冲区大小，减少Windows下的错误
                data, server_address = self.udp_socket.recvfrom(4096)
                if not data:
                    continue
                    
                try:
                    json_data = data.decode('utf-8')
                    message = json.loads(json_data)
                    self._handle_udp_message(message,server_address)
                    self.logger.debug(f"UDP收到消息: {message}")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    self.logger.error(f"UDP消息解析失败: {e}")
            except socket.timeout:
                # 超时是正常的，继续循环
                continue
            except OSError as e:
                # 处理Windows下的网络错误
                if e.winerror == 10022:  # 无效参数错误
                    self.logger.warning("UDP接收遇到无效参数，尝试重新设置socket")
                    try:
                        self.udp_socket.settimeout(1.0)
                        continue
                    except:
                        break
                elif self.running:
                    self.logger.error(f"UDP接收OS错误: {e}")
                break


                    

    
    def _handle_tcp_message(self, message):
        """处理TCP消息"""
        # 处理登录响应
        if message.get('status') == 'success' and 'data' in message and message['data'] is not None:
            data = message['data']
            if data.get('code') in [1, 2]:  # 注册成功或登录成功
                self.uid = data.get('uid',self.uid)
                self.phcathub_uid = data.get('phcathub_uid',self.phcathub_uid)

            if data.get('server_info'):
                # 检查版本
                if data['server_info']['need_client_version_'] > CLIENT_VERSION_ :
                    self.need_update = True
            # 调用动作特定回调
            action = message.get('action')
            if action and action in self.tcp_callbacks:
                self.tcp_callbacks[action](message.get('data'))


    
    def _handle_udp_message(self, message, address):
        """处理UDP消息"""

        # 调用类型特定回调
        msg_type = message.get('action')
        if msg_type and msg_type in self.udp_callbacks:

            self.udp_callbacks[msg_type](message.get('data'), address)


    def tcp_send(self, action, data):
        """发送TCP消息
        
        Args:
            action: 动作类型
            data: 数据内容
        """
        if not self.tcp_connected:
            self.logger.error("TCP未连接")
            return False
        
        try:
            message = {
                "action": action,
                "data": data,
                "timestamp": time.time()
            }
            #json_data = json.dumps(message, ensure_ascii=False)

            d = json.dumps(message).encode('utf-8')

            #threading.Thread(target=self.tcp_socket.sendall, args=(d,),
                    #         daemon=True).start()
            self.tcp_socket.sendall(d)
            # self.tcp_socket.sendall(json_data.encode('utf-8'))
            self.logger.debug(f"TCP发送消息: {action}")
            return True
        except Exception as e:
            self.logger.error(f"TCP发送失败: {e}")
            self.tcp_connected = False
            return False
    
    def udp_send(self, message_type, data):
        """发送UDP消息
        
        Args:
            message_type: 消息类型
            data: 数据内容
        """
        if not self.udp_connected:
            self.logger.error("UDP未连接")
            return False
        
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": time.time()
            }
            
            json_data = json.dumps(message, ensure_ascii=False)
            #threading.Thread(target= self.udp_socket.sendto, args=(json_data.encode('utf-8'),
                      #           (self.server_host, self.server_udp_port)),
                           #  daemon=True).start()
            self.udp_socket.sendto(json_data.encode('utf-8'),
                                 (self.server_host, self.server_udp_port))

            self.logger.debug(f"UDP发送消息: {message_type}")
            return True
        except Exception as e:
            self.logger.error(f"UDP发送失败: {e}")
            self.udp_connected = False
            return False
    
    def login(self, phcathub_uid):
        """登录/注册
        
        Args:
            phcathub_uid: 用户ID
        """
        def _(data):
            self.thread_name = data['thread_name']
            #self.udp_send(message_type='login', data=data)
        self.tcp_callbacks['login'] = _
        self.tcp_send("login", {"phcathub_uid": phcathub_uid})


    
    def get_user_info(self, uid=None, phcathub_uid=None):
        """获取用户信息
        
        Args:
            uid: 用户ID
            phcathub_uid: PHCATHUB用户ID
        """
        data = {}
        if uid:
            data["id"] = uid
        if phcathub_uid:
            data["phcathub_uid"] = phcathub_uid
        
        return self.tcp_send("get_user_info", data)
    
    def edit_user_name(self, name):
        """编辑用户名
        
        Args:
            name: 新用户名
        """
        data = {"name": name}
        if self.uid:
            data["id"] = self.uid
        elif self.phcathub_uid:
            data["phcathub_uid"] = self.phcathub_uid
        
        return self.tcp_send("edit_user_name", data)
    
    def match(self):
        """发起匹配请求"""
        return self.tcp_send("match", {})
    
    def send_game_data(self, game_data):
        """发送游戏数据（UDP）
        
        Args:
            game_data: 游戏数据
        """
        return self.udp_send("game_data", game_data)
    
    def send_player_action(self, action_data):
        """发送玩家动作（UDP）
        
        Args:
            action_data: 动作数据
        """
        return self.udp_send("player_action", action_data)
    
    def is_connected(self):
        """检查连接状态"""
        return self.connected and self.tcp_connected and self.udp_connected
    
    def disconnect(self):
        """断开连接"""
        self.running = False
        self.connected = False
        
        # 关闭TCP连接
        if self.tcp_socket:
            try:
                # 关闭读取操作
                self.tcp_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.tcp_socket.close()
            except:
                pass
            self.tcp_socket = None
            self.tcp_connected = False
        
        # 关闭UDP连接
        if self.udp_socket:
            try:
                # 先设置超时为0，让recvfrom立即返回
                self.udp_socket.settimeout(0.1)
            except:
                pass
            try:
                self.udp_socket.close()
            except:
                pass
            self.udp_socket = None
            self.udp_connected = False
        
        # 等待线程结束
        if self.tcp_receive_thread and self.tcp_receive_thread.is_alive():
            self.tcp_receive_thread.join(timeout=1.0)
        if self.udp_receive_thread and self.udp_receive_thread.is_alive():
            self.udp_receive_thread.join(timeout=1.0)
        if hasattr(self, 'message_process_thread') and self.message_process_thread.is_alive():
            self.message_process_thread.join(timeout=1.0)
        

        
        self.logger.info("客户端已断开连接")
    
    def reconnect(self):
        """重新连接"""
        self.logger.info("尝试重新连接...")
        self.disconnect()
        time.sleep(1)
        return self.connect(self.server_host, self.server_tcp_port, self.server_udp_port)
    
    def get_status(self):
        """获取连接状态"""
        return {
            "connected": self.connected,
            "tcp_connected": self.tcp_connected,
            "udp_connected": self.udp_connected,
            "uid": self.uid,
            "phcathub_uid": self.phcathub_uid
        }


# 全局客户端实例
client = Client()


