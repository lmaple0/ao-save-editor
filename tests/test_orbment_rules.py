import hashlib
import unittest

from ao_orbment_rules import (
    CHARACTER_SLOT_ELEMENTS,
    QUARTZ_PRIMARY_ELEMENTS,
    orbment_code_is_allowed,
    quartz_primary_element,
    required_slot_element,
)
from ao_save_layout import LOADOUT_CHARACTERS


class OrbmentRuleTests(unittest.TestCase):
    def test_verified_character_element_locks(self):
        expected = {
            "Elie": (5, 4),
            "Tio": (2, 2),
            "Randy": (3, 3),
            "Wazy": (4, 6),
            "Rixia": (4, 7),
            "Arios": (3, 5),
            "Noel": (3, 1),
            "Dudley": (4, 5),
        }
        self.assertEqual(tuple(CHARACTER_SLOT_ELEMENTS), LOADOUT_CHARACTERS)
        for character, (slot, element) in expected.items():
            with self.subTest(character=character):
                self.assertEqual(required_slot_element(character, slot), element)

    def test_t_quartz_primary_element_table(self):
        self.assertEqual(len(QUARTZ_PRIMARY_ELEMENTS), 117)
        self.assertEqual(quartz_primary_element(0x0064), 2)  # HP 1: water
        digest = hashlib.sha256(QUARTZ_PRIMARY_ELEMENTS).hexdigest()
        self.assertEqual(
            digest, "034c6bd862de4524b46082341ba30e4d4b5df8fa3511cb0f8db071e4ba9a2649"
        )
        self.assertEqual(quartz_primary_element(0x0083), 4)  # Emerald Gem: wind
        self.assertEqual(quartz_primary_element(0x008B), 5)  # Onyx Gem: time
        self.assertIsNone(quartz_primary_element(0x00DE))

    def test_element_locked_slot_accepts_only_matching_primary_element(self):
        self.assertTrue(orbment_code_is_allowed("Elie", 5, 0))
        self.assertTrue(orbment_code_is_allowed("Elie", 5, 0x0083))
        self.assertFalse(orbment_code_is_allowed("Elie", 5, 0x008B))
        self.assertTrue(orbment_code_is_allowed("Lloyd", 5, 0x008B))


if __name__ == "__main__":
    unittest.main()
