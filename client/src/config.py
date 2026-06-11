from pathlib import Path

GAME_NAME = "我不是画神"

CLIENT_VERSION = "0.3_alpha"
CLIENT_VERSION_ = 4


FONT_NAME = "Uranus Pixel 11Px"

ASSETS_PATH = Path(__file__).parent.parent / "assets"
FONTS_PATH = ASSETS_PATH / "fonts"
FONT_PATH = FONTS_PATH /  "Uranus_Pixel_11Px.ttf"
SHADERS_PATH = ASSETS_PATH / "shaders"
IMAGES_PATH = ASSETS_PATH / 'images'
UNITS_IMAGES_PATH = IMAGES_PATH / "units"

#这里有点问题
FONT_PATH = 'assets\\fonts\\Uranus_Pixel_11Px.ttf'

MODE = {
                0:"单线接龙",1:"多线接龙",2:"竞猜",3:"茶绘"
            }

DEBUG = 0