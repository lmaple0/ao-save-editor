import unittest

from ao_monsters_db import load_default_monster_catalog


class MonsterLocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_default_monster_catalog()

    def test_every_monster_has_at_least_one_location(self):
        self.assertEqual(len(self.catalog), 305)
        self.assertTrue(
            all(record.locations_zh_cle for record in self.catalog.records())
        )
        self.assertEqual(len(self.catalog.locations()), 75)

    def test_location_sources_preserve_primary_and_supplement_provenance(self):
        sources = [record.location_source for record in self.catalog.records()]
        self.assertEqual(sources.count("nisa_pc_scenario_scan"), 302)
        self.assertEqual(sources.count("local_town_name_supplement"), 3)
        supplements = {
            record.ms_file: record.locations_zh_cle
            for record in self.catalog.records()
            if record.location_source == "local_town_name_supplement"
        }
        self.assertEqual(
            supplements,
            {
                "ms82004.dat": ("唐古拉姆门",),
                "ms84000.dat": ("迎宾馆",),
                "ms84500.dat": ("迎宾馆",),
            },
        )

    def test_search_matches_location_text(self):
        matches = self.catalog.search("阿勒泰尔")
        self.assertTrue(matches)
        self.assertTrue(
            all(
                any("阿勒泰尔" in location for location in record.locations_zh_cle)
                for record in matches
            )
        )

    def test_exact_location_filter_combines_with_text_search(self):
        all_at_location = self.catalog.search("", "迎宾馆")
        named_at_location = self.catalog.search("村正", "迎宾馆")
        self.assertGreater(len(all_at_location), 1)
        self.assertEqual([record.zh_joyoland for record in named_at_location], ["村正"])


if __name__ == "__main__":
    unittest.main()
