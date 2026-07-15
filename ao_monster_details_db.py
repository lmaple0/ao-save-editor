"""Runtime access to the generated, read-only NISA monster detail catalog."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


UI_LOCALE_MAP = {"zh_cn": "zh_cle", "ja": "ja", "en": "en"}
ATTRIBUTE_KEYS = ("earth", "water", "fire", "wind", "time", "space", "mirage")


def _locale(locale):
    return UI_LOCALE_MAP.get(str(locale or "zh_cn"), "zh_cle")


@dataclass(frozen=True)
class MonsterDetail:
    data: dict

    @property
    def ms_file(self):
        return self.data["ms_file"]

    def name(self, locale="zh_cn"):
        return self.data["names"][_locale(locale)]

    def description(self, locale="zh_cn"):
        return self.data["descriptions"][_locale(locale)]

    def crafts(self, locale="zh_cn"):
        language = _locale(locale)
        return tuple(
            {
                **{key: value for key, value in row.items() if key not in {"names", "descriptions"}},
                "name": row["names"][language],
                "description": row["descriptions"][language],
            }
            for row in self.data["craft_info"]
        )

    def action_script_available(self, locale="zh_cn"):
        return bool(self.data["as_available"][_locale(locale)])


class MonsterDetailCatalog:
    def __init__(self, rows=(), metadata=None):
        self._details = tuple(MonsterDetail(dict(row)) for row in rows)
        self._by_file = {detail.ms_file.casefold(): detail for detail in self._details}
        if len(self._by_file) != len(self._details):
            raise ValueError("duplicate ms filename in monster details")
        self.metadata = dict(metadata or {})

    def __len__(self):
        return len(self._details)

    def get(self, ms_file):
        return self._by_file.get(str(ms_file).casefold())

    def records(self):
        return self._details

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise ValueError(f"unsupported monster detail schema: {data.get('schema_version')!r}")
        rows = data.get("monsters")
        if not isinstance(rows, list):
            raise ValueError("monster detail rows must be a list")
        return cls(rows, {key: value for key, value in data.items() if key != "monsters"})


def load_default_monster_detail_catalog(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    try:
        return MonsterDetailCatalog.load(root / "ao_monster_details.json")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return MonsterDetailCatalog()
