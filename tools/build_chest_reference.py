#!/usr/bin/env python3
"""Build the localized NISA chest reference from Ouroboros RecordViewer data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


TOWN_LOCALES = {
    "zh_cle": ("data_cn/text/t_town._dt", "gbk"),
    "ja": ("data/text/t_town._dt", "cp932"),
    "en": ("data/text_us/t_town._dt", "cp932"),
}


def _clean_text(value):
    return " ".join(value.replace("丄", " / ").replace("／", " / ").split())


def _read_town_names(path, encoding):
    data = path.read_bytes()
    count = struct.unpack_from("<H", data)[0]
    offsets = struct.unpack_from(f"<{count}H", data, 2)
    result = []
    for offset in offsets:
        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError(f"unterminated t_town entry at 0x{offset:X}: {path}")
        result.append(_clean_text(data[offset:end].decode(encoding)))
    return result


def _localized_town_names(game_root):
    tables = {
        locale: _read_town_names(game_root / relative, encoding)
        for locale, (relative, encoding) in TOWN_LOCALES.items()
    }
    if len({len(values) for values in tables.values()}) != 1:
        raise ValueError("localized t_town table sizes differ")
    return tables


def _read_recordviewer_rows(path):
    raw = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            data = json.loads(raw.decode(encoding))
            break
        except (UnicodeError, json.JSONDecodeError):
            continue
    else:
        raise ValueError(f"cannot decode RecordViewer data: {path}")
    return [row for row in data if "ID" in row]


def _normalized_item_name(value):
    return value.strip().replace("『", "_").replace("』", "")


def _item_lookup(item_index):
    data = json.loads(item_index.read_text(encoding="utf-8"))
    joyoland = {}
    cle = {}
    for row in data.get("items", []):
        name = _normalized_item_name(row.get("zh_joyoland") or "")
        if name:
            old = joyoland.get(name)
            if old is not None and old.get("id_dec") != row.get("id_dec"):
                raise ValueError(f"ambiguous Joyoland item name: {name}")
            joyoland[name] = row
        cle_name = _normalized_item_name(row.get("zh_cle") or "")
        if cle_name:
            cle.setdefault(cle_name, []).append(row)
    return joyoland, cle


def _scene_path(game_root, scene_file):
    for relative in ("data_cn/scena", "data/scena"):
        candidate = game_root / relative / scene_file
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"NISA scene is required: {scene_file}")


def _resolve_item(source_item, joyoland_items, cle_items):
    if source_item == "耀晶片":
        return None
    name = _normalized_item_name(source_item)
    item = joyoland_items.get(name)
    if item is not None:
        return item
    candidates = {int(row["id_dec"]): row for row in cle_items.get(name, [])}
    if len(candidates) == 1:
        return next(iter(candidates.values()))
    raise ValueError(f"unmapped or ambiguous chest item: {source_item}")


def build_reference(recordviewer_json, game_root, item_index):
    rows = _read_recordviewer_rows(recordviewer_json)
    towns = _localized_town_names(game_root)
    joyoland_items, cle_items = _item_lookup(item_index)
    result = []
    for row in rows:
        scene_file = f"{row['File']}.bin"
        scene_data = _scene_path(game_root, scene_file).read_bytes()
        map_index = struct.unpack_from("<H", scene_data, 0x14)[0]
        if not all(map_index < len(names) for names in towns.values()):
            raise ValueError(f"MapIndex out of range: {scene_file} -> {map_index}")

        source_item = row["Item"].strip()
        item = _resolve_item(source_item, joyoland_items, cle_items)
        item_names = (
            {"zh_cle": "耀晶片", "ja": "セピス", "en": "Sepith"}
            if item is None
            else {
                "zh_cle": item.get("zh_cle") or item.get("zh_joyoland"),
                "ja": item.get("ja") or item.get("zh_joyoland"),
                "en": item.get("en") or item.get("zh_joyoland"),
            }
        )
        if not all(item_names.values()):
            raise ValueError(f"incomplete item localization: {source_item}")

        result.append(
            {
                "id": row["ID"],
                "flag_offset": int(row["Offset"], 16),
                "flag_bit": int(row["Bit"]),
                "map_index": map_index,
                "map_names": {locale: names[map_index] for locale, names in towns.items()},
                "item_code": None if item is None else int(item["id_dec"]),
                "item_names": item_names,
                "scene_file": scene_file,
                "trigger": {
                    "x": int(row["TriggerX"]),
                    "y": int(row["TriggerY"]),
                    "z": int(row["TriggerZ"]),
                    "range": int(row["TriggerRange"]),
                },
                "actor": {
                    "x": int(row["ActorX"]),
                    "y": int(row["ActorY"]),
                    "z": int(row["ActorZ"]),
                },
                "talk_scena_index": int(row["TalkScenaIndex"]),
                "talk_function_index": int(row["TalkFunctionIndex"]),
                "source_line": int(row["Line"]),
                "source_map_zh_joyoland": row["Map"],
                "source_item_zh_joyoland": source_item,
            }
        )

    if len(result) != 280:
        raise ValueError(f"expected 280 chests, got {len(result)}")
    if len({row["id"] for row in result}) != len(result):
        raise ValueError("duplicate chest IDs")
    return {
        "schema_version": 1,
        "game": "ao_no_kiseki",
        "target_save_edition": "nisa_pc",
        "source": {
            "repository": "https://github.com/Ouroboros/Falcom",
            "path": "ED7/EDAO/RecordViewer/bin/box.json",
            "name_locale": "zh_joyoland",
            "locations": "installed NISA PC scena MapIndex plus localized t_town._dt",
            "items": "ao_item_index.json matched by source Chinese name",
        },
        "summary": {
            "chest_count": len(result),
            "map_count": len({row["map_index"] for row in result}),
            "scene_file_count": len({row["scene_file"] for row in result}),
        },
        "chests": result,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recordviewer_json", type=Path)
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--item-index", type=Path, default=WORKSPACE_ROOT / "ao_item_index.json")
    parser.add_argument("--output", type=Path, default=WORKSPACE_ROOT / "ao_chest_reference.json")
    args = parser.parse_args()
    data = build_reference(args.recordviewer_json, args.game_root, args.item_index)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
