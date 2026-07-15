import unittest
from pathlib import Path

import ao_loadout_ui


ROOT = Path(__file__).resolve().parent


class LoadoutUiContractTests(unittest.TestCase):
    def test_all_ui_languages_are_complete(self):
        expected = set(ao_loadout_ui.LOADOUT_TEXT["zh_cn"])
        self.assertEqual(set(ao_loadout_ui.LOADOUT_TEXT), {"zh_cn", "en", "ja"})
        for language, rows in ao_loadout_ui.LOADOUT_TEXT.items():
            with self.subTest(language=language):
                self.assertEqual(set(rows), expected)

    def test_editable_tab_methods_and_immediate_apply_are_present(self):
        source = (ROOT / "ao_loadout_ui.py").read_text(encoding="utf-8")
        for method in (
            "def _build_loadout_tab",
            "def _refresh_loadout_ui",
            "def _apply_loadout_from_ui",
            "def _on_loadout_value_changed",
        ):
            self.assertIn(method, source)
        self.assertIn("apply_character_loadout_changes", source)
        self.assertIn('"<<ComboboxSelected>>", self._on_loadout_value_changed', source)

    def test_save_editor_registers_loadout_tab_and_refresh_lifecycle(self):
        source = (ROOT / "ao_save_editor.py").read_text(encoding="utf-8")
        self.assertIn("class SaveEditor(LoadoutUiMixin, ReferenceIndexUiMixin, tk.Tk)", source)
        self.assertIn("self._build_loadout_tab(frm_loadout, item_name, character_name)", source)
        self.assertIn('self._is_active_tab("人物装备 / 回路")', source)


if __name__ == "__main__":
    unittest.main()
