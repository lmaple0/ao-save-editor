#!/usr/bin/env python3
"""
Build Chinese/English/Japanese localization candidates for the Ao save editor.

Input:
- ao_items_db.py: save item code -> current Joyoland/BZH Simplified Chinese name
- ao_save_editor.py: ITEM_WRITE_ORDER and achievement bitmap names
- wiki_azure_names_raw.json: raw EN/JA candidates scraped from Kiseki Wiki

Output:
- ao_i18n_candidates.json

This script deliberately emits candidates with confidence/source metadata. It is
not intended to overwrite the editor database without review.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "wiki_azure_names_raw.json"
OUT_PATH = ROOT / "ao_i18n_candidates.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


items_mod = load_module("ao_items_db", ROOT / "ao_items_db.py")
editor_mod = load_module("ao_save_editor", ROOT / "ao_save_editor.py")
ITEM_DB: dict[int, tuple[str, str]] = items_mod.ITEM_DB
ITEM_WRITE_ORDER: list[list[int]] = editor_mod.ITEM_WRITE_ORDER
ACHIEVEMENT_NAMES: list[tuple[int, int, str]] = editor_mod.ACHIEVEMENT_NAMES


def ordered_codes_by_category(*categories: str) -> list[int]:
    wanted = set(categories)
    result: list[int] = []
    for group in ITEM_WRITE_ORDER:
        for code in group:
            if ITEM_DB.get(code, ("", ""))[0] in wanted:
                result.append(code)
    return result


def ordered_codes_by_prefix(*prefixes: str) -> list[int]:
    result: list[int] = []
    for group in ITEM_WRITE_ORDER:
        for code in group:
            cat = ITEM_DB.get(code, ("", ""))[0]
            if cat.startswith(prefixes):
                result.append(code)
    return result


def wiki_entries(raw: dict[str, Any], page: str) -> list[dict[str, Any]]:
    return raw["pages"][page]["entries"]


def clean_entry(entry: dict[str, Any]) -> dict[str, str]:
    return {
        "en": str(entry.get("en") or "").strip(),
        "ja": str(entry.get("ja") or "").strip(),
        "section": str(entry.get("section") or "").strip(),
    }


def item_record(code: int, entry: dict[str, Any] | None, source: str, confidence: str, note: str = "") -> dict[str, Any]:
    category, zh = ITEM_DB.get(code, ("unknown", f"未知(0x{code:04x})"))
    rec: dict[str, Any] = {
        "code": f"0x{code:04x}",
        "code_int": code,
        "category": category,
        "zh_cn": zh,
        "match_source": source,
        "confidence": confidence,
    }
    if entry:
        e = clean_entry(entry)
        rec.update({"en": e["en"], "ja": e["ja"], "wiki_section": e["section"]})
    else:
        rec.update({"en": None, "ja": None, "wiki_section": None})
    if note:
        rec["note"] = note
    return rec


def order_match(codes: list[int], entries: list[dict[str, Any]], source: str, *, note: str = "") -> list[dict[str, Any]]:
    confidence = "review"
    records: list[dict[str, Any]] = []
    for idx, code in enumerate(codes):
        entry = entries[idx] if idx < len(entries) else None
        extra = note
        if len(codes) != len(entries):
            mismatch = f"count mismatch: codes={len(codes)}, wiki_entries={len(entries)}"
            extra = f"{extra}; {mismatch}" if extra else mismatch
        records.append(item_record(code, entry, source, confidence, extra))
    return records


def split_armor_entries(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {"armor": [], "boots": [], "accessories": []}
    for entry in entries:
        sec = str(entry.get("section") or "").lower()
        if "boots" in sec:
            groups["boots"].append(entry)
        elif "accessories" in sec:
            groups["accessories"].append(entry)
        else:
            groups["armor"].append(entry)
    return groups


def split_weapon_entries(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    owner_keys = {
        "lloyd": "equipment_weapon_Lloyd",
        "elie": "equipment_weapon_Elie",
        "tio": "equipment_weapon_Tio",
        "randy": "equipment_weapon_Randy",
        "wazy": "equipment_weapon_Lazy",
        "noel": "equipment_weapon_Noel",
        "rixia": "equipment_weapon_Rixia",
        "dudley": "equipment_weapon_Dudley",
        "arios": "equipment_weapon_Arios",
        "garcia": "equipment_weapon_Garcia",
        "zeit": "equipment_weapon_Zeit",
    }
    groups: dict[str, list[dict[str, Any]]] = {v: [] for v in owner_keys.values()}
    for entry in entries:
        sec = str(entry.get("section") or "").lower()
        for key, cat in owner_keys.items():
            if key in sec:
                groups[cat].append(entry)
                break
    return groups

def split_fishing_equipment_entries(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {"rods": [], "bait": []}
    for entry in entries:
        sec = str(entry.get("section") or "").lower()
        if "rod" in sec:
            groups["rods"].append(entry)
        elif "bait" in sec:
            groups["bait"].append(entry)
    return groups

def achievement_candidates(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # The Wiki page is page-order/trophy-order. The editor bitmap order is BZH's
    # bit order, so do not force a positional match. Emit both sides for review.
    wiki_seen: set[tuple[str, str]] = set()
    wiki_unique: list[dict[str, str]] = []
    for entry in entries:
        e = clean_entry(entry)
        key = (e["en"], e["ja"])
        if key not in wiki_seen:
            wiki_seen.add(key)
            wiki_unique.append(e)

    records: list[dict[str, Any]] = []
    for part, bit, zh in ACHIEVEMENT_NAMES:
        records.append({
            "bitmap_part": part,
            "bitmap_bit": bit,
            "zh_cn": zh,
            "en": None,
            "ja": None,
            "confidence": "review",
            "match_source": "achievement bitmap order differs from Wiki page order",
        })
    return records


def main() -> int:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    output: dict[str, Any] = {
        "source_raw": str(RAW_PATH.name),
        "note": "Candidate EN/JA matches. Wiki has no save IDs, so positional matches are review-only until checked against Chinese names/game data.",
        "items": {},
        "achievements": {},
        "unmatched_wiki": {},
    }

    # Weapons: split by character. The generic practice weapon is not listed on Wiki.
    weapon_groups = split_weapon_entries(wiki_entries(raw, "weapons"))
    weapon_records: list[dict[str, Any]] = []
    generic_codes = ordered_codes_by_category("equipment_weapon_generic")
    for code in generic_codes:
        weapon_records.append(item_record(code, None, "manual/review", "review", "generic practice weapon is not present on Wiki weapons page"))
    for cat, entries in weapon_groups.items():
        weapon_records.extend(order_match(ordered_codes_by_category(cat), entries, f"weapons:{cat}"))
    output["items"]["weapons"] = weapon_records

    # Armor page: armor, boots, accessories.
    armor_groups = split_armor_entries(wiki_entries(raw, "armor"))
    output["items"]["armor"] = order_match(
        ordered_codes_by_category("equipment_clothes"),
        armor_groups["armor"],
        "armor:armor",
        note="first generic/placeholder clothing codes may need review",
    )
    output["items"]["boots"] = order_match(
        ordered_codes_by_category("equipment_shoes"),
        armor_groups["boots"],
        "armor:boots",
        note="first generic/placeholder shoe codes may need review",
    )
    output["items"]["accessories"] = order_match(
        ordered_codes_by_category("equipment_jewelry"),
        armor_groups["accessories"],
        "armor:accessories",
    )

    # Other categories with stable count/order or useful review output.
    output["items"]["car_items"] = order_match(
        ordered_codes_by_category("event_car"),
        wiki_entries(raw, "car_items"),
        "car_items",
    )
    output["items"]["normal_quartz"] = order_match(
        ordered_codes_by_category("circuit_normal"),
        wiki_entries(raw, "quartz"),
        "quartz",
        note="normal quartz count/order differs from BZH item codes; includes possible duplicate/placeholder/debug-adjacent entries",
    )
    output["items"]["master_quartz"] = order_match(
        ordered_codes_by_category("circuit_core"),
        wiki_entries(raw, "master_quartz"),
        "master_quartz",
        note="current BZH core quartz names are unreliable; one code may be non-Wiki/debug/placeholder",
    )
    fishing_equipment = split_fishing_equipment_entries(wiki_entries(raw, "fishing_equipment"))
    output["items"]["fishing_rods"] = order_match(
        ordered_codes_by_category("fishing_rod"),
        fishing_equipment["rods"],
        "fishing_equipment:rods",
    )
    output["items"]["fishing_bait"] = order_match(
        ordered_codes_by_category("fishing_bait"),
        fishing_equipment["bait"],
        "fishing_equipment:bait",
        note="Wiki lists fish usable as bait too; editor item DB has only inventory bait codes here",
    )
    output["items"]["fish"] = order_match(
        ordered_codes_by_category("fishing_fish"),
        wiki_entries(raw, "fish"),
        "fish",
        note="current first fish code/name may be a package/placeholder; verify offset against in-game fish list",
    )

    # Crafts are not item codes. Keep them separately for later skill slot matching.
    output["crafts"] = [clean_entry(e) for e in wiki_entries(raw, "crafts")]
    output["achievements"]["editor_bitmap"] = achievement_candidates(wiki_entries(raw, "achievements"))
    output["achievements"]["wiki_page_order"] = [clean_entry(e) for e in wiki_entries(raw, "achievements")]

    # Preserve pages whose parser found no EN/JA pairs; raw_lines remain in raw JSON.
    for page in ("books", "enemies"):
        output["unmatched_wiki"][page] = {
            "url": raw["pages"][page]["url"],
            "entry_count": raw["pages"][page]["entry_count"],
            "note": "No structured EN/JA pairs extracted yet; inspect raw_lines in wiki_azure_names_raw.json.",
        }

    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
