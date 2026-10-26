"""Search the full item catalog and add quantities without replacing items."""

import tkinter as tk
from tkinter import ttk, messagebox

ITEM_ADD_TRANSLATIONS = {
    "zh_cn": {
        "清除筛选": "清除筛选", "添加物品": "添加物品", "持有数量": "持有数量",
        "添加数量 (1-99):": "添加数量 (1-99):", "关闭": "关闭",
        "已持有物品会增加数量，不替换其他物品。": "已持有物品会增加数量，不替换其他物品。",
        "添加数量必须是 1 到 99 之间的整数": "添加数量必须是 1 到 99 之间的整数",
        "添加后数量不能超过 99": "添加后数量不能超过 99",
        "已添加 {name} ×{quantity}，现持有 {total} · 请保存存档": "已添加 {name} ×{quantity}，现持有 {total} · 请保存存档",
    },
    "en": {
        "清除筛选": "Clear Filter", "添加物品": "Add Item", "持有数量": "Owned",
        "添加数量 (1-99):": "Add quantity (1-99):", "关闭": "Close",
        "已持有物品会增加数量，不替换其他物品。": "Adds to existing quantities without replacing other items.",
        "添加数量必须是 1 到 99 之间的整数": "Quantity to add must be an integer from 1 to 99.",
        "添加后数量不能超过 99": "The resulting quantity cannot exceed 99.",
        "已添加 {name} ×{quantity}，现持有 {total} · 请保存存档": "Added {quantity} × {name}; now owned: {total} · save the file",
    },
    "ja": {
        "清除筛选": "絞り込み解除", "添加物品": "アイテム追加", "持有数量": "所持数",
        "添加数量 (1-99):": "追加数 (1-99):", "关闭": "閉じる",
        "已持有物品会增加数量，不替换其他物品。": "所持済みの場合は個数を加算します。他のアイテムは置換しません。",
        "添加数量必须是 1 到 99 之间的整数": "追加数は1～99の整数で入力してください。",
        "添加后数量不能超过 99": "追加後の所持数は99を超えられません。",
        "已添加 {name} ×{quantity}，现持有 {total} · 请保存存档": "{name}を{quantity}個追加、所持数: {total} · セーブしてください",
    },
}


class AddItemDialog(tk.Toplevel):
    def __init__(self, parent, translate, catalog, owned, on_add):
        super().__init__(parent)
        self._t = translate
        self.catalog = catalog
        self.owned = dict(owned)
        self.on_add = on_add
        self.title(self._t("添加物品"))
        self.geometry("640x480")
        self.transient(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        search_bar = ttk.Frame(self)
        search_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        ttk.Label(search_bar, text=self._t("搜索:")).pack(side="left")
        self.search_var = tk.StringVar()
        search = ttk.Entry(search_bar, textvariable=self.search_var)
        search.pack(side="left", fill="x", expand=True, padx=6)
        self.search_var.trace_add("write", lambda *_: self._refresh())

        table = ttk.Frame(self)
        table.grid(row=1, column=0, sticky="nsew", padx=10)
        self.tree = ttk.Treeview(table, columns=("code", "name", "owned"), show="headings", selectmode="browse")
        for key, text, width in (("code", "代码", 95), ("name", "名称", 340), ("owned", "持有数量", 85)):
            self.tree.heading(key, text=self._t(text))
            self.tree.column(key, width=width, anchor="w" if key == "name" else "center")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        controls = ttk.Frame(self)
        controls.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ttk.Label(controls, text=self._t("添加数量 (1-99):")).pack(side="left")
        self.quantity_var = tk.StringVar(value="1")
        ttk.Spinbox(controls, from_=1, to=99, textvariable=self.quantity_var, width=6).pack(side="left", padx=6)
        self.add_button = ttk.Button(controls, text=self._t("添加物品"), command=self._add)
        self.add_button.pack(side="left", padx=6)
        ttk.Button(controls, text=self._t("关闭"), command=self.destroy).pack(side="right")
        ttk.Label(self, text=self._t("已持有物品会增加数量，不替换其他物品。"), wraplength=600).grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))
        self._refresh()
        search.focus_set()
        self.grab_set()

    def _refresh(self):
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        query = self.search_var.get().strip().casefold()
        for code, name, search_text in self.catalog:
            if not query or query in search_text.casefold():
                iid = f"{code:04x}"
                self.tree.insert("", "end", iid=iid, values=(f"0x{code:04x}", name, self.owned.get(code, 0)))
                if iid in selected:
                    self.tree.selection_set(iid)

    def _add(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(self._t("提示"), self._t("请先选择一个物品"), parent=self)
            return
        try:
            quantity = int(self.quantity_var.get())
        except ValueError:
            messagebox.showerror(self._t("错误"), self._t("添加数量必须是 1 到 99 之间的整数"), parent=self)
            return
        if not 1 <= quantity <= 99:
            messagebox.showerror(self._t("错误"), self._t("添加数量必须是 1 到 99 之间的整数"), parent=self)
            return
        code = int(selected[0], 16)
        if self.owned.get(code, 0) + quantity > 99:
            messagebox.showerror(self._t("错误"), self._t("添加后数量不能超过 99"), parent=self)
            return
        try:
            total = self.on_add(code, quantity)
        except ValueError as exc:
            messagebox.showerror(self._t("错误"), str(exc), parent=self)
            return
        self.owned[code] = total
        self._refresh()
