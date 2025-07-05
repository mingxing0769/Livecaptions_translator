import re
import subprocess
import sys
import threading
import time
from queue import Queue

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSizeGrip, QTextEdit, QSizePolicy, \
    QGraphicsDropShadowEffect
from llama_cpp import Llama
from nltk import sent_tokenize
from pywinauto import Desktop

import config


class Translator:
    def __init__(self, text_data_queue: Queue):
        self.llm = None
        self.window = None
        self.static_control = None
        self.text_data = text_data_queue
        self.last_text = ''
        self.en_pattern = re.compile(
            r'(?<!Mr\.|Ms\.|Dr\.|St\.|vs\.|jr\.|sr\.)(?<!Mrs\.|Rev\.|Hon\.|etc\.|inc\.)(?<!Prof\.|Capt\.|corp\.)(?<![A-Z]\.)(?<!\d.)(?<!\d,\d{3})(?<=[.!;?])\s*'
        )
        self.zh_pattern = re.compile(
            r'''(?<![A-Z]\.)(?<!\d\.)(?<!\d,\d{3})((?<=[。！；？]['"”’』》])|(?<=[。！；？])(?![’"”』》]))\s*''',
            flags=re.VERBOSE
        )

    def init_model(self, ):
        self.llm = Llama(**config.LLAMA_CONFIG)

    def split_text(self, text, language):
        if language == 'english':
            # sentences = self.en_pattern.split(text)
            # return [s for s in sentences if s]

            return sent_tokenize(text, language=language)

        elif language == 'zh':
            sentences = self.zh_pattern.split(text)
            return [s for s in sentences if s]

    def get_text(self):
        try:
            if not self.window:
                try:
                    subprocess.Popen(config.CAPTION_APP_PATH)
                except FileNotFoundError:
                    print(f"错误：找不到实时字幕软件，请检查路径是否正确：{config.CAPTION_APP_PATH}")
                    return None
                window_title = config.CAPTION_WINDOW_TITLE
                desktop = Desktop(backend='uia')
                self.window = desktop.window(title=window_title)
                self.static_control = self.window.child_window(control_type=config.CAPTION_CONTROL_TYPE)

            # 获取控件文本
            text = self.static_control.window_text().rstrip()

            replace_dict = {'已准备好在 英语(美国) 中显示实时字幕': '',
                            '\n': ' '
                            }
            for old, new in replace_dict.items():
                text = text.replace(old, new)

            # 分割单词
            words = text.split()
            text = ' '.join(words[-config.MAX_INPUT_WORDS:])

            if text != self.last_text and text:
                self.last_text = text
                sentences = self.split_text(text, language="english")

                return sentences[-config.SENTENCES_TO_TRANSLATE:]

        except Exception as e:
            print(f"程序运行出错: {e}")
            self.window = None
            return []

    def model_translate(self):
        n_ctx = self.llm.n_ctx()
        translator_cache = {'en': [], 'zh': []}
        last_inputs = []
        total_tokens = 0

        sys_prompt = config.SYS_PROMPT
        messages = [{"role": "system", "content": sys_prompt}]

        while True:
            start_dt = time.time()
            inputs = self.get_text()

            if inputs and inputs != last_inputs:
                last_inputs = inputs
                # print('输入：', ' '.join(inputs))

                # 最后一条缓存标点之前的内容 在 当前输入中, 以免字幕重复
                if translator_cache['en'] and translator_cache['en'][-1][:-1] in inputs[-1].lower():
                    del translator_cache['en'][-1]
                    del translator_cache['zh'][-1]

                # 处理完整句子
                if len(inputs) > 1:
                    for sen in inputs[:-1]:
                        if sen.lower() not in translator_cache['en']:
                            messages.append({"role": "user",
                                             "content": f'{config.PROMPT_2}{sen}'})
                            completion = self.llm.create_chat_completion(messages, **config.COMPLETION_CONFIG)
                            total_tokens = completion['usage']['total_tokens']

                            out_put = completion['choices'][0]['message']['content'].strip()
                            # print('输出：', out_put)

                            translator_cache['en'].append(sen.lower())
                            translator_cache['zh'].append(out_put)

                            messages[-1]["content"] = sen
                            messages.append({"role": "assistant", "content": out_put})

                # 处理最后一句,不完整句子
                last_sen = config.PROMPT_1 + inputs[-1]
                if not re.search(r'[.?!]$', last_sen.strip()):
                    last_sen = f'{last_sen.strip()}...'

                messages.append({"role": "user", "content": last_sen})
                temp_completion = self.llm.create_chat_completion(messages, **config.LIVE_COMPLETION_CONFIG)
                live_out_put = temp_completion['choices'][0]['message']['content'].strip()
                # print('输出：', live_out_put)
                del messages[-1]

                # 处理字幕文本
                history_to_out = ' '.join(translator_cache['zh'][-5:]) + live_out_put
                history_to_out = self.split_text(history_to_out, 'zh')

                to_ui_sen = []
                for sen in history_to_out:
                    if sen not in to_ui_sen:
                        to_ui_sen.append(sen)  #去重
                output = '\n'.join(to_ui_sen[-config.MAX_TO_UI:])

                self.text_data.put(output)

                # 维护翻译缓存及对话记录
                # 如果总tokens接近模型设置的n_ctx时 只保留最近几条历史记录
                translator_cache['en'], translator_cache['zh'] = translator_cache['en'][-config.TRANSLATOR_CACHE:], \
                translator_cache['zh'][-config.TRANSLATOR_CACHE:]

                if total_tokens >= n_ctx * config.MESSAGES_PRUNE_THRESHOLD:
                    if len(messages) > 6:
                        messages = [messages[0]] + messages[-6:]
                    else:
                        messages = [messages[0]]

                #处理循环间隔
                run_time = time.time() - start_dt
                # print(f"运行时间：{run_time:.2f}秒\t total_tokens:{total_tokens}\n")

                if run_time < config.DELAY_TIME:
                    time.sleep(config.DELAY_TIME - run_time)
            else:
                time.sleep(config.DELAY_TIME)


class SubtitleWindow(QWidget):
    def __init__(self, text_data):
        super().__init__()
        self.background_widget = None
        self.size_grip = None
        self.drag_position = None
        self.text_display = None
        self.oldPos = None
        self.text_data = text_data
        self.setup_ui()

        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(config.UPDATE_INTERVAL_MS)

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(*config.INITIAL_WINDOW_GEOMETRY)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background_widget = QWidget()
        self.background_widget.setStyleSheet(f"""
            background-color: rgba{config.BACKGROUND_COLOR};
            border-radius: 5px;
        """)
        self.background_widget.setMaximumWidth(config.MAX_WINDOW_WIDTH)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(3, 3)
        self.background_widget.setGraphicsEffect(shadow)

        main_layout.addWidget(self.background_widget)

        inner_layout = QVBoxLayout(self.background_widget)
        inner_layout.setContentsMargins(15, 10, 15, 10)

        # 创建尺寸调节控件
        self.size_grip = QSizeGrip(self.background_widget)
        inner_layout.addWidget(self.size_grip, 0, Qt.AlignTop | Qt.AlignRight)

        # 创建文本显示控件
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setTextInteractionFlags(Qt.NoTextInteraction)
        self.text_display.setFont(QFont(config.FONT_FAMILY, config.FONT_SIZE))

        #是否显示 滚动条
        if config.ScrollBarPolicy:
            self.text_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.text_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.text_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_display.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)  # 同时设置水平和垂直对齐

        # 设置尺寸策略
        self.text_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置初始高度
        font_metrics = self.text_display.fontMetrics()
        initial_height = int(font_metrics.height() * config.DISPLAY_LINES)
        self.text_display.setMinimumHeight(initial_height)

        # 设置样式
        self.text_display.setStyleSheet("""
            QTextEdit {
                color: white;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.4);
                min-height: 25px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.7);
            }
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, 
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        inner_layout.addWidget(self.text_display)

    def update_text(self):
        """更新文本并实现智能滚动"""
        if not self.text_data.empty():
            scrollbar = self.text_display.verticalScrollBar()
            is_at_bottom = scrollbar.value() >= scrollbar.maximum() - 2

            # 仅当有新内容时才更新
            text_block = self.text_data.get()
            if self.text_display.toPlainText() != text_block:
                self.text_display.setText(text_block)

                if is_at_bottom:
                    scrollbar.setValue(scrollbar.maximum())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 检查点击位置是否在文本区域内
            if self.text_display.rect().contains(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            elif not self.size_grip.underMouse():
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def mouseDoubleClickEvent(self, event):
        """双击关闭窗口"""
        if event.button() == Qt.LeftButton:
            self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)


def main():
    try:
        # 建议将 QApplication 的创建放在最前面
        app = QApplication(sys.argv)

        # 1. 在 main 函数中创建共享的 Queue
        text_data_queue = Queue()

        # 2. 创建 Translator 实例，并将队列“注入”进去
        translator = Translator(text_data_queue)
        translator.init_model()

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
