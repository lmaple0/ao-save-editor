import unittest

from ao_save_editor import SaveEditor, UI_TRANSLATIONS, get_monster_detail_catalog


class MonsterDetailUiContractTests(unittest.TestCase):
    def test_detail_catalog_and_read_only_ui_methods_are_available(self):
        self.assertEqual(len(get_monster_detail_catalog()), 333)
        for method in (
            "_refresh_monster_detail",
            "_set_monster_detail_text",
            "_clean_monster_detail_text",
        ):
            self.assertTrue(callable(getattr(SaveEditor, method)))

    def test_detail_ui_strings_cover_all_languages(self):
        keys = (
            "怪物详情",
            "请选择一个怪物查看详情",
            "怪物详情数据不可用",
            "属性有效率",
            "异常抗性",
            "掉落耀晶片",
            "掉落物",
            "战技",
            "说明",
        )
        for locale in ("zh_cn", "ja", "en"):
            for key in keys:
                self.assertTrue(UI_TRANSLATIONS[locale].get(key), (locale, key))

    def test_control_codes_are_flattened_for_detail_display(self):
        self.assertEqual(
            SaveEditor._clean_monster_detail_text("line one\\nline two\r\nline three"),
            "line one line two line three",
        )


if __name__ == "__main__":
    unittest.main()
