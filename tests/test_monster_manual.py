import struct
import unittest

from ao_monsters_db import load_default_monster_catalog
from ao_save_editor import (
    EXPECTED_SIZE,
    MONSTER_CODES,
    MONSTER_COMPLETE_PAYLOAD,
    MONSTER_RECORD_SIZE,
    MONSTER_START,
    SaveData,
    ui_text,
)
from ao_save_layout import monster_record_is_complete


class MonsterCatalogTests(unittest.TestCase):
    def test_catalog_covers_every_save_code(self):
        catalog = load_default_monster_catalog()
        self.assertEqual(len(catalog), len(MONSTER_CODES))
        self.assertEqual(catalog.compare_codes(MONSTER_CODES), {"missing": (), "extra": ()})
        self.assertEqual(
            sum(record.source_status == "commented" for record in catalog.records()),
            22,
        )

    def test_catalog_searches_code_name_and_file(self):
        catalog = load_default_monster_catalog()
        first = catalog.records()[0]
        self.assertIn(first, catalog.search(first.save_code_hex))
        self.assertIn(first, catalog.search(first.ms_file))
        self.assertIn(first, catalog.search(first.zh_joyoland))


class MonsterRecordTests(unittest.TestCase):
    def setUp(self):
        self.save = SaveData()
        self.save.data = bytearray(EXPECTED_SIZE)

    def _write_record(self, slot, code, payload):
        struct.pack_into(
            "<I4B",
            self.save.data,
            MONSTER_START + slot * MONSTER_RECORD_SIZE,
            code,
            *payload,
        )

    def test_empty_manual_is_reported_without_guessing_states(self):
        diag = self.save.monster_diagnostics()
        self.assertEqual(diag["populated"], 0)
        self.assertEqual(diag["complete"], 0)
        self.assertEqual(diag["partial"], 0)
        self.assertEqual(diag["missing_codes"], tuple(MONSTER_CODES))

    def test_selected_unlock_and_lock_preserve_unknown_records(self):
        unknown = 0xDEADBEEF
        self._write_record(0, unknown, (1, 2, 3, 4))
        selected = MONSTER_CODES[:2]

        self.save.set_monsters_unlocked(selected, True)

        records = self.save.read_monster_records()
        self.assertEqual(records[0].code, unknown)
        self.assertEqual(records[0].payload, bytes((1, 2, 3, 4)))
        self.assertEqual({record.code for record in records[1:]}, set(selected))
        self.assertTrue(all(record.is_complete for record in records[1:]))

        self.save.set_monsters_unlocked((selected[0],), False)
        self.assertEqual(
            {record.code for record in self.save.read_monster_records()},
            {unknown, selected[1]},
        )

    def test_partial_and_duplicate_records_are_diagnosed(self):
        code = MONSTER_CODES[0]
        self._write_record(0, code, (1, 0, 0, 0))
        self._write_record(1, code, (2, 0, 0, 0))

        diag = self.save.monster_diagnostics()

        self.assertEqual(diag["partial_codes"], (code,))
        self.assertEqual(diag["duplicate_codes"], (code,))
        self.assertEqual(diag["partial"], 1)

    def test_nisa_complete_records_ignore_counter_and_variant_bits(self):
        code_a, code_b = MONSTER_CODES[:2]
        self._write_record(0, code_a, (0x2A, 0x0F, 0x7F, 0xFF))
        self._write_record(1, code_b, (0x80, 0x7F, 0xFF, 0xFF))

        diag = self.save.monster_diagnostics()

        self.assertEqual(diag["complete"], 2)
        self.assertEqual(diag["partial"], 0)

    def test_nisa_record_missing_information_or_items_is_partial(self):
        code_a, code_b = MONSTER_CODES[:2]
        self._write_record(0, code_a, (1, 0x0F, 0x3F, 0xFF))
        self._write_record(1, code_b, (1, 0x0F, 0x7F, 0x10))

        diag = self.save.monster_diagnostics()

        self.assertEqual(diag["complete"], 0)
        self.assertEqual(diag["partial"], 2)

    def test_game_completion_cases_include_elements_and_conditional_drops(self):
        # Expected results from the two executables' checkmark branches, not
        # the editor's former hard-coded full-data payload.
        cases = (
            ((8, 0xFE, 0xFF, 0xFF), False),  # Player report: Earth missing.
            ((9, 0x0E, 0x7F, 0x00), False),
            ((9, 0x0F, 0x7F, 0x00), True),   # No drops: nothing to investigate.
            ((9, 0x0F, 0xFF, 0x00), False),  # Higher elements required.
            ((9, 0x7F, 0xFF, 0x00), True),
            ((9, 0x7F, 0x3F, 0x03), False),  # Information still missing.
            ((9, 0x0F, 0x7F, 0x10), False),  # Drop 1 exists, not observed.
            ((9, 0x0F, 0x7F, 0x11), True),
            ((9, 0x0F, 0x7F, 0x20), False),  # Drop 2 exists, not observed.
            ((9, 0x0F, 0x7F, 0x22), True),
            ((9, 0x0F, 0x7F, 0x31), False),
            ((9, 0x0F, 0x7F, 0x33), True),
        )
        for payload, expected in cases:
            with self.subTest(payload=payload):
                self.assertEqual(monster_record_is_complete(payload), expected)

    def test_legacy_full_payload_is_repaired_by_changing_only_earth_bit(self):
        code = MONSTER_CODES[0]
        self._write_record(0, code, (8, 0xFE, 0xFF, 0xFF))
        self.assertFalse(self.save.read_monster_records()[0].is_complete)
        self.save.set_monsters_unlocked((code,), True)
        record = self.save.read_monster_records()[0]
        self.assertEqual(record.payload, b"\x08\xFF\xFF\xFF")
        self.assertTrue(record.is_complete)

    def test_completion_preserves_counters_flags_duplicates_and_complete_entries(self):
        a, b = MONSTER_CODES[:2]
        self._write_record(0, a, (0x2A, 0x80, 0x80, 0xD0))
        self._write_record(1, a, (0x19, 0, 0, 0x20))
        self._write_record(2, b, (0x40, 0x0F, 0x7F, 0))
        original = self.save.read_monster_records()[2].binary()
        self.save.set_monsters_unlocked((a, b), True)
        records = self.save.read_monster_records()
        self.assertEqual(records[0].payload, bytes((0x2A, 0xFF, 0xFF, 0xD3)))
        self.assertEqual(records[1].payload, bytes((0x19, 0x7F, 0x7F, 0x23)))
        self.assertEqual(records[2].binary(), original)
        self.assertEqual(len(records), 3)

    def test_unlock_all_fills_every_known_slot(self):
        self.save.unlock_all_monsters()

        records = self.save.read_monster_records()
        self.assertEqual(len(records), len(MONSTER_CODES))
        self.assertEqual([record.code for record in records], list(MONSTER_CODES))
        self.assertTrue(all(record.payload == MONSTER_COMPLETE_PAYLOAD for record in records))

    def test_unlock_all_refuses_to_discard_unknown_record_when_full(self):
        self._write_record(0, 0xDEADBEEF, (1, 2, 3, 4))
        with self.assertRaises(ValueError):
            self.save.unlock_all_monsters()

    def test_unknown_requested_code_is_rejected(self):
        with self.assertRaises(ValueError):
            self.save.set_monsters_unlocked((0xDEADBEEF,), True)

    def test_manual_ui_labels_are_global_translations(self):
        self.assertEqual(ui_text("怪物图鉴", "en"), "Monster Manual")
        self.assertEqual(ui_text("全资料", "en"), "Full data")
        self.assertEqual(ui_text("未登记", "ja"), "未登録")


if __name__ == "__main__":
    unittest.main()
