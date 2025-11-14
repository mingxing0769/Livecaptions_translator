# E:/Python/PythonProject/main.py

import sys
import threading
from queue import Queue

from PyQt5.QtWidgets import QApplication

import configparser
from livecaptions import Get_text
from settings_ui import SettingsWindow
from subtitlewindow import SubtitleWindow
from translator import Translator


class MainApplication:
    """
    封装主应用程序逻辑，管理窗口、线程和应用状态。
    """
    # <--- 修改：传入 settings_window 实例 ---
    def __init__(self, text_getter: Get_text, settings_window: SettingsWindow):
        self.translator = None
        self.translate_thread = None
        self.subtitle_window = None
        self.text_getter = text_getter
        self.settings_window = settings_window  # 保存对设置窗口的引用

        # <--- 新增：应用状态变量 ---
        self.is_translating = False

    # <--- 新增：切换翻译状态的核心方法 ---
    def toggle_translation_process(self):
        """根据当前状态，开始或停止翻译。"""
        if self.is_translating:
            self.stop_translation_process()
        else:
            self.start_translation_process()

    def start_translation_process(self):
        """
        启动翻译流程：加载配置、创建实例、启动线程和窗口。
        """
        if self.is_translating:
            print("翻译已在运行中。")
            return

        print("收到启动信号，正在初始化翻译程序...")

        # 禁用UI控件并更新按钮文本
        self.settings_window.set_controls_enabled(False)

        # 关键：重新加载 Get_text 的配置，以应用最新的UI设置
        self.text_getter.reload_config()

        # 启动实时辅助字幕程序
        self.text_getter.start_livecaptions_windows()

        # 创建共享的 Queue
        text_data_queue = Queue()

        # 创建并显示字幕窗口
        self.subtitle_window = SubtitleWindow(text_data_queue)
        self.subtitle_window.show()
        print("字幕窗口已显示。")


        # 创建 Translator 实例
        try:
            # 关键：每次启动都重新加载最新的配置
            latest_config = configparser.ConfigParser()
            latest_config.read('config.ini', encoding='utf-8')
            self.translator = Translator(latest_config, text_data_queue, self.text_getter)
        except Exception as e:
            print(f"\033[91m错误：初始化 Translator 失败！请检查模型路径和配置。 {e}\033[0m")
            # 如果初始化失败，需要恢复UI状态
            self.settings_window.set_controls_enabled(True)
            return

        # 创建并启动翻译线程
        # self.translator.model_translate()
        self.translate_thread = threading.Thread(target=self.translator.model_translate)
        self.translate_thread.daemon = True
        self.translate_thread.start()
        print("翻译线程已启动。")

        # <--- 新增：更新状态 ---
        self.is_translating = True

    # <--- 新增：停止翻译流程的方法 ---
    def stop_translation_process(self):
        """安全地停止翻译线程和相关窗口。"""
        if not self.is_translating:
            print("翻译尚未开始。")
            return

        print("收到停止信号，正在停止翻译...")

        # 1. 停止翻译线程
        if self.translator:
            self.translator.stop()

        if self.translate_thread and self.translate_thread.is_alive():
            self.translate_thread.join(timeout=5)  # 等待线程结束
            if self.translate_thread.is_alive():
                print("警告：翻译线程在超时后仍未退出。")
            else:
                print("翻译线程已成功停止。")

        # 2. 关闭字幕窗口
        if self.subtitle_window:
            self.subtitle_window.close()
            print("字幕窗口已关闭。")

        # 关闭实时辅助字幕
        self.text_getter.shutdown()

        # 3. 清理实例
        self.translator = None
        self.translate_thread = None
        self.subtitle_window = None

        # 4. 更新状态并恢复UI
        self.is_translating = False
        self.settings_window.set_controls_enabled(True)
        print("翻译已停止，UI控件已解锁。")

    def cleanup(self):
        """在应用退出前被调用，用于安全地停止所有后台进程。"""
        print("应用程序即将退出...")
        # 如果翻译仍在运行，则停止它
        if self.is_translating:
            self.stop_translation_process()

        # 停止字幕源
        if self.text_getter:
            self.text_getter.shutdown()

        print("清理完成，程序退出。")


def main():
    try:
        app = QApplication(sys.argv)

        # 1. 创建 Get_text 实例并初始化
        get_text_app = Get_text()

        # 2. 创建设置窗口
        settings_window = SettingsWindow()
        settings_window.show()

        # 3. 创建主应用实例，并传入字幕源和设置窗口的引用
        main_app = MainApplication(get_text_app, settings_window)

        # 4. 将设置窗口的 "toggle" 信号连接到主应用的 "toggle" 方法上
        settings_window.toggle_translation_requested.connect(main_app.toggle_translation_process)

        # 5. 连接 aboutToQuit 信号到清理函数，实现优雅退出
        app.aboutToQuit.connect(main_app.cleanup)

        sys.exit(app.exec_())

    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()