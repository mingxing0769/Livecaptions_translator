import configparser
import tempfile
import unittest
from pathlib import Path

from live_translator.config import load_config


class ConfigTests(unittest.TestCase):
    def test_legacy_server_section_is_migrated_and_backed_up(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.ini"
            path.write_text(
                "[Sever]\nbase_url = http://old/v1\napi_key = key\nmodel = model-a\nmodel_context_window = 1234\n",
                encoding="utf-8",
            )

            app_config = load_config(path)
            parser = configparser.ConfigParser()
            parser.read(path, encoding="utf-8")

            self.assertEqual(app_config.server.base_url, "http://old/v1")
            self.assertTrue(parser.has_section("Server"))
            self.assertFalse(parser.has_section("Sever"))
            self.assertTrue(path.with_suffix(".ini.bak").exists())

    def test_defaults_are_created_when_config_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.ini"
            app_config = load_config(path)
            self.assertTrue(path.exists())
            self.assertEqual(app_config.logic.active_prompt, "Prompt_F1")


if __name__ == "__main__":
    unittest.main()

