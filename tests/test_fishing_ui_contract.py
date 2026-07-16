import inspect
import unittest

from ao_fishing_ui import FishingUiMixin
from ao_save_editor import SaveEditor, ui_text


class FishingUiContractTests(unittest.TestCase):
    def test_editor_registers_fishing_mixin(self):
        self.assertTrue(issubclass(SaveEditor, FishingUiMixin))

    def test_edit_actions_are_present(self):
        source = inspect.getsource(FishingUiMixin)
        self.assertIn("_register_selected_fish", source)
        self.assertIn("_unregister_selected_fish", source)
        self.assertIn("_apply_selected_fish_size", source)
        self.assertIn("register_all_fish(self.save.data)", source)

    def test_fishing_ui_strings_cover_all_languages(self):
        self.assertEqual(ui_text("钓鱼手册", "en"), "Fishing Notebook")
        self.assertEqual(ui_text("选中 → 登记", "ja"), "選択 → 登録")
        self.assertEqual(ui_text("选中 → 未登记", "en"), "Selected → Unregistered")


if __name__ == "__main__":
    unittest.main()
