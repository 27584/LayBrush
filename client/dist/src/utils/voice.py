import sounddevice as sd
import numpy as np
import queue
import base64
import json
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass


# ------------------------------
# JSON 数据格式定义（与你的UDP对齐）
# ------------------------------
@dataclass
class AudioJSONData:
    type: str = "audio"  # 消息类型标识
    data: str = ""  # 音频base64编码字符串
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "int16"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "dtype": self.dtype
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AudioJSONData":
        return AudioJSONData(
            type=data.get("type", "audio"),
            data=data.get("data", ""),
            sample_rate=data.get("sample_rate", 16000),
            channels=data.get("channels", 1),
            dtype=data.get("dtype", "int16")
        )


class AudioHandler:
    """
    支持独立开关的音频处理类（听/说分离控制）
    - 说（send_enabled）：开启=采集音频→编码JSON→通过UDP发送
    - 听（recv_enabled）：开启=接收UDP JSON→解码音频→播放
    """

    def __init__(
            self,
            sample_rate: int = 16000,
            channels: int = 1,
            dtype: str = "int16",
            blocksize: int = 512,
            device_index: Optional[int] = None,
            buffer_size: int = 10,
            # 外部UDP JSON发送函数（你已实现）：参数=JSON字典，无返回
            udp_send_func: Callable[[Dict[str, Any]], None] = None,
            # 可选：接收音频后的自定义回调
            on_audio_recv: Optional[Callable[[np.ndarray], None]] = None
    ):
        # 音频基础参数（两端必须一致）
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.device_index = device_index

        # 外部依赖（你的UDP逻辑）
        self.udp_send_func = udp_send_func
        self.on_audio_recv = on_audio_recv

        # 独立开关状态（默认都关闭，需手动开启）
        self.send_enabled = False  # 说：采集+发送开关
        self.recv_enabled = False  # 听：接收+播放开关

        # 音频队列（分离采集和播放队列，避免开关影响）
        self.record_queue = queue.Queue(maxsize=buffer_size)  # 采集→发送队列
        self.play_queue = queue.Queue(maxsize=buffer_size)  # 接收→播放队列

        # 音频流对象（分离采集流和播放流，支持单独启停）
        self.input_stream: Optional[sd.InputStream] = None  # 采集流（说）
        self.output_stream: Optional[sd.OutputStream] = None  # 播放流（听）

        # 发送/接收线程
        self.send_thread: Optional[Any] = None
        self.is_running = False  # 整体运行状态

    # ------------------------------
    # 设备验证
    # ------------------------------
    def _check_device(self):
        """验证采集设备是否存在（仅在开启“说”时调用）"""
        if self.device_index is not None:
            devices = [d["index"] for d in sd.query_devices()]
            if self.device_index not in devices:
                raise ValueError(f"采集设备索引 {self.device_index} 不存在！")

    # ------------------------------
    # 音频采集回调（仅“说”开启时生效）
    # ------------------------------
    def _record_callback(
            self,
            indata: np.ndarray,
            frames: int,
            time_info: dict,
            status: sd.CallbackFlags
    ):
        if status:
            print(f"采集警告：{status}", flush=True)

        # 仅当“说”开启时，才写入发送队列
        if self.send_enabled:
            try:
                self.record_queue.put_nowait(indata.copy())
            except queue.Full:
                try:
                    self.record_queue.get_nowait()
                    self.record_queue.put_nowait(indata.copy())
                except:
                    pass

    # ------------------------------
    # 音频播放回调（仅“听”开启时生效）
    # ------------------------------
    def _play_callback(
            self,
            outdata: np.ndarray,
            frames: int,
            time_info: dict,
            status: sd.CallbackFlags
    ):
        if status:
            print(f"播放警告：{status}", flush=True)

        outdata.fill(0)  # 默认静音

        # 仅当“听”开启时，才从播放队列读取数据
        if self.recv_enabled:
            try:
                audio_data = self.play_queue.get_nowait()
                if len(audio_data) == frames:
                    outdata[:] = audio_data
                else:
                    outdata[:len(audio_data)] = audio_data
            except queue.Empty:
                pass
            except ValueError:
                pass

    # ------------------------------
    # JSON与音频编解码（核心对接逻辑）
    # ------------------------------
    def audio_to_json(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """numpy音频数组 → JSON字典（base64编码）"""
        audio_bytes = audio_data.tobytes()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return AudioJSONData(
            type="audio",
            data=audio_base64,
            sample_rate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype
        ).to_dict()

    def json_to_audio(self, json_dict: Dict[str, Any]) -> Optional[np.ndarray]:
        """JSON字典 → numpy音频数组（base64解码）"""
        # 仅处理音频类型消息
        if json_dict.get("type") != "audio":
            return None

        # 解析并验证参数
        try:
            audio_data = AudioJSONData.from_dict(json_dict)
        except Exception as e:
            print(f"JSON解析失败：{e}", flush=True)
            return None

        if (audio_data.sample_rate != self.sample_rate
                or audio_data.channels != self.channels
                or audio_data.dtype != self.dtype):
            print(
                f"参数不匹配：对方[{audio_data.sample_rate}Hz, {audio_data.channels}声道]，本地[{self.sample_rate}Hz, {self.channels}声道]")
            return None

        # 解码为numpy数组
        try:
            audio_bytes = base64.b64decode(audio_data.data)
            audio_np = np.frombuffer(audio_bytes, dtype=self.dtype).reshape(-1, self.channels)
            return audio_np
        except Exception as e:
            print(f"音频解码失败：{e}", flush=True)
            return None

    # ------------------------------
    # 独立开关控制接口（核心功能）
    # ------------------------------
    def enable_send(self, enable: bool = True):
        """
        控制“说”开关：开启/关闭采集+发送
        :param enable: True=开启，False=关闭
        """
        if self.send_enabled == enable:
            return

        self.send_enabled = enable
        if enable:
            # 开启“说”：启动采集流和发送线程
            self._check_device()
            if not self.input_stream or not self.input_stream.active:
                self.input_stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    blocksize=self.blocksize,
                    device=self.device_index,
                    callback=self._record_callback
                )
                self.input_stream.start()
            # 启动发送线程（持续从队列取数据发送）
            if not self.send_thread or not self.send_thread.is_alive():
                import threading
                self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
                self.send_thread.start()
            print("“说”功能已开启（采集+发送）")
        else:
            # 关闭“说”：停止采集流，清空发送队列
            if self.input_stream and self.input_stream.active:
                self.input_stream.stop()
            # 清空队列（避免残留数据）
            while not self.record_queue.empty():
                self.record_queue.get_nowait()
            print("“说”功能已关闭（采集+发送）")

    def enable_recv(self, enable: bool = True):
        """
        控制“听”开关：开启/关闭接收+播放
        :param enable: True=开启，False=关闭
        """
        if self.recv_enabled == enable:
            return

        self.recv_enabled = enable
        if enable:
            # 开启“听”：启动播放流
            if not self.output_stream or not self.output_stream.active:
                self.output_stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    blocksize=self.blocksize,
                    callback=self._play_callback
                )
                self.output_stream.start()
            print("“听”功能已开启（接收+播放）")
        else:
            # 关闭“听”：停止播放流，清空播放队列
            if self.output_stream and self.output_stream.active:
                self.output_stream.stop()
            # 清空队列
            while not self.play_queue.empty():
                self.play_queue.get_nowait()
            print("“听”功能已关闭（接收+播放）")

    # ------------------------------
    # 发送循环（仅“说”开启时运行）
    # ------------------------------
    def _send_loop(self):
        """持续从采集队列读取数据，编码为JSON后通过UDP发送"""
        while self.is_running:
            if self.send_enabled:
                try:
                    audio_data = self.record_queue.get(timeout=0.1)
                    json_dict = self.audio_to_json(audio_data)
                    self.udp_send_func(json_dict)  # 调用你的UDP发送函数
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"音频发送失败：{e}", flush=True)
                    continue
            else:
                # “说”关闭时，短暂休眠减少CPU占用
                import time
                time.sleep(0.1)

    # ------------------------------
    # 外部对接接口（与你的UDP接收逻辑对接）
    # ------------------------------
    def handle_recv_json(self, json_dict: Dict[str, Any]):
        """
        【给你调用的接口】你的UDP收到JSON后，调用此函数
        仅当“听”开启时，才解码并播放
        """
        if not self.recv_enabled:
            return  # “听”关闭时，直接忽略音频消息

        # JSON → 音频数组
        audio_data = self.json_to_audio(json_dict)
        if audio_data is None:
            return

        # 可选：自定义回调（如日志、保存）
        if self.on_audio_recv:
            self.on_audio_recv(audio_data)

        # 加入播放队列（仅“听”开启时）
        try:
            self.play_queue.put_nowait(audio_data)
        except queue.Full:
            self.play_queue.get_nowait()
            self.play_queue.put_nowait(audio_data)

    # ------------------------------
    # 整体启停控制
    # ------------------------------
    def start(self):
        """启动整体服务（需后续通过 enable_send/enable_recv 开启具体功能）"""
        if self.is_running:
            print("音频服务已在运行中")
            return

        self.is_running = True
        print("音频服务已启动（默认“听”“说”均关闭，需手动开启）")

    def stop(self):
        """停止所有功能（包括“听”“说”和线程）"""
        if not self.is_running:
            return

        # 先关闭所有开关
        self.send_enabled = False
        self.recv_enabled = False

        # 停止线程和流
        self.is_running = False
        if self.input_stream and self.input_stream.active:
            self.input_stream.stop()
            self.input_stream.close()
        if self.output_stream and self.output_stream.active:
            self.output_stream.stop()
            self.output_stream.close()

        # 清空队列
        for q in [self.record_queue, self.play_queue]:
            while not q.empty():
                q.get_nowait()

        print("音频服务已完全停止")


# ------------------------------
# 对接示例（模拟你的UDP逻辑+独立开关控制）
# ------------------------------
def demo_your_udp_with_switches():
    """模拟你的UDP JSON通信 + 音频类独立开关控制"""
    import socket
    import threading
    import time

    # UDP配置（替换为你的实际配置）
    LOCAL_IP = "0.0.0.0"
    LOCAL_PORT = 8888
    REMOTE_IP = "192.168.1.100"  # 对方IP
    REMOTE_PORT = 9999  # 对方端口

    # 1. 初始化你的UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((LOCAL_IP, LOCAL_PORT))
    udp_socket.settimeout(0.1)

    # 2. 你的UDP发送函数（已实现）
    def your_udp_send_func(json_dict):
        json_str = json.dumps(json_dict)
        udp_socket.sendto(json_str.encode("utf-8"), (REMOTE_IP, REMOTE_PORT))

    # 3. 初始化音频处理类（传入你的UDP发送函数）
    audio_handler = AudioJSONHandler(
        sample_rate=16000,
        channels=1,
        dtype="int16",
        blocksize=512,
        udp_send_func=your_udp_send_func,
        on_audio_recv=lambda x: print(f"收到音频块：{x.shape}")  # 可选回调
    )

    # 4. 你的UDP接收循环（已实现）
    def udp_recv_loop():
        print("UDP接收循环已启动")
        while audio_handler.is_running:
            try:
                data, addr = udp_socket.recvfrom(4096)
                json_str = data.decode("utf-8")
                json_dict = json.loads(json_str)
                # 收到JSON后，调用音频类的处理接口
                audio_handler.handle_recv_json(json_dict)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"UDP接收异常：{e}", flush=True)
                continue

    # 5. 启动音频服务和UDP接收循环
    audio_handler.start()
    recv_thread = threading.Thread(target=udp_recv_loop, daemon=True)
    recv_thread.start()

    # 6. 模拟独立开关控制（实际使用时，可通过UI/命令行调用）
    try:
        print("\n===== 控制说明 =====")
        print("1. 输入 'send on' 开启“说”（采集+发送）")
        print("2. 输入 'send off' 关闭“说”")
        print("3. 输入 'recv on' 开启“听”（接收+播放）")
        print("4. 输入 'recv off' 关闭“听”")
        print("5. 输入 'quit' 退出")
        print("====================\n")

        while audio_handler.is_running:
            cmd = input("请输入命令：").strip().lower()
            if cmd == "send on":
                audio_handler.enable_send(enable=True)
            elif cmd == "send off":
                audio_handler.enable_send(enable=False)
            elif cmd == "recv on":
                audio_handler.enable_recv(enable=True)
            elif cmd == "recv off":
                audio_handler.enable_recv(enable=False)
            elif cmd == "quit":
                break
            else:
                print("无效命令！请输入 'send on/off' 'recv on/off' 或 'quit'")
    except KeyboardInterrupt:
        print("\n收到停止信号")
    finally:
        audio_handler.stop()
        udp_socket.close()
        print("UDP连接已关闭")


if __name__ == "__main__":
    # 运行示例（模拟完整流程）
    demo_your_udp_with_switches()