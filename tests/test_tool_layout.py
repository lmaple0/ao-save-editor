import unittest
from pathlib import Path

from tools import build_chest_reference, build_monster_details, build_reference_graph
from tools.build_monster_reference import build_reference


ROOT = Path(__file__).resolve().parent.parent


class ToolLayoutTests(unittest.TestCase):
    def test_generators_resolve_runtime_data_from_package_root(self):
        for module in (
            build_chest_reference,
            build_monster_details,
            build_reference_graph,
        ):
            self.assertEqual(module.WORKSPACE_ROOT, ROOT)

    def test_generator_module_interface_is_importable(self):
        self.assertTrue(callable(build_reference))

    def test_documentation_and_tool_directories_are_present(self):
        self.assertTrue((ROOT / "docs" / "ao_save_editor_roadmap.md").is_file())
        self.assertTrue((ROOT / "docs" / "research").is_dir())
        self.assertTrue((ROOT / "tools" / "build_reference_graph.py").is_file())

    def test_legacy_root_layout_does_not_return(self):
        legacy_tools = (
            "build_chest_reference.py",
            "build_monster_details.py",
            "build_monster_locations.py",
            "build_monster_reference.py",
            "build_reference_graph.py",
        )
        self.assertFalse(any((ROOT / name).exists() for name in legacy_tools))
        legacy_docs = (
            "ao_nisa_loadout_fishing_research.md",
            "ao_save_editor_roadmap.md",
            "cle_kai_save_research.md",
            "nisa_party_id_research.md",
            "project1_zero_feasibility.md",
        )
        self.assertFalse(any((ROOT / name).exists() for name in legacy_docs))
