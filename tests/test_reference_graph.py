import unittest

from ao_reference_graph_db import load_default_reference_graph


class ReferenceGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = load_default_reference_graph()

    def test_generated_graph_has_all_core_resource_kinds(self):
        summary = self.graph.metadata["summary"]
        self.assertEqual(summary["character_count"], 36)
        self.assertEqual(summary["status_file_count"], 333)
        self.assertEqual(summary["action_script_count"], 276)
        self.assertEqual(summary["kind_counts"]["monster"], 305)
        self.assertGreater(summary["kind_counts"]["action_entry"], 4000)

    def test_cross_language_and_reverse_file_search(self):
        for query in ("幻魔", "ビジョウ", "Vizou", "ms72200.dat", "as72200.dat"):
            matches = self.graph.search(query)
            self.assertTrue(matches, query)

    def test_known_monster_chain_reaches_status_script_crafts_and_actions(self):
        monster = self.graph.search("0x30072200", kind="monster")[0]
        status_links = [link for link in self.graph.neighbors(monster.id) if link.node.kind == "status_file"]
        self.assertEqual(len(status_links), 1)
        status = status_links[0].node
        self.assertEqual(status.data["identifiers"]["ms_file"], "ms72200.dat")
        linked_kinds = {link.node.kind for link in self.graph.neighbors(status.id)}
        self.assertIn("action_script", linked_kinds)
        self.assertIn("craft", linked_kinds)
        craft = self.graph.search("Debilitating Bite", kind="craft")[0]
        self.assertTrue(any(link.node.kind == "action_entry" for link in self.graph.neighbors(craft.id)))

    def test_character_variants_remain_candidates(self):
        lloyd = self.graph.search("0x0060", kind="character")[0]
        candidate_links = [
            link for link in self.graph.neighbors(lloyd.id)
            if link.edge.relation == "possible_variant_of"
        ]
        self.assertEqual(len(candidate_links), 1)
        self.assertEqual(candidate_links[0].edge.confidence, "candidate")

    def test_runtime_graph_is_read_only_and_invalid_skill_links_are_not_claimed(self):
        self.assertFalse(hasattr(self.graph, "save"))
        diagnostics = self.graph.diagnostics()
        self.assertEqual(diagnostics["missing_status_references"], [])
        self.assertEqual(diagnostics["missing_script_references"], [])
        self.assertIn("ms72200.dat:0x03ED->0x0047", diagnostics["unresolved_action_references"])


if __name__ == "__main__":
    unittest.main()
