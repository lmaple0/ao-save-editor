import struct
import unittest

from ao_character_loadout import apply_character_loadout_changes, read_character_loadouts
from ao_save_layout import (
    EQUIPMENT_RECORD_SIZE,
    EQUIPMENT_START,
    EXPECTED_SIZE,
    LOADOUT_CHARACTERS,
    ORBMENT_RECORD_SIZE,
    ORBMENT_START,
)


class LoadoutTransactionTests(unittest.TestCase):
    def setUp(self):
        self.data = bytearray(EXPECTED_SIZE)
        self.categories = {
            0x0009: "equipment_weapon_generic",
            0x03F2: "equipment_weapon_Lloyd",
            0x0407: "equipment_weapon_Elie",
            0x05F5: "equipment_clothes",
            0x065A: "equipment_shoes",
            0x0056: "equipment_jewelry",
            0x00DE: "circuit_core",
            0x00DF: "circuit_core",
            0x008B: "circuit_normal",
        }

    def apply(self, character, equipment, orbment, levels, items=None):
        return apply_character_loadout_changes(
            self.data, items or {}, character, equipment, orbment, levels, self.categories
        )

    def test_swaps_equipment_and_updates_inventory(self):
        elie = LOADOUT_CHARACTERS.index("Elie")
        struct.pack_into(
            "<5H", self.data, EQUIPMENT_START + elie * EQUIPMENT_RECORD_SIZE,
            0x0407, 0x05F5, 0x065A, 0x0056, 0x0056,
        )
        new_data, new_items = self.apply(
            "Elie",
            (0x0009, 0x05F5, 0x065A, 0x0056, 0x0056),
            (0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 0),
            {0x0009: 1, 0x0407: 1},
        )
        self.assertEqual(read_character_loadouts(new_data)[elie].equipment.weapon, 0x0009)
        self.assertEqual(new_items[0x0407], 2)
        self.assertEqual(new_items[0x0009], 1)

    def test_moves_core_quartz_and_preserves_slot_levels(self):
        struct.pack_into(
            "<14H", self.data, ORBMENT_START,
            0x00DE, 2, 0x008B, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
        )
        new_data, new_items = self.apply(
            "Lloyd",
            (0, 0, 0, 0, 0),
            (0x00DF, 0x008B, 0, 0, 0, 0, 0),
            (2, 1, 2, 0, 0, 0, 0),
            {0x00DF: 1},
        )
        loadout = read_character_loadouts(new_data)[0]
        self.assertEqual(loadout.orbment[0].item_code, 0x00DF)
        self.assertEqual(loadout.orbment[1].enhancement_level, 1)
        self.assertEqual(new_items, {0x00DE: 1})

    def test_failure_is_atomic_when_item_is_unavailable(self):
        before = bytes(self.data)
        items = {0x05F5: 1}
        with self.assertRaisesRegex(ValueError, "not available"):
            self.apply(
                "Elie", (0x0407, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0),
                (0, 0, 0, 0, 0, 0, 0), items,
            )
        self.assertEqual(bytes(self.data), before)
        self.assertEqual(items, {0x05F5: 1})

    def test_rejects_duplicate_normal_quartz(self):
        with self.assertRaisesRegex(ValueError, "cannot be equipped twice"):
            self.apply(
                "Lloyd", (0, 0, 0, 0, 0), (0, 0x008B, 0x008B, 0, 0, 0, 0),
                (0, 0, 0, 0, 0, 0, 0), {0x008B: 2},
            )

    def test_rejects_core_equipped_by_another_character(self):
        struct.pack_into("<HH", self.data, ORBMENT_START, 0x00DE, 2)
        with self.assertRaisesRegex(ValueError, "already equipped"):
            self.apply(
                "Elie", (0, 0, 0, 0, 0), (0x00DE, 0, 0, 0, 0, 0, 0),
                (2, 0, 0, 0, 0, 0, 0), {},
            )

    def test_rejects_wrong_character_weapon(self):
        with self.assertRaisesRegex(ValueError, "not valid"):
            self.apply(
                "Elie", (0x03F2, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0),
                (0, 0, 0, 0, 0, 0, 0), {0x03F2: 1},
            )


if __name__ == "__main__":
    unittest.main()
