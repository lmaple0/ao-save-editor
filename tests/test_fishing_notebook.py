import unittest

from ao_fishing import (
    FISH_MAX_SIZE_OFFSET,
    FISH_RECORD_COUNT,
    FISH_RECORD_SIZE,
    FISH_RECORDS_OFFSET,
    FISH_SIZE_RANGES,
    read_fishing_notebook,
    register_all_fish,
    write_fish_maximum_size,
)


class FishingNotebookTests(unittest.TestCase):
    def setUp(self):
        self.data = bytearray(0x2643C)

    def test_reads_31_fixed_records(self):
        first = FISH_RECORDS_OFFSET
        last = first + (FISH_RECORD_COUNT - 1) * FISH_RECORD_SIZE
        self.data[first + 4:first + 8] = b"\x02\x00\x03\x00"
        self.data[first + 0x68:first + 0x70] = (5).to_bytes(8, "little")
        self.data[first + 0x70:first + 0x72] = (7).to_bytes(2, "little")
        self.data[first + 0x72:first + 0x74] = (15).to_bytes(2, "little")
        self.data[last + 0x72:last + 0x74] = (392).to_bytes(2, "little")

        rows = read_fishing_notebook(self.data)

        self.assertEqual(len(rows), 31)
        self.assertEqual(rows[0].item_id, 0x015E)
        self.assertEqual(rows[-1].item_id, 0x017C)
        self.assertEqual(rows[0].caught_count, 5)
        self.assertEqual(rows[0].bait_flags, 5)
        self.assertEqual(rows[0].reward_flags, 7)
        self.assertEqual(rows[0].maximum_size, 15)
        self.assertTrue(rows[-1].registered)

    def test_single_edit_changes_only_maximum_size(self):
        self.data[:] = b"\xA5" * len(self.data)
        before = bytes(self.data)
        index = 10
        write_fish_maximum_size(self.data, index, 50)
        offset = FISH_RECORDS_OFFSET + index * FISH_RECORD_SIZE + FISH_MAX_SIZE_OFFSET

        self.assertEqual(self.data[offset:offset + 2], b"\x32\x00")
        self.assertEqual(self.data[:offset], before[:offset])
        self.assertEqual(self.data[offset + 2:], before[offset + 2:])

    def test_edit_accepts_zero_and_rejects_out_of_range(self):
        write_fish_maximum_size(self.data, 0, 0)
        with self.assertRaises(ValueError):
            write_fish_maximum_size(self.data, 0, FISH_SIZE_RANGES[0][1] + 1)

    def test_register_all_preserves_every_other_byte(self):
        self.data[:] = b"\x5A" * len(self.data)
        before = bytes(self.data)
        register_all_fish(self.data)
        changed = {
            FISH_RECORDS_OFFSET + index * FISH_RECORD_SIZE + FISH_MAX_SIZE_OFFSET + byte
            for index in range(FISH_RECORD_COUNT)
            for byte in range(2)
        }
        self.assertTrue(all(self.data[pos] == before[pos] for pos in range(len(self.data)) if pos not in changed))
        self.assertEqual(
            [row.maximum_size for row in read_fishing_notebook(self.data)],
            [maximum for _minimum, maximum in FISH_SIZE_RANGES],
        )


if __name__ == "__main__":
    unittest.main()
