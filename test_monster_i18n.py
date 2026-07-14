import unittest

from ao_monsters_db import load_default_monster_catalog


class MonsterI18nTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_default_monster_catalog()

    def test_every_reference_has_localized_name_and_location(self):
        self.assertEqual(len(self.catalog), 305)
        for record in self.catalog.records():
            for locale in ("zh_cn", "ja", "en"):
                self.assertTrue(record.name(locale), (record.ms_file, locale))
                self.assertTrue(record.locations(locale), (record.ms_file, locale))

    def test_local_ms_names_cover_variant_records(self):
        record = self.catalog.get(0x30080700)
        self.assertEqual(record.name("zh_cn"), "矿岩领主")
        self.assertEqual(record.name("ja"), "ロックドミナ")
        self.assertEqual(record.name("en"), "Rock Domina")

    def test_localized_location_filter_and_cross_locale_search(self):
        self.assertTrue(self.catalog.search("Altair Lodge", locale="en"))
        matches = self.catalog.search("", "Altair Lodge", "en")
        self.assertTrue(matches)
        self.assertTrue(all("Altair Lodge" in record.locations("en") for record in matches))


if __name__ == "__main__":
    unittest.main()
