import unittest

from ao_monsters_db import load_default_monster_catalog


class MonsterLocationHierarchyTests(unittest.TestCase):
    def test_parent_location_filter_includes_detailed_subareas(self):
        catalog = load_default_monster_catalog()
        matches = catalog.search("", "阿勒泰尔据点")

        self.assertGreater(len(matches), 1)
        self.assertTrue(
            all(
                any(
                    location == "阿勒泰尔据点"
                    or location.startswith("阿勒泰尔据点 / ")
                    for location in record.locations_zh_cle
                )
                for record in matches
            )
        )


if __name__ == "__main__":
    unittest.main()
