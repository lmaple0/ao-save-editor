import unittest

from ao_fishing import (
    FishNotebookRecord,
    bait_item_ids_for_flags,
    known_reward_flags,
    reward_items_for_flags,
)
from ao_fishing import fishing_reward_item_name
from ao_fishing_ui import format_bait_names, format_reward_names


def record(*, index=0, reward_flags=0, bait_flags=0):
    return FishNotebookRecord(
        index=index,
        item_id=0x015E + index,
        min_size=6,
        natural_max_size=16,
        maximum_size=10,
        recent_location_ids=(),
        location_counts=(),
        bait_flags=bait_flags,
        reward_flags=reward_flags,
    )


class FishingDisplayNameTests(unittest.TestCase):
    def test_reward_bits_select_t_fish_reward_entries(self):
        self.assertEqual(
            reward_items_for_flags(0, 0x000E),
            ((0x0130, 1), (0x03E3, 10), (0x03E4, 20)),
        )
        self.assertEqual(known_reward_flags(30), 0x0002)

    def test_reward_pseudo_items_have_three_language_names(self):
        fallback = lambda item_id, lang: f"unknown-{item_id:04X}"
        self.assertEqual(fishing_reward_item_name(0x03DE, "zh_cn", fallback), "地之耀晶片")
        self.assertEqual(fishing_reward_item_name(0x03E3, "en", fallback), "Space Sepith")
        self.assertEqual(fishing_reward_item_name(0x03E5, "ja", fallback), "セピス塊")
        self.assertEqual(fishing_reward_item_name(0x0130, "en", fallback), "unknown-0130")

    def test_bait_bits_map_from_fish_item_base(self):
        self.assertEqual(
            bait_item_ids_for_flags((1 << 1) | (1 << 42)),
            (0x015F, 0x0188),
        )

    def test_gui_formatters_use_localized_item_names(self):
        names = {
            (0x0130, "zh_cn"): "魔兽之肉",
            (0x03E3, "zh_cn"): "should-not-use-fallback",
            (0x015F, "en"): "Snow Crab",
            (0x0188, "en"): "Red Flies",
        }
        item_name = lambda item_id, lang: names[(item_id, lang)]

        rewards = format_reward_names(record(reward_flags=0x0006), item_name, "zh_cn")
        baits = format_bait_names(
            record(bait_flags=(1 << 1) | (1 << 42)), item_name, "en"
        )

        self.assertEqual(rewards, "魔兽之肉 ×1、空之耀晶片 ×10")
        self.assertEqual(baits, "Snow Crab, Red Flies")

    def test_empty_data_uses_dash(self):
        item_name = lambda item_id, lang: str(item_id)
        self.assertEqual(format_reward_names(record(), item_name, "zh_cn"), "—")
        self.assertEqual(format_bait_names(record(), item_name, "zh_cn"), "—")


if __name__ == "__main__":
    unittest.main()
