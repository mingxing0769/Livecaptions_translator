# E:/Python/PythonProject/translator.py

import re
import time
from queue import Queue
from llama_cpp import Llama
import config
from livecaptions import Get_text


class Translator:
    def __init__(self, text_data_queue: Queue, text_getter: Get_text):
        self.llm = Llama(**config.LLAMA_CONFIG)
        self.text_getter = text_getter
        self.text_data = text_data_queue
        self.running = True

    def stop(self):
        """设置停止标志，用于从外部停止线程"""
        print("翻译线程收到停止信号...")
        self.running = False

    @staticmethod
    def preprocess(text):
        # 删除除数字标记之外的标点 返回的是无标点的 小写字母文本
        text = re.sub(r"(?<!\d)[.,;:!?-](?!\d)", "", text).lower()
        return text

    def model_translate(self):
        n_ctx = self.llm.n_ctx()
        messages = [{"role": "system", "content": config.SYS_PROMPT}]
        total_tokens = 0
        translator_cache = {'en': [], 'zh': []}

        while self.running:
            start_dt = time.time()

            # 1. 获取文本块
            complete_sentences, live_sentence = self.text_getter.main_event()

            # 如果没有任何新内容，则短暂休眠后继续
            if not complete_sentences and not live_sentence:
                time.sleep(0.1)  # 避免空轮询占用CPU
                continue

            live_out_put = "..."  # 默认的实时句子翻译

            # 2. 翻译完整句子 (如果存在)
            if complete_sentences:
                sen_to_tran = ' '.join(complete_sentences)
                messages.append({"role": "user", "content": sen_to_tran})
                completion = self.llm.create_chat_completion(messages, **config.COMPLETION_CONFIG)
                out_put = completion['choices'][0]['message']['content'].strip()

                print(f'\033[1;32m[完整句翻译]\n输入: {sen_to_tran}\n输出: {out_put}\033[0m')

                total_tokens = completion['usage']['total_tokens']
                translator_cache['en'].append(self.preprocess(sen_to_tran))
                translator_cache['zh'].append(out_put)
                messages.append({"role": "assistant", "content": out_put})

            # 3. 翻译实时不完整句子 (如果存在)
            if live_sentence:
                # 为LLM准备一个提示，表示这是不完整的
                live_prompt = f'{live_sentence.strip()}...'

                # 使用临时消息进行实时翻译，不污染对话历史
                messages.append({"role": "user", "content": live_prompt})
                temp_completion = self.llm.create_chat_completion(messages, **config.LIVE_CONFIG)
                live_out_put = temp_completion['choices'][0]['message']['content'].strip()
                del messages[-1]  # 删除临时信息

                print(f'\033[94m[实时句翻译]\n输入: {live_sentence}\n输出: {live_out_put}\033[0m')

            # 4. 更新UI队列
            self.sub_text_processing(live_out_put, translator_cache)

            # 5. 维护信息 (token和缓存)
            translator_cache, messages = self.information_maintenance(translator_cache, total_tokens, n_ctx,
                                                                      messages)

            # 6. 处理循环延时
            run_time = time.time() - start_dt
            print(f"--- 循环用时: {run_time:.2f}s | Tokens: {total_tokens} ---\n")

            if run_time < config.DELAY_TIME:
                time.sleep(config.DELAY_TIME - run_time)

        print("翻译线程已安全退出。")

    def sub_text_processing(self, text, translator_cache):
        # 将历史记录和当前实时翻译组合后放入队列
        history_to_out = '\n'.join(translator_cache['zh']) + '\n' + text
        self.text_data.put(history_to_out)

    def information_maintenance(self, translator_cache, total_tokens, n_ctx, messages):
        # 维护翻译缓存及对话记录
        translator_cache['en'] = translator_cache['en'][-config.TRANSLATOR_CACHE:]
        translator_cache['zh'] = translator_cache['zh'][-config.TRANSLATOR_CACHE:]

        if total_tokens >= n_ctx - config.AVAILABLE_TOKENS:
            print("\033[1;33m[警告] Token 上下文接近上限，重置对话历史。\033[0m")
            self.llm.reset()
            if len(messages) > 6:
                messages = [messages[0]] + messages[-6:]
            else:
                messages = [messages[0]]

        return translator_cache, messages