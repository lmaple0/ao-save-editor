#!/usr/bin/env python3
"""Build the localized monster reference without executing upstream Python."""

import argparse
import ast
import json
import re

from .build_monster_locations import attach_monster_locations


ENTRY_RE = re.compile(
    r'^(?P<comment>#)?AddChar\(\s*(?P<dbmon_id>0x[0-9A-Fa-f]+),\s*'
    r'"(?P<label>[^"]*)",\s*"[^"]*",\s*"[^"]*",\s*'
    r'"ms(?P<ms_id>[0-9]{5})\.dat"'
)
LABEL_RE = re.compile(r"^(?P<number>[0-9]{3})(?P<name>.*?)(?:\s+(?P<level>[0-9]+))?$")
MS_LOCALES = {
    "zh_cle": ("data_cn/battle/dat", "gbk"),
    "ja": ("data/battle/dat", "cp932"),
    "en": ("data/battle_us/dat", "cp932"),
}


def extract_monster_codes(editor_path):
    source = editor_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(editor_path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "MONSTER_CODES" for target in node.targets):
            value = ast.literal_eval(node.value)
            if not isinstance(value, tuple) or not all(isinstance(code, int) for code in value):
                raise ValueError("MONSTER_CODES must be a tuple of integers")
            return value
    raise ValueError("MONSTER_CODES was not found")


def extract_dbmon_entries(path):
    entries = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        match = ENTRY_RE.match(line)
        if not match:
            continue
        label_match = LABEL_RE.match(match.group("label"))
        if not label_match or not label_match.group("level"):
            raise ValueError(f"cannot parse t_dbmon label at line {line_number}: {match.group('label')!r}")
        ms_id = match.group("ms_id").upper()
        row = {
            "dbmon_id": int(match.group("dbmon_id"), 16),
            "ms_file": f"ms{ms_id}.dat",
            "zh_joyoland": label_match.group("name").strip(),
            "level": int(label_match.group("level")),
            "source_status": "commented" if match.group("comment") else "active",
            "source_line": line_number,
        }
        previous = entries.get(ms_id)
        if previous is None or (previous["source_status"] == "commented" and row["source_status"] == "active"):
            entries[ms_id] = row
    return entries


def _skip_cstring(data, offset):
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"unterminated ms string at 0x{offset:X}")
    return end + 1


def extract_ms_name(path, encoding):
    """Read BattleMonsterStatus.Name using the documented ED7 binary layout."""
    data = path.read_bytes()
    offset = 0x8B + 0x18  # fixed status fields + Attack BattleCraftAIInfo
    for _ in range(4):  # arts, crafts, S-crafts, support crafts
        count = data[offset]
        offset += 1 + count * 0x18
    craft_info_count = data[offset]
    offset += 1
    for _ in range(craft_info_count):
        offset += 0x18
        offset = _skip_cstring(data, offset)
        offset = _skip_cstring(data, offset)
    offset += 4  # runaway fields
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"unterminated monster name: {path}")
    return data[offset:end].decode(encoding).strip()


def _localized_ms_names(game_root, ms_file):
    names = {}
    for locale, (relative_dir, encoding) in MS_LOCALES.items():
        path = game_root / relative_dir / ms_file
        if not path.is_file():
            raise FileNotFoundError(f"localized monster status file is required: {path}")
        value = extract_ms_name(path, encoding)
        if not value:
            raise ValueError(f"empty {locale} monster name: {path}")
        names[locale] = value
    return names


def build_reference(editor_path, dbmon_path, game_root):
    codes = extract_monster_codes(editor_path)
    entries = extract_dbmon_entries(dbmon_path)
    monsters = []
    missing = []
    for code in codes:
        ms_id = f"{code & 0xFFFFF:05X}"
        row = entries.get(ms_id)
        if row is None:
            missing.append(f"0x{code:08X}")
            continue
        names = _localized_ms_names(game_root, row["ms_file"])
        monsters.append(
            {
                "save_code": code,
                "save_code_hex": f"0x{code:08X}",
                "dbmon_id": row["dbmon_id"],
                "dbmon_id_hex": f"0x{row['dbmon_id']:04X}",
                "ms_file": row["ms_file"],
                "zh_joyoland": row["zh_joyoland"],
                **names,
                "level": row["level"],
                "source_status": row["source_status"],
                "source_line": row["source_line"],
                "verified_for_nisa_save": False,
            }
        )
    if missing:
        raise ValueError(f"t_dbmon does not cover MONSTER_CODES: {', '.join(missing)}")
    if len(monsters) != len(set(codes)):
        raise ValueError("MONSTER_CODES contains duplicates")
    return {
        "schema_version": 3,
        "game": "ao_no_kiseki",
        "target_save_edition": "nisa_pc",
        "generated_by": "tools/build_monster_reference.py",
        "source": {
            "identity": {
                "repository": "https://github.com/Ouroboros/Falcom",
                "path": "ED7/Decompiler/p/t_dbmon.py",
                "name_locale": "zh_joyoland",
                "note": "Commented upstream mappings are retained and explicitly marked.",
            },
            "names": {
                "type": "installed_nisa_pc_game_data",
                "paths": {
                    locale: f"{relative_dir}/ms*.dat"
                    for locale, (relative_dir, _encoding) in MS_LOCALES.items()
                },
                "method": "BattleMonsterStatus.Name field",
            },
        },
        "summary": {
            "monster_count": len(monsters),
            "active_count": sum(row["source_status"] == "active" for row in monsters),
            "commented_count": sum(row["source_status"] == "commented" for row in monsters),
            "localized_name_count": {locale: len(monsters) for locale in MS_LOCALES},
        },
        "monsters": monsters,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--editor", required=True, type=__import__("pathlib").Path)
    parser.add_argument("--t-dbmon", required=True, type=__import__("pathlib").Path)
    parser.add_argument("--output", required=True, type=__import__("pathlib").Path)
    parser.add_argument("--game-root", required=True, type=__import__("pathlib").Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = attach_monster_locations(
        build_reference(args.editor, args.t_dbmon, args.game_root), args.game_root
    )
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"out of date: {args.output}")
        return
    args.output.write_text(rendered, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
