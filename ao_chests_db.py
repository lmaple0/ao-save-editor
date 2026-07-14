"""Localized, read-only chest catalog for Ao Save Editor."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


SCENA_FLAGS_OFFSET = 0x1B008
UI_LOCALE_MAP = {"zh_cn": "zh_cle", "ja": "ja", "en": "en"}


def _data_locale(locale):
    return UI_LOCALE_MAP.get(str(locale or "zh_cn"), "zh_cle")


@dataclass(frozen=True)
class ChestRecord:
    id: str
    flag_offset: int
    flag_bit: int
    map_index: int
    map_names: dict
    item_code: int | None
    item_names: dict
    scene_file: str
    trigger: dict
    actor: dict
    talk_scena_index: int
    talk_function_index: int
    source_line: int
    source_map_zh_joyoland: str
    source_item_zh_joyoland: str

    def map_name(self, locale="zh_cn"):
        return self.map_names[_data_locale(locale)]

    def item_name(self, locale="zh_cn"):
        return self.item_names[_data_locale(locale)]

    def is_opened(self, save_data):
        position = SCENA_FLAGS_OFFSET + self.flag_offset
        if position >= len(save_data):
            raise ValueError(f"save data is too short for chest flag: {self.id}")
        return bool(save_data[position] & (1 << self.flag_bit))

    def coordinates(self):
        return tuple(self.actor[key] / 1000.0 for key in ("x", "y", "z"))


class ChestCatalog:
    def __init__(self, rows):
        self._records = tuple(ChestRecord(**row) for row in rows)
        if len({record.id for record in self._records}) != len(self._records):
            raise ValueError("duplicate chest IDs")

    def __len__(self):
        return len(self._records)

    def records(self):
        return self._records

    def maps(self, locale="zh_cn"):
        return tuple(sorted({record.map_name(locale) for record in self._records}, key=str.casefold))

    def search(self, query="", map_name=None, missing_only=False, save_data=None, locale="zh_cn"):
        needle = str(query or "").strip().casefold()
        result = []
        for record in self._records:
            opened = record.is_opened(save_data) if save_data is not None else False
            if missing_only and opened:
                continue
            localized_map = record.map_name(locale)
            if map_name and localized_map != map_name:
                continue
            haystack = " ".join(
                [
                    record.id,
                    record.scene_file,
                    *(record.map_names.values()),
                    *(record.item_names.values()),
                ]
            ).casefold()
            if needle and needle not in haystack:
                continue
            result.append(record)
        return tuple(result)

    def progress(self, save_data):
        opened = sum(record.is_opened(save_data) for record in self._records)
        return opened, len(self._records)


def load_default_chest_catalog(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    path = root / "ao_chest_reference.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return ChestCatalog(data["chests"])
