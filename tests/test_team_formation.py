import unittest

from ao_save_editor import format_team_member, parse_team_member, team_member_choices


class TeamFormationTests(unittest.TestCase):
    def test_choices_cover_all_known_members_and_empty_slot(self):
        choices = team_member_choices("zh_cn")
        self.assertEqual(len(choices), 18)
        self.assertEqual(choices[0], "0 · 罗伊德")
        self.assertEqual(choices[-1], "255 · 空位")

    def test_choices_are_localized(self):
        self.assertEqual(format_team_member(1, "en"), "1 · Elie")
        self.assertEqual(format_team_member(2, "ja"), "2 · ティオ")
        self.assertEqual(format_team_member(255, "en"), "255 · Empty")

    def test_nisa_logical_party_id_is_not_confused_with_resource_variant_id(self):
        self.assertEqual(format_team_member(5, "zh_cn"), "5 · 莉夏")
        self.assertEqual(format_team_member(5, "en"), "5 · Rixia")

    def test_nisa_guest_ids_seen_in_natural_saves_are_named(self):
        expected = {
            15: "魔兽",
            61: "约纳",
            82: "琪雅",
            140: "莉丝修女",
            160: "雷蒙德",
            161: "秦",
        }
        for member_id, name in expected.items():
            with self.subTest(member_id=member_id):
                self.assertEqual(format_team_member(member_id, "zh_cn"), f"{member_id} · {name}")

    def test_parser_accepts_combo_labels_and_legacy_raw_values(self):
        self.assertEqual(parse_team_member("10 · 加尔西亚"), 10)
        self.assertEqual(parse_team_member("255"), 255)
        self.assertEqual(parse_team_member("0x00ff"), 255)

    def test_unknown_value_is_preserved_and_identified(self):
        label = format_team_member(42, "zh_cn")
        self.assertEqual(label, "42 · 未知")
        self.assertEqual(parse_team_member(label), 42)

    def test_invalid_values_are_rejected(self):
        for value in ("", "not-a-number", "65536", "-1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_team_member(value)


if __name__ == "__main__":
    unittest.main()
