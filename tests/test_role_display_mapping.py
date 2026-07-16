import unittest

from ao_save_editor import (
    ROLE_DISPLAY_NAMES,
    role_display_name,
    role_display_slot_name,
)
from ao_save_layout import KNOWN_ROLE_DISPLAY_IDS, KNOWN_TEAM_IDS


class RoleDisplayMappingTests(unittest.TestCase):
    def test_late_wazy_and_rixia_use_raw_nisa_resource_ids(self):
        self.assertEqual(role_display_name(0x1F, "zh_cn"), "瓦吉(后期)")
        self.assertEqual(role_display_name(0x20, "zh_cn"), "莉夏")
        self.assertEqual(role_display_name(0x1F, "en"), "Wazy (Late)")
        self.assertEqual(role_display_name(0x20, "ja"), "リーシャ")

    def test_early_wazy_and_yin_keep_their_own_ids(self):
        self.assertEqual(role_display_name(4, "zh_cn"), "瓦吉(初期)")
        self.assertEqual(role_display_name(5, "en"), "Yin")

    def test_high_guest_ids_are_raw_values_not_combo_indexes(self):
        self.assertEqual(role_display_name(0xA0, "en"), "Raymond")
        self.assertEqual(role_display_name(0xA1, "zh_cn"), "秦")
        self.assertEqual(role_display_name(0xA2, "ja"), "シャーリィ")
        self.assertEqual(role_display_name(0xA4, "en"), "KeA")

    def test_intermission_swimsuit_resource_ids(self):
        self.assertEqual(role_display_name(0x60, "zh_cn"), "罗伊德(泳装)")
        self.assertEqual(role_display_name(0x61, "en"), "Randy (Swimsuit)")
        self.assertEqual(role_display_name(0x62, "ja"), "ワジ(水着)")

    def test_fixed_slots_are_labeled_as_characters(self):
        self.assertEqual(role_display_slot_name(0, "zh_cn"), "罗伊德")
        self.assertEqual(role_display_slot_name(4, "en"), "Wazy")
        self.assertEqual(role_display_slot_name(5, "ja"), "リーシャ")
        self.assertEqual(role_display_slot_name(11, "zh_cn"), "其他")

    def test_audit_accepts_observed_nisa_ids(self):
        self.assertTrue({61, 82, 140, 160, 161}.issubset(KNOWN_TEAM_IDS))
        self.assertTrue({0x1F, 0x20, 0x60, 0x61, 0x62}.issubset(KNOWN_ROLE_DISPLAY_IDS))

    def test_obsolete_combo_indexes_are_not_claimed_as_character_ids(self):
        for value in (13, 16, 17, 18, 19, 20):
            with self.subTest(value=value):
                self.assertNotIn(value, ROLE_DISPLAY_NAMES)


if __name__ == "__main__":
    unittest.main()
