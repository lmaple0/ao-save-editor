import struct
import unittest

from ao_character_loadout import (
    EQUIPMENT_RECORD_SIZE,
    EQUIPMENT_START,
    LOADOUT_CHARACTERS,
    ORBMENT_RECORD_SIZE,
    ORBMENT_START,
    equipment_code_is_allowed,
    read_character_loadouts,
    validate_character_loadouts,
)
from ao_save_layout import EXPECTED_SIZE


class CharacterLoadoutTests(unittest.TestCase):
    def setUp(self):
        self.data = bytearray(EXPECTED_SIZE)
        self.categories = {
            0x0009: "equipment_weapon_generic",
            0x03F2: "equipment_weapon_Lloyd",
            0x0407: "equipment_weapon_Elie",
            0x0474: "equipment_weapon_Zeit",
            0x05F5: "equipment_clothes",
            0x065A: "equipment_shoes",
            0x0056: "equipment_jewelry",
            0x00DE: "circuit_core",
            0x008B: "circuit_normal",
        }

    def test_parses_verified_equipment_and_orbment_offsets(self):
        elie = LOADOUT_CHARACTERS.index("Elie")
        struct.pack_into(
            "<5H", self.data, EQUIPMENT_START + elie * EQUIPMENT_RECORD_SIZE,
            0x0407, 0x05F5, 0x065A, 0x0056, 0x0056,
        )
        struct.pack_into(
            "<14H", self.data, ORBMENT_START + elie * ORBMENT_RECORD_SIZE,
            0x00DE, 2, 0x008B, 2, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0,
        )

        loadout = read_character_loadouts(self.data)[elie]
        self.assertEqual(loadout.equipment.values(), (0x0407, 0x05F5, 0x065A, 0x0056, 0x0056))
        self.assertEqual((loadout.orbment[0].item_code, loadout.orbment[0].enhancement_level), (0x00DE, 2))
        self.assertEqual((loadout.orbment[1].item_code, loadout.orbment[1].enhancement_level), (0x008B, 2))

    def test_weapon_rules_include_generic_and_verified_garcia_exceptions(self):
        self.assertTrue(equipment_code_is_allowed("Elie", "weapon", 0x0009, self.categories))
        self.assertTrue(equipment_code_is_allowed("Garcia", "weapon", 0x03F2, self.categories))
        self.assertTrue(equipment_code_is_allowed("Garcia", "weapon", 0x0474, self.categories))
        self.assertFalse(equipment_code_is_allowed("Elie", "weapon", 0x03F2, self.categories))

    def test_validation_reports_wrong_categories_levels_and_duplicate_cores(self):
        struct.pack_into("<H", self.data, EQUIPMENT_START, 0x0407)
        struct.pack_into("<HH", self.data, ORBMENT_START, 0x00DE, 3)
        struct.pack_into("<HH", self.data, ORBMENT_START + ORBMENT_RECORD_SIZE, 0x00DE, 2)

        codes = [issue.code for issue in validate_character_loadouts(self.data, self.categories)]
        self.assertIn("equipment_category", codes)
        self.assertIn("orbment_enhancement_level", codes)
        self.assertEqual(codes.count("duplicate_core_quartz"), 2)

    def test_unknown_values_are_preserved_by_parser(self):
        struct.pack_into("<H", self.data, EQUIPMENT_START, 0xBEEF)
        self.assertEqual(read_character_loadouts(self.data)[0].equipment.weapon, 0xBEEF)

    def test_rejects_wrong_save_size(self):
        with self.assertRaises(ValueError):
            read_character_loadouts(b"short")


if __name__ == "__main__":
    unittest.main()
