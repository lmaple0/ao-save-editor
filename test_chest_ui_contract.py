import unittest

from ao_save_editor import CHEST_CATALOG, SaveEditor, UI_TRANSLATIONS


class ChestUiContractTests(unittest.TestCase):
    def test_catalog_and_ui_methods_are_available(self):
        self.assertEqual(len(CHEST_CATALOG), 280)
        for method in ("_build_chest_tab", "_refresh_chest_ui", "_clear_chest_filter"):
            self.assertTrue(callable(getattr(SaveEditor, method)))

    def test_chest_ui_strings_cover_all_languages(self):
        keys = (
            "宝箱进度",
            "搜索宝箱:",
            "全部地图",
            "仅显示缺失",
            "已取得",
            "未取得",
            "宝箱: 已取得 {opened}/{total}，缺失 {missing}，当前显示 {shown}",
        )
        for locale in ("zh_cn", "ja", "en"):
            for key in keys:
                self.assertTrue(UI_TRANSLATIONS[locale].get(key), (locale, key))


if __name__ == "__main__":
    unittest.main()
