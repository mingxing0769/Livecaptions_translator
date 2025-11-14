# E:/Python/PythonProject/translator.py

import re
import time
from queue import Queue
from openai import OpenAI
import configparser
from datetime import datetime
from livecaptions import Get_text


class Translator:
    def _parse_llm_config(self, section: str) -> dict:
        """从config.ini解析LLM参数，并智能转换为正确的类型"""
        config_dict = {}
        if self.config.has_section(section):
            for key, value in self.config.items(section):
                if '.' in value:
                    config_dict[key] = float(value)
                else:
                    config_dict[key] = int(value)
        return config_dict

    def __init__(self, config: configparser.ConfigParser, text_data_queue: Queue, text_getter: Get_text):
        self.config = config

        # API 设置
        base_url = self.config.get('Sever', 'base_url', fallback='')
        api_key = self.config.get('Sever', 'api_key', fallback='')
        self.model = self.config.get('Sever', 'model', fallback='')
        self.llm = OpenAI(base_url=base_url, api_key=api_key)

        # 逻辑设置
        self.model_context_window = self.config.getint('Sever', 'model_context_window', fallback=4096)
        self.available_tokens = self.config.getint('Logic', 'available_tokens', fallback=256)
        self.delay_time = self.config.getfloat('Logic', 'delay_time', fallback=1.0)
        self.translator_cache_size = self.config.getint('Logic', 'translator_cache', fallback=10)

        # Completion 参数
        self.completion_config = self._parse_llm_config('COMPLETION_CONFIG')
        self.live_config = self._parse_llm_config('LIVE_CONFIG')

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

    def get_sys_prompt(self):
        """动态生成系统提示，确保时间总是最新的"""
        active_prompt_section = self.config.get('Logic', 'active_prompt', fallback='Prompt_General')
        now_str = datetime.now().strftime("%m/%d/%Y, %H:%M")
        raw_prompt = self.config.get(active_prompt_section, 'content', fallback='').replace('|', '').strip()
        return raw_prompt.format(now=now_str)

    def model_translate(self):
        sys_prompt = self.get_sys_prompt()
        messages = [{"role": "system", "content": sys_prompt}]
        print(sys_prompt)
        total_tokens = 0
        translator_cache = {'en': [], 'zh': []}

        while self.running:
            start_dt = time.time()

            # 1. 获取原始文本，仅当有新内容时才处理
            raw_text = self.text_getter.get_text()
            if not raw_text or raw_text == self.text_getter.previous_raw_text:
                time.sleep(0.1)  # 避免空轮询
                continue

            # 2. 对新文本进行分句处理
            complete_sentences, live_sentence = self.text_getter.main_event(raw_text)
            if not complete_sentences and not live_sentence.strip():
                time.sleep(0.1)  # 避免空轮询占用CPU
                continue

            live_out_put = "..."  # 默认的实时句子翻译

            # 2. 翻译完整句子 (如果存在)
            if complete_sentences:
                sen_to_tran = ' '.join(complete_sentences)
                messages.append({"role": "user", "content": sen_to_tran})
                completion = self.llm.chat.completions.create(model=self.model, messages=messages, **self.completion_config)
                out_put = completion.choices[0].message.content

                print(f'\033[1;32m[完整句翻译]\n输入: {sen_to_tran}\n输出: {out_put}\033[0m')

                total_tokens = completion.usage.total_tokens
                translator_cache['en'].append(self.preprocess(sen_to_tran))
                translator_cache['zh'].append(out_put)
                messages.append({"role": "assistant", "content": out_put})

            # 3. 翻译实时不完整句子 (如果存在)
            if live_sentence:
                # 为LLM准备一个提示，表示这是不完整的
                live_prompt = f'{live_sentence.strip()}...'

                # 使用临时消息进行实时翻译，不污染对话历史
                messages.append({"role": "user", "content": live_prompt})
                temp_completion = self.llm.chat.completions.create(model=self.model, messages=messages, **self.live_config)
                live_out_put = temp_completion.choices[0].message.content
                total_tokens = temp_completion.usage.total_tokens # 累加实时翻译的token
                del messages[-1]  # 删除临时信息

                print(f'\033[94m[实时句翻译]\n输入: {live_sentence}\n输出: {live_out_put}\033[0m')

            # 4. 更新UI队列
            self.sub_text_processing(live_out_put, translator_cache)

            # 5. 维护上下文 (token和缓存)
            translator_cache, messages = self.information_maintenance(translator_cache, total_tokens, messages)

            # 6. 处理循环延时
            run_time = time.time() - start_dt
            print(f"--- 循环用时: {run_time:.2f}s | Tokens: {total_tokens} ---\n")
            if run_time>5:
                print(f"循环用时: {run_time:.2f}s 严重超时！\n")


            if run_time < self.delay_time:
                time.sleep(self.delay_time - run_time)

        print("翻译线程已安全退出。")

    def sub_text_processing(self, text, translator_cache):
        # 将历史记录和当前实时翻译组合后放入队列
        history_to_out = '\n'.join(translator_cache['zh']) + '\n' + text
        self.text_data.put(history_to_out)

    def information_maintenance(self, translator_cache, total_tokens, messages):
        # 维护翻译缓存及对话记录
        translator_cache['en'] = translator_cache['en'][-self.translator_cache_size:]
        translator_cache['zh'] = translator_cache['zh'][-self.translator_cache_size:]

        if total_tokens >= self.model_context_window - self.available_tokens:
            print("\033[1;33m[警告] Token 上下文接近上限，重置对话历史。\033[0m")
            if len(messages) > 6:
                messages = [messages[0]] + messages[-6:]
            else:
                messages = [messages[0]]

        return translator_cache, messages