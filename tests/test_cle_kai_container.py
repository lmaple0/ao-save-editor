import unittest
from datetime import datetime
from pathlib import Path
import struct

from ao_save_container import cle_aes_key, decode_cle_kai, encode_cle_kai
from ao_save_formats import (
    CLE_ACTORS, CLE_ACTOR_SIZE, CLE_PAYLOAD_SIZE, NISA_ACTORS,
    NISA_ACTOR_SIZE, NISA_SCENE_THREAD, cle_to_nisa, nisa_to_cle,
    thread_pairs, update_checksum,
)
from ao_save_layout import EXPECTED_SIZE, DIFFICULTY_OFFSET
from ao_save_editor import SaveData, OFFSETS
from ao_save_metadata import SaveMetadata, cle_info

REAL_SAMPLE = Path(__file__).resolve().parents[2] / "data/samples/039_save.bin"


class CleKaiContainerTests(unittest.TestCase):
    def test_full_container_and_key(self):
        self.assertEqual(cle_aes_key().hex(), "3e93bf9995dd9a86c2d48d85cc06ca1f")
        payload = bytes((i * 17 + 3) & 255 for i in range(CLE_PAYLOAD_SIZE))
        raw = encode_cle_kai(payload)
        self.assertEqual(len(raw), 0x27450)
        self.assertEqual(decode_cle_kai(raw).payload, payload)
        with self.assertRaises(ValueError):
            decode_cle_kai(raw[:-16])

    def test_last_actor_scene_and_tail_are_not_lost(self):
        data = bytearray(EXPECTED_SIZE)
        data[NISA_SCENE_THREAD:NISA_SCENE_THREAD + 4] = b"SCNE"
        last = NISA_ACTORS + 127 * NISA_ACTOR_SIZE
        data[last:last + 4] = b"LAST"
        data[last + 0x20:last + 0x24] = b"UNIT"
        data[0x19C04:0x19C08] = b"TAIL"
        data[-12:-8] = b"END!"
        update_checksum(data)
        cle = nisa_to_cle(data)
        self.assertEqual(cle[CLE_ACTORS + 127 * CLE_ACTOR_SIZE:][:4], b"LAST")
        self.assertEqual(cle_to_nisa(cle), data)

    def test_same_format_preserves_all_cle_only_bytes(self):
        original = bytes((i * 19 + 5) & 255 for i in range(CLE_PAYLOAD_SIZE))
        data = cle_to_nisa(original)
        self.assertEqual(nisa_to_cle(data, original=original), original)
        data[0x304:0x306] = b"\xE8\x03"
        result = nisa_to_cle(data, original=original)
        expected = bytearray(original)
        expected[0x304:0x306] = b"\xE8\x03"
        self.assertEqual(result, expected)

    def test_thread_instruction_bytes_are_preserved_without_old_offset_patch(self):
        data = bytearray(EXPECTED_SIZE)
        data[NISA_SCENE_THREAD:NISA_SCENE_THREAD + 0x96] = bytes(range(0x96))
        data[0x5E2C:0x5E2F] = b"\x2B\x2E\x5C"
        update_checksum(data)
        cle = nisa_to_cle(data)
        n, c = next(thread_pairs())
        self.assertEqual(cle[c:c + 0x3C], data[n:n + 0x3C])
        self.assertEqual(cle[c + 0x40:c + 0x9A], data[n + 0x3C:n + 0x96])
        self.assertEqual(cle_to_nisa(cle), data)

    def test_final_chapter_is_not_clear_and_difficulty_uses_correct_offset(self):
        data = bytearray(EXPECTED_SIZE)
        data[0x19C78] = 7
        data[DIFFICULTY_OFFSET] = 2
        data[0x1F372] = 45
        meta = SaveMetadata("终章", "", "支援科", datetime(2026, 7, 7, 2, 21))
        index = cle_info(None, 60, data, meta)
        base = 0x1BC + 59 * 0x678 + 2 * 0x228
        self.assertEqual(struct.unpack_from("<I", index, base + 0x224)[0], 0)
        self.assertEqual(index[base + 0x204:base + 0x214].split(b"\0")[0], b"Nightmare")
        meta.clear = True
        second = cle_info(index, 61, data, meta)
        self.assertEqual(second[base:base + 0x228], index[base:base + 0x228])
        self.assertEqual(struct.unpack_from("<I", second, base + 0x678 + 0x224)[0], 1)

    @unittest.skipUnless(REAL_SAMPLE.is_file(), "private CLE sample unavailable")
    def test_real_sample_normalizes_and_nochange_is_identical(self):
        source = SaveData()
        self.assertTrue(source.load(REAL_SAMPLE))
        self.assertEqual(source.read_u32(OFFSETS["mira"]), 97300)
        self.assertEqual(source.read_u32(OFFSETS["dp"]), 355)
        self.assertEqual(source.read_u8(OFFSETS["difficulty"]), 2)
        self.assertEqual(len(source.read_items()), 595)
        self.assertEqual(encode_cle_kai(nisa_to_cle(source.data, original=source.cle_payload)), REAL_SAMPLE.read_bytes())


if __name__ == "__main__":
    unittest.main()
