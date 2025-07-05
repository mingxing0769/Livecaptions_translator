# config.py
import os

# --- Caption Source Settings ---
# Windows Live Captions
CAPTION_APP_PATH = os.getenv('caption_path', 'C:\\Windows\\System32\\livecaptions.exe')
CAPTION_WINDOW_TITLE = '实时辅助字幕'
CAPTION_CONTROL_TYPE = "Text"
MAX_INPUT_WORDS = 500  # 从窗口截取的最大单词数
SENTENCES_TO_TRANSLATE = 3  # 每次从窗口发送给模型的句子数

# --- Model Settings ---

MODEL_PATH = 'models/deepseek-v2-lite-chat-q4_k_m.gguf'
# models/deepseek-v2-lite-chat-q5_k_m.gguf
# models/Qwen2_5/7B/qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf


# --- Llama.cpp Loader/Completion Configuration ---
LLAMA_CONFIG = {
    'model_path': MODEL_PATH,
    'verbose': False,
    'n_gpu_layers': -1,
    'n_ctx': 1024 + 512,
    'n_threads': 6,
    'use_mmap': True,
    'use_mlock': True,
    'n_batch': 64,
    'n_ubatch': 64,
    'flash_attn': True if 'deepseek' not in MODEL_PATH else False
}

COMPLETION_CONFIG = {
    'temperature': 1.0,
    'max_tokens': 128,
    'top_k': 40,
    'top_p': 0.95,
    'min_p': 0.05,
    'typical_p': 1.0,
    'repeat_penalty': 1.1,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}

LIVE_COMPLETION_CONFIG = {
    'temperature': 0.3,
    'max_tokens': 128,
    'top_k': 20,
    'top_p': 0.85,
    'min_p': 0.15,
    'typical_p': 1.0,
    'repeat_penalty': 1.1,
    'presence_penalty': 0.0,
    'frequency_penalty': 0.0
}

# --- System Prompt ---
SYS_PROMPT = """你是优秀的翻译助手，任务是结合对话历史，及当时语境，将输入的英文意思翻译为中文。请严格遵循示例及以下规则：
1.当句子语义不完整时，暂用'…'代替，待下次翻译后更新替换；
2.输入为语音转录，可能存在识别错误，辨识后自动修正翻译；
3.任务仅为翻译，严禁发表任何观点、评论、解释。

示例：
The US President Trump said...
美国总统 Trump 表示…
"""

PROMPT_1 = """请按照系统指令中的示例，将英文翻译为中文，无需输出额外提示、提醒：\n"""

PROMPT_2 = """请结合对话历史，将英文翻译为中文，仅回复翻译后的中文，无需输出额外提示、提醒：\n"""

# --- Translation Logic Settings ---
MESSAGES_PRUNE_THRESHOLD = 0.75  # 总计tokens / n_ctx 占用比 达到该值时清理历史
MAX_TO_UI = 10  # 输出到字幕的句子数
DELAY_TIME = 1  #延时秒:上次开始翻译到下次翻译开始的时间,包含翻译用时，如果翻译用时超过当前设置，即时开始
TRANSLATOR_CACHE = 10  #翻译缓存



# --- UI Settings ---
INITIAL_WINDOW_GEOMETRY = (390, 700, 1200, 80)  # (x, y, width, height)
BACKGROUND_COLOR = (0, 0, 0, 70)  # (R, G, B, A)背景透明度
FONT_FAMILY = "微软雅黑"
FONT_SIZE = 17
MAX_WINDOW_WIDTH = 1200  # 最大窗口Width
UPDATE_INTERVAL_MS = 50  # UI刷新率
DISPLAY_LINES = 3  #字幕显示行数
ScrollBarPolicy = False  #是否显示滚动条
