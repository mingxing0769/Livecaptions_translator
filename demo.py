import os
import re
import subprocess
import sys
import threading
import time
from queue import Queue

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSizeGrip
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from llama_cpp import Llama
from nltk import sent_tokenize
from pywinauto import Desktop


class Translator:
    def __init__(self, ):
        self.llm = None
        self.window = None
        self.static_control = None
        self.text_data = Queue()
        self.config = None
        self.caption_path = os.getenv('caption_path', 'C:\\Windows\\System32\\livecaptions.exe')
        self.last_text = ''


    def init_model(self, ):
        model_path = "E:/download/qwen3-4b-q8_0.gguf"
        self.config = {
            'llama_config':
                {
                    'model_path': model_path,
                    'verbose': False,
                    'n_gpu_layers': -1,
                    'n_ctx': 2048,
                    'seed': 2056,
                    'n_threads': 6,
                    'use_mmap': True,
                    'use_mlock': True,
                    'n_batch': 512,
                    'n_ubatch': 512,
                    'flash_attn': False,

                },
            'completion_config':
                {
                    'temperature': 1.0,
                    'max_tokens': 128,
                    'seed': 2056,
                    'top_k': 50,
                    'top_p': 0.95,
                    'typical_p': 0.85,
                    'repeat_penalty': 1.1,
                    'presence_penalty': 0.0,
                    'frequency_penalty': 0.0
                }
        }

        # 加载模型
        self.llm = Llama(**self.config['llama_config'])

    def split_text(self, text, language):
        if language == 'english':
            # pattern = r'(?<!Mr\.|Ms\.|Dr\.|St\.|vs\.|jr\.|sr\.)(?<!Mrs\.|Rev\.|Hon\.|etc\.|inc\.)(?<!Prof\.|Capt\.|corp\.)(?<![A-Z]\.)(?<!\d.)(?<!\d,\d{3})(?<=[.!;?])\s*'
            # sentences = re.split(pattern, text)
            #
            # return [s for s in sentences if s]

            return sent_tokenize(text, language=language)


        elif language =='zh':
            pattern = r'(?<![A-Z]\.)(?<!\d.)(?<!\d,\d{3})(?<=[。！；？])\s*'
            sentences = re.split(pattern, text)

            return [s for s in sentences if s]

    def get_text(self):
        try:
            if not self.window:
                try:
                    subprocess.Popen([self.caption_path])
                except FileNotFoundError:
                    print(f"错误：找不到实时字幕软件，请检查路径是否正确：{self.caption_path}")
                    return None
                window_title = '实时辅助字幕'
                desktop = Desktop(backend='uia')
                self.window = desktop.window(title=window_title)
                self.static_control = self.window.child_window(auto_id="CaptionsTextBlock", control_type="Text")

            # 获取控件文本
            text = self.static_control.window_text().rstrip()

            replace_dict = {'已准备好在 英语(美国) 中显示实时字幕': '',
                            '\n': ' '
                            }
            for old, new in replace_dict.items():
                text = text.replace(old, new)

            # 分割单词
            words = text.split()

            text = ' '.join(words[-500:])

            if text != self.last_text and text:
                self.last_text = text
                # # 按标点分割句字
                sentences = self.split_text(text, language="english")
                return sentences[-3:]
        except Exception as e:
            print(f"程序运行出错: {e}")
            self.window = None
            return []


    def model_translate(self):
        n_ctx = self.llm.n_ctx()
        history = {'en': [], 'zh': []}
        last_inputs = []
        sys_prompt ='/<no_think>请结合对话历史，将文本翻译为流畅、自然的中文，无需额外提示、解释或总结。'
        messages = [{"role": "system", "content":sys_prompt}]

        while True:
            start_dt = time.time()
            inputs = self.get_text()

            if inputs and inputs != last_inputs:
                last_inputs = inputs
                print('输入：', ' '.join(inputs))

                # 处理完整句子
                for input in inputs[:-1]:
                    if input.lower() not in history['en']:
                        messages.append({"role": "user",
                                         "content": input})
                        completion = self.llm.create_chat_completion(messages, **self.config['completion_config'])

                        out_put = completion['choices'][0]['message']['content'].strip().replace('<think>\n\n</think>\n\n','')
                        print('输出：', out_put)
                        if out_put:
                            history['en'].append(input.lower())  #避免太小写不同而重复
                            history['zh'].append(out_put)
                            messages.append({"role": "assistant", "content": out_put})
                        else:
                            del messages[-1]


                # 处理不完整句子
                input = inputs[-1]
                messages.append({"role": "user",
                                 "content": input})

                completion = self.llm.create_chat_completion(messages, **self.config['completion_config'])
                out_put = completion['choices'][0]['message']['content'].strip().replace('<think>\n\n</think>\n\n','')
                print('输出：', out_put)
                del messages[-1]  #不保存临时对话

                history_to_out = '\n'.join(history['zh'][-5:])
                history_to_out = self.split_text(history_to_out, 'zh')

                self.text_data.put('\n'.join(history_to_out[-2:]) + '\n' + out_put)

                total_tokens = completion['usage']['total_tokens']
                # 如果总tokens接近模型设置的n_ctx时 只保留最近几条历史记录
                if total_tokens >= n_ctx * .75:
                    sys_message = next((message for message in messages if message["role"] == "system"),
                                       None)
                    # 保留最新的消息
                    messages = messages[-6:]
                    if sys_message:
                        messages.insert(0, sys_message)

                run_time = time.time() - start_dt
                print(f"运行时间：{run_time:.2f}秒\ttotal_tokens:{total_tokens}\n")

                history['en'], history['zh'] = history['en'][-10:], history['zh'][-10:]

                if run_time < 1.0:
                    time.sleep(1.0 - run_time)
            else:
                time.sleep(1)

    def create_subtitle_window(self):
        app = QApplication([])
        window = SubtitleWindow(self.text_data)
        window.show()
        app.exec_()

    def start(self):
        try:
            self.init_model()
            translate_thread = threading.Thread(target=self.model_translate)
            translate_thread.daemon = True
            translate_thread.start()
            self.create_subtitle_window()

        except SystemExit:
            print("主线程退出")
            sys.exit()


class SubtitleWindow(QWidget):
    def __init__(self, text_data):
        super().__init__()
        self.size_grip = None
        self.drag_position = None
        self.chinese_label = None
        self.oldPos = None
        self.text_data = text_data
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(150)

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(360, 0, 1250, 400)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.chinese_label = QLabel()
        self.chinese_label.setFont(QFont("微软雅黑", 18))
        self.chinese_label.setWordWrap(True)
        self.chinese_label.setMaximumWidth(1250)

        outline_style = """
        QLabel {
            color: white;            
        }
        """

        self.chinese_label.setStyleSheet(outline_style)

        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(0, 1)
        shadow_effect.setColor(QColor('black'))
        shadow_effect.setBlurRadius(8)
        self.chinese_label.setGraphicsEffect(shadow_effect)

        layout.addWidget(self.chinese_label)
        self.size_grip = QSizeGrip(self)
        layout.addWidget(self.size_grip)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)

    def update_text(self):
        if not self.text_data.empty():
            local_C_text = self.text_data.get()
            self.chinese_label.setText(local_C_text)


def main():
    try:
        # 打开实时字幕软件
        subprocess.Popen(['C:\\Windows\\System32\\livecaptions.exe'])
        time.sleep(2)
        app = Translator()
        app.start()
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
