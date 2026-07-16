import struct
import unittest

from ao_save_audit import (
    DIFFICULTY_OFFSET,
    EXPECTED_SIZE,
    ITEMS_START,
    MONSTER_COMPLETE_PAYLOAD,
    MONSTER_START,
    RECIPE_BOOK_OFFSETS,
    ROLE_DISPLAY_OFFSETS,
    SaveAuditor,
    TEAM_SLOTS,
    load_default_save_auditor,
)


KNOWN_ITEM = 0x01F4
KNOWN_MONSTER = 0x30072200


def clean_save():
    data = bytearray(EXPECTED_SIZE)
    data[DIFFICULTY_OFFSET] = 1
    for offset in TEAM_SLOTS:
        struct.pack_into("<H", data, offset, 0xFF)
    return data


class SaveAuditTests(unittest.TestCase):
    def setUp(self):
        self.auditor = SaveAuditor({KNOWN_ITEM}, {KNOWN_MONSTER}, "nisa_pc")

    def test_clean_snapshot_is_read_only_and_reports_progress(self):
        data = clean_save()
        before = bytes(data)
        report = self.auditor.audit(data, checksum_valid=True)
        self.assertEqual(bytes(data), before)
        self.assertTrue(report.is_clean)
        self.assertEqual(report.metrics["items"]["capacity"], 713)
        self.assertEqual(report.metrics["monsters"]["missing"], 1)
        self.assertEqual([finding.code for finding in report.findings], ["monster_missing"])

    def test_known_complete_monster_and_item_are_counted(self):
        data = clean_save()
        struct.pack_into("<HH", data, ITEMS_START, KNOWN_ITEM, 12)
        struct.pack_into("<I4s", data, MONSTER_START, KNOWN_MONSTER, MONSTER_COMPLETE_PAYLOAD)
        report = self.auditor.audit(data, checksum_valid=True)
        self.assertEqual(report.metrics["items"]["populated"], 1)
        self.assertEqual(report.metrics["monsters"]["known"], 1)
        self.assertEqual(report.metrics["monsters"]["complete"], 1)
        self.assertEqual(report.metrics["monsters"]["missing"], 0)

    def test_nisa_complete_variant_matches_editor_semantics(self):
        data = clean_save()
        struct.pack_into("<I4B", data, MONSTER_START, KNOWN_MONSTER, 0x2A, 0x0F, 0x7F, 0xFF)

        report = self.auditor.audit(data, checksum_valid=True)

        self.assertEqual(report.metrics["monsters"]["complete"], 1)
        self.assertEqual(report.metrics["monsters"]["partial"], 0)

    def test_structural_anomalies_are_reported_without_guessing_repairs(self):
        data = clean_save()
        data[DIFFICULTY_OFFSET] = 9
        struct.pack_into("<HH", data, ITEMS_START, 0xEEEE, 120)
        struct.pack_into("<HH", data, ITEMS_START + 4, 0xEEEE, 1)
        struct.pack_into("<H", data, ITEMS_START + 10, 4)
        struct.pack_into("<H", data, TEAM_SLOTS[0], 99)
        struct.pack_into("<H", data, TEAM_SLOTS[1], 2)
        struct.pack_into("<H", data, TEAM_SLOTS[2], 2)
        struct.pack_into("<H", data, ROLE_DISPLAY_OFFSETS[0], 99)
        struct.pack_into("<I", data, RECIPE_BOOK_OFFSETS[1], 2)
        struct.pack_into("<I4s", data, MONSTER_START, 0xDEADBEEF, b"\x01\x02\x03\x04")
        struct.pack_into("<I4s", data, MONSTER_START + 8, 0xDEADBEEF, b"\x01\x02\x03\x04")
        struct.pack_into("<I4s", data, MONSTER_START + 16, KNOWN_MONSTER, b"\x01\x00\x00\x00")
        data[MONSTER_START + 24 + 4] = 1

        report = self.auditor.audit(data, checksum_valid=False)
        codes = {finding.code for finding in report.findings}
        self.assertTrue({
            "checksum", "difficulty", "item_unknown", "item_duplicate", "item_quantity",
            "item_orphan", "team_unknown", "team_duplicate", "appearance_unknown",
            "recipe_mirror", "monster_unknown", "monster_duplicate", "monster_partial",
            "monster_orphan",
        }.issubset(codes))
        self.assertFalse(report.is_clean)

    def test_wrong_size_returns_a_bounded_report(self):
        report = self.auditor.audit(b"short", checksum_valid=False)
        self.assertEqual([finding.code for finding in report.findings], ["save_size"])
        for locale in ("zh_cn", "en", "ja"):
            rendered = report.render(locale)
            self.assertIn("5", rendered)

    def test_default_references_cover_published_catalogs(self):
        auditor = load_default_save_auditor()
        self.assertGreaterEqual(len(auditor.known_item_codes), 700)
        self.assertEqual(len(auditor.known_monster_codes), 305)
        self.assertEqual(auditor.reference_edition, "nisa_pc")


if __name__ == "__main__":
    unittest.main()
