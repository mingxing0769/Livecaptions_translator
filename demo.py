import re
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
        self.llm = Llama(**config.LLAMA_CONFIG)
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

    def split_text(self, text, language):
        if language == 'english':
            # sentences = self.en_pattern.split(text)
            # return [s for s in sentences if s]

            return sent_tokenize(text, language=language)

        elif language == 'zh':
            sentences = self.zh_pattern.split(text)
            return [s for s in sentences if s]

    def preprocess(self, text):
        #删除除数字标记之外的标点  返回的是无标点的 小写字母文本
        text = re.sub(r"(?<!\d)[.,;:!?](?!\d)", "", text).lower()
        return text

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

            text = text.replace('已准备好在 英语(美国) 中显示实时字幕', '')

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
        messages = [{"role": "system", "content": config.SYS_PROMPT}]
        total_tokens = 0

        #去重变量
        endswith = 'end'
        startswith = 'start'
        last_fullSentence = ''
        translator_cache = {'en': [], 'zh': []}
        last_inputs = []

        while True:
            start_dt = time.time()
            inputs = self.get_text()  #最后几句的文本列表

            if inputs and inputs != last_inputs:  #文本列表不为空， 且和上次不一致
                last_inputs = inputs

                # 处理完整句子
                complete_sentences = inputs[:-1]
                # 最后一个句子视为可能不完整的实时句子
                live_sentence = inputs[-1]

                # 整合完整的句子，并进行去标点及小写化
                fullSentence = self.preprocess(' '.join(complete_sentences))

                if fullSentence != last_fullSentence and \
                                not fullSentence.endswith(endswith):
                    #此处可以跳过 整体内容一样，但标点有改变的文本。若中间有英文数字 转换为了阿拉伯数字 无法判断！
                    #同时避免第一句前部发生变化 而后部完全一样而重复。

                    last_fullSentence = fullSentence

                    for sen in complete_sentences:
                        sen_To_Tran = sen
                        if self.preprocess(sen) not in translator_cache['en'] :
                            # 句子不在缓存中

                            # print(f'当前输入: {sen}\n上次结尾: {endswith}\n上次开头: {startswith}\n')

                            if self.preprocess(sen).startswith(startswith):   #和上次输入开头部分相同
                                sen_To_Tran = ' '.join(sen.split()[len(startswith.split()):])
                                # print(f'句子开头 {startswith} 相同\n裁剪为:{sen_To_Tran}')

                            if not sen_To_Tran or self.preprocess(sen) in startswith:
                                #裁剪后为空，或者当前输入的文本在上次的开头里面，可以避免将上次的输入重新断句，去掉了上次句子的尾部。
                                # print('sen_TO_tran为空跳过翻译！\n')
                                continue

                            endswith = self.preprocess(sen)
                            startswith = endswith

                            messages.append({"role": "user",
                                             "content": f'{config.LIVE_PROMPT}{sen_To_Tran}'})
                            completion = self.llm.create_chat_completion(messages, **config.COMPLETION_CONFIG)
                            total_tokens = completion['usage']['total_tokens']

                            out_put = completion['choices'][0]['message']['content'].strip().replace(
                                '请继续将英文翻译为中文，仅输出译文不添加任何解释或评论：\n', '')
                            # print('输出：', out_put)

                            translator_cache['en'].append(self.preprocess(sen))
                            translator_cache['zh'].append(out_put)

                            messages[-1]["content"] = sen_To_Tran  # 更新user内容 不包含 即时指令config.COMPLETION_PROMPT
                            messages.append({"role": "assistant", "content": out_put})

                # 处理最后一句,不完整句子
                # 去掉已经翻译的 重复前段句子 startswith
                if self.preprocess(live_sentence).startswith(startswith):
                    live_sentence = ' '.join(inputs[-1].split()[len(startswith.split()):]).strip()
                    # print(f'即时翻译句子开头 {startswith} 相同被裁切\n{live_sentence}')

                if not live_sentence:
                    # print('跳过即时翻译')
                    continue

                if not re.search(r'[.?!]$', live_sentence.strip()):
                    live_sentence = f'{live_sentence.strip()}...'

                messages.append({"role": "user", "content": config.LIVE_PROMPT + live_sentence})
                temp_completion = self.llm.create_chat_completion(messages, **config.LIVE_COMPLETION_CONFIG)
                live_out_put = temp_completion['choices'][0]['message']['content'].strip().replace(
                    '请继续将英文翻译为中文，仅输出译文不添加任何解释或评论：\n', '')
                # print('输出：', live_out_put)
                del messages[-1]  # 删除临时信息

                # 处理字幕文本
                self.sub_text_processing(live_out_put, translator_cache)

                # 维护翻译缓存及对话记录
                translator_cache, messages = self.information_maintenance(translator_cache, total_tokens, n_ctx,
                                                                          messages)

                #处理循环间隔
                run_time = time.time() - start_dt
                # print(f"运行时间：{run_time:.2f}秒\t total_tokens:{total_tokens}\n")

                if run_time < config.DELAY_TIME:
                    time.sleep(config.DELAY_TIME - run_time)
            else:
                time.sleep(config.DELAY_TIME)

    def sub_text_processing(self, text, translator_cache):
        # 处理字幕文本
        history_to_out = ' '.join(translator_cache['zh']) + ' ' + text
        history_to_out = self.split_text(history_to_out, 'zh')

        # 去重
        to_ui_sen = []
        for sen in history_to_out:
            if sen not in to_ui_sen:
                to_ui_sen.append(sen)  # 去重

        output = '\n'.join(to_ui_sen[-config.MAX_TO_UI:])

        self.text_data.put(output)

    @staticmethod
    def information_maintenance(translator_cache, total_tokens, n_ctx, messages):
        # 维护翻译缓存及对话记录
        translator_cache['en'] = translator_cache['en'][-config.TRANSLATOR_CACHE:]
        translator_cache['zh'] = translator_cache['zh'][-config.TRANSLATOR_CACHE:]

        if total_tokens >= n_ctx * config.MESSAGES_PRUNE_THRESHOLD:
            if len(messages) > 6:
                messages = [messages[0]] + messages[-6:]
            else:
                messages = [messages[0]]

        return translator_cache, messages


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

    # 在 SubtitleWindow 类中
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 只要鼠标不在尺寸调节器上，就启动拖动
            if not self.size_grip.geometry().contains(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            else:
                self.drag_position = None  # 确保在点击size_grip时不拖动

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
