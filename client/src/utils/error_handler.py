import tkinter as tk
from tkinter import messagebox, scrolledtext, font
import traceback
import sys
import threading
import os

class ErrorHandler:
    # 定义样式常量
    PRIMARY_COLOR = '#3498db'
    SECONDARY_COLOR = '#2c3e50'
    BACKGROUND_COLOR = '#f8f9fa'
    ERROR_COLOR = '#e74c3c'
    TEXT_COLOR = '#333333'
    DETAILS_BG_COLOR = '#ffffff'
    BUTTON_HOVER_COLOR = '#2980b9'

    @staticmethod
    def show_error_window(title, message, error_details=None):
        """显示美化的错误窗口"""
        # 在主线程中创建GUI
        def create_error_window():
            root = tk.Tk()
            root.title(title)
            root.geometry('1200x800')
            root.resizable(False, False)
            root.configure(bg=ErrorHandler.BACKGROUND_COLOR)
            root.iconbitmap(default='assets/icon.ico')  # 尝试加载应用图标

            # 设置窗口居中
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
            x = (root.winfo_screenwidth() // 2) - (width // 2)
            y = (root.winfo_screenheight() // 2) - (height // 2)
            root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

            # 创建标题栏框架
            title_frame = tk.Frame(root, bg=ErrorHandler.SECONDARY_COLOR, height=50)
            title_frame.pack(fill=tk.X)

            # 错误图标
            try:
                # 尝试创建一个简单的错误图标
                error_icon = tk.Canvas(title_frame, width=30, height=30, bg=ErrorHandler.SECONDARY_COLOR, highlightthickness=0)
                error_icon.pack(side=tk.LEFT, padx=10, pady=10)
                error_icon.create_oval(5, 5, 25, 25, fill=ErrorHandler.ERROR_COLOR, outline='white')
                error_icon.create_text(15, 15, text='!', fill='white', font=('Arial', 16, 'bold'))
            except Exception as e:
                print(f"无法创建错误图标: {e}")

            # 标题标签
            title_label = tk.Label(title_frame, text=title, bg=ErrorHandler.SECONDARY_COLOR,
                                  fg='white', font=('Microsoft YaHei', 12, 'bold'))
            title_label.pack(side=tk.LEFT, padx=10)

            # 错误消息框架
            msg_frame = tk.Frame(root, bg=ErrorHandler.BACKGROUND_COLOR)
            msg_frame.pack(padx=20, pady=15, fill=tk.BOTH, expand=False)

            # 错误消息标签
            msg_label = tk.Label(msg_frame, text=message, bg=ErrorHandler.BACKGROUND_COLOR,
                                fg=ErrorHandler.TEXT_COLOR, font=('Microsoft YaHei', 11), wraplength=600)
            msg_label.pack(anchor=tk.W)

            # 分隔线
            separator = tk.Frame(root, height=2, bg=ErrorHandler.PRIMARY_COLOR)
            separator.pack(fill=tk.X, padx=20)

            # 错误详情框架
            details_frame = tk.Frame(root, bg=ErrorHandler.BACKGROUND_COLOR)
            details_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

            # 详情标签
            details_label = tk.Label(details_frame, text='错误详情:', bg=ErrorHandler.BACKGROUND_COLOR,
                                    fg=ErrorHandler.SECONDARY_COLOR, font=('Microsoft YaHei', 10, 'bold'))
            details_label.pack(anchor=tk.W)

            # 创建样式化的文本框
            text_font = font.Font(family='Courier New', size=10)
            details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                    font=text_font, bg=ErrorHandler.DETAILS_BG_COLOR,
                                                    fg=ErrorHandler.TEXT_COLOR, borderwidth=1,
                                                    relief=tk.SUNKEN, highlightbackground=ErrorHandler.PRIMARY_COLOR)
            details_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            details_text.insert(tk.END, error_details or '无可用详情')
            details_text.config(state=tk.DISABLED)  # 设为只读

            # 按钮框架
            btn_frame = tk.Frame(root, bg=ErrorHandler.BACKGROUND_COLOR)
            btn_frame.pack(padx=20, pady=15, fill=tk.X)

            # 复制按钮
            copy_btn = tk.Button(btn_frame, text='复制错误信息', bg=ErrorHandler.PRIMARY_COLOR,
                                fg='white', font=('Microsoft YaHei', 10), relief=tk.FLAT,
                                command=lambda: copy_to_clipboard(details_text, root))
            copy_btn.pack(side=tk.LEFT, padx=5)
            # 添加悬停效果
            copy_btn.bind('<Enter>', lambda e: copy_btn.config(bg=ErrorHandler.BUTTON_HOVER_COLOR))
            copy_btn.bind('<Leave>', lambda e: copy_btn.config(bg=ErrorHandler.PRIMARY_COLOR))

            # 确定按钮
            ok_btn = tk.Button(btn_frame, text='确定', bg=ErrorHandler.SECONDARY_COLOR,
                              fg='white', font=('Microsoft YaHei', 10), relief=tk.FLAT,
                              command=root.destroy)
            ok_btn.pack(side=tk.RIGHT, padx=5)
            # 添加悬停效果
            ok_btn.bind('<Enter>', lambda e: ok_btn.config(bg='#34495e'))
            ok_btn.bind('<Leave>', lambda e: ok_btn.config(bg=ErrorHandler.SECONDARY_COLOR))

            root.mainloop()

        def copy_to_clipboard(text_widget, root_window):
            text = text_widget.get(1.0, tk.END)
            root_window.clipboard_clear()
            root_window.clipboard_append(text)
            # 创建自定义提示框
            msg_window = tk.Toplevel(root_window)
            msg_window.title('提示')
            msg_window.geometry('200x100')
            msg_window.resizable(False, False)
            msg_window.configure(bg=ErrorHandler.BACKGROUND_COLOR)
            # 居中显示
            msg_window.update_idletasks()
            width = msg_window.winfo_width()
            height = msg_window.winfo_height()
            x = (root_window.winfo_x() + root_window.winfo_width() // 2) - (width // 2)
            y = (root_window.winfo_y() + root_window.winfo_height() // 2) - (height // 2)
            msg_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

            msg_label = tk.Label(msg_window, text='错误信息已复制到剪贴板',
                                bg=ErrorHandler.BACKGROUND_COLOR, fg=ErrorHandler.SECONDARY_COLOR,
                                font=('Microsoft YaHei', 10))
            msg_label.pack(pady=20)

            ok_button = tk.Button(msg_window, text='确定', bg=ErrorHandler.PRIMARY_COLOR,
                                 fg='white', font=('Microsoft YaHei', 10), relief=tk.FLAT,
                                 command=msg_window.destroy)
            ok_button.pack()
            ok_button.bind('<Enter>', lambda e: ok_button.config(bg=ErrorHandler.BUTTON_HOVER_COLOR))
            ok_button.bind('<Leave>', lambda e: ok_button.config(bg=ErrorHandler.PRIMARY_COLOR))

        # 确保在主线程中运行
        if threading.current_thread().name == 'MainThread':
            create_error_window()
        else:
            # 如果在非主线程，使用invoke()
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            root.after(0, lambda: [create_error_window(), root.destroy()])
            root.mainloop()

    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        """处理全局异常"""
        # 忽略 KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 格式化错误信息
        error_message = f'{exc_type.__name__}: {exc_value}'
        error_details = ''.join(traceback.format_tb(exc_traceback)) + f'\n{error_message}'

        # 显示错误窗口
        ErrorHandler.show_error_window('错误', error_message, error_details)

        # 调用原始的异常处理函数
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    @staticmethod
    def setup_global_handler():
        """设置全局异常处理器"""
        sys.excepthook = ErrorHandler.handle_exception

# 测试代码
if __name__ == '__main__':
    # 设置全局异常处理
    ErrorHandler.setup_global_handler()

    # 测试异常
    raise ValueError('这是一个测试错误')