import sys
import traceback

from PyQt5.QtWidgets import QApplication

from live_translator.app import MainApplication
from live_translator.settings_ui import SettingsWindow


def main() -> int:
    try:
        app = QApplication(sys.argv)
        settings_window = SettingsWindow()
        settings_window.show()
        main_app = MainApplication(settings_window)
        settings_window.toggle_translation_requested.connect(main_app.toggle_translation_process)
        app.aboutToQuit.connect(main_app.cleanup)
        return app.exec_()
    except Exception as exc:
        print(f"程序运行出错: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

