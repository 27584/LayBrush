
import arcade.gui.widgets.layout

from src.config import FONT_NAME
CARD_BUTTON_STYLE = {
    # 默认状态

    "normal": {
        "bg": arcade.color.LIGHT_SLATE_GRAY,  # 背景色：浅石板灰
        "font_color": arcade.color.WHITE_SMOKE,  # 浅白字体，高对比
        "border": arcade.color.DARK_SLATE_GRAY,  # 边框色：深石板灰
        "border_width": 2,                          # 边框宽度：2px
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    },
    # 鼠标悬浮状态
    "hover": {
        "bg": arcade.color.SLATE_GRAY,        # 背景色：石板灰（加深）
        "font_color": arcade.color.WHITE,
        "border": arcade.color.BLACK,         # 边框色：黑色（加粗视觉）
        "border_width": 3,                           # 边框宽度：3px（悬浮时变粗）
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    },
    # 鼠标点击状态
    "press": {
        "bg": arcade.color.DARK_SLATE_GRAY,   # 背景色：深石板灰（最深）
        "font_color": arcade.color.WHITE_SMOKE,  # 浅白字体，高对比
        "border": arcade.color.YELLOW,        # 边框色：黄色（点击反馈）
        "border_width": 3,
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    },
    # 禁用状态（可选，需手动设置 button.disabled = True）
    "disabled": {
        "bg": arcade.color.LIGHT_GRAY,
        "font_color": arcade.color.DARK_GRAY,
        "border": arcade.color.DARK_GRAY,
        "border_width": 1,
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    }
}
COMMON_BUTTON_STYLE = {
    # 默认状态

    "normal": {
        "bg": arcade.color.LIGHT_SLATE_GRAY,  # 背景色：浅石板灰
        "font_color": arcade.color.WHITE_SMOKE,  # 浅白字体，高对比
        "border": arcade.color.DARK_SLATE_GRAY,  # 边框色：深石板灰
        "border_width": 2,                          # 边框宽度：2px
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    },
    # 鼠标悬浮状态
    "hover": {
        "bg": arcade.color.SLATE_GRAY,        # 背景色：石板灰（加深）
        "font_color": arcade.color.WHITE,
        "border": arcade.color.BLACK,         # 边框色：黑色（加粗视觉）
        "border_width": 3,                           # 边框宽度：3px（悬浮时变粗）
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    },
    # 鼠标点击状态
    "press": {
        "bg": arcade.color.DARK_SLATE_GRAY,   # 背景色：深石板灰（最深）
        "font_color": arcade.color.WHITE_SMOKE,  # 浅白字体，高对比
        "border": arcade.color.YELLOW,        # 边框色：黄色（点击反馈）
        "border_width": 3,
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    },
    # 禁用状态（可选，需手动设置 button.disabled = True）
    "disabled": {
        "bg": arcade.color.LIGHT_GRAY,
        "font_color": arcade.color.DARK_GRAY,
        "border": arcade.color.DARK_GRAY,
        "border_width": 1,
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    }
}

# 3. 退出按钮单独样式（演示：不同按钮不同样式）
QUIT_BUTTON_STYLE = {
    "normal": {
        "bg": arcade.color.RUBY_RED,
        "font_color": arcade.color.WHITE,
        "border": arcade.color.RED,
        "border_width": 2,
        "padding": (15, 10),
        "font_name": FONT_NAME,
        "font_size": 24
    },
    "hover": {
        "bg": arcade.color.RED,
        "font_color": arcade.color.YELLOW,
        "border": arcade.color.DARK_RED,
        "border_width": 3,
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    },
    "press": {
        "bg": arcade.color.DARK_RED,
        "font_color": arcade.color.WHITE,
        "border": arcade.color.YELLOW,
        "border_width": 3,
        "padding": (15, 10),                        # 内边距：上下15px，左右10px
        "font_name": FONT_NAME,                  # 中文字体
        "font_size": 24                             # 字体大小
    }
}

