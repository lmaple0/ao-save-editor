from __future__ import annotations

import struct
import unittest

from ao_cle_kai_tables import (
    ITEM_TYPE_CATEGORIES,
    ORBMENT_SLOT_ELEMENT_OFFSETS,
    parse_item_table,
    parse_orbment_slot_elements,
    parse_quartz_table,
    validate_item_categories,
)


class CleKaiTableTests(unittest.TestCase):
    def test_item_pointer_table_and_category_validation(self):
        header_size = 6
        first = bytearray(28)
        second = bytearray(28)
        struct.pack_into("<H", first, 0x10, 0x0064)
        first[0x15] = 0x12
        struct.pack_into("<H", second, 0x10, 0x03E9)
        second[0x15] = 0x01
        data = struct.pack("<3H", header_size, header_size + 28, header_size + 56)
        data += first + second + b"end"
        records = parse_item_table(data)
        self.assertEqual([record.item_id for record in records], [0x64, 0x3E9])
        self.assertEqual(
            validate_item_categories(
                records,
                {0x64: ("circuit_normal", "HP1"), 0x3E9: ("equipment_weapon_Lloyd", "Weapon")},
            ),
            (),
        )
        self.assertIn("circuit_debug", ITEM_TYPE_CATEGORIES[0x12])

    def test_quartz_layout(self):
        data = bytearray(4234)
        pos = 6
        for logical_id in range(1, 117):
            struct.pack_into("<HH", data, pos + 0x0C, logical_id, (logical_id % 7) + 1)
            pos += 28
        pos += 12
        for item_id in range(0xDC, 0xF2):
            struct.pack_into("<HH", data, pos, item_id, (item_id % 7) + 1)
            pos += 44
        table = parse_quartz_table(data)
        self.assertEqual((table.normal[0].item_id, table.normal[-1].item_id), (0x65, 0xD8))
        self.assertEqual((table.master[0].item_id, table.master[-1].item_id), (0xDC, 0xF1))

    def test_orbment_slot_offsets(self):
        data = bytearray(306)
        expected = {}
        for index, (name, offset) in enumerate(ORBMENT_SLOT_ELEMENT_OFFSETS.items()):
            slots = (0, 0, 0, (index % 7) + 1, 0, 0, 0)
            data[offset:offset + 7] = bytes(slots)
            expected[name] = slots
        self.assertEqual(parse_orbment_slot_elements(data), expected)


if __name__ == "__main__":
    unittest.main()
