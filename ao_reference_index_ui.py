"""Tkinter mixin for the read-only character/monster/script research index."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import sys


REFERENCE_RESULT_LIMIT = 500
REFERENCE_KIND_KEYS = {
    "character": "角色",
    "monster": "怪物",
    "status_file": "状态文件",
    "action_script": "动作脚本",
    "craft": "战技",
    "action_entry": "动作入口",
}
REFERENCE_CONFIDENCE_KEYS = {
    "verified": "已验证",
    "derived": "推导",
    "candidate": "候选",
}


class ReferenceIndexUiMixin:
    """Read-only GUI adapter over the reference graph's small Interface."""

    def _build_reference_tab(self, frm):
        toolbar = ttk.Frame(frm)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(toolbar, text=self._t("搜索资源:")).pack(side="left", padx=(0, 3))
        self._reference_search_var = tk.StringVar()
        search = ttk.Entry(toolbar, textvariable=self._reference_search_var, width=30)
        search.pack(side="left", padx=3)
        search.bind("<Return>", lambda _event: self._refresh_reference_ui())

        self._reference_kind_var = tk.StringVar(value=self._t("全部类型"))
        self._reference_kind_combo = ttk.Combobox(
            toolbar, textvariable=self._reference_kind_var, width=18, state="readonly"
        )
        self._reference_kind_combo.pack(side="left", padx=(10, 3))
        self._reference_kind_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._refresh_reference_ui()
        )
        self._refresh_reference_kind_choices()

        self._reference_issues_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            toolbar,
            text=self._t("只看异常"),
            variable=self._reference_issues_var,
            command=self._refresh_reference_ui,
        ).pack(side="left", padx=(10, 3))
        ttk.Button(toolbar, text=self._t("过滤"), command=self._refresh_reference_ui).pack(
            side="left", padx=3
        )
        ttk.Button(toolbar, text=self._t("全部显示"), command=self._clear_reference_filter).pack(
            side="left", padx=3
        )

        table = ttk.Frame(frm)
        table.pack(fill="both", expand=True, padx=8, pady=4)
        columns = ("kind", "name", "identifier", "ms", "as", "confidence")
        self._reference_tree = ttk.Treeview(
            table, columns=columns, show="headings", selectmode="browse", height=14
        )
        headings = {
            "kind": "类型", "name": "名称", "identifier": "标识",
            "ms": "状态文件", "as": "动作脚本", "confidence": "可信度",
        }
        widths = {
            "kind": 95, "name": 230, "identifier": 175,
            "ms": 105, "as": 105, "confidence": 85,
        }
        for column in columns:
            self._reference_tree.heading(column, text=self._t(headings[column]))
            self._reference_tree.column(column, width=widths[column], anchor="w")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self._reference_tree.yview)
        self._reference_tree.configure(yscrollcommand=scroll.set)
        self._reference_tree.bind("<<TreeviewSelect>>", self._refresh_reference_detail)
        self._reference_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self._reference_summary_lbl = ttk.Label(frm, text="")
        self._reference_summary_lbl.pack(fill="x", padx=10, pady=(2, 5))
        detail = ttk.LabelFrame(frm, text=self._t("关系详情"))
        detail.pack(fill="both", padx=8, pady=(0, 8))
        self._reference_detail_text = tk.Text(detail, height=12, wrap="word", relief="flat")
        detail_scroll = ttk.Scrollbar(
            detail, orient="vertical", command=self._reference_detail_text.yview
        )
        self._reference_detail_text.configure(
            yscrollcommand=detail_scroll.set, state="disabled"
        )
        self._reference_detail_text.pack(side="left", fill="both", expand=True, padx=6, pady=5)
        detail_scroll.pack(side="right", fill="y")
        self._reference_ui_dirty = True

    def _selected_reference_kind(self):
        selected = self._reference_kind_var.get() if hasattr(self, "_reference_kind_var") else ""
        if not selected or selected == self._t("全部类型"):
            return ""
        for locale in ("zh_cn", "ja", "en"):
            for kind, key in REFERENCE_KIND_KEYS.items():
                # ui_text is exposed by the host module through this helper.
                if selected == self._reference_text_for_locale(key, locale):
                    return kind
        return ""

    def _reference_text_for_locale(self, key, locale):
        # Host implementation deliberately owns the localization table.
        return sys.modules[self.__class__.__module__].ui_text(key, locale)

    def _refresh_reference_kind_choices(self):
        if not hasattr(self, "_reference_kind_combo"):
            return
        current_kind = self._selected_reference_kind()
        values = (self._t("全部类型"),) + tuple(
            self._t(key) for key in REFERENCE_KIND_KEYS.values()
        )
        self._reference_kind_combo.configure(values=values)
        self._reference_kind_var.set(
            self._t(REFERENCE_KIND_KEYS[current_kind]) if current_kind else values[0]
        )

    def _clear_reference_filter(self):
        self._reference_search_var.set("")
        self._reference_kind_var.set(self._t("全部类型"))
        self._reference_issues_var.set(False)
        self._refresh_reference_ui()

    def _reference_kind_label(self, kind):
        return self._t(REFERENCE_KIND_KEYS.get(kind, kind))

    def _reference_confidence_label(self, confidence):
        return self._t(REFERENCE_CONFIDENCE_KEYS.get(confidence, confidence))

    @staticmethod
    def _reference_primary_identifier(node):
        identifiers = node.data.get("identifiers", {})
        for key in (
            "save_code_hex", "character_id_hex", "craft_index_hex",
            "action_index_hex", "ms_file", "as_file",
        ):
            if identifiers.get(key) not in (None, ""):
                return str(identifiers[key])
        return node.id

    def _refresh_reference_ui(self):
        if not hasattr(self, "_reference_tree"):
            return
        graph = sys.modules[self.__class__.__module__].get_reference_graph()
        self._reference_tree.delete(*self._reference_tree.get_children())
        if graph is None or not len(graph):
            self._reference_summary_lbl.config(text=self._t("资源索引数据不可用"))
            self._set_reference_detail_text(self._t("资源索引数据不可用"))
            self._reference_ui_dirty = False
            return

        language = self._current_ui_language()
        matches = graph.search(
            self._reference_search_var.get(),
            kind=self._selected_reference_kind(),
            locale=language,
            issues_only=self._reference_issues_var.get(),
        )
        matches = sorted(
            matches,
            key=lambda node: (
                tuple(REFERENCE_KIND_KEYS).index(node.kind)
                if node.kind in REFERENCE_KIND_KEYS else len(REFERENCE_KIND_KEYS),
                node.label(language).casefold(),
                node.id,
            ),
        )
        shown = matches[:REFERENCE_RESULT_LIMIT]
        for node in shown:
            identifiers = node.data.get("identifiers", {})
            self._reference_tree.insert(
                "", "end", iid=node.id,
                values=(
                    self._reference_kind_label(node.kind),
                    node.label(language),
                    self._reference_primary_identifier(node),
                    identifiers.get("ms_file") or "",
                    identifiers.get("as_file") or "",
                    self._reference_confidence_label(node.data.get("confidence", "verified")),
                ),
                tags=("issue",) if node.issue else (),
            )
        self._reference_tree.tag_configure("issue", foreground="#A13A2B")
        self._reference_summary_lbl.config(
            text=self._t("资源索引: 共 {total} 项，当前显示 {shown} 项", total=len(matches), shown=len(shown))
        )
        self._refresh_reference_detail()
        self._reference_ui_dirty = False

    def _set_reference_detail_text(self, value):
        if not hasattr(self, "_reference_detail_text"):
            return
        self._reference_detail_text.configure(state="normal")
        self._reference_detail_text.delete("1.0", "end")
        self._reference_detail_text.insert("1.0", value)
        self._reference_detail_text.configure(state="disabled")

    @staticmethod
    def _reference_value(value):
        if isinstance(value, bool):
            return "yes" if value else "no"
        if isinstance(value, (list, tuple)):
            return "、".join(str(item) for item in value) or "—"
        return "—" if value in (None, "") else str(value)

    def _refresh_reference_detail(self, _event=None):
        selection = self._reference_tree.selection() if hasattr(self, "_reference_tree") else ()
        if not selection:
            self._set_reference_detail_text(self._t("关系详情"))
            return
        graph = sys.modules[self.__class__.__module__].get_reference_graph()
        explanation = graph.explain(selection[0], self._current_ui_language()) if graph else None
        if explanation is None:
            self._set_reference_detail_text(self._t("资源索引数据不可用"))
            return
        node = explanation.node
        data = node.data
        language = self._current_ui_language()
        lines = [
            f"{self._reference_kind_label(node.kind)} · {node.label(language)}",
            f"ID: {node.id}",
        ]
        labels = data.get("labels", {})
        if labels:
            lines.append("zh_cle / ja / en: " + " / ".join(labels.get(key, "—") for key in ("zh_cle", "ja", "en")))
        identifiers = data.get("identifiers", {})
        for key, value in identifiers.items():
            lines.append(f"{key}: {self._reference_value(value)}")
        for key in (
            "aliases", "walk_model", "run_model", "level", "craft_count",
            "action_count", "valid_action_count", "offset", "builtin_name",
            "action_resolution", "preload_models",
        ):
            if key in data:
                lines.append(f"{key}: {self._reference_value(data[key])}")
        locations = data.get("locations", {})
        if locations:
            data_locale = {"zh_cn": "zh_cle", "ja": "ja", "en": "en"}.get(language, "zh_cle")
            lines.append(f"{self._t('地点')}: {self._reference_value(locations.get(data_locale, []))}")
        lines.append(
            f"{self._t('可信度')}: {self._reference_confidence_label(data.get('confidence', 'verified'))}"
        )
        if node.issue:
            lines.append(f"{self._t('异常')}: yes")

        sources = data.get("sources")
        if isinstance(sources, dict):
            lines.append("")
            lines.append(f"{self._t('来源')}:")
            for locale, source in sources.items():
                if isinstance(source, dict):
                    digest = source.get("sha256")
                    suffix = f" sha256={digest[:12]}…" if digest else ""
                    lines.append(f"  {locale}: {source.get('file', 'embedded')}{suffix}")

        lines.append("")
        lines.append(f"{self._t('关系')} ({len(explanation.links)}):")
        links = sorted(
            explanation.links,
            key=lambda link: (link.edge.relation, link.node.kind, link.node.id),
        )
        for link in links[:300]:
            direction = self._t("出站" if link.direction == "outbound" else "入站")
            confidence = self._reference_confidence_label(link.edge.confidence)
            lines.append(
                f"  {direction} · {link.edge.relation} · {self._reference_kind_label(link.node.kind)} "
                f"{link.node.label(language)} [{link.node.id}] · {confidence}"
            )
            provenance = link.edge.data.get("provenance")
            if provenance:
                lines.append(f"    {self._t('来源')}: {provenance}")
            note = link.edge.data.get("note")
            if note:
                lines.append(f"    note: {note}")
        if len(links) > 300:
            lines.append(f"  … {len(links) - 300} more")
        self._set_reference_detail_text("\n".join(lines))
