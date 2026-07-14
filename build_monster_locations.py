#!/usr/bin/env python3
"""Attach localized NISA scenario locations to monster reference rows."""

from collections import defaultdict
from pathlib import Path
import struct


LOCATION_SUPPLEMENTS_ZH_CLE = {
    # These local event scenes contain the monster code but have MapIndex == 0.
    # Resolve their already-identified parent label through the local t_town tables.
    "ms82004.dat": "唐古拉姆门",
    "ms84000.dat": "迎宾馆",
    "ms84500.dat": "迎宾馆",
}

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
    names = []
    for offset in offsets:
        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError(f"unterminated t_town entry at 0x{offset:X}")
        names.append(_clean_text(data[offset:end].decode(encoding)))
    return names


def _localized_town_names(game_root):
    tables = {}
    for locale, (relative_path, encoding) in TOWN_LOCALES.items():
        path = game_root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"localized t_town._dt is required: {path}")
        tables[locale] = _read_town_names(path, encoding)
    lengths = {len(values) for values in tables.values()}
    if len(lengths) != 1:
        raise ValueError(f"localized t_town table sizes differ: {lengths}")
    return tables


def _effective_scenarios(game_root):
    scenarios = {
        path.name.casefold(): path
        for path in (game_root / "data" / "scena").glob("*.bin")
    }
    scenarios.update(
        {
            path.name.casefold(): path
            for path in (game_root / "data_cn" / "scena").glob("*.bin")
        }
    )
    if not scenarios:
        raise FileNotFoundError(f"no NISA scena files found below: {game_root}")
    return tuple(scenarios[key] for key in sorted(scenarios))


def scan_monster_locations(monsters, game_root):
    """Return local town indexes and scene-file evidence keyed by save code."""
    game_root = Path(game_root)
    needles = {
        struct.pack("<I", int(row["save_code"])): int(row["save_code"])
        for row in monsters
    }
    map_indexes = defaultdict(set)
    scene_files = defaultdict(set)
    for path in _effective_scenarios(game_root):
        data = path.read_bytes()
        if len(data) < 0x16:
            continue
        map_index = struct.unpack_from("<H", data, 0x14)[0]
        for needle, code in needles.items():
            if needle not in data:
                continue
            scene_files[code].add(path.name)
            if map_index:
                map_indexes[code].add(map_index)
    return map_indexes, scene_files


def _supplement_index(tables, ms_file):
    label = LOCATION_SUPPLEMENTS_ZH_CLE.get(ms_file)
    if not label:
        return None
    return next(
        (index for index, value in enumerate(tables["zh_cle"]) if value == label),
        None,
    )


def attach_monster_locations(reference, game_root):
    """Mutate a generated reference document with localized location data."""
    game_root = Path(game_root)
    monsters = reference["monsters"]
    tables = _localized_town_names(game_root)
    map_indexes, scene_files = scan_monster_locations(monsters, game_root)
    scenario_mapped = 0
    supplemented = 0

    for row in monsters:
        code = int(row["save_code"])
        indexes = set(map_indexes[code])
        source = "nisa_pc_scenario_scan"
        if indexes:
            scenario_mapped += 1
        else:
            supplement = _supplement_index(tables, row["ms_file"])
            if supplement is not None:
                indexes.add(supplement)
                source = "local_town_name_supplement"
                supplemented += 1
        if not indexes:
            raise ValueError(
                "local location sources do not cover monster: "
                f"{row['save_code_hex']} {row['zh_cle']} {row['ms_file']}"
            )
        for locale, names in tables.items():
            values = sorted({names[index] for index in indexes if index < len(names)})
            if not values or any(not value for value in values):
                raise ValueError(f"empty {locale} location for {row['ms_file']}")
            row[f"locations_{locale}"] = values
        row["location_map_indexes"] = sorted(indexes)
        row["location_scene_files"] = sorted(scene_files[code], key=str.casefold)
        row["location_source"] = source

    reference["source"]["locations"] = {
        "type": "installed_nisa_pc_game_data",
        "paths": [
            "data/scena/*.bin",
            "data_cn/scena/*.bin",
            *(path for path, _encoding in TOWN_LOCALES.values()),
        ],
        "method": "little-endian save-code scan plus scenario MapIndex lookup",
        "supplement": {
            "type": "local_town_name_lookup",
            "reason": "three local event scenarios have MapIndex 0",
            "ms_files": sorted(LOCATION_SUPPLEMENTS_ZH_CLE),
        },
    }
    reference["summary"].update(
        {
            "location_count": {
                locale: len(
                    {
                        location
                        for row in monsters
                        for location in row[f"locations_{locale}"]
                    }
                )
                for locale in TOWN_LOCALES
            },
            "scenario_location_count": scenario_mapped,
            "local_supplement_location_count": supplemented,
            "multi_location_monster_count": sum(
                len(row["locations_zh_cle"]) > 1 for row in monsters
            ),
        }
    )
    return reference
