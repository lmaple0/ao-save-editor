import unittest

import ao_save_editor
from ao_save_editor import SaveEditor, UI_TRANSLATIONS, get_save_auditor


class SaveAuditUiContractTests(unittest.TestCase):
    def test_auditor_and_read_only_ui_methods_are_available(self):
        auditor = get_save_auditor()
        self.assertEqual(len(auditor.known_monster_codes), 305)
        for method in (
            "_build_save_audit_tab",
            "_set_save_audit_text",
            "_refresh_save_audit",
        ):
            self.assertTrue(callable(getattr(SaveEditor, method)))

    def test_lazy_catalog_getters_cache_instances(self):
        self.assertIs(get_save_auditor(), get_save_auditor())
        self.assertIs(
            ao_save_editor.get_monster_detail_catalog(),
            ao_save_editor.get_monster_detail_catalog(),
        )

    def test_audit_ui_strings_cover_all_languages(self):
        for locale in ("zh_cn", "en", "ja"):
            for key in ("存档诊断", "刷新诊断", "诊断数据不可用"):
                self.assertTrue(UI_TRANSLATIONS[locale].get(key), (locale, key))


if __name__ == "__main__":
    unittest.main()
