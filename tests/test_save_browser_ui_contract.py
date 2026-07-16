import inspect
import unittest

from ao_save_browser import SAVE_BROWSER_TRANSLATIONS
from ao_save_editor import SaveEditor, TAB_TITLE_I18N, UI_TRANSLATIONS, tab_title


class SaveBrowserUiContractTests(unittest.TestCase):
    def test_editor_exposes_browser_and_safe_loader(self):
        source = inspect.getsource(SaveEditor)
        for method in (
            "_build_save_browser",
            "_refresh_save_browser",
            "_load_selected_save",
            "_load_save_path",
            "_toggle_save_browser",
            "_apply_compact_tab_titles",
        ):
            self.assertTrue(hasattr(SaveEditor, method))
        self.assertIn("candidate = SaveData()", source)
        self.assertIn("messagebox.askyesno", source)

    def test_browser_text_has_all_languages(self):
        for locale in ("zh_cn", "en", "ja"):
            for key in SAVE_BROWSER_TRANSLATIONS["zh_cn"]:
                self.assertTrue(UI_TRANSLATIONS[locale].get(key), (locale, key))


    def test_compact_tab_titles_cover_every_tab_without_long_english_labels(self):
        expected_keys = set(TAB_TITLE_I18N["zh_cn"])
        self.assertEqual(len(expected_keys), 15)
        for locale in ("zh_cn", "en", "ja"):
            self.assertEqual(set(TAB_TITLE_I18N[locale]), expected_keys)
            self.assertTrue(all(tab_title(key, locale) for key in expected_keys))
        self.assertLessEqual(max(map(len, TAB_TITLE_I18N["en"].values())), 12)

if __name__ == "__main__":
    unittest.main()
