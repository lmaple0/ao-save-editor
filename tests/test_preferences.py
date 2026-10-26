import json
from pathlib import Path
import tempfile
import unittest

from ao_preferences import language_for_locale, load_language, save_language


class LanguagePreferencesTests(unittest.TestCase):
    def test_system_language_mapping(self):
        for value, expected in (("zh-CN", "zh_cn"), ("zh_TW", "zh_cn"),
                                ("ja_JP", "ja"), ("en_US", "en"), ("fr_FR", "en")):
            with self.subTest(locale=value):
                self.assertEqual(language_for_locale(value), expected)

    def test_first_launch_then_saved_choice_overrides_system(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "AoSaveEditor/settings.json"
            self.assertEqual(load_language(path, "ja_JP"), "ja")
            self.assertFalse(path.exists())
            save_language(path, "en")
            self.assertEqual(load_language(path, "ja_JP"), "en")
            self.assertEqual(json.loads(path.read_text())['language'], "en")
            save_language(path, "zh_cn")
            self.assertEqual(load_language(path, "en_US"), "zh_cn")


if __name__ == "__main__":
    unittest.main()
