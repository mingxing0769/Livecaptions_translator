import re
import subprocess
import time
import win32gui
import win32con
import win32api
from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError as PywinautoTimeoutError
import config

# 确保已安装 nltk
try:
    from nltk import sent_tokenize
except ImportError:
    print("正在安装 NLTK... 请稍候。")
    subprocess.run(['pip', 'install', 'nltk'], check=True)
    from nltk import sent_tokenize

    print("NLTK 安装完成。正在下载分句模型 'punkt'...")
    import nltk

    nltk.download('punkt')
    print("模型下载完成。")


# 定义每个锚点“下一句预览”最多保留的单词数
NEXT_SENTENCE_PREVIEW_WORDS = 5


class Get_text:
    def __init__(self):
        self.text_control_wrapper = None
        self.window_wrapper = None

        # 从 config.py 读取实时字幕软件路径和窗口标题
        self.CAPTION_APP_PATH = config.CAPTION_APP_PATH
        self.CAPTION_WINDOW_TITLE = config.CAPTION_WINDOW_TITLE

        # 存储所有完整句子
        self.total_sentences_list = []
        # 存储所有锚点（句子词序列 + 下一句预览）
        self.anchor_history = []
        # 存储上一次抓到的完整原始文本
        self.previous_raw_text = ""

    # ---------------- 基础处理工具 ---------------- #

    @staticmethod
    def segmenting_sentences(text, language="english"):
        """使用 nltk 分句"""
        return sent_tokenize(text, language=language)

    @staticmethod
    def preprocess(text, to_list=False):
        """
        将文本标准化：小写、去除部分标点、合并空白。
        若 to_list=True，则返回词列表。
        """
        text_lower = text.lower()
        text_no_punct = re.sub(r"[.,;:!?]", "", text_lower)
        text_normalized = re.sub(r'\s+', ' ', text_no_punct).strip()

        if to_list:
            return [word for word in text_normalized.split() if word]
        return text_normalized

    @staticmethod
    def find_last_sublist_end_index(main_list, sub_list):
        """在主列表中查找子列表最后一次出现，返回其结束索引。"""
        if not sub_list or not main_list:
            return -1
        sub_len = len(sub_list)
        for i in range(len(main_list) - sub_len, -1, -1):
            if main_list[i:i + sub_len] == sub_list:
                return i + sub_len
        return -1

    @staticmethod
    def find_first_sublist_start_index(main_list, sub_list, start_from=0):
        """从指定位置起查找子列表第一次出现，返回起始索引。"""
        if not sub_list or not main_list:
            return -1
        sub_len = len(sub_list)
        for i in range(start_from, len(main_list) - sub_len + 1):
            if main_list[i:i + sub_len] == sub_list:
                return i
        return -1
    

    def get_text(self):
        """
        [优化方案] 使用动态等待和性能分析。
        """
        try:
            if not self.window_wrapper or not self.window_wrapper.exists():
                print("包装器失效或未初始化，开始查找窗口...")
                try:
                    subprocess.Popen(self.CAPTION_APP_PATH)
                    # [优化一] 使用动态等待代替 time.sleep(2)
                    # 我们给它最多5秒的时间去启动和出现
                    print("等待 livecaptions.exe 启动...")
                    time.sleep(1)  # 等待进程创建
                except FileNotFoundError:
                    print(f"错误：找不到实时字幕软件，请检查路径：{self.CAPTION_APP_PATH}")
                    return None

                desktop = Desktop(backend='uia')
                print(f"正在使用 pywinauto 查找窗口: '{self.CAPTION_WINDOW_TITLE}'...")

                try:
                    # 使用 wait 方法，它会轮询直到找到窗口或超时
                    self.window_wrapper = desktop.window(title=self.CAPTION_WINDOW_TITLE)
                    self.window_wrapper.wait('exists', timeout=5)
                    self.text_control_wrapper = self.window_wrapper.child_window(control_type="Text")
                    self.text_control_wrapper.wait('exists', timeout=5)
                except PywinautoTimeoutError:
                    print("错误：查找窗口或控件超时，将在下次循环重试。")
                    return ''

                print(f"成功连接到主窗口和文本控件的包装器。")

                window_hwnd = self.window_wrapper.handle
                print(f"提取到主窗口句柄 (HWND: {window_hwnd}) 用于移动。")

                if window_hwnd:
                    print("将窗口移出屏幕，实现“隐藏”效果...")
                    try:
                        win32gui.SetWindowPos(window_hwnd, 0, -2000, -2000, 0, 0,
                                              win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
                        print("窗口移动成功 (使用 WinAPI SetWindowPos)。")
                    except Exception as move_error:
                        print(f"警告：移动窗口失败，它可能会保持可见。错误: {move_error or '无详细错误信息'}")
                else:
                    print("警告：未能获取主窗口句柄，无法将其移出屏幕。")
            
            text = self.text_control_wrapper.window_text()           

            return ' '.join(text.split()[-300:]).replace("已准备好在 英语(美国) 中显示实时字幕", '').replace('\n',
                                                                                                             ' ').strip()

        except (ElementNotFoundError, win32api.error, PywinautoTimeoutError) as e:
            print(f"窗口或控件已关闭/失效，将在下次循环时重试... 错误: {e}")
            self.window_wrapper = None
            self.text_control_wrapper = None
            return ''
        except Exception as e:
            print(f"获取文本时发生未知错误: {e}")
            self.window_wrapper = None
            self.text_control_wrapper = None
            return ''

    # ---------------- 锚点与句子处理 ---------------- #

    def _handle_sentence_batch(self, sentences_to_process, last_incomplete_sentence):
        """
        处理一批句子，更新总句子列表与锚点历史。
        返回新增的句子列表。
        """
        added_sentences = []

        for i, sentence in enumerate(sentences_to_process):
            clean_sentence = sentence.strip()
            if not clean_sentence:
                continue

            added_sentences.append(clean_sentence)
            self.total_sentences_list.append(clean_sentence)

            # 获取“下一句预览”
            if i + 1 < len(sentences_to_process):
                next_preview_text = sentences_to_process[i + 1]
            else:
                next_preview_text = last_incomplete_sentence

            next_preview_words = self.preprocess(next_preview_text, to_list=True)

            # 若末尾不是空格，可能最后一个词未完整显示，则删掉最后一个词
            if next_preview_words and not next_preview_text.endswith(' '):
                next_preview_words = next_preview_words[:-1]

            # 限制预览词数
            next_preview_words = next_preview_words[:NEXT_SENTENCE_PREVIEW_WORDS]

            self.anchor_history.append({
                'words': self.preprocess(clean_sentence, to_list=True),
                'next_preview': next_preview_words
            })

        return added_sentences

    def _reset_and_process_all(self, current_sentences):
        """在首次运行或重大跳跃时清空历史并重新初始化最近的句子"""
        self.total_sentences_list.clear()
        self.anchor_history.clear()

        if len(current_sentences) > 1:
            return self._handle_sentence_batch(current_sentences[-3:-1], current_sentences[-1])
        return []

    # ---------------- 主循环逻辑 ---------------- #

    def main_event(self):
        """实时抓取文本 + 上下文锚点逻辑"""
        raw_text = self.get_text()
        if not raw_text or raw_text == self.previous_raw_text:
            # time.sleep(0.5)
            return [], ''

        self.previous_raw_text = raw_text
        current_sentences = self.segmenting_sentences(raw_text)
        if len(current_sentences) < 1:
            return [], ''

        newly_added_sentences = []
        new_text_to_process = ''
        action_taken = None

        # ----------- 首次运行 ----------- #
        if not self.anchor_history:
            action_taken = "[首次运行]"
            newly_added_sentences = self._reset_and_process_all(current_sentences)

        # ----------- 后续运行 ----------- #
        else:
            current_text_words = self.preprocess(raw_text, to_list=True)
            latest_anchor = self.anchor_history[-1]

            # print(f"\033[94m[调试] 当前锚点历史（最后 2 个）:")
            # for i in range(max(0, len(self.anchor_history) - 2), len(self.anchor_history)):
            #     print(
            #         f"  - Anchor[{i}]: words={self.anchor_history[i]['words'][:10]}..., next_preview={self.anchor_history[i]['next_preview']}")
            # print("\033[0m", end="")

            anchor_end_word_index = self.find_last_sublist_end_index(current_text_words, latest_anchor['words'])

            # --- 正常匹配 --- #
            if anchor_end_word_index != -1:
                action_taken = "[正常流程]"

            # --- 尝试“上下文重构” --- #
            elif len(self.anchor_history) > 1:
                prev_anchor = self.anchor_history[-2]
                prev_anchor_end_idx = self.find_last_sublist_end_index(current_text_words, prev_anchor['words'])

                if prev_anchor_end_idx != -1:
                    next_preview_start_idx = self.find_first_sublist_start_index(
                        current_text_words,
                        latest_anchor['next_preview'],
                        start_from=prev_anchor_end_idx
                    )

                    if next_preview_start_idx != -1:
                        action_taken = "[修正流程]"
                        print(f"\033[93m  [调试] {action_taken} 启动！使用上下文重构锚点...\033[0m")

                        reconstructed_words = current_text_words[prev_anchor_end_idx:next_preview_start_idx]

                        print(f"    旧锚点: {latest_anchor['words']}")
                        print(f"    新锚点: {reconstructed_words}")

                        self.anchor_history[-1]['words'] = reconstructed_words
                        latest_anchor = self.anchor_history[-1]
                        anchor_end_word_index = self.find_last_sublist_end_index(current_text_words,
                                                                                 latest_anchor['words'])

                else:
                    # 降级方案：若前锚点也失效但 next_preview 还存在
                    next_preview_start_idx = self.find_first_sublist_start_index(
                        current_text_words,
                        latest_anchor['next_preview']
                    )
                    if next_preview_start_idx != -1:
                        action_taken = "[部分修正-降级]"
                        print(f"\033[96m  [调试] {action_taken}：前锚点丢失，但找到 next_preview。\033[0m")
                        anchor_end_word_index = next_preview_start_idx

            # --- 重大跳跃 --- #
            if not action_taken:
                action_taken = "[重大跳跃]"
                print(f"\033[1;31m  [调试] {action_taken}：无法匹配任何锚点，重置状态。\033[0m")
                newly_added_sentences = self._reset_and_process_all(current_sentences)

            # --- 分析新内容 --- #
            elif anchor_end_word_index != -1 and anchor_end_word_index < len(current_text_words):
                # 使用更稳健的方式定位新内容的字符起点
                word_spans = [m.span() for m in re.finditer(r'\S+', raw_text)]
                if anchor_end_word_index < len(word_spans):
                    new_text_start_char_index = word_spans[anchor_end_word_index][0]
                    new_text_to_process = raw_text[new_text_start_char_index:]
                else:
                    new_text_to_process = ''

                # print(f"\033[92m[调试] 正在分析锚点后的新内容: '{new_text_to_process}'\033[0m")

                new_potential_sentences = self.segmenting_sentences(new_text_to_process)
                if len(new_potential_sentences) > 1:
                    newly_added_sentences = self._handle_sentence_batch(
                        new_potential_sentences[:-1],
                        new_potential_sentences[-1]
                    )

        # --- 打印结果 --- #
        # if newly_added_sentences:
        #     print(f"{'=' * 60}\n原始文本：{raw_text}\n")
        #     print("=" * 60)
        #     print(f"【本轮新增句子】({action_taken}):")
        #     for sent in newly_added_sentences:
        #         print(f"  -> {sent}")
        #     print("\n【当前句子总列表（最近3句）】: ")
        #     for idx, sent in enumerate(self.total_sentences_list[-3:]):
        #         print(f"  [{idx}] {sent}")
        #     print("=" * 60 + "\n")

        return newly_added_sentences, new_text_to_process


# ---------------- 程序入口 ---------------- #
if __name__ == "__main__":
    text_getter = Get_text()
    try:
        while True:
            text_getter.main_event()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n程序已停止。")
