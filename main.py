import sys
import threading
from queue import Queue
from PyQt5.QtWidgets import QApplication
from subtitlewindow import SubtitleWindow
from translator import Translator


def main():
    try:
        app = QApplication(sys.argv)

        # 1. 在 main 函数中创建共享的 Queue
        text_data_queue = Queue()

        # 2. 创建 Translator 实例，并将队列“注入”进去
        translator = Translator(text_data_queue)

        # 3. 创建并启动翻译线程，将 translator.model_translate 作为目标
        translate_thread = threading.Thread(target=translator.model_translate)
        translate_thread.daemon = True  # 确保主程序退出时，线程也会退出
        translate_thread.start()

        # 4. 创建字幕窗口，同样将队列传入
        window = SubtitleWindow(text_data_queue)
        window.show()

        # 5. 启动 Qt 的事件循环，并确保程序能干净地退出
        sys.exit(app.exec_())

    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()