import concurrent.futures
import os
import subprocess
import time

import psutil
import uiautomation as auto
import win32con
import win32gui
from uiautomation import UIAutomationInitializerInThread

from .caption_tracker import CaptionTracker, CaptionUpdate
from .config import AppConfig


READY_TEXT = "已准备好在 英语(美国) 中显示实时字幕"


class LiveCaptionsSource:
    def __init__(self, config: AppConfig):
        self.config = config
        self.caption_app_path = os.getenv("caption_path", r"C:\Windows\System32\livecaptions.exe")
        self.caption_window_title = "实时辅助字幕"
        self.tracker = CaptionTracker()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def reload_config(self, config: AppConfig) -> None:
        self.config = config

    def start(self) -> tuple[bool, str]:
        try:
            window = auto.WindowControl(Name=self.caption_window_title, searchDepth=1)
            if not window.Exists(0, 0):
                try:
                    subprocess.Popen(self.caption_app_path)
                    time.sleep(2)
                    window = auto.WindowControl(Name=self.caption_window_title, searchDepth=1)
                except FileNotFoundError:
                    return False, f"找不到实时辅助字幕程序: {self.caption_app_path}"

            if not window.Exists(0, 0):
                return False, "实时辅助字幕窗口未出现"

            if self.config.display.hide_livecaptions_window:
                win32gui.SetWindowPos(
                    window.NativeWindowHandle,
                    0,
                    -3000,
                    -3000,
                    0,
                    0,
                    win32con.SWP_NOSIZE | win32con.SWP_NOZORDER,
                )
            return True, "实时辅助字幕已连接"
        except Exception as exc:
            return False, f"连接实时辅助字幕失败: {exc}"

    def shutdown(self) -> tuple[bool, str]:
        try:
            window = auto.WindowControl(Name=self.caption_window_title, searchDepth=1)
            if window.Exists(0, 0):
                process = psutil.Process(window.ProcessId)
                process.terminate()
                process.wait(timeout=2)
                return True, "实时辅助字幕已关闭"
            return True, "未找到实时辅助字幕窗口"
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            return False, "关闭实时辅助字幕时进程已不存在或超时"
        except Exception as exc:
            return False, f"关闭实时辅助字幕失败: {exc}"

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def get_text(self) -> str:
        try:
            future = self._executor.submit(self._fetch_text)
            text = future.result(timeout=0.5)
            if not text:
                window = auto.WindowControl(Name=self.caption_window_title, searchDepth=1)
                if not window.Exists(0, 0):
                    self.start()
            return self._normalize_text(text)
        except concurrent.futures.TimeoutError:
            return ""
        except Exception:
            return ""

    def process_text(self, raw_text: str) -> CaptionUpdate:
        return self.tracker.process(raw_text)

    def _fetch_text(self) -> str:
        with UIAutomationInitializerInThread():
            window = auto.WindowControl(Name=self.caption_window_title, searchDepth=1)
            if window.Exists(0, 0):
                text_control = window.TextControl()
                if text_control.Exists(0, 0):
                    return text_control.Name or ""
        return ""

    def _normalize_text(self, text: str) -> str:
        words = (text or "").replace(READY_TEXT, "").replace("\n", " ").split()
        return " ".join(words[-self.config.logic.max_input_words:]).strip()

