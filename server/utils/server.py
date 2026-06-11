#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器工具
TCP+UDP
UDP目前不太稳定，断连后无法恢复
"""

import socket
import threading
import time
import json

def split_list( lst: list, max_size: int = 100) -> list[list]:
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

class Server:
    def __init__(self, host, tcp_port,udp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port

        # tcp连接线程
        self.threads = []
        # udp接收线程
        self.udp_thread = None

        self.running = False

        self.manager = None
        self.tcp_socket = None
        self.udp_socket = None


        self.clients = {}

        # 用于线程安全操作的锁
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        # 创建TCP套接字
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置套接字选项，允许端口复用
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定地址和端口
        self.tcp_socket.bind((self.host, self.tcp_port))
        # 开始监听，最大连接数为5
        self.tcp_socket.listen(50)
        print(f"TCP服务器启动成功，正在监听 {self.host}:{self.tcp_port}")

        # 创建UDP套接字
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 设置套接字选项，允许端口复用
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定地址和端口
        self.udp_socket.bind((self.host, self.udp_port))
        print(f"UDP服务器启动成功，正在监听 {self.host}:{self.udp_port}")

        # 启动UDP接收线程
        self.udp_thread = threading.Thread(target=self.udp_receive_loop, daemon=True)
        self.udp_thread.start()


        # 绑定manager
        from core import manager
        self.manager = manager.manager


        # 主循环，接受客户端连接
        try:
            while self.running:
                # 接受客户端连接
                client_socket, client_address = self.tcp_socket.accept()
                print(f"接受到来自 {client_address} 的连接")

                # 创建线程处理客户端连接
                client_thread = threading.Thread(
                    target=self.tcp_handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                self.threads.append(client_thread)
        except Exception as e:
            if self.running:  # 只有在运行状态下的异常才输出
                print(f"服务器异常: {e}")

    def build_message(self,action,data,status = 'success'):
        return { "action": action, "data": data, "status": status ,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")

                  }

    def tcp_handle_client(self, client_socket, client_address):
        """处理客户端连接

        Args:
            client_socket: 客户端套接字
            client_address: 客户端地址（IP, 端口）
        """
        thread_name = threading.current_thread().name

        # 保存客户端信息
        self.clients[thread_name] = {
            'socket': client_socket,
            'address': client_address,
            'udp_address': None,
            'user_info': {
                'uid': None,
                'phcathub_uid': None
            },
        }


        while True:
            # 接收客户端发送的数据，最大接收1024字节
            data = client_socket.recv(4096*1024)
            if not data:  # 客户端关闭连接
                print(f"【 {client_address}】 断开连接")
                break

            # 解码收到的数据并解析JSON
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

                # 单独解析每个 JSON 串
              #  print(json.loads('{\"action\": \"login\", \"data\": {\"phcathub_uid\": 6175}, \"timestamp\": 1763452710.281758}'))
               # print(json_str)
                message = json.loads(json_str)
                print(f"【TCP】【{client_address}】 {message.get('action', 'unknown')}")

                response = {
                    "status": "success", "action": message.get('action', 'unknown'),
                    "data": self.manager.handle_message(message, client_address),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                if message.get('action') == 'login':
                    response['data']['thread_name'] = thread_name
                    # 保存用户信息到客户端记录
                    if response['data'].get('code') in [1, 2]:  # 注册成功或登录成功
                        self.clients[thread_name]['user_info']['phcathub_uid'] = response['data'].get(
                            'phcathub_uid')
                        self.clients[thread_name]['user_info']['uid'] = response['data'].get('uid')

                # 发送响应
                self.send_to_client(thread_name, response, 1)
                print(f"已回复客户端 {client_address} 响应")







        # 清理客户端信息
        if thread_name in self.clients:

            # 从clients字典中移除
            del self.clients[thread_name]

        # 移除匹配队列
        self.manager.outline(client_address)


        # 关闭客户端套接字
        client_socket.close()
        print(f"客户端 {client_address} 资源已清理")

    def udp_receive_loop(self):
        """UDP接收主循环"""

        while self.running:
            # 接收UDP数据包，最大接收1024字节
            data, client_address = self.udp_socket.recvfrom(4096)
            try:
                # 解码收到的数据并解析JSON
                json_data = data.decode('utf-8')
                message = json.loads(json_data)
              #  print(f"【UDP {client_address}】收到消息: {message.get('type', 'unknown')}")

                # 处理消息
                if message.get('type') == 'ping':
                   # print(message)
                    if message['data']['thread_name'] in self.clients :
                        self.clients[message['data']['thread_name']]['udp_address'] = client_address
                        self.send_to_client(message['data']['thread_name'], self.build_message('pong', {}),0)
                    else:
                        pass
                elif message.get('type') == 'room':
                    for room in self.manager.rooms:
                        tcp_address = self.get_tcp_address_by_udp_address(client_address)
                        if tcp_address in room.get_players_tcp_address() :

                            room.handle(message['data'], tcp_address)



            except json.JSONDecodeError:
                print(f"UDP接收错误: 无效的JSON格式")


    def get_tcp_address_by_udp_address(self, udp_address):
        for c in self.clients.values():
            if c['udp_address'] == udp_address:
                return c['address']
        return None


    def stop(self):
        """停止服务器"""
        self.running = False

        # 关闭所有客户端连接
        with threading.Lock():
            for thread_name, client_info in list(self.clients.items()):
                try:
                    client_info['socket'].close()
                except:
                    pass
            self.clients.clear()

        # 关闭服务器套接字
        if self.tcp_socket:
            self.tcp_socket.close()
        if self.udp_socket:
            self.udp_socket.close()

        print("服务器套接字已关闭")

        # 等待所有线程结束
        for thread in self.threads:
            if thread.is_alive():
                thread.join(1)  # 等待最多1秒

    def send_to_client(self, thread_name, message,type):
        """发送消息给指定客户端

               Args:
                   thread_name: 线程名称
                   message: 要发送的消息字典
                    type:1/0 TCP/UDP
               Returns:
                   bool: 是否发送成功
               """
        if thread_name in self.clients:
            client_info = self.get_client_info(thread_name)
            try:
                json_data = json.dumps(message, ensure_ascii=False)+ "\n"
                if type == 1:
                    client_info['socket'].sendall(json_data.encode('utf-8')  )

                   # threading.Thread(target=client_info['socket'].sendall, args=(json_data.encode('utf-8') ,),
                                   #  daemon=True).start()
                else :
                  #  threading.Thread(target=self.udp_socket.sendto, args=(json_data.encode('utf-8'),client_info['udp_address'],),
                                #     daemon=True).start()
                    self.udp_socket.sendto(json_data.encode('utf-8'), client_info['udp_address'])
                return True
            except Exception as e:
                print(f"发送消息给客户端 {thread_name} 失败: {e}")
                return False
        return False

    def send_to_client_by_address(self,address, message,type):
        """
        发送消息给根据uid指定的客户端
        :param uid:
        :param message:
        :return:
        """
        for thread_name, client_info in self.clients.items():
            if client_info['address']==address:
                return self.send_to_client(thread_name, message,type)
        return False

    def send_to_client_by_uid(self, uid, message,type):
        """
        发送消息给根据uid指定的客户端
        :param uid:
        :param message:
        :return:
        """
        for thread_name, client_info in self.clients.items():
            if client_info['user_info']['uid'] == uid:
                return self.send_to_client(thread_name, message,type)
        return False

    def send_to_client_by_phcathub_uid(self, phcathub_uid, message,type):
        """
        发送消息给根据uid指定的客户端
        :param phcathub_uid:
        :param message:
        :return:
        """
        for thread_name, client_info in self.clients.items():
            if client_info['user_info']['phcathub_uid'] == phcathub_uid:
                return self.send_to_client(thread_name, message,type)
        return False

    def get_client_info(self, thread_name):
        """获取客户端信息

        Args:
            thread_name: 线程名称

        Returns:
            dict: 客户端信息
        """
        return self.clients.get(thread_name)

    def get_client_info_by_address(self, address):
        for thread_name, client_info in self.clients.items():
            if client_info['address'] == address:
                return self.get_client_info(thread_name)
        return None
    def get_client_info_by_uid(self, uid):
        for thread_name, client_info in self.clients.items():
            if client_info['user_info']['uid'] == uid:
                return self.get_client_info(thread_name)
        return None
    def get_client_info_by_phcathub_uid(self, phcathub_uid):
        for thread_name, client_info in self.clients.items():
            if client_info['user_info']['uid'] == phcathub_uid:
                return self.get_client_info(thread_name)
        return None


server = None