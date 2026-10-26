import unittest

from ao_item_add_ui import ITEM_ADD_TRANSLATIONS
from ao_save_container import FORMAT_CLE_KAI, FORMAT_NISA_ZSTD
from ao_save_editor import SaveData, EXPECTED_SIZE, ITEM_ORDERED_CODES


class AddItemsTests(unittest.TestCase):
    def test_add_missing_then_owned_item_without_replacement(self):
        for edition in (FORMAT_NISA_ZSTD, FORMAT_CLE_KAI):
            with self.subTest(edition=edition):
                save = SaveData()
                save.data = bytearray(EXPECTED_SIZE)
                save.container_format = edition
                first, second = ITEM_ORDERED_CODES[:2]
                save.write_items({first: 3})
                self.assertEqual(save.add_item(second, 5), 5)
                self.assertEqual(save.read_items(), {first: 3, second: 5})
                self.assertEqual(save.add_item(second, 2), 7)
                self.assertEqual(save.read_items(), {first: 3, second: 7})
                before = bytes(save.data)
                with self.assertRaises(ValueError):
                    save.add_item(second, 99)
                self.assertEqual(bytes(save.data), before)

    def test_add_to_empty_inventory_and_validate_quantity(self):
        save = SaveData()
        save.data = bytearray(EXPECTED_SIZE)
        code = ITEM_ORDERED_CODES[0]
        self.assertEqual(save.add_item(code, 99), 99)
        for quantity in (0, -1, 100):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                save.add_item(code, quantity)
        self.assertEqual(save.read_items(), {code: 99})

    def test_dialog_labels_cover_all_supported_languages(self):
        for language in ("zh_cn", "en", "ja"):
            self.assertEqual(set(ITEM_ADD_TRANSLATIONS[language]), set(ITEM_ADD_TRANSLATIONS["zh_cn"]))
            self.assertTrue(all(ITEM_ADD_TRANSLATIONS[language].values()))


if __name__ == "__main__":
    unittest.main()
