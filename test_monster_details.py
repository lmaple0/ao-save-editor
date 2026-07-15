import unittest

from ao_monster_details_db import load_default_monster_detail_catalog
from ao_monsters_db import load_default_monster_catalog


class MonsterDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.details = load_default_monster_detail_catalog()
        cls.monsters = load_default_monster_catalog()

    def test_full_nisa_ms_catalog_is_loaded(self):
        self.assertEqual(len(self.details), 333)
        self.assertEqual(
            self.details.metadata["summary"]["localized_name_count"],
            {"zh_cle": 333, "ja": 333, "en": 333},
        )
        self.assertEqual(self.details.metadata["summary"]["with_effective_action_script"], 333)

    def test_all_save_monsters_have_matching_details(self):
        self.assertEqual(len(self.monsters), 305)
        for monster in self.monsters.records():
            detail = self.details.get(monster.ms_file)
            self.assertIsNotNone(detail, monster.ms_file)
            self.assertEqual(detail.data["level"], monster.level)
            for locale in ("zh_cn", "ja", "en"):
                self.assertEqual(detail.name(locale), monster.name(locale))

    def test_known_monster_numeric_fields_and_drops(self):
        detail = self.details.get("ms72200.dat")
        self.assertEqual(detail.data["level"], 47)
        self.assertEqual(detail.data["maximum_hp"], 9817)
        self.assertEqual(detail.data["stats"]["str"], 599)
        self.assertEqual(detail.data["attribute_rates"]["space"], 180)
        self.assertEqual(detail.data["sepith"]["wind"], 5)
        self.assertEqual(detail.data["drops"], [
            {"item_code": 500, "rate": 100},
            {"item_code": 507, "rate": 100},
        ])
        self.assertEqual(detail.data["as_file"], "as72200.dat")
        self.assertTrue(detail.action_script_available("en"))

    def test_custom_crafts_are_localized_without_exposing_writes(self):
        detail = self.details.get("ms72200.dat")
        english = detail.crafts("en")
        japanese = detail.crafts("ja")
        self.assertEqual(len(english), 7)
        self.assertEqual(english[1]["name"], "Debilitating Bite")
        self.assertTrue(japanese[1]["name"])
        self.assertFalse(hasattr(self.details, "save"))

    def test_known_upstream_trailing_extensions_are_reported(self):
        summary = self.details.metadata["summary"]
        self.assertEqual(summary["with_unparsed_trailing_data"], 2)
        extended = {
            detail.ms_file
            for detail in self.details.records()
            if any(source["unparsed_trailing_size"] for source in detail.data["source"].values())
        }
        self.assertEqual(extended, {"ms60000.dat", "ms60001.dat"})


if __name__ == "__main__":
    unittest.main()
