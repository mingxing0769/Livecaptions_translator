import concurrent.futures
import re
import subprocess
import time

import psutil
import uiautomation as auto
import win32con
import win32gui
from uiautomation import UIAutomationInitializerInThread

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
        # 从 config.py 读取实时字幕软件路径和窗口标题
        self.CAPTION_APP_PATH = config.CAPTION_APP_PATH
        self.CAPTION_WINDOW_TITLE = config.CAPTION_WINDOW_TITLE

        # 存储所有完整句子
        self.total_sentences_list = []
        # 存储所有锚点（句子词序列 + 下一句预览）
        self.anchor_history = []
        # 存储上一次抓到的完整原始文本
        self.previous_raw_text = ""



    def start_livecaptions_windows(self):
        """
        使用动态等待和性能分析。
        """
        try:
            window = auto.WindowControl(Name=self.CAPTION_WINDOW_TITLE, searchDepth=1)
            if not window.Exists(0, 0):
                print("包装器失效或未初始化，开始查找窗口...")
                try:
                    subprocess.Popen(self.CAPTION_APP_PATH)
                    print("等待 livecaptions.exe 启动...")
                    time.sleep(2)
                    print("成功连接到主窗口")

                except FileNotFoundError:
                    print(f"错误：找不到实时字幕软件，请检查路径：{self.CAPTION_APP_PATH}")
                    return

            if config.HIDE_LIVECAPTIONS_WINDOW:
                win32gui.SetWindowPos(window.NativeWindowHandle, 0, -3000, -3000, 0, 0,
                                      win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)
                print("窗口移动成功。")

        except Exception as e:
            print(f"start_livecaptions_windows 发生未知错误: {e}")
            self.shutdown()  # 发生严重错误时，尝试清理

    def shutdown(self):
        try:
            window = auto.WindowControl(Name=self.CAPTION_WINDOW_TITLE, searchDepth=1)
            if window.Exists(0, 0):
                pid = window.ProcessId
                p = psutil.Process(pid)
                p.terminate()
                p.wait(timeout=2)
                print("livecaptions.exe 已成功关闭。")
            else:
                print("未找到正在运行的 livecaptions.exe 窗口。")
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            print("⚠️ 关闭已在运行的进程时出现问题。")
        except Exception as e:
            print(f"❌ 关闭 livecaptions.exe 时发生未知错误: {e}")

    def _fetch_text(self):
        """
        【已优化】在后台线程中获取文本。职责单一，只管获取。
        """
        with UIAutomationInitializerInThread():
            window = auto.WindowControl(Name=self.CAPTION_WINDOW_TITLE, searchDepth=1)
            if window.Exists(0, 0):
                text_control = window.TextControl()
                if text_control.Exists(0, 0):
                    return text_control.Name or ""
            # 如果窗口或控件不存在，直接返回空
            return ""

    def get_text(self):
        """
        【已优化】在一个独立的线程中获取文本，并设置超时保护和重启逻辑。
        """
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._fetch_text)
                text = future.result(timeout=0.5)

                # 如果返回空，检查一下是不是窗口真的关闭了
                if not text:
                    window = auto.WindowControl(Name=self.CAPTION_WINDOW_TITLE, searchDepth=1)
                    if not window.Exists(0, 0):
                        print("⚠️ Live Captions 窗口已关闭，正在尝试重启...")
                        self.start_livecaptions_windows()

                return ' '.join(text.split()[-config.MAX_INPUT_WORDS:]).replace("已准备好在 英语(美国) 中显示实时字幕",
                                                                                '').replace('\n', ' ').strip()

        except concurrent.futures.TimeoutError:
            return ""  # 超时是正常保护，返回空

        except Exception as e:
            print(f"get_text 发生严重错误: {e}")
            return ""


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
            return self._handle_sentence_batch(current_sentences[-5:-1], current_sentences[-1])
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
        live_sentence_fragment = ''
        action_taken = None

        # ----------- 首次运行 ----------- #
        if not self.anchor_history:
            action_taken = "[首次运行]"
            newly_added_sentences = self._reset_and_process_all(current_sentences)
            live_sentence_fragment = current_sentences[-1] if current_sentences else ''


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
                        reconstructed_words = current_text_words[prev_anchor_end_idx:next_preview_start_idx]

                        # --- 漏洞修复点：只有当重构结果非空时才更新锚点 ---
                        if reconstructed_words:  # 确保重构的词列表不为空
                            action_taken = "[修正流程]"
                            print(f"\033[93m  [调试] {action_taken} 启动！使用上下文重构锚点...\033[0m")

                            print(f"    旧锚点: {latest_anchor['words']}")
                            print(f"    新锚点: {reconstructed_words}")

                            self.anchor_history[-1]['words'] = reconstructed_words
                            latest_anchor = self.anchor_history[-1]  # 更新本地引用
                            anchor_end_word_index = self.find_last_sublist_end_index(current_text_words,
                                                                                     latest_anchor['words'])
                        else:
                            # 如果重构结果为空，说明修正失败，不更新锚点，让其进入“重大跳跃”逻辑
                            print(f"\033[91m  [调试] [修正流程] 失败：重构词列表为空。将尝试重大跳跃。\033[0m")
                            action_taken = None  # 重置 action_taken，以便触发后续的“重大跳跃”
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

                    live_sentence_fragment = new_potential_sentences[-1]
                else:
                    # 如果只分割出一个或零个句子，说明还没有新的完整句
                    # 那么整块新文本都是实时句
                    live_sentence_fragment = new_text_to_process

        return newly_added_sentences, live_sentence_fragment


# ---------------- 程序入口 ---------------- #
if __name__ == "__main__":
    text_getter = Get_text()
    try:
        text_getter.start_livecaptions_windows()
        while True:
            text_getter.main_event()
            time.sleep(0.5)
    except KeyboardInterrupt:
        text_getter.shutdown()
        print("\n程序已停止。")