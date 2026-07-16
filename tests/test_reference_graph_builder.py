import struct
import tempfile
import unittest
from pathlib import Path

from tools.build_reference_graph import ParseError, parse_action_script, parse_t_name


class ReferenceGraphBuilderTests(unittest.TestCase):
    def test_t_name_parser_decodes_resources_without_executing_python(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "t_name._dt"
            path.write_bytes(
                struct.pack("<HHIIII", 1, 40, 0x00700000, 0x00700001, 0x30000100, 0)
                + struct.pack("<HHIIII", 0x03E7, 0, 0, 0, 0, 0)
                + b"Lloyd\0"
            )
            rows, source = parse_t_name(path, "cp932")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Lloyd")
        self.assertEqual(rows[0]["walk_model"], "chr/ch00000.itc")
        self.assertEqual(rows[0]["run_model"], "chr/ch00001.itc")
        self.assertEqual(rows[0]["battle_file"], "ms00100.dat")
        self.assertEqual(source["size"], 46)

    @staticmethod
    def _minimal_action_script(action_offset=36):
        return (
            struct.pack("<HHH", 32, 16, 0)
            + struct.pack("<I", 0xFFFFFFFF)
            + b"\0" * 6
            + b"\0" * 16
            + struct.pack("<HH", action_offset, 0)
            + b"\x01"
        )

    def test_action_parser_reads_header_preloads_positions_and_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "as00000.dat"
            path.write_bytes(self._minimal_action_script())
            parsed = parse_action_script(path)
        self.assertEqual(parsed["action_list_offset"], 32)
        self.assertEqual(parsed["preload_models"], [])
        self.assertEqual(len(parsed["character_positions"]), 8)
        self.assertEqual(parsed["actions"], [
            {"index": 0, "offset": 36, "builtin_name": "SysCraft_Init"}
        ])

    def test_bounds_checks_reject_truncated_or_out_of_range_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            bad_name = directory / "t_name._dt"
            bad_name.write_bytes(b"\0" * 19)
            with self.assertRaises(ParseError):
                parse_t_name(bad_name, "cp932")

            bad_action = directory / "as00000.dat"
            bad_action.write_bytes(self._minimal_action_script(0x2000))
            with self.assertRaises(ParseError):
                parse_action_script(bad_action)


if __name__ == "__main__":
    unittest.main()
