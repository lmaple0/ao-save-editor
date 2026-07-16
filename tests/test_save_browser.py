import tempfile
import unittest
from pathlib import Path

from ao_save_browser import default_ao_save_root, discover_save_slots


class SaveBrowserTests(unittest.TestCase):
    def test_default_root_is_under_saved_games(self):
        root = default_ao_save_root(Path("C:/Users/Test/Saved Games"))
        self.assertEqual(root, Path("C:/Users/Test/Saved Games/FALCOM/Ao"))

    def test_discovers_only_numbered_slots_with_savedata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, payload in (
                ("data0010", b"ten"),
                ("data0002", b"two"),
                ("DATA0003", b"three"),
            ):
                folder = root / name
                folder.mkdir()
                (folder / "savedata.dat").write_bytes(payload)
            (root / "data0004").mkdir()
            (root / "data12").mkdir()
            (root / "data12" / "savedata.dat").write_bytes(b"ignored")

            entries = discover_save_slots(root)

        self.assertEqual([entry.slot for entry in entries], [2, 3, 10])
        self.assertTrue(all(entry.status == "unchecked" for entry in entries))
        self.assertEqual(entries[0].size, 3)

    def test_validation_isolated_per_slot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for slot, payload in ((1, b"ok"), (2, b"bad")):
                folder = root / f"data{slot:04d}"
                folder.mkdir()
                (folder / "savedata.dat").write_bytes(payload)

            entries = discover_save_slots(
                root, validator=lambda path: path.read_bytes() == b"ok"
            )

        self.assertEqual([entry.status for entry in entries], ["valid", "invalid"])

    def test_missing_root_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "missing"
            self.assertEqual(discover_save_slots(missing), [])


if __name__ == "__main__":
    unittest.main()
