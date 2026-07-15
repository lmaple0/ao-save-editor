"""Read-only parsing and validation for verified Ao NISA character loadouts.

Writing remains deliberately outside this module until inventory transfer and
core-quartz ownership semantics are backed by controlled before/after evidence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import struct

from ao_save_layout import (
    EQUIPMENT_RECORD_SIZE,
    EQUIPMENT_SLOT_NAMES,
    EQUIPMENT_START,
    EXPECTED_SIZE,
    LOADOUT_CHARACTERS,
    ORBMENT_ENHANCEMENT_LEVELS,
    ORBMENT_RECORD_SIZE,
    ORBMENT_SLOT_COUNT,
    ORBMENT_SLOT_RECORD_SIZE,
    ORBMENT_START,
)


@dataclass(frozen=True)
class EquipmentLoadout:
    weapon: int
    clothes: int
    shoes: int
    accessory_1: int
    accessory_2: int

    def values(self):
        return (self.weapon, self.clothes, self.shoes, self.accessory_1, self.accessory_2)


@dataclass(frozen=True)
class OrbmentSlot:
    item_code: int
    enhancement_level: int


@dataclass(frozen=True)
class CharacterLoadout:
    character: str
    equipment: EquipmentLoadout
    orbment: tuple[OrbmentSlot, ...]


@dataclass(frozen=True)
class LoadoutIssue:
    code: str
    character: str
    slot: str
    value: int


def read_character_loadouts(data):
    """Parse all eleven fixed loadout records without normalizing unknown IDs."""
    raw = bytes(data or b"")
    if len(raw) != EXPECTED_SIZE:
        raise ValueError(f"unexpected save size: {len(raw)} != {EXPECTED_SIZE}")

    result = []
    for index, character in enumerate(LOADOUT_CHARACTERS):
        equipment_offset = EQUIPMENT_START + index * EQUIPMENT_RECORD_SIZE
        equipment = EquipmentLoadout(*struct.unpack_from("<5H", raw, equipment_offset))

        orbment_offset = ORBMENT_START + index * ORBMENT_RECORD_SIZE
        orbment = tuple(
            OrbmentSlot(*struct.unpack_from("<HH", raw, orbment_offset + slot * ORBMENT_SLOT_RECORD_SIZE))
            for slot in range(ORBMENT_SLOT_COUNT)
        )
        result.append(CharacterLoadout(character, equipment, orbment))
    return tuple(result)


def _weapon_categories(character):
    category_character = "Lazy" if character == "Wazy" else character
    categories = {"equipment_weapon_generic", f"equipment_weapon_{category_character}"}
    # Natural NISA saves use Lloyd weapons for Garcia, then 0x0474, which the
    # source item table groups with Zeit. Both are evidence-backed exceptions.
    if character == "Garcia":
        categories.update(("equipment_weapon_Lloyd", "equipment_weapon_Zeit"))
    return categories


def equipment_code_is_allowed(character, slot, item_code, item_categories):
    """Check category compatibility; zero always represents an empty slot."""
    if item_code == 0:
        return True
    category = item_categories.get(item_code)
    if slot == "weapon":
        return category in _weapon_categories(character)
    expected = {
        "clothes": "equipment_clothes",
        "shoes": "equipment_shoes",
        "accessory_1": "equipment_jewelry",
        "accessory_2": "equipment_jewelry",
    }
    return category == expected.get(slot)


def validate_character_loadouts(data, item_categories):
    """Return structural/category issues without changing the save."""
    loadouts = read_character_loadouts(data)
    issues = []
    equipped_cores = []

    for loadout in loadouts:
        for slot, item_code in zip(EQUIPMENT_SLOT_NAMES, loadout.equipment.values()):
            if not equipment_code_is_allowed(loadout.character, slot, item_code, item_categories):
                issues.append(LoadoutIssue("equipment_category", loadout.character, slot, item_code))

        for index, orbment_slot in enumerate(loadout.orbment):
            expected = "circuit_core" if index == 0 else "circuit_normal"
            if orbment_slot.item_code and item_categories.get(orbment_slot.item_code) != expected:
                issues.append(
                    LoadoutIssue("orbment_category", loadout.character, f"orbment_{index}", orbment_slot.item_code)
                )
            if orbment_slot.enhancement_level not in ORBMENT_ENHANCEMENT_LEVELS:
                issues.append(
                    LoadoutIssue(
                        "orbment_enhancement_level",
                        loadout.character,
                        f"orbment_{index}",
                        orbment_slot.enhancement_level,
                    )
                )
            if index == 0 and orbment_slot.item_code:
                equipped_cores.append((loadout.character, orbment_slot.item_code))

    core_counts = Counter(item_code for _character, item_code in equipped_cores)
    for character, item_code in equipped_cores:
        if core_counts[item_code] > 1:
            issues.append(LoadoutIssue("duplicate_core_quartz", character, "orbment_0", item_code))
    return tuple(issues)


def apply_character_loadout_changes(
    data,
    items,
    character,
    equipment_codes,
    orbment_codes,
    enhancement_levels,
    item_categories,
    quantity_max=99,
):
    """Atomically replace one character's equipment and orbment.

    Equipped items are not present in the inventory table. This operation
    returns the old loadout to a temporary inventory pool, consumes the new
    loadout from that pool, validates the complete target state, and only then
    returns replacement save bytes and inventory data.
    """
    equipment_codes = tuple(int(code) for code in equipment_codes)
    orbment_codes = tuple(int(code) for code in orbment_codes)
    enhancement_levels = tuple(int(level) for level in enhancement_levels)
    if len(equipment_codes) != len(EQUIPMENT_SLOT_NAMES):
        raise ValueError("equipment slot count must be 5")
    if len(orbment_codes) != ORBMENT_SLOT_COUNT:
        raise ValueError("orbment slot count must be 7")
    if len(enhancement_levels) != ORBMENT_SLOT_COUNT:
        raise ValueError("orbment enhancement level count must be 7")
    try:
        character_index = LOADOUT_CHARACTERS.index(character)
    except ValueError as exc:
        raise ValueError(f"unknown loadout character: {character}") from exc

    current_loadouts = read_character_loadouts(data)
    current = current_loadouts[character_index]
    for slot, old_code, new_code in zip(
        EQUIPMENT_SLOT_NAMES, current.equipment.values(), equipment_codes
    ):
        if new_code != old_code and not equipment_code_is_allowed(
            character, slot, new_code, item_categories
        ):
            raise ValueError(f"item 0x{new_code:04X} is not valid for {character} {slot}")

    for index, (old_slot, new_code, level) in enumerate(
        zip(current.orbment, orbment_codes, enhancement_levels)
    ):
        expected = "circuit_core" if index == 0 else "circuit_normal"
        if new_code != old_slot.item_code and new_code and item_categories.get(new_code) != expected:
            raise ValueError(f"item 0x{new_code:04X} is not valid for orbment slot {index}")
        if level not in ORBMENT_ENHANCEMENT_LEVELS:
            raise ValueError(f"invalid orbment enhancement level: {level}")

    normal_codes = [code for code in orbment_codes[1:] if code]
    if len(normal_codes) != len(set(normal_codes)):
        raise ValueError("the same normal quartz cannot be equipped twice on one orbment")

    target_core = orbment_codes[0]
    if target_core:
        for index, loadout in enumerate(current_loadouts):
            if index != character_index and loadout.orbment[0].item_code == target_core:
                raise ValueError(
                    f"core quartz 0x{target_core:04X} is already equipped by {loadout.character}"
                )

    inventory = Counter()
    for code, quantity in dict(items or {}).items():
        code = int(code)
        quantity = int(quantity)
        if code and quantity > 0:
            inventory[code] += quantity

    # 0x0009 is the natural inactive-character placeholder, not transferable
    # equipment. All real equipped items and quartz re-enter the temporary pool.
    for code in current.equipment.values():
        if code not in (0, 0x0009):
            inventory[code] += 1
    for slot in current.orbment:
        if slot.item_code:
            inventory[slot.item_code] += 1

    requested = [code for code in equipment_codes if code not in (0, 0x0009)]
    requested.extend(code for code in orbment_codes if code)
    for code in requested:
        if inventory[code] <= 0:
            raise ValueError(f"item 0x{code:04X} is not available in inventory")
        inventory[code] -= 1

    result_items = {
        code: quantity for code, quantity in inventory.items() if quantity > 0
    }
    over_limit = {code: qty for code, qty in result_items.items() if qty > quantity_max}
    if over_limit:
        code, quantity = next(iter(over_limit.items()))
        raise ValueError(f"inventory quantity exceeds {quantity_max}: 0x{code:04X}={quantity}")

    result_data = bytearray(data)
    equipment_offset = EQUIPMENT_START + character_index * EQUIPMENT_RECORD_SIZE
    struct.pack_into("<5H", result_data, equipment_offset, *equipment_codes)
    orbment_offset = ORBMENT_START + character_index * ORBMENT_RECORD_SIZE
    for index, (code, level) in enumerate(zip(orbment_codes, enhancement_levels)):
        struct.pack_into(
            "<HH", result_data, orbment_offset + index * ORBMENT_SLOT_RECORD_SIZE, code, level
        )
    return result_data, result_items
