import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "packaging" / "ao_save_editor.spec"
BUILD_SCRIPT = ROOT / "packaging" / "build_windows.ps1"
BUILD_REQUIREMENTS = ROOT / "packaging" / "requirements-build.txt"
ICON_PATH = ROOT / "packaging" / "kea.ico"

EXPECTED_RUNTIME_DATA = {
    "ao_achievement_i18n.json",
    "ao_chest_reference.json",
    "ao_item_i18n.json",
    "ao_item_index.json",
    "ao_monster_details.json",
    "ao_monster_reference.json",
    "ao_reference_graph.json",
}


def spec_runtime_data_files():
    tree = ast.parse(SPEC_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "RUNTIME_DATA_FILES"
                for target in node.targets
            ):
                return set(ast.literal_eval(node.value))
    raise AssertionError("RUNTIME_DATA_FILES was not found in the spec")


class WindowsPackagingTests(unittest.TestCase):
    def test_spec_bundles_only_required_runtime_data(self):
        self.assertEqual(spec_runtime_data_files(), EXPECTED_RUNTIME_DATA)
        for name in EXPECTED_RUNTIME_DATA:
            self.assertTrue((ROOT / name).is_file(), name)

    def test_spec_supports_debug_and_release_shapes_without_upx(self):
        source = SPEC_PATH.read_text(encoding="utf-8")
        self.assertIn('{"onefile", "onedir"}', source)
        self.assertIn("upx=False", source)
        self.assertIn("console=False", source)
        self.assertIn('icon=str(ICON_PATH)', source)

    def test_windows_icon_is_a_packaged_ico_resource(self):
        header = ICON_PATH.read_bytes()[:6]
        self.assertEqual(header, b"\x00\x00\x01\x00\x01\x00")

    def test_build_script_has_a_small_stable_interface(self):
        source = BUILD_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('[ValidateSet("OneFile", "OneDir")]', source)
        self.assertIn('[string]$PythonPath = ""', source)
        self.assertIn("Get-FileHash", source)

    def test_build_dependency_is_pinned(self):
        requirements = BUILD_REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        self.assertIn("-r ../requirements.txt", requirements)
        self.assertIn("pyinstaller==6.21.0", requirements)


if __name__ == "__main__":
    unittest.main()
