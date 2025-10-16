# E:/Python/PythonProject/main.py (最终集成版)

import sys
import threading
import importlib
from queue import Queue
from PyQt5.QtWidgets import QApplication
from livecaptions import Get_text
from settings_ui import SettingsWindow
from subtitlewindow import SubtitleWindow
from translator import Translator
import config


class MainApplication:
    """
    封装主应用程序逻辑，以便在设置完成后启动。
    这有助于管理窗口、线程等对象的生命周期。
    """

    # --- 修改这里 (1/3) ---
    # 让 MainApplication 持有 Get_text 实例
    def __init__(self, text_getter: Get_text):
        self.translator = None
        self.translate_thread = None
        self.subtitle_window = None
        self.text_getter = text_getter  # 保存传入的实例

    def start_translation_process(self):
        """
        这是应用程序的核心启动方法。
        它会在接收到来自设置窗口的信号后被调用。
        """
        print("收到启动信号，正在初始化翻译程序...")

        # 关键步骤：重新加载配置模块
        # 这可以确保刚才在UI上保存的设置被正确加载
        importlib.reload(config)
        print("配置已重新加载。")

        # --- 以下是你原来 main 函数的核心逻辑 ---

        # 创建共享的 Queue
        text_data_queue = Queue()

        # --- 修改这里 (2/3) ---
        # 创建 Translator 实例时，将 text_getter 实例传递进去
        self.translator = Translator(text_data_queue, self.text_getter)

        # 创建并启动翻译线程
        self.translate_thread = threading.Thread(target=self.translator.model_translate)
        self.translate_thread.daemon = True
        self.translate_thread.start()
        print("翻译线程已启动。")

        # 创建并显示字幕窗口
        self.subtitle_window = SubtitleWindow(text_data_queue)
        self.subtitle_window.show()
        print("字幕窗口已显示。")

    def cleanup(self):
        """在应用退出前被调用，用于安全地停止后台线程。"""
        print("应用程序即将退出，正在停止翻译线程...")
        if self.translator:
            self.translator.stop()  # 在 Translator 类中设置停止标志

        if self.translate_thread and self.translate_thread.is_alive():
            # 等待线程最多5秒钟，然后主程序退出
            self.translate_thread.join(timeout=5)
            if self.translate_thread.is_alive():
                print("警告：翻译线程在超时后仍未退出。")
            else:
                print("翻译线程已成功停止。")


def main():
    try:
        app = QApplication(sys.argv)

        # 1. 创建唯一的 Get_text 实例
        get_text_app = Get_text()
        # 2. 初始化它
        get_text_app.start_livecaptions_windows()

        # --- 修改这里 (3/3) ---
        # 3. 将这个唯一的实例传递给 MainApplication
        main_app = MainApplication(get_text_app)

        settings_window = SettingsWindow()

        # 将设置窗口的 "start_requested" 信号连接到主应用的启动方法上
        settings_window.start_requested.connect(main_app.start_translation_process)

        # 连接 aboutToQuit 信号到清理函数，实现优雅退出
        app.aboutToQuit.connect(main_app.cleanup)

        # 显示设置窗口
        settings_window.show()

        # 启动 Qt 事件循环 (PyQt5 中是 exec_())
        sys.exit(app.exec_())

    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()