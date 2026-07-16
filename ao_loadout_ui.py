"""Editable character equipment/orbment tab for the Ao NISA save editor."""

from __future__ import annotations

from tkinter import messagebox, ttk
import tkinter as tk

from ao_character_loadout import (
    EQUIPMENT_SLOT_NAMES,
    LOADOUT_CHARACTERS,
    ORBMENT_SLOT_COUNT,
    apply_character_loadout_changes,
    equipment_code_is_allowed,
    read_character_loadouts,
)
from ao_items_db import ITEM_DB
from ao_orbment_rules import orbment_code_is_allowed


LOADOUT_TEXT = {
    "zh_cn": {
        "tab": "人物装备 / 回路",
        "character": "人物",
        "equipment": "人物装备",
        "weapon": "武器",
        "clothes": "服装",
        "shoes": "鞋",
        "accessory_1": "饰品 1",
        "accessory_2": "饰品 2",
        "orbment": "核心回路 / 普通回路",
        "core": "核心回路",
        "quartz": "回路 {index}",
        "enhancement": "槽强化",
        "empty": "空",
        "backpack": "背包 {quantity}",
        "equipped": "已装备",
        "apply": "应用当前人物",
        "refresh": "重新读取",
        "warning": "修改会同步装备槽与背包数量，并校验武器类别、槽位类型、元素限定槽、同人物重复普通回路及核心回路唯一性。建议先备份存档。",
        "applied": "{character} 的装备/回路已写入内存 · 请保存存档",
        "load_first": "请先打开存档文件",
        "error": "装备/回路修改失败：\n{error}",
    },
    "en": {
        "tab": "Equipment / Orbment",
        "character": "Character",
        "equipment": "Equipment",
        "weapon": "Weapon",
        "clothes": "Clothes",
        "shoes": "Shoes",
        "accessory_1": "Accessory 1",
        "accessory_2": "Accessory 2",
        "orbment": "Core / Normal Quartz",
        "core": "Core Quartz",
        "quartz": "Quartz {index}",
        "enhancement": "Slot level",
        "empty": "Empty",
        "backpack": "Inventory {quantity}",
        "equipped": "Equipped",
        "apply": "Apply character",
        "refresh": "Reload",
        "warning": "Changes update both loadout slots and inventory quantities. Weapon categories, slot types, element locks, duplicate normal quartz, and core uniqueness are checked. Back up the save first.",
        "applied": "Updated {character} equipment/orbment in memory · save the file to persist",
        "load_first": "Open a save file first",
        "error": "Equipment/orbment update failed:\n{error}",
    },
    "ja": {
        "tab": "装備 / オーブメント",
        "character": "キャラクター",
        "equipment": "装備",
        "weapon": "武器",
        "clothes": "服",
        "shoes": "靴",
        "accessory_1": "アクセサリ 1",
        "accessory_2": "アクセサリ 2",
        "orbment": "マスター / 通常クオーツ",
        "core": "マスタークオーツ",
        "quartz": "クオーツ {index}",
        "enhancement": "スロット強化",
        "empty": "空き",
        "backpack": "所持 {quantity}",
        "equipped": "装備中",
        "apply": "このキャラに適用",
        "refresh": "再読み込み",
        "warning": "装備スロットと所持数を同時に更新し、武器種、スロット種別、属性限定、同一通常クオーツの重複、マスタークオーツの一意性を検査します。先にバックアップしてください。",
        "applied": "{character} の装備/クオーツをメモリに反映しました · セーブしてください",
        "load_first": "先にセーブデータを開いてください",
        "error": "装備/クオーツの変更に失敗しました：\n{error}",
    },
}


class LoadoutUiMixin:
    def _loadout_t(self, key, **kwargs):
        lang = self._current_ui_language()
        text = LOADOUT_TEXT.get(lang, LOADOUT_TEXT["zh_cn"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def _build_loadout_tab(self, frame, item_name_callback, character_name_callback):
        self._loadout_tab_frame = frame
        self._loadout_item_name = item_name_callback
        self._loadout_character_name = character_name_callback
        self._loadout_refreshing = False
        self._loadout_ui_dirty = True

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=10, pady=(10, 5))
        self._loadout_character_label = ttk.Label(top)
        self._loadout_character_label.pack(side="left", padx=(0, 5))
        self._loadout_character_var = tk.StringVar(value="0")
        self._loadout_character_combo = ttk.Combobox(
            top, textvariable=self._loadout_character_var, width=24, state="readonly"
        )
        self._loadout_character_combo.pack(side="left", padx=3)
        self._loadout_character_combo.bind(
            "<<ComboboxSelected>>", lambda _event: self._refresh_loadout_ui()
        )
        self._loadout_apply_button = ttk.Button(top, command=self._apply_loadout_from_ui)
        self._loadout_apply_button.pack(side="right", padx=3)
        self._loadout_refresh_button = ttk.Button(top, command=self._refresh_loadout_ui)
        self._loadout_refresh_button.pack(side="right", padx=3)

        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True, padx=10, pady=5)
        body.grid_columnconfigure(0, weight=1, uniform="loadout")
        body.grid_columnconfigure(1, weight=1, uniform="loadout")

        self._loadout_equipment_frame = ttk.LabelFrame(body)
        self._loadout_equipment_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._loadout_orbment_frame = ttk.LabelFrame(body)
        self._loadout_orbment_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self._loadout_equipment_vars = []
        self._loadout_equipment_labels = []
        self._loadout_equipment_combos = []
        for row, slot in enumerate(EQUIPMENT_SLOT_NAMES):
            label = ttk.Label(self._loadout_equipment_frame)
            label.grid(row=row, column=0, sticky="e", padx=5, pady=7)
            var = tk.StringVar()
            combo = ttk.Combobox(
                self._loadout_equipment_frame, textvariable=var, width=46, state="readonly"
            )
            combo.grid(row=row, column=1, sticky="ew", padx=5, pady=7)
            combo.bind("<<ComboboxSelected>>", self._on_loadout_value_changed)
            self._loadout_equipment_labels.append((label, slot))
            self._loadout_equipment_vars.append(var)
            self._loadout_equipment_combos.append(combo)
        self._loadout_equipment_frame.grid_columnconfigure(1, weight=1)

        self._loadout_orbment_vars = []
        self._loadout_orbment_labels = []
        self._loadout_orbment_combos = []
        self._loadout_level_vars = []
        self._loadout_level_combos = []
        for row in range(ORBMENT_SLOT_COUNT):
            label = ttk.Label(self._loadout_orbment_frame)
            label.grid(row=row, column=0, sticky="e", padx=5, pady=5)
            item_var = tk.StringVar()
            item_combo = ttk.Combobox(
                self._loadout_orbment_frame, textvariable=item_var, width=36, state="readonly"
            )
            item_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
            item_combo.bind("<<ComboboxSelected>>", self._on_loadout_value_changed)
            level_var = tk.StringVar(value="0")
            level_combo = ttk.Combobox(
                self._loadout_orbment_frame,
                textvariable=level_var,
                values=("0", "1", "2"),
                width=4,
                state="readonly",
            )
            level_combo.grid(row=row, column=2, sticky="w", padx=(2, 5), pady=5)
            level_combo.bind("<<ComboboxSelected>>", self._on_loadout_value_changed)
            self._loadout_orbment_labels.append((label, row))
            self._loadout_orbment_vars.append(item_var)
            self._loadout_orbment_combos.append(item_combo)
            self._loadout_level_vars.append(level_var)
            self._loadout_level_combos.append(level_combo)
        self._loadout_orbment_frame.grid_columnconfigure(1, weight=1)

        self._loadout_warning_label = ttk.Label(frame, wraplength=1040, justify="left")
        self._loadout_warning_label.pack(fill="x", padx=12, pady=(3, 10))
        self._refresh_loadout_language()

    def _loadout_character_index(self):
        try:
            return int(self._loadout_character_var.get().split(":", 1)[0])
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _loadout_parse_choice(value):
        token = str(value).split("|", 1)[0].strip()
        if token.lower().startswith("0x"):
            return int(token, 16)
        return int(token)

    def _loadout_format_choice(self, code, current_codes):
        if not code:
            return f"0x0000 | {self._loadout_t('empty')}"
        name = self._loadout_item_name(code, self._current_ui_language())
        notes = []
        if code in current_codes:
            notes.append(self._loadout_t("equipped"))
        quantity = int(self._items_data.get(code, 0) or 0)
        if quantity:
            notes.append(self._loadout_t("backpack", quantity=quantity))
        suffix = f" | {', '.join(notes)}" if notes else ""
        return f"0x{code:04X} | {name}{suffix}"

    def _refresh_loadout_language(self):
        if not hasattr(self, "_loadout_tab_frame"):
            return
        self._nb.tab(self._loadout_tab_frame, text=self._loadout_t("tab"))
        self._loadout_character_label.configure(text=self._loadout_t("character"))
        self._loadout_equipment_frame.configure(text=self._loadout_t("equipment"))
        self._loadout_orbment_frame.configure(text=self._loadout_t("orbment"))
        self._loadout_apply_button.configure(text=self._loadout_t("apply"))
        self._loadout_refresh_button.configure(text=self._loadout_t("refresh"))
        self._loadout_warning_label.configure(text=self._loadout_t("warning"))
        for label, slot in self._loadout_equipment_labels:
            label.configure(text=self._loadout_t(slot))
        for label, index in self._loadout_orbment_labels:
            key = "core" if index == 0 else "quartz"
            label.configure(text=self._loadout_t(key, index=index))

        selected = self._loadout_character_index()
        lang = self._current_ui_language()
        values = [
            f"{index}: {self._loadout_character_name(character, lang)}"
            for index, character in enumerate(LOADOUT_CHARACTERS)
        ]
        self._loadout_character_combo.configure(values=values)
        self._loadout_character_var.set(values[min(selected, len(values) - 1)])
        if self.save.data is not None:
            self._refresh_loadout_ui()

    def _refresh_loadout_ui(self):
        if not hasattr(self, "_loadout_character_combo"):
            return
        if self.save.data is None:
            self._loadout_ui_dirty = False
            return
        self._loadout_refreshing = True
        try:
            if not hasattr(self, "_items_data"):
                self._items_data = self.save.read_items()
            loadouts = read_character_loadouts(self.save.data)
            index = max(0, min(self._loadout_character_index(), len(loadouts) - 1))
            loadout = loadouts[index]
            categories = {code: row[0] for code, row in ITEM_DB.items()}
            inventory_codes = {code for code, qty in self._items_data.items() if qty > 0}

            current_equipment = set(loadout.equipment.values()) - {0}
            for slot, current_code, var, combo in zip(
                EQUIPMENT_SLOT_NAMES,
                loadout.equipment.values(),
                self._loadout_equipment_vars,
                self._loadout_equipment_combos,
            ):
                candidates = {0, current_code}
                candidates.update(
                    code for code in inventory_codes
                    if equipment_code_is_allowed(loadout.character, slot, code, categories)
                    and code != 0x0009
                )
                values = [
                    self._loadout_format_choice(code, current_equipment)
                    for code in sorted(candidates)
                ]
                combo.configure(values=values)
                var.set(self._loadout_format_choice(current_code, current_equipment))

            current_core = {loadout.orbment[0].item_code} - {0}
            current_normal = {slot.item_code for slot in loadout.orbment[1:] if slot.item_code}
            for slot_index, (slot, var, combo, level_var) in enumerate(zip(
                loadout.orbment,
                self._loadout_orbment_vars,
                self._loadout_orbment_combos,
                self._loadout_level_vars,
            )):
                category = "circuit_core" if slot_index == 0 else "circuit_normal"
                current_codes = current_core if slot_index == 0 else current_normal
                candidates = {0, slot.item_code}
                candidates.update(
                    code for code in inventory_codes
                    if categories.get(code) == category
                    and orbment_code_is_allowed(loadout.character, slot_index, code)
                )
                values = [
                    self._loadout_format_choice(code, current_codes)
                    for code in sorted(candidates)
                ]
                combo.configure(values=values)
                var.set(self._loadout_format_choice(slot.item_code, current_codes))
                level_var.set(str(slot.enhancement_level))
            self._loadout_ui_dirty = False
        finally:
            self._loadout_refreshing = False

    def _on_loadout_value_changed(self, _event=None):
        if not self._loadout_refreshing:
            self._apply_loadout_from_ui()

    def _apply_loadout_from_ui(self):
        if self._loadout_refreshing:
            return
        if self.save.data is None:
            self._set_status(self._loadout_t("load_first"))
            return
        index = max(0, min(self._loadout_character_index(), len(LOADOUT_CHARACTERS) - 1))
        character = LOADOUT_CHARACTERS[index]
        try:
            equipment_codes = tuple(
                self._loadout_parse_choice(var.get()) for var in self._loadout_equipment_vars
            )
            orbment_codes = tuple(
                self._loadout_parse_choice(var.get()) for var in self._loadout_orbment_vars
            )
            levels = tuple(int(var.get()) for var in self._loadout_level_vars)
            categories = {code: row[0] for code, row in ITEM_DB.items()}
            new_data, new_items = apply_character_loadout_changes(
                self.save.data,
                self._items_data,
                character,
                equipment_codes,
                orbment_codes,
                levels,
                categories,
            )
            previous_data = self.save.data
            self.save.data = new_data
            try:
                self.save.write_items(new_items)
            except Exception:
                self.save.data = previous_data
                raise
        except (TypeError, ValueError) as exc:
            messagebox.showerror(self._loadout_t("tab"), self._loadout_t("error", error=str(exc)))
            self._refresh_loadout_ui()
            return

        self._items_data = new_items
        self._items_ui_dirty = True
        self._save_audit_dirty = True
        self._refresh_loadout_ui()
        name = self._loadout_character_name(character, self._current_ui_language())
        self._set_status(self._loadout_t("applied", character=name))
