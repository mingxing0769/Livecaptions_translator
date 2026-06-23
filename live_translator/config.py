import configparser
import shutil
from dataclasses import dataclass
from pathlib import Path


CONFIG_PATH = Path("config.ini")
SERVER_SECTION = "Server"
LEGACY_SERVER_SECTION = "Sever"


@dataclass(frozen=True)
class ServerConfig:
    base_url: str
    api_key: str
    model: str
    model_context_window: int


@dataclass(frozen=True)
class LogicConfig:
    available_tokens: int
    delay_time: float
    active_prompt: str
    max_input_words: int
    translator_cache: int


@dataclass(frozen=True)
class DisplayConfig:
    font_family: str
    font_size: int
    display_lines: int
    scrollbar_policy: bool
    hide_livecaptions_window: bool
    update_interval_ms: int
    x: int
    y: int
    width: int
    height: int
    background_color: str
    max_window_width: int


@dataclass(frozen=True)
class AppConfig:
    parser: configparser.ConfigParser
    path: Path
    server: ServerConfig
    logic: LogicConfig
    display: DisplayConfig
    completion_config: dict
    live_config: dict

    def prompt_sections(self) -> list[str]:
        return [section for section in self.parser.sections() if section.startswith("Prompt_")]

    def system_prompt(self, now_text: str) -> str:
        section = self.logic.active_prompt
        if not self.parser.has_section(section):
            sections = self.prompt_sections()
            section = sections[0] if sections else ""
        raw_prompt = self.parser.get(section, "content", fallback="")
        return raw_prompt.format(now=now_text)


def load_config(path: Path | str = CONFIG_PATH, migrate: bool = True) -> AppConfig:
    config_path = Path(path)
    parser = configparser.ConfigParser()
    if config_path.exists():
        parser.read(config_path, encoding="utf-8")
    else:
        parser.read_dict(default_config_dict())
        write_config(parser, config_path)

    changed = normalize_config(parser)
    if changed and migrate:
        backup_path = config_path.with_suffix(config_path.suffix + ".bak")
        if config_path.exists() and not backup_path.exists():
            shutil.copy2(config_path, backup_path)
        write_config(parser, config_path)

    return build_app_config(parser, config_path)


def write_config(parser: configparser.ConfigParser, path: Path | str = CONFIG_PATH) -> None:
    with Path(path).open("w", encoding="utf-8") as file:
        parser.write(file)


def normalize_config(parser: configparser.ConfigParser) -> bool:
    changed = False
    defaults = default_config_dict()

    if parser.has_section(LEGACY_SERVER_SECTION):
        if not parser.has_section(SERVER_SECTION):
            parser.add_section(SERVER_SECTION)
            changed = True
        for key, value in parser.items(LEGACY_SERVER_SECTION):
            parser.set(SERVER_SECTION, key, value)
            changed = True
        parser.remove_section(LEGACY_SERVER_SECTION)
        changed = True

    for section, values in defaults.items():
        if not parser.has_section(section):
            parser.add_section(section)
            changed = True
        for key, value in values.items():
            if not parser.has_option(section, key):
                parser.set(section, key, str(value))
                changed = True

    return changed


def build_app_config(parser: configparser.ConfigParser, path: Path) -> AppConfig:
    return AppConfig(
        parser=parser,
        path=path,
        server=ServerConfig(
            base_url=parser.get(SERVER_SECTION, "base_url", fallback=""),
            api_key=parser.get(SERVER_SECTION, "api_key", fallback=""),
            model=parser.get(SERVER_SECTION, "model", fallback=""),
            model_context_window=parser.getint(SERVER_SECTION, "model_context_window", fallback=4096),
        ),
        logic=LogicConfig(
            available_tokens=parser.getint("Logic", "available_tokens", fallback=256),
            delay_time=parser.getfloat("Logic", "delay_time", fallback=1.0),
            active_prompt=parser.get("Logic", "active_prompt", fallback="Prompt_General"),
            max_input_words=parser.getint("Logic", "max_input_words", fallback=300),
            translator_cache=parser.getint("Logic", "translator_cache", fallback=10),
        ),
        display=DisplayConfig(
            font_family=parser.get("Display_set", "font_family", fallback="微软雅黑"),
            font_size=parser.getint("Display_set", "font_size", fallback=15),
            display_lines=parser.getint("Display_set", "display_lines", fallback=3),
            scrollbar_policy=parser.getboolean("Display_set", "scrollbarpolicy", fallback=False),
            hide_livecaptions_window=parser.getboolean("Display_set", "hide_livecaptions_window", fallback=True),
            update_interval_ms=parser.getint("Display_set", "update_interval_ms", fallback=50),
            x=parser.getint("Display_set", "x", fallback=390),
            y=parser.getint("Display_set", "y", fallback=700),
            width=parser.getint("Display_set", "width", fallback=1000),
            height=parser.getint("Display_set", "height", fallback=80),
            background_color=parser.get("Display_set", "background_color", fallback="0, 0, 0, 70"),
            max_window_width=parser.getint("Display_set", "max_window_width", fallback=1200),
        ),
        completion_config=parse_llm_config(parser, "COMPLETION_CONFIG"),
        live_config=parse_llm_config(parser, "LIVE_CONFIG"),
    )


def parse_llm_config(parser: configparser.ConfigParser, section: str) -> dict:
    parsed = {}
    if not parser.has_section(section):
        return parsed
    for key, value in parser.items(section):
        value = value.strip()
        try:
            parsed[key] = float(value) if "." in value else int(value)
        except ValueError:
            parsed[key] = value
    return parsed


def default_config_dict() -> dict[str, dict[str, str]]:
    return {
        "COMPLETION_CONFIG": {
            "max_tokens": "512",
            "top_p": "0.95",
            "temperature": "0.8",
            "seed": "42",
        },
        "LIVE_CONFIG": {
            "temperature": "0.6",
            "max_tokens": "512",
            "top_p": "0.95",
            "seed": "42",
        },
        "Logic": {
            "available_tokens": "128",
            "delay_time": "0.8",
            "active_prompt": "Prompt_F1",
            "max_input_words": "300",
            "translator_cache": "10",
        },
        "Display_set": {
            "font_family": "微软雅黑",
            "font_size": "15",
            "display_lines": "3",
            "scrollbarpolicy": "False",
            "hide_livecaptions_window": "False",
            "update_interval_ms": "50",
            "x": "390",
            "y": "700",
            "width": "1000",
            "height": "80",
            "background_color": "0, 0, 0, 70",
            "max_window_width": "1200",
        },
        SERVER_SECTION: {
            "base_url": "http://127.0.0.1:5000/v1",
            "api_key": "lm-studio",
            "model": "publisher@q3_k_xl",
            "model_context_window": "8192",
        },
        "Prompt_General": {
            "name": "通用翻译",
            "content": "你好! 现在是北京时间{now}。\n你是我的同声传译助手，请将英文文本翻译为简洁、自然、准确的中文。",
        },
        "Prompt_F1": {
            "name": "F1赛事专用",
            "content": "你好! 现在是北京时间{now}。\n你是我的F1赛事同声传译助手，请将F1赛事英文评论翻译为简洁、专业、准确的中文。",
        },
        "Prompt_自定义": {
            "name": "自定义",
            "content": "",
        },
    }
