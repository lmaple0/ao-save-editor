import unittest

from ao_save_editor import SaveEditor, UI_TRANSLATIONS, get_reference_graph


class ReferenceIndexUiContractTests(unittest.TestCase):
    def test_lazy_graph_and_read_only_ui_methods_are_available(self):
        graph = get_reference_graph()
        self.assertEqual(graph.metadata["summary"]["character_count"], 36)
        for method in (
            "_build_reference_tab",
            "_refresh_reference_ui",
            "_refresh_reference_detail",
            "_set_reference_detail_text",
        ):
            self.assertTrue(callable(getattr(SaveEditor, method)))
        self.assertFalse(hasattr(graph, "save"))

    def test_reference_ui_strings_cover_all_languages(self):
        keys = (
            "资源索引", "搜索资源:", "全部类型", "只看异常", "类型",
            "标识", "可信度", "关系详情", "资源索引数据不可用",
            "角色", "怪物", "状态文件", "动作脚本", "动作入口",
            "已验证", "推导", "候选", "异常", "关系", "出站", "入站",
        )
        for locale in ("zh_cn", "ja", "en"):
            for key in keys:
                self.assertTrue(UI_TRANSLATIONS[locale].get(key), (locale, key))

    def test_result_limit_prevents_large_tree_population(self):
        from ao_reference_index_ui import REFERENCE_RESULT_LIMIT

        self.assertEqual(REFERENCE_RESULT_LIMIT, 500)


if __name__ == "__main__":
    unittest.main()
