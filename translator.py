import re
import subprocess
import time
from difflib import SequenceMatcher
from queue import Queue
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

        if config.RESET_PUNCTUATION:
            from punctuation import PunctuationModel
            self.reset_punctuation= PunctuationModel()

        self.zh_pattern = re.compile(
            r'''(?<![A-Z]\.)(?<!\d\.)(?<!\d,\d{3})((?<=[。！；？]['"”’』》])|(?<=[。！；？])(?![’"”』》]))\s*''',
            flags=re.VERBOSE
        )

    def split_text(self, text, language):
        if language == 'english':
            return sent_tokenize(text, language=language)

        elif language == 'zh':
            sentences = self.zh_pattern.split(text)
            return [s for s in sentences if s]

    @staticmethod
    def preprocess(text):
        #删除除数字标记之外的标点  返回的是无标点的 小写字母文本
        text = re.sub(r"(?<!\d)[.,;:!?-](?!\d)", "", text).lower()
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
            text = text.replace('已准备好在 英语(美国) 中显示实时字幕', '').replace('\n', ' ')

            # 分割单词
            words = text.split()
            text = ' '.join(words[-config.MAX_INPUT_WORDS:])

            if text != self.last_text and text:
                self.last_text = text

                # 重置标点
                if config.RESET_PUNCTUATION:
                    text = self.reset_punctuation.restore_punctuation(text)

                sentences = self.split_text(text, language="english")

                return sentences[-config.SENTENCES_TO_TRANSLATE:]

        except Exception as e:
            print(f"程序运行出错: {e}")
            self.window = None
            return []

    @staticmethod
    def is_similar(a, b, thresh=0.97):
        return SequenceMatcher(None, a, b).ratio() >= thresh

    def model_translate(self):
        n_ctx = self.llm.n_ctx()
        messages = [{"role": "system", "content": config.SYS_PROMPT}]
        total_tokens = 0

        translator_cache = {'en': [], 'zh': []}
        startswith = 'start'
        last_complete_sentences = ''

        last_inputs = []

        while True:
            start_dt = time.time()
            inputs = self.get_text()

            if inputs and inputs != last_inputs:  #文本列表不为空， 且和上次不一致
                last_inputs = inputs

                # 完整句子
                complete_sentences = inputs[:-1]
                preprocessed_complete_sentences = self.preprocess(' '.join(complete_sentences))

                # 最后一个句子视为可能不完整的实时句子
                live_sentence = inputs[-1]

                if not self.is_similar(last_complete_sentences, preprocessed_complete_sentences):
                    last_complete_sentences = preprocessed_complete_sentences

                    for sen in complete_sentences:

                        preprocessed_sen = self.preprocess(sen)

                        if preprocessed_sen not in ' '.join(translator_cache['en'][-4:]):
                            sen_to_tran = sen

                            # 和上次输入开头部分相同
                            if preprocessed_sen.startswith(startswith):
                                sen_to_tran = ' '.join(sen.split()[len(startswith.split()):])

                            # 和上次输入结尾部分相同
                            if preprocessed_sen.endswith(startswith) or not sen_to_tran:
                                continue

                            messages.append({"role": "user", "content": sen_to_tran})
                            completion = self.llm.create_chat_completion(messages, **config.COMPLETION_CONFIG)
                            out_put = completion['choices'][0]['message']['content'].strip()

                            print(f'======\n输入：{sen}\n输出：{out_put}')

                            total_tokens = completion['usage']['total_tokens']
                            startswith = preprocessed_sen
                            translator_cache['en'].append(preprocessed_sen)
                            translator_cache['zh'].append(out_put)

                            messages.append({"role": "assistant", "content": out_put})

                # 处理最后一句,不完整句子
                if self.preprocess(live_sentence).startswith(startswith):
                    live_sentence = ' '.join(live_sentence.split()[len(startswith.split()):])

                if not live_sentence: continue

                if not re.search(r'[.?!]$', live_sentence.strip()):
                    live_sentence = f'{live_sentence.strip()}...'

                messages.append({"role": "user", "content": live_sentence})
                temp_completion = self.llm.create_chat_completion(messages, **config.LIVE_CONFIG)
                live_out_put = temp_completion['choices'][0]['message']['content'].strip()
                print(f'------\n输入：{live_sentence}\n输出：{live_out_put}')
                del messages[-1]  # 删除临时信息

                # 处理字幕文本
                self.sub_text_processing(live_out_put, translator_cache)

                # 维护翻译缓存及对话记录
                translator_cache, messages = self.information_maintenance(translator_cache, total_tokens, n_ctx,
                                                                          messages)

                #处理循环间隔
                run_time = time.time() - start_dt
                print(f"运行时间：{run_time:.2f}秒\t total_tokens:{total_tokens}\n")

                if run_time < config.DELAY_TIME:
                    time.sleep(config.DELAY_TIME - run_time)

    def sub_text_processing(self, text, translator_cache):
        # 处理字幕文本
        history_to_out = ' '.join(translator_cache['zh']) + ' ' + text
        history_to_out = self.split_text(history_to_out, 'zh')

        # 去重 避免英文数字转阿拉伯数字的重复
        # to_ui_sen = ['\n'] * 10
        # for sen in history_to_out:
        #     if sen not in to_ui_sen:
        #         to_ui_sen.append(sen)  # 去重

        output = '\n'.join(history_to_out)

        self.text_data.put(output)

    def information_maintenance(self, translator_cache, total_tokens, n_ctx, messages):
        # 维护翻译缓存及对话记录
        translator_cache['en'] = translator_cache['en'][-config.TRANSLATOR_CACHE:]
        translator_cache['zh'] = translator_cache['zh'][-config.TRANSLATOR_CACHE:]

        if total_tokens >= n_ctx - config.AVAILABLE_TOKENS:
            self.llm.reset()
            if len(messages) > 6:
                messages = [messages[0]] + messages[-6:]
            else:
                messages = [messages[0]]

        return translator_cache, messages
