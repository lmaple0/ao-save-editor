"""Read-only verifier for core tables from an installed CLE Ao Kai copy."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ao_cle_kai_tables import (  # noqa: E402
    decrypt_table_file,
    parse_item_table,
    parse_orbment_slot_elements,
    parse_quartz_table,
    validate_item_categories,
)
from ao_items_db import ITEM_DB  # noqa: E402
from ao_orbment_rules import CHARACTER_SLOT_ELEMENTS, QUARTZ_PRIMARY_ELEMENTS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_dir", type=Path)
    args = parser.parse_args()
    text_dir = args.game_dir / "data" / "text"

    plaintext = {
        name: decrypt_table_file(text_dir / name)
        for name in ("t_item._dt", "t_item2._dt", "t_quartz._dt", "t_orb._dt")
    }
    item_records = (
        parse_item_table(plaintext["t_item._dt"], "t_item")
        + parse_item_table(plaintext["t_item2._dt"], "t_item2")
    )
    issues = validate_item_categories(item_records, ITEM_DB)
    quartz = parse_quartz_table(plaintext["t_quartz._dt"])
    slots = parse_orbment_slot_elements(plaintext["t_orb._dt"])
    expected_slots = {
        name: tuple(values)
        for name, values in CHARACTER_SLOT_ELEMENTS.items()
        if name != "Zeit"
    }

    print(f"items={len(item_records)} unique={len({r.item_id for r in item_records})}")
    print("item_types=" + repr(dict(sorted(Counter(r.item_type for r in item_records).items()))))
    print(f"item_category_issues={len(issues)}")
    for issue in issues:
        print("  " + issue)
    print(f"normal_quartz={len(quartz.normal)} master_quartz={len(quartz.master)}")
    cle_elements = bytes(record.element for record in quartz.normal)
    print(f"normal_elements_match_nisa_tail={cle_elements == QUARTZ_PRIMARY_ELEMENTS[1:]}")
    print(f"orbment_slots_match_nisa={slots == expected_slots}")
    for name, data in plaintext.items():
        print(f"{name}: plaintext_size={len(data)} sha256={hashlib.sha256(data).hexdigest().upper()}")
    return 1 if issues or slots != expected_slots else 0


if __name__ == "__main__":
    raise SystemExit(main())
