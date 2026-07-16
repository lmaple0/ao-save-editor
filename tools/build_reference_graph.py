#!/usr/bin/env python3
"""Build the read-only character/monster/battle-script cross-reference graph."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


T_NAME_SOURCES = {
    "zh_cle": ("data_cn/text/t_name._dt", "gbk"),
    "ja": ("data/text/t_name._dt", "cp932"),
    # NISA keeps the Falcom Shift-JIS code page for punctuation in this table.
    "en": ("data/text_us/t_name._dt", "cp932"),
}
AS_DIRS = {
    "zh_cle": ("data_cn/battle/dat", "data/battle/dat"),
    "ja": ("data/battle/dat",),
    "en": ("data/battle_us/dat",),
}
LAST_CHARACTER_ID = 0x03E7
T_NAME_ENTRY_SIZE = 0x14
INVALID_ACTION_OFFSET = 0xFFFF
BUILTIN_ACTION_NAMES = {
    0: "SysCraft_Init", 1: "SysCraft_Stand", 2: "SysCraft_Move",
    3: "SysCraft_UnderAttack", 4: "SysCraft_Dead", 5: "SysCraft_NormalAttack",
    6: "SysCraft_ArtsAria", 7: "SysCraft_ArtsCast", 8: "SysCraft_Win",
    9: "SysCraft_EnterBattle", 10: "SysCraft_UseItem", 11: "SysCraft_Stun",
    12: "SysCraft_Unknown2", 13: "SysCraft_Reserve1", 14: "SysCraft_Reserve2",
    15: "SysCraft_Counter", 30: "SysCraft_TeamRushInit", 31: "SysCraft_TeamRushAction",
}


class ParseError(ValueError):
    pass


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _cstring(raw, offset, encoding, source):
    if not 0 <= offset < len(raw):
        raise ParseError(f"string offset out of bounds: {source} offset=0x{offset:X}")
    end = raw.find(b"\0", offset)
    if end < 0:
        raise ParseError(f"unterminated string: {source} offset=0x{offset:X}")
    try:
        return raw[offset:end].decode(encoding)
    except UnicodeDecodeError as exc:
        raise ParseError(f"cannot decode string: {source} offset=0x{offset:X}") from exc


def _model_name(value):
    if value in {0, 0xFFFFFFFF}:
        return None
    model_type = value >> 20
    directory = {7: "chr", 8: "apl", 9: "monster"}.get(model_type)
    if directory is None:
        return f"unknown:{value:08X}"
    return f"{directory}/ch{value & 0xFFFFF:05X}.itc"


def _battle_file_name(value):
    if value == 0:
        return None
    file_type = (value >> 20) & 0xF
    prefixes = ("ms", "as", "bs")
    if file_type >= len(prefixes):
        return f"unknown:{value:08X}"
    return f"{prefixes[file_type]}{value & 0xFFFFF:05x}.dat"


def parse_t_name(path, encoding):
    path = Path(path)
    raw = path.read_bytes()
    records = []
    offset = 0
    seen = set()
    while True:
        if offset + T_NAME_ENTRY_SIZE > len(raw):
            raise ParseError(f"missing t_name terminator: {path}")
        ident, name_offset, walk, run, battle, unknown = struct.unpack_from(
            "<HHIIII", raw, offset
        )
        offset += T_NAME_ENTRY_SIZE
        if ident == LAST_CHARACTER_ID:
            break
        if ident in seen:
            raise ParseError(f"duplicate t_name id: {path} 0x{ident:04X}")
        seen.add(ident)
        records.append(
            {
                "id": ident,
                "name": _cstring(raw, name_offset, encoding, path),
                "walk_model": _model_name(walk),
                "run_model": _model_name(run),
                "battle_file": _battle_file_name(battle),
                "unknown": unknown,
            }
        )
    return records, {"size": len(raw), "sha256": _sha256(raw)}


def parse_action_script(path):
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) < 2:
        raise ParseError(f"action script header is truncated: {path}")
    special = path.name.casefold() in {"as90000.dat", "as90001.dat"}
    action_list_offset = struct.unpack_from("<H", raw, 0)[0]
    if not 0 < action_list_offset < len(raw):
        raise ParseError(f"invalid action list offset: {path} 0x{action_list_offset:X}")

    preload_models = []
    character_positions = []
    character_position_offset = None
    if not special:
        if len(raw) < 10:
            raise ParseError(f"action script header is truncated: {path}")
        character_position_offset = struct.unpack_from("<H", raw, 2)[0]
        cursor = 6
        for _ in range(512):
            if cursor + 4 > len(raw):
                raise ParseError(f"unterminated preload list: {path}")
            value = struct.unpack_from("<I", raw, cursor)[0]
            cursor += 4
            if value == 0xFFFFFFFF:
                break
            preload_models.append(_model_name(value))
        else:
            raise ParseError(f"preload list exceeds safety limit: {path}")
        if not 0 <= character_position_offset <= len(raw) - 16:
            raise ParseError(f"invalid character position offset: {path}")
        character_positions = [
            list(struct.unpack_from("<BB", raw, character_position_offset + index * 2))
            for index in range(8)
        ]

    actions = []
    cursor = action_list_offset
    minimum_code_offset = len(raw)
    for index in range(4096):
        if cursor >= minimum_code_offset:
            break
        if cursor + 2 > len(raw):
            raise ParseError(f"action list is truncated: {path}")
        action_offset = struct.unpack_from("<H", raw, cursor)[0]
        cursor += 2
        if action_offset == 0:
            break
        if action_offset != INVALID_ACTION_OFFSET:
            if not action_offset <= len(raw):
                raise ParseError(
                    f"action offset out of bounds: {path} index={index} offset=0x{action_offset:X}"
                )
            minimum_code_offset = min(minimum_code_offset, action_offset)
        actions.append(
            {
                "index": index,
                "offset": None if action_offset == INVALID_ACTION_OFFSET else action_offset,
                "builtin_name": BUILTIN_ACTION_NAMES.get(index),
            }
        )
    else:
        raise ParseError(f"action list exceeds safety limit: {path}")
    if not actions:
        raise ParseError(f"action script contains no actions: {path}")
    return {
        "action_list_offset": action_list_offset,
        "character_position_offset": character_position_offset,
        "character_positions": character_positions,
        "preload_models": preload_models,
        "actions": actions,
        "source": {"size": len(raw), "sha256": _sha256(raw)},
    }


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _effective_as_files(game_root):
    game_root = Path(game_root)
    result = {locale: {} for locale in AS_DIRS}
    for locale, directories in AS_DIRS.items():
        # First directory has higher priority; later directories only fill gaps.
        for relative in directories:
            for path in sorted((game_root / relative).glob("as*.dat")):
                result[locale].setdefault(path.name.casefold(), (path, relative))
    return result


def _source(pattern, confidence="verified", note=None):
    result = {"file": pattern, "confidence": confidence}
    if note:
        result["note"] = note
    return result


def _add_node(nodes, row):
    if row["id"] in nodes:
        raise ValueError(f"duplicate generated node: {row['id']}")
    row.setdefault("issue", False)
    nodes[row["id"]] = row


def _add_edge(edges, source, target, relation, confidence, provenance, note=None, **extra):
    row = {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
        "provenance": provenance,
    }
    if note:
        row["note"] = note
    row.update(extra)
    edges.append(row)


def build_graph(game_root, monster_reference_path, monster_details_path):
    game_root = Path(game_root)
    references = _load_json(monster_reference_path)
    details = _load_json(monster_details_path)
    if references.get("schema_version") != 3 or details.get("schema_version") != 1:
        raise ValueError("unsupported monster source schema")

    parsed_names = {}
    name_sources = {}
    for locale, (relative, encoding) in T_NAME_SOURCES.items():
        parsed_names[locale], name_sources[locale] = parse_t_name(game_root / relative, encoding)
    ids_by_locale = {
        locale: tuple(row["id"] for row in rows) for locale, rows in parsed_names.items()
    }
    if len(set(ids_by_locale.values())) != 1:
        raise ParseError(f"localized t_name ids differ: {ids_by_locale}")
    names_by_locale = {
        locale: {row["id"]: row for row in rows} for locale, rows in parsed_names.items()
    }
    for ident in ids_by_locale["zh_cle"]:
        projections = {
            locale: {
                key: value for key, value in names_by_locale[locale][ident].items() if key != "name"
            }
            for locale in T_NAME_SOURCES
        }
        if len({json.dumps(value, sort_keys=True) for value in projections.values()}) != 1:
            raise ParseError(f"localized t_name resources differ: 0x{ident:04X}")

    action_files = _effective_as_files(game_root)
    all_action_names = sorted({name for rows in action_files.values() for name in rows})
    parsed_actions = {}
    action_sources = {}
    missing_action_locales = []
    for name in all_action_names:
        available = {}
        for locale in AS_DIRS:
            entry = action_files[locale].get(name)
            if entry is None:
                missing_action_locales.append(f"{locale}:{name}")
                continue
            path, relative = entry
            available[locale] = parse_action_script(path)
            available[locale]["relative_source"] = f"{relative}/{name}"
        canonical = available.get("ja") or available.get("en") or available.get("zh_cle")
        parsed_actions[name] = canonical
        action_sources[name] = {
            locale: {
                **data["source"],
                "file": data["relative_source"],
                "fallback": locale == "zh_cle" and data["relative_source"].startswith("data/battle/"),
            }
            for locale, data in available.items()
        }

    nodes = {}
    edges = []
    issue_nodes = set()
    missing_status_references = []
    missing_script_references = []
    unresolved_action_references = []

    craft_labels_by_action = defaultdict(lambda: {"zh_cle": [], "ja": [], "en": []})
    for row in details["monsters"]:
        as_file = row["as_file"].casefold()
        for craft in row["craft_info"]:
            key = (as_file, int(craft["action_index"]))
            for locale in craft_labels_by_action[key]:
                name = str(craft["names"].get(locale, "")).strip()
                if name and name not in craft_labels_by_action[key][locale]:
                    craft_labels_by_action[key][locale].append(name)

    for name in all_action_names:
        parsed = parsed_actions[name]
        script_id = f"script:{name}"
        script_issue = len(action_sources[name]) != len(AS_DIRS)
        _add_node(
            nodes,
            {
                "id": script_id,
                "kind": "action_script",
                "labels": {locale: name for locale in T_NAME_SOURCES},
                "identifiers": {"as_file": name},
                "confidence": "verified",
                "action_count": len(parsed["actions"]),
                "valid_action_count": sum(action["offset"] is not None for action in parsed["actions"]),
                "preload_models": parsed["preload_models"],
                "character_positions": parsed["character_positions"],
                "sources": action_sources[name],
                "issue": script_issue,
            },
        )
        if script_issue:
            issue_nodes.add(script_id)
        for action in parsed["actions"]:
            if action["offset"] is None:
                continue
            index = action["index"]
            labels = craft_labels_by_action[(name, index)]
            fallback = action["builtin_name"] or f"Action {index}"
            localized = {
                locale: " / ".join(labels[locale]) if labels[locale] else fallback
                for locale in T_NAME_SOURCES
            }
            action_id = f"action:{name}:{index:04x}"
            _add_node(
                nodes,
                {
                    "id": action_id,
                    "kind": "action_entry",
                    "labels": localized,
                    "identifiers": {
                        "as_file": name,
                        "action_index": index,
                        "action_index_hex": f"0x{index:04X}",
                    },
                    "confidence": "verified",
                    "offset_ja": action["offset"],
                    "builtin_name": action["builtin_name"],
                    "empty": action["offset"] is None,
                    "issue": False,
                },
            )
            _add_edge(
                edges, action_id, script_id, "entry_of", "verified",
                f"{action_sources[name].get('ja', next(iter(action_sources[name].values())))['file']}:action_table",
            )

    status_rows = {}
    for row in details["monsters"]:
        ms_file = row["ms_file"].casefold()
        status_id = f"status:{ms_file}"
        as_file = row["as_file"].casefold()
        status_rows[ms_file] = row
        script_id = f"script:{as_file}"
        missing_script = script_id not in nodes
        _add_node(
            nodes,
            {
                "id": status_id,
                "kind": "status_file",
                "labels": dict(row["names"]),
                "identifiers": {"ms_file": ms_file, "as_file": as_file},
                "confidence": "verified",
                "level": row["level"],
                "craft_count": len(row["craft_info"]),
                "sources": row["source"],
                "issue": missing_script,
            },
        )
        if missing_script:
            issue_nodes.add(status_id)
            missing_script_references.append(f"{ms_file}->{as_file}")
        else:
            _add_edge(
                edges, status_id, script_id, "uses_action_script", "verified",
                f"data/battle/dat/{ms_file}:as_index",
            )

        for craft in row["craft_info"]:
            craft_index = int(craft["index"])
            action_index = int(craft["action_index"])
            craft_id = f"craft:{ms_file}:{craft_index:04x}"
            action_id = f"action:{as_file}:{action_index:04x}"
            action_resolved = action_id in nodes
            _add_node(
                nodes,
                {
                    "id": craft_id,
                    "kind": "craft",
                    "labels": dict(craft["names"]),
                    "identifiers": {
                        "ms_file": ms_file,
                        "craft_index": craft_index,
                        "craft_index_hex": f"0x{craft_index:04X}",
                        "action_index": action_index,
                        "action_index_hex": f"0x{action_index:04X}",
                    },
                    "confidence": "verified",
                    "descriptions": dict(craft["descriptions"]),
                    "action_resolution": "local_verified" if action_resolved else "unresolved",
                    "issue": False,
                },
            )
            _add_edge(
                edges, status_id, craft_id, "defines_craft", "verified",
                f"data/battle/dat/{ms_file}:craft_info",
            )
            if not action_resolved:
                unresolved_action_references.append(
                    f"{ms_file}:0x{craft_index:04X}->0x{action_index:04X}"
                )
            if action_resolved:
                _add_edge(
                    edges, craft_id, action_id, "enters_action", "verified",
                    f"data/battle/dat/{ms_file}:craft_info.action_index",
                )

    for row in references["monsters"]:
        save_code = int(str(row["save_code"]), 0)
        monster_id = f"monster:{save_code:08x}"
        ms_file = row["ms_file"].casefold()
        status_id = f"status:{ms_file}"
        missing_status = status_id not in nodes
        _add_node(
            nodes,
            {
                "id": monster_id,
                "kind": "monster",
                "labels": {"zh_cle": row["zh_cle"], "ja": row["ja"], "en": row["en"]},
                "aliases": [row["zh_joyoland"]],
                "identifiers": {
                    "save_code": save_code,
                    "save_code_hex": f"0x{save_code:08X}",
                    "dbmon_id": int(str(row["dbmon_id"]), 0),
                    "dbmon_id_hex": f"0x{int(str(row['dbmon_id']), 0):04X}",
                    "ms_file": ms_file,
                },
                "confidence": "verified" if row["verified_for_nisa_save"] else "candidate",
                "locations": {
                    locale: list(row[f"locations_{locale}"]) for locale in T_NAME_SOURCES
                },
                "level": row["level"],
                "source_status": row["source_status"],
                "issue": missing_status or row["source_status"] != "active",
            },
        )
        if nodes[monster_id]["issue"]:
            issue_nodes.add(monster_id)
        if missing_status:
            missing_status_references.append(f"{monster_id}->{ms_file}")
        else:
            _add_edge(
                edges, monster_id, status_id, "uses_status_file", "verified",
                "ao_monster_reference.json:save_code_to_ms",
            )

    character_ids = ids_by_locale["zh_cle"]
    identity_groups = defaultdict(list)
    for ident in character_ids:
        base = names_by_locale["zh_cle"][ident]
        labels = {locale: names_by_locale[locale][ident]["name"] for locale in T_NAME_SOURCES}
        character_id = f"character:{ident:04x}"
        battle_file = base["battle_file"]
        status_id = f"status:{battle_file.casefold()}" if battle_file and battle_file.startswith("ms") else None
        missing_status = bool(status_id and status_id not in nodes)
        _add_node(
            nodes,
            {
                "id": character_id,
                "kind": "character",
                "labels": labels,
                "identifiers": {
                    "character_id": ident,
                    "character_id_hex": f"0x{ident:04X}",
                    "ms_file": battle_file,
                },
                "confidence": "verified",
                "walk_model": base["walk_model"],
                "run_model": base["run_model"],
                "unknown": base["unknown"],
                "sources": {
                    locale: {**name_sources[locale], "file": T_NAME_SOURCES[locale][0]}
                    for locale in T_NAME_SOURCES
                },
                "issue": missing_status,
            },
        )
        if missing_status:
            issue_nodes.add(character_id)
            missing_status_references.append(f"{character_id}->{battle_file}")
        elif status_id:
            _add_edge(
                edges, character_id, status_id, "uses_status_file", "verified",
                "t_name._dt:battle_file",
            )
        identity_groups[tuple(labels[locale].strip().casefold() for locale in T_NAME_SOURCES)].append(
            character_id
        )

    candidate_variant_groups = []
    for group in identity_groups.values():
        if len(group) < 2:
            continue
        candidate_variant_groups.append(group)
        canonical = group[0]
        for variant in group[1:]:
            _add_edge(
                edges, variant, canonical, "possible_variant_of", "candidate",
                "localized t_name labels", note="same labels in all three locales; identity is not proven",
            )

    kind_counts = defaultdict(int)
    for row in nodes.values():
        kind_counts[row["kind"]] += 1
    diagnostics = {
        "issue_node_count": len(issue_nodes),
        "missing_status_references": sorted(missing_status_references),
        "missing_script_references": sorted(missing_script_references),
        "unresolved_action_references": sorted(unresolved_action_references),
        "missing_action_locales": sorted(missing_action_locales),
        "candidate_variant_groups": candidate_variant_groups,
    }
    return {
        "schema_version": 1,
        "game": "ao_no_kiseki",
        "target_save_edition": "nisa_pc",
        "source": {
            "format_reference": "Ouroboros/Falcom ED7/Decompiler NameList2py.py and BattleActionScript.py",
            "method": "independent bounds-checked read-only parsers; no generated Python execution",
            "monster_reference": "ao_monster_reference.json",
            "monster_details": "ao_monster_details.json",
        },
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "kind_counts": dict(sorted(kind_counts.items())),
            "character_count": len(character_ids),
            "status_file_count": len(status_rows),
            "action_script_count": len(all_action_names),
            "candidate_variant_group_count": len(candidate_variant_groups),
        },
        "diagnostics": diagnostics,
        "nodes": list(nodes.values()),
        "edges": edges,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument(
        "--monster-reference", type=Path,
        default=WORKSPACE_ROOT / "ao_monster_reference.json",
    )
    parser.add_argument(
        "--monster-details", type=Path,
        default=WORKSPACE_ROOT / "ao_monster_details.json",
    )
    parser.add_argument(
        "--output", type=Path,
        default=WORKSPACE_ROOT / "ao_reference_graph.json",
    )
    args = parser.parse_args()
    graph = build_graph(args.game_root, args.monster_reference, args.monster_details)
    args.output.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(graph["summary"], ensure_ascii=False))
    print(json.dumps(graph["diagnostics"], ensure_ascii=False))


if __name__ == "__main__":
    main()
