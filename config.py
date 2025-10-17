# config.py
import os
from datetime import datetime
import configparser


# --- 配置加载器 ---
config = configparser.ConfigParser()
config_path = "./config.ini"
if not os.path.exists(config_path):
    raise FileNotFoundError(f"配置文件 'config.ini' 未在程序目录中找到！")
config.read(config_path, encoding='utf-8')


# --- Caption Source Settings ---
# Windows Live Captions
CAPTION_APP_PATH = os.getenv('caption_path', 'C:\\Windows\\System32\\livecaptions.exe')
CAPTION_WINDOW_TITLE = '实时辅助字幕'
CAPTION_CONTROL_TYPE = "Text"
MAX_INPUT_WORDS = 300  # 从窗口截取的最大单词数
SENTENCES_TO_TRANSLATE = 3  # 每次从窗口发送给模型的句子数 最后一句是不完整句子 不建议设置1
HIDE_LIVECAPTIONS_WINDOW = config.getboolean("Display_set", "hide_livecaptions_window")

# --- Extended Feature Settings ---
RESET_PUNCTUATION = False  # 重置标点

# --- Model Settings ---
MODEL_PATH = "models/ERNIE-4.5-21B-A3B-PT-UD-Q3_K_XL.gguf"

# --- Llama.cpp Loader/Completion Configuration ---
LLAMA_CONFIG = {
    'model_path': MODEL_PATH,
    'verbose': False,
    'n_gpu_layers': config.getint('LLM', 'n_gpu_layers'),
    'n_ctx': config.getint('LLM', 'n_ctx'),
    'n_threads': 6,
    'seed': 25,
    'use_mmap': True,
    'use_mlock': True,
    'flash_attn': config.getboolean('LLM', 'flash_attn')
}

COMPLETION_CONFIG = {
    'temperature': config.getfloat('COMPLETION_CONFIG', 'temperature'),
    'max_tokens': config.getint('COMPLETION_CONFIG', 'max_tokens'),
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
    'temperature': config.getfloat('LIVE_CONFIG', 'temperature'),
    'max_tokens': config.getint('LIVE_CONFIG', 'max_tokens'),
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
DRIVERS = """
| ID | Driver            | Nat. | Car          |
|----|-------------------|------|--------------|
| 1  | Oscar Piastri     | AUS  | McLaren      |
| 2  | Lando Norris      | GBR  | McLaren      |
| 3  | Max Verstappen    | NED  | Red Bull     |
| 4  | George Russell    | GBR  | Mercedes     |
| 5  | Charles Leclerc   | MON  | Ferrari      |
| 6  | Lewis Hamilton    | GBR  | Ferrari      |
| 7  | Kimi Antonelli    | ITA  | Mercedes     |
| 8  | Alexander Albon   | THA  | Williams     |
| 9  | Esteban Ocon      | FRA  | Haas         |
| 10 | Lance Stroll      | CAN  | Aston Martin |
| 11 | Carlos Sainz      | ESP  | Williams     |
| 12 | Yuki Tsunoda      | JPN  | Red Bull     |
| 13 | Pierre Gasly      | FRA  | Alpine       |
| 14 | Isack Hadjar      | FRA  | Racing Bulls |
| 15 | Nico Hulkenberg   | GER  | Kick Sauber  |
| 16 | Oliver Bearman    | GBR  | Haas         |
| 17 | Fernando Alonso   | ESP  | Aston Martin |
| 18 | Liam Lawson       | NZL  | Racing Bulls |
| 19 | Gabriel Bortoleto | BRA  | Kick Sauber  |
| 20 | Franco Colapinto  | ARG  | Alpine       |
| 21 | Jack Doohan       | AUS  | Alpine       |
"""

LOCATION = '新加坡'
F1TV_LIVE_INFO = f"""目前播放的是:F1TV，正在直播{LOCATION}大奖赛正赛。车手名单:{DRIVERS}，车手 Yuki Tsunoda 的中文名是：角田裕毅"""
EXTENDED_INFO = """目前播放的是:Sky News"""

# --- System Prompt ---
def get_sys_prompt():
    """动态生成系统提示，确保时间总是最新的"""
    now_str = datetime.now().strftime("%m/%d/%Y, %H:%M")
    # 读取多行 prompt
    raw_prompt = config.get('Prompt', 'sys_prompt').replace('|', '').strip()
    return raw_prompt.format(now=now_str)

# now = datetime.now().strftime("%m/%d/%Y, %H:%M")

SYS_PROMPT = get_sys_prompt()

RAW_SYS_PROMPT = """
你好! 现在是北京时间{now}。
你是我的同声传译助手，请将实时语音转录的英文文本翻译为简洁、自然、准确的中文。
请注意以下几点：
1.**人名规范**：统一格式为'中文译名(英文名)'，如'维斯塔潘(Verstappen)'。
2.**自动纠错**：如语音转录出现 同音/近音单词转录错误，自动修正为最合理的表达。
3.**不完整处理**：当输入不完整时，不确定信息暂用'……'代替，待输入更新补充翻译，不要输出任何额外提示。
4.**立场中立**：忠实翻译文本，禁止发表任何观点、评论。

示例：
The US President Trump said...
美国总统特朗普(Trump)表示……"""



# --- Translation Logic Settings ---
AVAILABLE_TOKENS = config.getint('Logic', 'AVAILABLE_TOKENS')
MAX_TO_UI = 10  # 输出到字幕的句子数
DELAY_TIME = config.getfloat('Logic', 'delay_time')  #翻译间隔，含翻译用时，如果翻译用时超过当前设置，即时开始。延时为模型翻译用时。
TRANSLATOR_CACHE = 10  #翻译缓存

# --- UI Settings ---
INITIAL_WINDOW_GEOMETRY = (390, 700, 1000, 80)  # 初始字幕窗口位置及大小(x, y, width, height)
BACKGROUND_COLOR = (0, 0, 0, 70)  # (R, G, B, A)字幕窗口背景颜色及透明度
FONT_FAMILY =config.get('Display_set', 'FONT_FAMILY')  # 字体系列
FONT_SIZE = config.getint('Display_set', 'FONT_SIZE')  # 字体大小
MAX_WINDOW_WIDTH = 1200  # 最大窗口Width
UPDATE_INTERVAL_MS = 50  # UI刷新率
DISPLAY_LINES = config.getint('Display_set', 'DISPLAY_LINES')  # 显示行数
ScrollBarPolicy = config.getboolean('Display_set', 'ScrollBarPolicy')  # 是否显示滚动条
