import re
import threading
import time
from datetime import datetime
from queue import Queue
from typing import TYPE_CHECKING, Any

from .config import AppConfig

if TYPE_CHECKING:
    from .livecaptions import LiveCaptionsSource


class TranslatorService:
    def __init__(
        self,
        config: AppConfig,
        captions: "LiveCaptionsSource",
        subtitle_queue: Queue,
        status_queue: Queue,
        client: Any | None = None,
    ):
        self.config = config
        self.captions = captions
        self.subtitle_queue = subtitle_queue
        self.status_queue = status_queue
        self.client = client or self._create_client(config)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="TranslatorService", daemon=True)
        self._running = True
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> bool:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        stopped = not (self._thread and self._thread.is_alive())
        if stopped:
            self._running = False
            self._thread = None
        return stopped

    def _run(self) -> None:
        now_text = datetime.now().strftime("%m/%d/%Y, %H:%M")
        messages = [{"role": "system", "content": self.config.system_prompt(now_text)}]
        total_tokens = 0
        translator_cache = {"en": [], "zh": []}
        self._put_status("message", message="翻译线程已启动")

        try:
            while not self._stop_event.is_set():
                start_time = time.time()
                raw_text = self.captions.get_text()
                if not raw_text:
                    self._sleep_short()
                    continue

                update = self.captions.process_text(raw_text)
                if not update.complete_sentences and not update.live_sentence.strip():
                    self._sleep_short()
                    continue

                live_output = "..."
                if update.complete_sentences:
                    complete_input = " ".join(update.complete_sentences)
                    output, total_tokens = self._translate_complete(messages, complete_input, total_tokens)
                    if output:
                        translator_cache["en"].append(self.preprocess(complete_input))
                        translator_cache["zh"].append(output)
                        messages.append({"role": "assistant", "content": output})

                if update.live_sentence:
                    live_output, total_tokens = self._translate_live(
                        messages,
                        update.live_sentence,
                        total_tokens,
                    )

                self._put_subtitle(live_output, translator_cache)
                self._put_status(
                    "token_usage",
                    current=total_tokens,
                    total=self.config.server.model_context_window,
                )
                translator_cache, messages = self._maintain_context(
                    translator_cache,
                    total_tokens,
                    messages,
                )

                run_time = time.time() - start_time
                delay = max(0.0, self.config.logic.delay_time - run_time)
                if delay:
                    self._stop_event.wait(delay)
        finally:
            self._running = False
            self._put_status("message", message="翻译线程已停止")

    def _translate_complete(
        self,
        messages: list[dict[str, str]],
        text: str,
        current_tokens: int,
    ) -> tuple[str, int]:
        messages.append({"role": "user", "content": text})
        try:
            completion = self.client.chat.completions.create(
                model=self.config.server.model,
                messages=messages,
                **self.config.completion_config,
            )
            output = completion.choices[0].message.content or ""
            return output, self._extract_tokens(completion, current_tokens)
        except Exception as exc:
            messages.pop()
            self._put_status("error", message=f"完整句翻译失败: {exc}")
            return "", current_tokens

    def _translate_live(
        self,
        messages: list[dict[str, str]],
        text: str,
        current_tokens: int,
    ) -> tuple[str, int]:
        live_prompt = f"{text.strip()}..." if not text.endswith(".") else text
        messages.append({"role": "user", "content": live_prompt})
        try:
            completion = self.client.chat.completions.create(
                model=self.config.server.model,
                messages=messages,
                **self.config.live_config,
            )
            output = completion.choices[0].message.content or "..."
            return output, self._extract_tokens(completion, current_tokens)
        except Exception as exc:
            self._put_status("error", message=f"实时句翻译失败: {exc}")
            return "...", current_tokens
        finally:
            messages.pop()

    def _put_subtitle(self, live_text: str, translator_cache: dict[str, list[str]]) -> None:
        history = "\n".join(translator_cache["zh"])
        subtitle = f"{history}\n{live_text}".strip()
        self.subtitle_queue.put({"subtitle": subtitle})

    def _put_status(self, status_type: str, **payload) -> None:
        self.status_queue.put({"type": status_type, **payload})

    def _sleep_short(self) -> None:
        self._stop_event.wait(0.1)

    def _maintain_context(
        self,
        translator_cache: dict[str, list[str]],
        total_tokens: int,
        messages: list[dict[str, str]],
    ) -> tuple[dict[str, list[str]], list[dict[str, str]]]:
        cache_size = self.config.logic.translator_cache
        translator_cache["en"] = translator_cache["en"][-cache_size:]
        translator_cache["zh"] = translator_cache["zh"][-cache_size:]

        threshold = self.config.server.model_context_window - self.config.logic.available_tokens
        if total_tokens >= threshold:
            self._put_status("message", message="Token 上下文接近上限，已裁剪对话历史")
            messages = [messages[0]] + messages[-6:] if len(messages) > 6 else [messages[0]]
        return translator_cache, messages

    @staticmethod
    def preprocess(text: str) -> str:
        return re.sub(r"(?<!\d)[.,;:!?-](?!\d)", "", text or "").lower()

    @staticmethod
    def _extract_tokens(completion: Any, fallback: int) -> int:
        usage = getattr(completion, "usage", None)
        return getattr(usage, "total_tokens", fallback) if usage else fallback

    @staticmethod
    def _create_client(config: AppConfig):
        from openai import OpenAI

        return OpenAI(
            base_url=config.server.base_url,
            api_key=config.server.api_key,
            timeout=20,
        )
