import re
from dataclasses import dataclass, field
from typing import Callable

from .sentence import split_english_sentences


NEXT_SENTENCE_PREVIEW_WORDS = 5


@dataclass
class CaptionUpdate:
    complete_sentences: list[str]
    live_sentence: str
    action: str = ""


@dataclass
class CaptionTracker:
    sentence_splitter: Callable[[str], list[str]] = split_english_sentences
    total_sentences_list: list[str] = field(default_factory=list)
    anchor_history: list[dict[str, list[str]]] = field(default_factory=list)
    previous_raw_text: str = ""

    @staticmethod
    def preprocess(text: str, to_list: bool = False):
        text_lower = (text or "").lower()
        text_no_punct = re.sub(r"[.,;:!?]", "", text_lower)
        text_normalized = re.sub(r"\s+", " ", text_no_punct).strip()
        if to_list:
            return [word for word in text_normalized.split() if word]
        return text_normalized

    @staticmethod
    def find_last_sublist_end_index(main_list: list[str], sub_list: list[str]) -> int:
        if not sub_list or not main_list:
            return -1
        sub_len = len(sub_list)
        for i in range(len(main_list) - sub_len, -1, -1):
            if main_list[i:i + sub_len] == sub_list:
                return i + sub_len
        return -1

    @staticmethod
    def find_first_sublist_start_index(
        main_list: list[str],
        sub_list: list[str],
        start_from: int = 0,
    ) -> int:
        if not sub_list or not main_list:
            return -1
        sub_len = len(sub_list)
        for i in range(start_from, len(main_list) - sub_len + 1):
            if main_list[i:i + sub_len] == sub_list:
                return i
        return -1

    def process(self, raw_text: str) -> CaptionUpdate:
        """Return complete and live caption text while preserving the legacy anchor logic."""
        if not raw_text or raw_text == self.previous_raw_text:
            return CaptionUpdate([], "", "no_change")

        self.previous_raw_text = raw_text
        current_sentences = self.sentence_splitter(raw_text)
        if len(current_sentences) < 1:
            return CaptionUpdate([], "", "empty")

        newly_added_sentences: list[str] = []
        live_sentence_fragment = ""
        action_taken = None

        if not self.anchor_history:
            action_taken = "first_run"
            newly_added_sentences = self._reset_and_process_all(current_sentences)
            live_sentence_fragment = current_sentences[-1] if current_sentences else ""
        else:
            current_text_words = self.preprocess(raw_text, to_list=True)
            latest_anchor = self.anchor_history[-1]
            anchor_end_word_index = self.find_last_sublist_end_index(
                current_text_words,
                latest_anchor["words"],
            )

            if anchor_end_word_index != -1:
                action_taken = "normal"
            elif len(self.anchor_history) > 1:
                prev_anchor = self.anchor_history[-2]
                prev_anchor_end_idx = self.find_last_sublist_end_index(
                    current_text_words,
                    prev_anchor["words"],
                )

                if prev_anchor_end_idx != -1:
                    next_preview_start_idx = self.find_first_sublist_start_index(
                        current_text_words,
                        latest_anchor["next_preview"],
                        start_from=prev_anchor_end_idx,
                    )

                    if next_preview_start_idx != -1:
                        reconstructed_words = current_text_words[
                            prev_anchor_end_idx:next_preview_start_idx
                        ]
                        if reconstructed_words:
                            action_taken = "repair"
                            self.anchor_history[-1]["words"] = reconstructed_words
                            latest_anchor = self.anchor_history[-1]
                            anchor_end_word_index = self.find_last_sublist_end_index(
                                current_text_words,
                                latest_anchor["words"],
                            )
                        else:
                            action_taken = None
                else:
                    next_preview_start_idx = self.find_first_sublist_start_index(
                        current_text_words,
                        latest_anchor["next_preview"],
                    )
                    if next_preview_start_idx != -1:
                        action_taken = "fallback"
                        anchor_end_word_index = next_preview_start_idx

            if not action_taken:
                action_taken = "reset"
                newly_added_sentences = self._reset_and_process_all(current_sentences)
            elif anchor_end_word_index != -1 and anchor_end_word_index < len(current_text_words):
                word_spans = [match.span() for match in re.finditer(r"\S+", raw_text)]
                if anchor_end_word_index < len(word_spans):
                    new_text_start_char_index = word_spans[anchor_end_word_index][0]
                    new_text_to_process = raw_text[new_text_start_char_index:]
                else:
                    new_text_to_process = ""

                new_potential_sentences = self.sentence_splitter(new_text_to_process)
                if len(new_potential_sentences) > 1:
                    newly_added_sentences = self._handle_sentence_batch(
                        new_potential_sentences[:-1],
                        new_potential_sentences[-1],
                    )
                    live_sentence_fragment = new_potential_sentences[-1]
                else:
                    live_sentence_fragment = new_text_to_process

        return CaptionUpdate(newly_added_sentences, live_sentence_fragment, action_taken or "")

    def _handle_sentence_batch(
        self,
        sentences_to_process: list[str],
        last_incomplete_sentence: str,
    ) -> list[str]:
        added_sentences: list[str] = []

        for index, sentence in enumerate(sentences_to_process):
            clean_sentence = sentence.strip()
            if not clean_sentence:
                continue

            added_sentences.append(clean_sentence)
            self.total_sentences_list.append(clean_sentence)

            if index + 1 < len(sentences_to_process):
                next_preview_text = sentences_to_process[index + 1]
            else:
                next_preview_text = last_incomplete_sentence

            next_preview_words = self.preprocess(next_preview_text, to_list=True)
            if next_preview_words and not next_preview_text.endswith(" "):
                next_preview_words = next_preview_words[:-1]
            next_preview_words = next_preview_words[:NEXT_SENTENCE_PREVIEW_WORDS]

            self.anchor_history.append({
                "words": self.preprocess(clean_sentence, to_list=True),
                "next_preview": next_preview_words,
            })

        return added_sentences

    def _reset_and_process_all(self, current_sentences: list[str]) -> list[str]:
        self.total_sentences_list.clear()
        self.anchor_history.clear()
        if len(current_sentences) > 1:
            return self._handle_sentence_batch(current_sentences[-5:-1], current_sentences[-1])
        return []

