import unittest

from ao_chests_db import SCENA_FLAGS_OFFSET, load_default_chest_catalog


class ChestCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_default_chest_catalog()

    def test_reference_is_complete_and_localized(self):
        self.assertEqual(len(self.catalog), 280)
        self.assertEqual(len(self.catalog.maps("zh_cn")), 44)
        self.assertEqual(len(self.catalog.maps("ja")), 44)
        self.assertEqual(len(self.catalog.maps("en")), 44)
        for record in self.catalog.records():
            for locale in ("zh_cn", "ja", "en"):
                self.assertTrue(record.map_name(locale), (record.id, locale))
                self.assertTrue(record.item_name(locale), (record.id, locale))

    def test_flags_are_read_without_mutating_save(self):
        data = bytearray(SCENA_FLAGS_OFFSET + 0x220)
        record = self.catalog.records()[0]
        before = bytes(data)
        self.assertFalse(record.is_opened(data))
        data[SCENA_FLAGS_OFFSET + record.flag_offset] |= 1 << record.flag_bit
        self.assertTrue(record.is_opened(data))
        data[SCENA_FLAGS_OFFSET + record.flag_offset] &= ~(1 << record.flag_bit)
        self.assertEqual(bytes(data), before)

    def test_missing_filter_and_cross_locale_search(self):
        data = bytearray(SCENA_FLAGS_OFFSET + 0x220)
        first = self.catalog.records()[0]
        data[SCENA_FLAGS_OFFSET + first.flag_offset] |= 1 << first.flag_bit
        missing = self.catalog.search(missing_only=True, save_data=data)
        self.assertEqual(len(missing), 279)
        self.assertNotIn(first, missing)
        self.assertTrue(self.catalog.search("Altair Lodge", locale="zh_cn"))

    def test_coordinates_use_recordviewer_world_units(self):
        first = self.catalog.records()[0]
        self.assertEqual(first.coordinates(), (147.32, 22.18, -4.0))


if __name__ == "__main__":
    unittest.main()
