from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parent
INDEX_JSON = ROOT / "ao_item_index.json"


def _load_item_db() -> dict[int, tuple[str, str]]:
    try:
        data = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    result: dict[int, tuple[str, str]] = {}
    for row in data.get("items", []):
        try:
            code = int(row["id_dec"])
        except (KeyError, TypeError, ValueError):
            continue
        category = row.get("category") or "unknown"
        name = row.get("zh_joyoland") or row.get("zh_cle") or f"未知(0x{code:04x})"
        result[code] = (category, name)
    return result


# Compatibility surface used by ao_save_editor.py and glossary builders.
# Key: item_code (int), Value: (category, zh_joyoland_name)
ITEM_DB = _load_item_db()
