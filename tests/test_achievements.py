import json
import os
import unittest

from ao_save_editor import (
    ACHIEVEMENT_NAMES,
    ACHIEVEMENT_OFFSETS,
    SaveData,
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
        missing = {
            part * 8 + bit
            for part, values in bits.items()
            for bit, value in enumerate(values)
            if not value
        }
        self.assertEqual(missing, {0, 18, 21, 26, 27, 35, 43, 49, 55})

    def test_write_changes_only_the_seven_achievement_bytes(self):
        save = self.make_save(b"\xA5" * 7)
        before = bytes(save.data)
        bits = {part: [1] * 8 for part in range(7)}

        save.write_achievements(bits)

        start = ACHIEVEMENT_OFFSETS[0]
        self.assertEqual(save.data[start:start + 7], b"\xFF" * 7)
        self.assertEqual(save.data[:start], before[:start])
        self.assertEqual(save.data[start + 7:], before[start + 7:])

    def test_ui_catalog_covers_each_nisa_id_once(self):
        ids = [achievement_id for achievement_id, _name in ACHIEVEMENT_NAMES]
        self.assertEqual(ids, list(range(56)))

    def test_chinese_catalog_remains_available_without_localization_file(self):
        fallback = dict(build_achievement_names({}))
        self.assertEqual(len(fallback), 56)
        self.assertEqual(fallback[15], "持续的雅士")
        self.assertEqual(fallback[55], "传至的思念～不断的羁绊")

    def test_localization_ids_are_unique_and_complete(self):
        path = os.path.join(app_dir(), "ao_achievement_i18n.json")
        with open(path, "r", encoding="utf-8") as stream:
            rows = json.load(stream)["achievements"]
        ids = [row["game_achievement_id"] for row in rows]

        self.assertEqual(sorted(ids), list(range(56)))
        self.assertEqual(len(load_achievement_i18n()), 56)
        playtime = load_achievement_i18n()[15]
        self.assertEqual(playtime["en"], "Search and Leisure")

        names = {
            achievement_id: row["zh_cn"]
            for achievement_id, row in load_achievement_i18n().items()
        }
        self.assertEqual(names[13], "鬼屋射击大师")
        self.assertEqual(names[15], "持续的雅士")
        self.assertEqual(names[23], "绚烂攻守")
        self.assertEqual(names[25], "八头击灭")
        self.assertEqual(names[26], "赶尽杀绝")
        self.assertEqual(names[30], "七耀之贤士")
        self.assertEqual(names[55], "传至的思念～不断的羁绊")


if __name__ == "__main__":
    unittest.main()
