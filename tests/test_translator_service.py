import configparser
import unittest
from queue import Queue
from types import SimpleNamespace

from live_translator.config import build_app_config, normalize_config
from live_translator.translator_service import TranslatorService


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="译文"))],
            usage=SimpleNamespace(total_tokens=42),
        )


class FakeClient:
    def __init__(self):
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class TranslatorServiceTests(unittest.TestCase):
    def make_service(self):
        parser = configparser.ConfigParser()
        normalize_config(parser)
        config = build_app_config(parser, path=None)
        return TranslatorService(config, captions=None, subtitle_queue=Queue(), status_queue=Queue(), client=FakeClient())

    def test_complete_translation_appends_user_message_on_success(self):
        service = self.make_service()
        messages = [{"role": "system", "content": "sys"}]
        output, tokens = service._translate_complete(messages, "Hello.", 0)
        self.assertEqual(output, "译文")
        self.assertEqual(tokens, 42)
        self.assertEqual(messages[-1], {"role": "user", "content": "Hello."})

    def test_live_translation_removes_temporary_user_message(self):
        service = self.make_service()
        messages = [{"role": "system", "content": "sys"}]
        output, tokens = service._translate_live(messages, "Hello", 0)
        self.assertEqual(output, "译文")
        self.assertEqual(tokens, 42)
        self.assertEqual(messages, [{"role": "system", "content": "sys"}])

    def test_context_maintenance_trims_messages_when_near_limit(self):
        service = self.make_service()
        messages = [{"role": "system", "content": "sys"}] + [
            {"role": "user", "content": str(index)} for index in range(10)
        ]
        cache, trimmed = service._maintain_context({"en": [], "zh": []}, 9999, messages)
        self.assertEqual(trimmed[0]["role"], "system")
        self.assertLessEqual(len(trimmed), 7)
        self.assertEqual(cache, {"en": [], "zh": []})


if __name__ == "__main__":
    unittest.main()

