import json
import os
import unittest

from ao_save_editor import (
    ACHIEVEMENT_NAMES,
    ACHIEVEMENT_OFFSETS,
    SaveData,
    NISA_ACHIEVEMENT_GAME_IDS,
    NISA_ACHIEVEMENT_PLATFORM_KEYS,
    app_dir,
    build_achievement_names,
    load_achievement_i18n,
)


class AchievementLayoutTests(unittest.TestCase):
    def make_save(self, payload=b"\x00" * 7):
        save = SaveData()
        save.data = bytearray(0x1F500)
        start = ACHIEVEMENT_OFFSETS[0]
        save.data[start:start + 7] = payload
        return save

    def test_nisa_offsets_and_latest_known_47_achievement_bitmap(self):
        self.assertEqual(ACHIEVEMENT_OFFSETS, list(range(0x1F454, 0x1F45B)))
        save = self.make_save(bytes.fromhex("FE FF DB F3 F7 F7 7D"))

        bits = save.read_achievements()

        self.assertEqual(sum(sum(part) for part in bits.values()), 47)
        catalog = {
            part * 8 + bit: name for part, bit, name in ACHIEVEMENT_NAMES
        }
        missing_names = {
            catalog[part * 8 + bit]
            for part, values in bits.items()
            for bit, value in enumerate(values)
            if not value
        }
        self.assertEqual(
            missing_names,
            {
                "赶尽杀绝",
                "干练的搜查官",
                "传说的搜查官",
                "持续的雅士",
                "天眼的智者",
                "七曜之贤士",
                "红之讨伐者",
                "即使如此，我们也……",
                "无双之烈士",
            },
        )

    def test_nisa_bitmap_uses_ao_exe_platform_table_order(self):
        localized = load_achievement_i18n()
        expected = {
            0: "天眼的智者",
            18: "持续的雅士",
            21: "无双之烈士",
            26: "干练的搜查官",
            27: "传说的搜查官",
            35: "即使如此，我们也……",
            43: "红之讨伐者",
            49: "赶尽杀绝",
            55: "七曜之贤士",
        }
        self.assertEqual(len(NISA_ACHIEVEMENT_GAME_IDS), 56)
        self.assertEqual(sorted(NISA_ACHIEVEMENT_GAME_IDS), list(range(56)))
        self.assertEqual(len(NISA_ACHIEVEMENT_PLATFORM_KEYS), 56)
        for save_bit, name in expected.items():
            achievement_id = NISA_ACHIEVEMENT_GAME_IDS[save_bit]
            self.assertEqual(localized[achievement_id]["zh_cn"], name)

    def test_write_changes_only_the_seven_achievement_bytes(self):
        save = self.make_save(b"\xA5" * 7)
        before = bytes(save.data)
        bits = {part: [1] * 8 for part in range(7)}

        save.write_achievements(bits)

        start = ACHIEVEMENT_OFFSETS[0]
        self.assertEqual(save.data[start:start + 7], b"\xFF" * 7)
        self.assertEqual(save.data[:start], before[:start])
        self.assertEqual(save.data[start + 7:], before[start + 7:])

    def test_ui_catalog_covers_each_bitmap_position_once(self):
        positions = [part * 8 + bit for part, bit, _name in ACHIEVEMENT_NAMES]
        self.assertEqual(positions, list(range(56)))

    def test_chinese_catalog_remains_available_without_localization_file(self):
        fallback = {
            part * 8 + bit: name
            for part, bit, name in build_achievement_names({})
        }
        self.assertEqual(len(fallback), 56)
        self.assertEqual(fallback[0], "天眼的智者")
        self.assertEqual(fallback[55], "七曜之贤士")

    def test_localization_ids_and_bitmap_positions_are_unique(self):
        path = os.path.join(app_dir(), "ao_achievement_i18n.json")
        with open(path, "r", encoding="utf-8") as stream:
            rows = json.load(stream)["achievements"]

        ids = [row["game_achievement_id"] for row in rows]
        positions = [row["bitmap_part"] * 8 + row["bit"] for row in rows]
        self.assertEqual(sorted(ids), list(range(56)))
        self.assertEqual(sorted(positions), list(range(56)))
        self.assertEqual(len(load_achievement_i18n()), 56)

        names_by_id = {row["game_achievement_id"]: row["zh_cn"] for row in rows}
        self.assertEqual(names_by_id[13], "鬼屋射击大师")
        self.assertEqual(names_by_id[15], "持续的雅士")
        self.assertEqual(names_by_id[23], "绚烂攻守")
        self.assertEqual(names_by_id[25], "八头击灭")
        self.assertEqual(names_by_id[26], "赶尽杀绝")
        self.assertEqual(names_by_id[30], "七曜之贤士")
        self.assertEqual(names_by_id[55], "传至的思念～不断的羁绊")


if __name__ == "__main__":
    unittest.main()
