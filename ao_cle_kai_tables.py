"""Parsers and validators for core Clouded Leopard Ao Kai data tables.

The module intentionally operates on caller-provided bytes.  It never writes
to the game directory and does not require an installed copy of the game at
runtime.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from ao_save_container import decode_cle_asset


ITEM_RECORD_SIZE = 0x1C
ITEM_ID_OFFSET = 0x10
ITEM_TYPE_OFFSET = 0x15

# CLE t_item/t_item2 type byte at record +0x15.  Weapon types 1..10 are
# character-specific; type 5 is shared by Wazy and one Zeit weapon.
ITEM_TYPE_CATEGORIES = {
    0x01: ("equipment_weapon_generic", "equipment_weapon_Lloyd"),
    0x02: ("equipment_weapon_Elie",),
    0x03: ("equipment_weapon_Tio",),
    0x04: ("equipment_weapon_Randy",),
    0x05: ("equipment_weapon_Lazy", "equipment_weapon_Zeit"),
    0x06: ("equipment_weapon_Rixia",),
    0x07: ("equipment_weapon_Zeit",),
    0x08: ("equipment_weapon_Arios",),
    0x09: ("equipment_weapon_Noel",),
    0x0A: ("equipment_weapon_Dudley",),
    0x0B: ("equipment_clothes",),
    0x0C: ("equipment_shoes",),
    0x0D: ("equipment_jewelry",),
    0x0E: ("props_normal",),
    0x12: ("circuit_normal", "circuit_debug"),
    0x13: ("props_cooking",),
    0x14: ("food",),
    0x15: ("book",),
    0x16: ("props_cooking",),
    0x17: ("fishing_bait",),
    0x18: ("fishing_fish",),
    0x19: ("fishing_rod",),
    0x1A: ("circuit_core",),
}


@dataclass(frozen=True)
class CleItemRecord:
    item_id: int
    item_type: int
    source: str
    offset: int
    raw: bytes


@dataclass(frozen=True)
class CleQuartzRecord:
    item_id: int
    element: int
    raw: bytes


@dataclass(frozen=True)
class CleMasterQuartzRecord:
    item_id: int
    element: int
    raw: bytes


@dataclass(frozen=True)
class CleQuartzTable:
    normal: tuple[CleQuartzRecord, ...]
    master: tuple[CleMasterQuartzRecord, ...]


def decrypt_table_file(path: str | Path) -> bytes:
    """Read and decrypt one CLE Kai ``._dt`` table without modifying it."""
    return decode_cle_asset(Path(path).read_bytes())


def parse_item_table(data: bytes, source: str = "t_item") -> tuple[CleItemRecord, ...]:
    """Parse the indexed 0x1C-byte records in t_item or t_item2."""
    if len(data) < 2:
        raise ValueError(f"{source}: table is truncated")
    record_area = struct.unpack_from("<H", data)[0]
    if record_area < 2 or record_area > len(data) or record_area % 2:
        raise ValueError(f"{source}: invalid pointer-table size 0x{record_area:X}")
    pointers = struct.unpack_from(f"<{record_area // 2}H", data)
    offsets = sorted({p for p in pointers if record_area <= p < len(data)})
    records = []
    for index, offset in enumerate(offsets[:-1]):
        end = offsets[index + 1]
        if end - offset != ITEM_RECORD_SIZE:
            continue
        raw = bytes(data[offset:end])
        item_id = struct.unpack_from("<H", raw, ITEM_ID_OFFSET)[0]
        records.append(CleItemRecord(
            item_id=item_id,
            item_type=raw[ITEM_TYPE_OFFSET],
            source=source,
            offset=offset,
            raw=raw,
        ))
    if not records:
        raise ValueError(f"{source}: no 0x1C-byte item records found")
    ids = [record.item_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{source}: duplicate item IDs")
    return tuple(records)


def validate_item_categories(
    records: tuple[CleItemRecord, ...],
    item_db: Mapping[int, tuple[str, str]],
) -> tuple[str, ...]:
    """Return category mismatches against the editor's item database."""
    issues = []
    for record in records:
        expected = ITEM_TYPE_CATEGORIES.get(record.item_type)
        current = item_db.get(record.item_id)
        if expected is None:
            issues.append(
                f"0x{record.item_id:04X}: unknown CLE type 0x{record.item_type:02X}"
            )
        elif current is None:
            issues.append(f"0x{record.item_id:04X}: missing from ITEM_DB")
        elif current[0] not in expected:
            issues.append(
                f"0x{record.item_id:04X}: CLE type 0x{record.item_type:02X} "
                f"expects {expected}, got {current[0]}"
            )
    return tuple(issues)


def parse_quartz_table(data: bytes) -> CleQuartzTable:
    """Parse the CLE Kai Ao normal- and master-quartz records.

    The CLE Kai table has a six-byte zero prefix, 116 normal 0x1C-byte
    records (logical IDs 1..116), twelve zero alignment bytes, and 22
    0x2C-byte master-quartz records (item IDs 0xDC..0xF1).
    """
    prefix_size = 6
    normal_count = 116
    normal_size = 0x1C
    alignment_size = 12
    master_count = 22
    master_size = 0x2C
    expected_size = (
        prefix_size + normal_count * normal_size + alignment_size
        + master_count * master_size
    )
    if len(data) != expected_size:
        raise ValueError(f"t_quartz: expected {expected_size} bytes, got {len(data)}")
    if data[:prefix_size] != bytes(prefix_size):
        raise ValueError("t_quartz: unexpected prefix")

    normal = []
    pos = prefix_size
    for logical_id in range(1, normal_count + 1):
        raw = bytes(data[pos:pos + normal_size])
        actual_id, element = struct.unpack_from("<HH", raw, 0x0C)
        if actual_id != logical_id or not 1 <= element <= 7:
            raise ValueError(
                f"t_quartz: invalid normal record {logical_id}: "
                f"id={actual_id}, element={element}"
            )
        # Logical ID 1 maps to item 0x65; item 0x64 is the one omitted
        # leading entry relative to the NISA table.
        normal.append(CleQuartzRecord(actual_id + 0x64, element, raw))
        pos += normal_size

    if data[pos:pos + alignment_size] != bytes(alignment_size):
        raise ValueError("t_quartz: unexpected master-quartz alignment bytes")
    pos += alignment_size

    master = []
    for expected_id in range(0xDC, 0xF2):
        raw = bytes(data[pos:pos + master_size])
        item_id, element = struct.unpack_from("<HH", raw)
        if item_id != expected_id or not 1 <= element <= 7:
            raise ValueError(
                f"t_quartz: invalid master record 0x{expected_id:04X}: "
                f"id=0x{item_id:04X}, element={element}"
            )
        if any(raw[offset] for offset in (4, 12, 20, 28, 36)):
            raise ValueError(f"t_quartz: invalid level markers for 0x{item_id:04X}")
        master.append(CleMasterQuartzRecord(item_id, element, raw))
        pos += master_size
    return CleQuartzTable(tuple(normal), tuple(master))


# The first seven bytes at these offsets are the elemental slot restrictions.
# They match the NISA-derived rules byte for byte.  Zeit has no usable record.
ORBMENT_SLOT_ELEMENT_OFFSETS = {
    "Lloyd": 0x00A,
    "Elie": 0x026,
    "Tio": 0x042,
    "Randy": 0x056,
    "Wazy": 0x07A,
    "Rixia": 0x096,
    "Garcia": 0x0BA,
    "Arios": 0x0CE,
    "Noel": 0x0EA,
    "Dudley": 0x116,
}


def parse_orbment_slot_elements(data: bytes) -> dict[str, tuple[int, ...]]:
    """Extract the ten CLE Kai character slot-element restrictions."""
    if len(data) != 306:
        raise ValueError(f"t_orb: expected 306 bytes, got {len(data)}")
    result = {}
    for character, offset in ORBMENT_SLOT_ELEMENT_OFFSETS.items():
        slots = tuple(data[offset:offset + 7])
        if len(slots) != 7 or any(value > 7 for value in slots):
            raise ValueError(f"t_orb: invalid slot elements for {character}")
        result[character] = slots
    return result
