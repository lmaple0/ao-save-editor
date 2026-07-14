import unittest

from ao_save_editor import (
    EXPECTED_SIZE,
    MONSTER_CODES,
    MONSTER_END,
    MONSTER_RECORD_SIZE,
    SaveData,
)


class MonsterRegionBoundaryTests(unittest.TestCase):
    def test_rewrite_clears_entire_last_slot(self):
        save = SaveData()
        save.data = bytearray(EXPECTED_SIZE)
        save.data[MONSTER_END:MONSTER_END + MONSTER_RECORD_SIZE] = b"\xAA" * MONSTER_RECORD_SIZE

        save.set_monsters_unlocked((MONSTER_CODES[0],), True)

        self.assertEqual(
            save.data[MONSTER_END:MONSTER_END + MONSTER_RECORD_SIZE],
            b"\x00" * MONSTER_RECORD_SIZE,
        )


if __name__ == "__main__":
    unittest.main()
