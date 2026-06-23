from queue import Queue

from PyQt5.QtCore import QTimer

from .config import CONFIG_PATH, load_config
from .livecaptions import LiveCaptionsSource
from .settings_ui import SettingsWindow
from .subtitle_window import SubtitleWindow
from .translator_service import TranslatorService


class MainApplication:
    def __init__(self, settings_window: SettingsWindow):
        self.settings_window = settings_window
        self.status_queue = Queue()
        self.subtitle_queue = Queue()
        self.config = load_config(CONFIG_PATH)
        self.captions = LiveCaptionsSource(self.config)
        self.translator: TranslatorService | None = None
        self.subtitle_window: SubtitleWindow | None = None
        self.is_translating = False

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.poll_status)
        self.status_timer.start(100)

    def toggle_translation_process(self) -> None:
        if self.is_translating:
            self.stop_translation_process()
        else:
            self.start_translation_process()

    def start_translation_process(self) -> None:
        if self.is_translating:
            return

        self.config = load_config(CONFIG_PATH)
        self.captions.reload_config(self.config)
        self.settings_window.set_controls_enabled(False)
        self.settings_window.set_status("正在连接实时辅助字幕...")

        ok, message = self.captions.start()
        if not ok:
            self.settings_window.set_status(message, is_error=True)
            self.settings_window.set_controls_enabled(True)
            return

        self.subtitle_queue = Queue()
        self.subtitle_window = SubtitleWindow(self.config, self.subtitle_queue)
        self.subtitle_window.show()

        self.translator = TranslatorService(
            self.config,
            self.captions,
            self.subtitle_queue,
            self.status_queue,
        )
        self.translator.start()
        self.is_translating = True
        self.settings_window.set_status(message)

    def stop_translation_process(self) -> None:
        if not self.is_translating:
            return

        self.settings_window.set_status("正在停止翻译...")
        stopped = True
        if self.translator:
            stopped = self.translator.stop(timeout=5)

        if self.subtitle_window:
            self.subtitle_window.close()

        ok, message = self.captions.shutdown()
        self.translator = None
        self.subtitle_window = None
        self.is_translating = False
        self.settings_window.set_controls_enabled(True)
        self.settings_window.update_token_usage(0, self.config.server.model_context_window)

        if not stopped:
            self.settings_window.set_status("翻译线程停止超时", is_error=True)
        elif not ok:
            self.settings_window.set_status(message, is_error=True)
        else:
            self.settings_window.set_status("翻译已停止")

    def poll_status(self) -> None:
        while not self.status_queue.empty():
            status = self.status_queue.get()
            status_type = status.get("type")
            if status_type == "token_usage":
                self.settings_window.update_token_usage(status["current"], status["total"])
            elif status_type == "error":
                self.settings_window.set_status(status.get("message", "发生错误"), is_error=True)
            elif status_type == "message":
                self.settings_window.set_status(status.get("message", ""))

    def cleanup(self) -> None:
        if self.is_translating:
            self.stop_translation_process()
        self.captions.close()

