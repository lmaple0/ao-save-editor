import unittest

from ao_save_editor import DIFFICULTY_NAMES, UI_TRANSLATIONS


class DifficultyMappingTests(unittest.TestCase):
    def test_verified_bzh_difficulty_enum_is_exposed(self):
        self.assertEqual(
            DIFFICULTY_NAMES,
            {0: "Normal", 1: "Hard", 2: "Nightmare", 3: "Easy"},
        )

    def test_difficulty_hint_uses_verified_order_in_all_languages(self):
        key = "难度 (0=Normal 1=Hard 2=Nightmare 3=Easy)"
        expected = {
            "zh_cn": key,
            "en": "Difficulty (0=Normal 1=Hard 2=Nightmare 3=Easy)",
            "ja": "難易度 (0=Normal 1=Hard 2=Nightmare 3=Easy)",
        }
        for locale, value in expected.items():
            self.assertEqual(UI_TRANSLATIONS[locale].get(key), value)


if __name__ == "__main__":
    unittest.main()
