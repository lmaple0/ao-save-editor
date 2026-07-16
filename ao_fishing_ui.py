"""Editable fishing-notebook UI backed by verified NISA record fields."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ao_fishing import (
    fishing_reward_item_name,
    FISH_SIZE_RANGES,
    bait_item_ids_for_flags,
    known_reward_flags,
    read_fishing_notebook,
    register_all_fish,
    reward_items_for_flags,
    write_fish_maximum_size,
)


def format_reward_names(record, item_name, lang: str) -> str:
    labels = [
        f"{fishing_reward_item_name(item_id, lang, item_name)} ×{quantity}"
        for item_id, quantity in reward_items_for_flags(record.index, record.reward_flags)
    ]
    unknown = record.reward_flags & ~known_reward_flags(record.index)
    if unknown:
        labels.append(f"0x{unknown:04X}")
    separator = ", " if lang == "en" else "、"
    return separator.join(labels) if labels else "—"


def format_bait_names(record, item_name, lang: str) -> str:
    labels = [item_name(item_id, lang) for item_id in bait_item_ids_for_flags(record.bait_flags)]
    separator = ", " if lang == "en" else "、"
    return separator.join(labels) if labels else "—"


class FishingUiMixin:
    def _build_fishing_tab(self, frame, item_name):
        self._fishing_item_name = item_name
        self._fishing_ui_dirty = True

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        self._fishing_progress_label = ttk.Label(toolbar, text=self._t("登记进度: 0/31"))
        self._fishing_progress_label.pack(side="left", padx=(0, 12))
        self._fishing_register_button = ttk.Button(
            toolbar, text=self._t("选中 → 登记"), command=self._register_selected_fish
        )
        self._fishing_register_button.pack(side="left", padx=3)
        self._fishing_unregister_button = ttk.Button(
            toolbar, text=self._t("选中 → 未登记"), command=self._unregister_selected_fish
        )
        self._fishing_unregister_button.pack(side="left", padx=3)
        self._fishing_register_all_button = ttk.Button(
            toolbar, text=self._t("全部登记"), command=self._register_all_fish
        )
        self._fishing_register_all_button.pack(side="left", padx=3)

        editor = ttk.Frame(frame)
        editor.pack(fill="x", padx=8, pady=4)
        self._fishing_size_label = ttk.Label(editor, text=self._t("最大尺寸:"))
        self._fishing_size_label.pack(side="left")
        self._fishing_size_var = tk.StringVar()
        self._fishing_size_entry = ttk.Entry(editor, textvariable=self._fishing_size_var, width=9)
        self._fishing_size_entry.pack(side="left", padx=4)
        self._fishing_apply_button = ttk.Button(
            editor, text=self._t("应用最大尺寸"), command=self._apply_selected_fish_size
        )
        self._fishing_apply_button.pack(side="left", padx=3)
        self._fishing_hint_label = ttk.Label(
            editor, text=self._t("0 表示未登记；登记尺寸必须位于自然范围内")
        )
        self._fishing_hint_label.pack(side="left", padx=10)

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        columns = ("index", "name", "status", "maximum", "range", "count", "reward", "bait")
        self._fishing_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        widths = {"index": 55, "name": 150, "status": 75, "maximum": 80, "range": 90, "count": 80, "reward": 290, "bait": 250}
        for column in columns:
            self._fishing_tree.column(column, width=widths[column], anchor="center" if column != "name" else "w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self._fishing_tree.yview)
        self._fishing_tree.configure(yscrollcommand=scrollbar.set)
        self._fishing_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._fishing_tree.bind("<<TreeviewSelect>>", self._on_fishing_selection)
        self._refresh_fishing_language(refresh_rows=False)

    def _refresh_fishing_language(self, refresh_rows=True):
        if not hasattr(self, "_fishing_tree"):
            return
        headings = {
            "index": "序号", "name": "名称", "status": "状态", "maximum": "最大尺寸",
            "range": "自然范围", "count": "累计次数", "reward": "奖励资料", "bait": "鱼饵资料",
        }
        for column, key in headings.items():
            self._fishing_tree.heading(column, text=self._t(key))
        self._fishing_register_button.configure(text=self._t("选中 → 登记"))
        self._fishing_unregister_button.configure(text=self._t("选中 → 未登记"))
        self._fishing_register_all_button.configure(text=self._t("全部登记"))
        self._fishing_size_label.configure(text=self._t("最大尺寸:"))
        self._fishing_apply_button.configure(text=self._t("应用最大尺寸"))
        self._fishing_hint_label.configure(text=self._t("0 表示未登记；登记尺寸必须位于自然范围内"))
        if refresh_rows and self.save.data is not None:
            self._refresh_fishing_ui()

    def _refresh_fishing_ui(self):
        if self.save.data is None:
            return
        selected = set(self._fishing_tree.selection())
        records = read_fishing_notebook(self.save.data)
        self._fishing_tree.delete(*self._fishing_tree.get_children())
        lang = self._current_ui_language()
        for record in records:
            iid = str(record.index)
            self._fishing_tree.insert("", "end", iid=iid, values=(
                f"{record.index + 1:02d}",
                self._fishing_item_name(record.item_id, lang),
                self._t("已登记") if record.registered else self._t("未登记"),
                record.maximum_size if record.registered else "—",
                f"{record.min_size}–{record.natural_max_size}",
                record.caught_count,
                format_reward_names(record, self._fishing_item_name, lang),
                format_bait_names(record, self._fishing_item_name, lang),
            ))
        restored = tuple(iid for iid in selected if self._fishing_tree.exists(iid))
        if restored:
            self._fishing_tree.selection_set(restored)
        registered = sum(record.registered for record in records)
        self._fishing_progress_label.configure(text=self._t("登记进度: {count}/31", count=registered))
        self._fishing_ui_dirty = False

    def _selected_fish_indices(self):
        return tuple(sorted(int(iid) for iid in self._fishing_tree.selection()))

    def _require_selected_fish(self):
        indices = self._selected_fish_indices()
        if not indices:
            self._set_status("请先选择鱼类记录")
        return indices

    def _on_fishing_selection(self, _event=None):
        indices = self._selected_fish_indices()
        if len(indices) != 1 or self.save.data is None:
            return
        record = read_fishing_notebook(self.save.data)[indices[0]]
        self._fishing_size_var.set(str(record.maximum_size))

    def _register_selected_fish(self):
        if self.save.data is None:
            self._set_status("请先打开存档文件")
            return
        indices = self._require_selected_fish()
        if not indices:
            return
        for index in indices:
            write_fish_maximum_size(self.save.data, index, FISH_SIZE_RANGES[index][1])
        self._fishing_after_edit("已登记选中鱼类: {count}", count=len(indices))

    def _unregister_selected_fish(self):
        if self.save.data is None:
            self._set_status("请先打开存档文件")
            return
        indices = self._require_selected_fish()
        if not indices:
            return
        for index in indices:
            write_fish_maximum_size(self.save.data, index, 0)
        self._fishing_after_edit("已设为未登记: {count}", count=len(indices))

    def _register_all_fish(self):
        if self.save.data is None:
            self._set_status("请先打开存档文件")
            return
        register_all_fish(self.save.data)
        self._fishing_after_edit("全部鱼类已登记")

    def _apply_selected_fish_size(self):
        if self.save.data is None:
            self._set_status("请先打开存档文件")
            return
        indices = self._require_selected_fish()
        if len(indices) != 1:
            self._set_status("修改最大尺寸时只能选择一项")
            return
        try:
            value = int(self._fishing_size_var.get(), 10)
            write_fish_maximum_size(self.save.data, indices[0], value)
        except ValueError:
            minimum, maximum = FISH_SIZE_RANGES[indices[0]]
            self._set_status("最大尺寸必须为 0 或 {minimum} 到 {maximum}", minimum=minimum, maximum=maximum)
            return
        self._fishing_after_edit("最大尺寸已设为 {value}", value=value)

    def _fishing_after_edit(self, status, **kwargs):
        self._refresh_fishing_ui()
        if hasattr(self, "_save_audit_dirty"):
            self._save_audit_dirty = True
        self._set_status(status, **kwargs)
