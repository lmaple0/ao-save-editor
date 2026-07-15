#!/usr/bin/env python3
"""Build a localized, read-only monster detail catalog from installed NISA data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct


LOCALE_SOURCES = {
    "zh_cle": ("data_cn/battle/dat", "gbk"),
    "ja": ("data/battle/dat", "cp932"),
    "en": ("data/battle_us/dat", "cp932"),
}
AI_LIMITS = {"arts": 80, "crafts": 16, "s_crafts": 5, "support_crafts": 3}
ATTRIBUTE_KEYS = ("earth", "water", "fire", "wind", "time", "space", "mirage")


class ParseError(ValueError):
    pass


class Reader:
    def __init__(self, data, source):
        self.data = data
        self.source = str(source)
        self.position = 0

    def read(self, size):
        end = self.position + size
        if size < 0 or end > len(self.data):
            raise ParseError(
                f"read out of bounds: {self.source} offset=0x{self.position:X} size={size}"
            )
        value = self.data[self.position:end]
        self.position = end
        return value

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.read(size))

    def u8(self):
        return self.unpack("<B")[0]

    def u16(self):
        return self.unpack("<H")[0]

    def i16(self):
        return self.unpack("<h")[0]

    def u32(self):
        return self.unpack("<I")[0]

    def cstring(self, encoding):
        end = self.data.find(b"\0", self.position)
        if end < 0:
            raise ParseError(f"unterminated string: {self.source} offset=0x{self.position:X}")
        raw = self.data[self.position:end]
        self.position = end + 1
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError as exc:
            raise ParseError(
                f"cannot decode string: {self.source} offset=0x{self.position:X} encoding={encoding}"
            ) from exc


def _read_ai(reader):
    return {
        "condition": reader.u8(),
        "probability": reader.u8(),
        "target": reader.u8(),
        "target_condition": reader.u8(),
        "aria_action_index": reader.u8(),
        "action_index": reader.u8(),
        "craft_index": reader.u16(),
        "parameters": [reader.u32() for _ in range(4)],
    }


def _read_ai_list(reader, name):
    count = reader.u8()
    limit = AI_LIMITS[name]
    if count > limit:
        raise ParseError(f"{name} count exceeds {limit}: {reader.source} -> {count}")
    return [_read_ai(reader) for _ in range(count)]


def _read_craft_info(reader, encoding, index):
    info = {
        "index": 0x3E8 + index,
        "action_index": reader.u16(),
        "target": reader.u8(),
        "unknown_03": reader.u8(),
        "attribute": reader.u8(),
        "range_type": reader.u8(),
        "state_1": reader.u8(),
        "state_2": reader.u8(),
        "rng": reader.u8(),
        "range_size": reader.u8(),
        "aria_time": reader.u8(),
        "skill_time": reader.u8(),
        "ep_cp": reader.u16(),
        "range_size_2": reader.u16(),
        "state_1_parameter": reader.i16(),
        "state_1_time": reader.i16(),
        "state_2_parameter": reader.i16(),
        "state_2_time": reader.i16(),
    }
    info["name"] = reader.cstring(encoding)
    info["description"] = reader.cstring(encoding)
    return info


def parse_ms_file(path, encoding):
    path = Path(path)
    raw = path.read_bytes()
    reader = Reader(raw, path)
    as_index = reader.u32()
    result = {
        "as_index": as_index,
        "as_file": f"as{as_index & 0xFFFFF:05x}.dat",
        "level": reader.u16(),
        "maximum_hp": reader.u32(),
        "initial_hp": reader.u32(),
        "maximum_ep": reader.u16(),
        "initial_ep": reader.u16(),
        "maximum_cp": reader.u16(),
        "initial_cp": reader.u16(),
    }
    stat_keys = ("spd", "move_spd", "mov", "str", "def", "ats", "adf", "dex", "agl", "rng")
    result["stats"] = {key: reader.u16() for key in stat_keys}
    result["unknown_2a"] = reader.u16()
    result["exp_reward"] = reader.u16()
    result["unknown_2e"] = reader.u16()
    result["unknown_30"] = reader.u8()
    result["ai_type"] = reader.u16()
    result["unknown_33"] = reader.u16()
    result["unknown_35"] = reader.u8()
    result["unknown_36"] = reader.u16()
    result["enemy_flags"] = reader.u16()
    result["battle_flags"] = reader.u16()
    result["unknown_3c"] = reader.u16()
    result["unknown_3e"] = reader.u16()
    result["sex"] = reader.u8()
    result["unknown_41"] = reader.u8()
    result["character_size"] = reader.u32()
    result["default_effect"] = {key: reader.u32() for key in ("x", "z", "y")}
    result["unknown_52_55"] = list(reader.read(4))
    result["symbol_index"] = reader.u32()
    result["resistance"] = reader.u32()
    result["attribute_rates"] = dict(zip(ATTRIBUTE_KEYS, reader.unpack("<7H")))
    result["sepith"] = dict(zip(ATTRIBUTE_KEYS, reader.read(7)))
    drop_codes = reader.unpack("<2H")
    drop_rates = reader.read(2)
    result["drops"] = [
        {"item_code": code, "rate": rate}
        for code, rate in zip(drop_codes, drop_rates)
    ]
    result["equipment"] = list(reader.unpack("<5H"))
    result["orbment"] = list(reader.unpack("<4H"))
    result["attack"] = _read_ai(reader)
    for name in AI_LIMITS:
        result[name] = _read_ai_list(reader, name)
    craft_count = reader.u8()
    if craft_count > 16:
        raise ParseError(f"craft info count exceeds 16: {path} -> {craft_count}")
    result["craft_info"] = [_read_craft_info(reader, encoding, i) for i in range(craft_count)]
    result["runaway"] = {
        "type": reader.u8(), "rate": reader.u8(),
        "parameter": reader.u8(), "reserved": reader.u8(),
    }
    result["name"] = reader.cstring(encoding)
    result["description"] = reader.cstring(encoding)
    trailing = reader.read(len(raw) - reader.position)
    result["unparsed_trailing_size"] = len(trailing)
    result["unparsed_trailing_sha256"] = hashlib.sha256(trailing).hexdigest() if trailing else None
    result["source_size"] = len(raw)
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def _numeric_projection(row):
    ignored = {
        "name", "description", "source_size", "source_sha256",
        "unparsed_trailing_size", "unparsed_trailing_sha256",
    }
    result = {key: value for key, value in row.items() if key not in ignored and key != "craft_info"}
    result["craft_info"] = [
        {key: value for key, value in craft.items() if key not in {"name", "description"}}
        for craft in row["craft_info"]
    ]
    return result


def _localized_crafts(parsed):
    counts = {locale: len(row["craft_info"]) for locale, row in parsed.items()}
    if len(set(counts.values())) != 1:
        raise ParseError(f"localized craft counts differ: {counts}")
    result = []
    for index in range(next(iter(counts.values()))):
        base = {
            key: value
            for key, value in parsed["zh_cle"]["craft_info"][index].items()
            if key not in {"name", "description"}
        }
        base["names"] = {locale: row["craft_info"][index]["name"] for locale, row in parsed.items()}
        base["descriptions"] = {
            locale: row["craft_info"][index]["description"] for locale, row in parsed.items()
        }
        result.append(base)
    return result


def build_catalog(game_root):
    game_root = Path(game_root)
    locale_files = {
        locale: {path.name.casefold(): path for path in (game_root / relative).glob("ms*.dat")}
        for locale, (relative, _encoding) in LOCALE_SOURCES.items()
    }
    file_sets = {locale: set(files) for locale, files in locale_files.items()}
    if len({frozenset(files) for files in file_sets.values()}) != 1:
        raise ValueError(
            "localized ms file sets differ: "
            + ", ".join(f"{locale}={len(files)}" for locale, files in file_sets.items())
        )
    filenames = sorted(next(iter(file_sets.values())))
    monsters = []
    for filename in filenames:
        parsed = {
            locale: parse_ms_file(locale_files[locale][filename], encoding)
            for locale, (_relative, encoding) in LOCALE_SOURCES.items()
        }
        projections = {locale: _numeric_projection(row) for locale, row in parsed.items()}
        if len({json.dumps(value, sort_keys=True) for value in projections.values()}) != 1:
            raise ParseError(f"localized numeric monster data differs: {filename}")
        base = projections["zh_cle"]
        base.update(
            {
                "ms_file": filename,
                "names": {locale: row["name"] for locale, row in parsed.items()},
                "descriptions": {locale: row["description"] for locale, row in parsed.items()},
                "craft_info": _localized_crafts(parsed),
                "source": {
                    locale: {
                        "size": row["source_size"], "sha256": row["source_sha256"],
                        "unparsed_trailing_size": row["unparsed_trailing_size"],
                        "unparsed_trailing_sha256": row["unparsed_trailing_sha256"],
                    }
                    for locale, row in parsed.items()
                },
            }
        )
        as_file = base["as_file"]
        base["as_available"] = {
            "zh_cle": (game_root / LOCALE_SOURCES["zh_cle"][0] / as_file).is_file()
            or (game_root / LOCALE_SOURCES["ja"][0] / as_file).is_file(),
            "ja": (game_root / LOCALE_SOURCES["ja"][0] / as_file).is_file(),
            "en": (game_root / LOCALE_SOURCES["en"][0] / as_file).is_file(),
        }
        monsters.append(base)
    return {
        "schema_version": 1,
        "game": "ao_no_kiseki",
        "target_save_edition": "nisa_pc",
        "source": {
            "format_reference": "Ouroboros/Falcom ED7/Decompiler/BattleMonsterStatus.py",
            "installed_game_paths": {
                locale: f"{relative}/ms*.dat" for locale, (relative, _encoding) in LOCALE_SOURCES.items()
            },
            "method": "independent bounds-checked read-only parser; no generated Python execution",
        },
        "summary": {
            "monster_file_count": len(monsters),
            "localized_name_count": {
                locale: sum(bool(row["names"][locale]) for row in monsters) for locale in LOCALE_SOURCES
            },
            "localized_description_count": {
                locale: sum(bool(row["descriptions"][locale]) for row in monsters) for locale in LOCALE_SOURCES
            },
            "with_custom_crafts": sum(bool(row["craft_info"]) for row in monsters),
            "with_effective_action_script": sum(row["as_available"]["zh_cle"] for row in monsters),
            "with_unparsed_trailing_data": sum(
                any(source["unparsed_trailing_size"] for source in row["source"].values())
                for row in monsters
            ),
        },
        "monsters": monsters,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("ao_monster_details.json"))
    args = parser.parse_args()
    catalog = build_catalog(args.game_root)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(catalog["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
