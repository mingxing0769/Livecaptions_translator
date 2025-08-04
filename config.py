# config.py
import os

# --- Caption Source Settings ---
# Windows Live Captions
CAPTION_APP_PATH = os.getenv('caption_path', 'C:\\Windows\\System32\\livecaptions.exe')
CAPTION_WINDOW_TITLE = '实时辅助字幕'
CAPTION_CONTROL_TYPE = "Text"
MAX_INPUT_WORDS = 200  # 从窗口截取的最大单词数
SENTENCES_TO_TRANSLATE = 3  # 每次从窗口发送给模型的句子数

# --- Model Settings ---
MODEL_PATH = "models/deepseek-v2-lite-chat-q5_k_m.gguf"

# --- Llama.cpp Loader/Completion Configuration ---
LLAMA_CONFIG = {
    'model_path': MODEL_PATH,
    'verbose': False,
    'n_gpu_layers': -1,
    'n_ctx': 4096,
    'n_threads': 6,
    'use_mmap': True,
    'use_mlock': True,
    'n_batch': 64,
    'n_ubatch': 64,
    # 'op_offloat': True,
    # 'swa_ful': True,
    'flash_attn': False  # deepseek开启flash_attn 会引起CPU占用率100%
}

COMPLETION_CONFIG = {
    'temperature': 0.6,
    'max_tokens': 128,
    'top_k': 40,
    'top_p': 0.95,
    'min_p': 0.05,
    'typical_p': 1.0,
    'repeat_penalty': 1.0,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}

LIVE_COMPLETION_CONFIG = {
    'temperature': 0.3,
    'max_tokens': 128,
    'top_k': 10,
    'top_p': 0.95,
    'min_p': 0.05,
    'typical_p': 1.0,
    'repeat_penalty': 1.0,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}

# --- System Prompt ---
SYS_PROMPT = """你是优秀的翻译助手，任务非常艰巨，因为输入的是实时语音转录的文本，1：音频转录时包含多人的声音，转录软件并不能正确识别，因此断句不一定合理；2：转录时非常可能出现相似音单词转录错误。这两点都可能让你误解意思。因此你的任务是联系上下文，尽量将当前输入的正确语义翻译为中文。
要求：
1. 译文流畅、连贯，符合中文表达习惯。
2. 不添加任何解释或评论。

示例：
输入: The US President Trump said...
输出: 美国总统 Trump 说过…

希望你能完美的完成任务，加油！现在开始：
"""

LIVE_PROMPT = """请继续将英文翻译为中文，仅输出译文不添加任何解释或评论：\n"""

# --- Translation Logic Settings ---
MESSAGES_PRUNE_THRESHOLD = 0.7  # 总计tokens / n_ctx 占用比 达到该值时清理历史
MAX_TO_UI = 10  # 输出到字幕的句子数
DELAY_TIME = 1.0  #翻译间隔，含翻译用时，如果翻译用时超过当前设置，即时开始。延时为模型翻译用时。
TRANSLATOR_CACHE = 10  #翻译缓存

# --- UI Settings ---
INITIAL_WINDOW_GEOMETRY = (390, 700, 1000, 80)  # 初始字幕窗口位置及大小(x, y, width, height)
BACKGROUND_COLOR = (0, 0, 0, 70)  # (R, G, B, A)字幕窗口背景颜色及透明度
FONT_FAMILY = "微软雅黑"  # 字体
FONT_SIZE = 17  # 字体大小
MAX_WINDOW_WIDTH = 1200  # 最大窗口Width
UPDATE_INTERVAL_MS = 50  # UI刷新率
DISPLAY_LINES = 3  #字幕显示行数
ScrollBarPolicy = False  #是否显示滚动条
