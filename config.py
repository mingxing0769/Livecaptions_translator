# config.py
import os
from datetime import datetime

#Current Date Time
now = datetime.now()

# --- Caption Source Settings ---
# Windows Live Captions
CAPTION_APP_PATH = os.getenv('caption_path', 'C:\\Windows\\System32\\livecaptions.exe')
CAPTION_WINDOW_TITLE = '实时辅助字幕'
CAPTION_CONTROL_TYPE = "Text"
MAX_INPUT_WORDS = 300  # 从窗口截取的最大单词数
SENTENCES_TO_TRANSLATE = 3  # 每次从窗口发送给模型的句子数

# --- Extended Feature Settings ---
RESET_PUNCTUATION = False  # 重置标点

# --- Model Settings ---
MODEL_PATH = "models/ERNIE-4.5-21B-A3B-PT-UD-Q3_K_XL.gguf"

# --- Llama.cpp Loader/Completion Configuration ---
LLAMA_CONFIG = {
    'model_path': MODEL_PATH,
    'verbose': False,
    'n_gpu_layers': -1,
    'n_ctx': 8192,
    'n_threads': 6,
    'seed': 25,
    'use_mmap': True,
    'use_mlock': True,
    'flash_attn': False
}

COMPLETION_CONFIG = {
    'temperature': 0.6,
    'max_tokens': 128,
    'seed': 55,
    'top_k': 40,
    'top_p': 0.95,
    'min_p': 0.05,
    'typical_p': 1.0,
    'repeat_penalty': 1.0,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}

LIVE_CONFIG = {
    'temperature': 0.3,
    'max_tokens': 64,
    'seed': 55,
    'top_k': 20,
    'top_p': 0.95,
    'min_p': 0.05,
    'typical_p': 1.0,
    'repeat_penalty': 1.0,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}

# --- System Prompt ---
SYS_PROMPT = f"""你好！现在是中国时间:{now.strftime("%m/%d/%Y, %H:%M")}。
你是我的同声传译助手，请将实时语音转录的英文文本翻译为简洁、自然、准确的中文。
请注意以下几点：
1.**人名规范**：统一格式为'中文译名(英文原名)'，如'维斯塔潘(Verstappen)'。
2.**自动纠错**：如语音转录出现 同音/近音单词转录错误或语法错误，自动修正为最合理的表达。
3.**不完整处理**：当输入不完整时，不确定信息暂用'……'代替，待输入更新补充翻译，不要输出任何额外提示。
4.**翻译一致**：连续翻译时，尽量保持与上下文一致性。
5.**立场中立**：忠实翻译文本，禁止发表任何观点、评论。

示例：
The US President Trump said...
美国总统 特朗普(Trump) 表示……
"""

# --- Translation Logic Settings ---
AVAILABLE_TOKENS = 256  # n_ctx-total_tokens<AVAILABLE_TOKENS 时重置历史记录
MAX_TO_UI = 10  # 输出到字幕的句子数
DELAY_TIME = 1.0  #翻译间隔，含翻译用时，如果翻译用时超过当前设置，即时开始。延时为模型翻译用时。
TRANSLATOR_CACHE = 10  #翻译缓存

# --- UI Settings ---
INITIAL_WINDOW_GEOMETRY = (390, 700, 1000, 80)  # 初始字幕窗口位置及大小(x, y, width, height)
BACKGROUND_COLOR = (0, 0, 0, 70)  # (R, G, B, A)字幕窗口背景颜色及透明度
FONT_FAMILY = "微软雅黑"  # 字体
FONT_SIZE = 14  # 字体大小
MAX_WINDOW_WIDTH = 1200  # 最大窗口Width
UPDATE_INTERVAL_MS = 50  # UI刷新率
DISPLAY_LINES = 3  #字幕显示行数
ScrollBarPolicy = False  #是否显示滚动条


