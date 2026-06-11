

from utils import server

from config import IP,TCP_PORT,UDP_PORT
import time
import threading

from utils.server import Server


def main():
    """主函数"""
    
    try:
        server.server = Server(IP,TCP_PORT,UDP_PORT)
        print("启动服务器...")
        server_thread = threading.Thread(target=server.server.start, daemon=True)
        server_thread.start()

        print(f"双协议服务器已启动！TCP端口: {TCP_PORT}, UDP端口: {UDP_PORT}")
        print("服务器运行中，按Ctrl+C停止...")
        # manager连接数据库
        from core.manager import manager
        manager.connect_db()
        # 保持主程序运行
        while True:
            # 定期检查服务器状态
            time.sleep(5)
            
            # 检查服务器是否仍在运行
            if  not server.server.running:
                print("服务器已停止，程序将退出")
                break

    
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止服务器...")

    finally:
        # 先停止TCP服务器
        if server.server:
            server.server.stop()
            

            
        print("服务器已停止")

if __name__ == '__main__':
    main()