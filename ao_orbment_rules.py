"""Element-lock rules extracted from the NISA PC t_orb/t_quartz tables."""

from __future__ import annotations


# t_orb._dt SHA-256:
# 50D55E84672B0213FCCFA2D8A473957F91F8236750FEC9C6CDAB2B2F86292C0E
# Slots are core (0), followed by six normal-quartz slots (1..6).
CHARACTER_SLOT_ELEMENTS = {
    "Lloyd": (0, 0, 0, 0, 0, 0, 0),
    "Elie": (0, 0, 0, 0, 0, 4, 0),
    "Tio": (0, 0, 2, 0, 0, 0, 0),
    "Randy": (0, 0, 0, 3, 0, 0, 0),
    "Wazy": (0, 0, 0, 0, 6, 0, 0),
    "Rixia": (0, 0, 0, 0, 7, 0, 0),
    "Garcia": (0, 0, 0, 0, 0, 0, 0),
    "Arios": (0, 0, 0, 5, 0, 0, 0),
    "Noel": (0, 0, 0, 1, 0, 0, 0),
    "Dudley": (0, 0, 0, 0, 5, 0, 0),
    # Zeit has no t_orb record and no usable orbment in natural saves.
    "Zeit": (0, 0, 0, 0, 0, 0, 0),
}

QUARTZ_FIRST_ITEM_CODE = 0x0064

# Primary-element byte from each 0x1C-byte t_quartz._dt record covering
# item IDs 0x0064..0x00D8. Source SHA-256:
# 02CB1687508E346697FB21FD55E3ED78456B7C71AF1B7745667FEB4230A38062
QUARTZ_PRIMARY_ELEMENTS = bytes((
    2, 2, 2, 2, 7, 7, 7, 7, 3, 3, 3, 3, 1, 1, 1, 1,
    7, 7, 7, 7, 2, 2, 2, 2, 6, 6, 6, 6, 4, 4, 4, 4,
    4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6,
    6, 6, 1, 1, 2, 2, 3, 3, 4, 4, 7, 3, 1, 6, 2, 5,
    4, 1, 2, 3, 4, 5, 6, 7, 1, 1, 2, 2, 3, 3, 3, 4,
    1, 4, 5, 6, 6, 6, 7, 7, 5, 7, 1, 1, 2, 2, 3, 3,
    4, 4, 7, 6, 6, 6, 6, 6, 6, 1, 1, 1, 1, 2, 2, 3,
    3, 4, 4, 7, 7,
))


def quartz_primary_element(item_code):
    """Return the t_quartz primary element, or None for non-table IDs."""
    index = int(item_code) - QUARTZ_FIRST_ITEM_CODE
    if 0 <= index < len(QUARTZ_PRIMARY_ELEMENTS):
        return QUARTZ_PRIMARY_ELEMENTS[index]
    return None


def required_slot_element(character, slot_index):
    """Return the t_orb element code required by one save orbment slot."""
    slots = CHARACTER_SLOT_ELEMENTS.get(character)
    if slots is None:
        raise ValueError(f"unknown orbment character: {character}")
    if not 0 <= int(slot_index) < len(slots):
        raise ValueError(f"invalid orbment slot: {slot_index}")
    return slots[int(slot_index)]


def orbment_code_is_allowed(character, slot_index, item_code):
    """Check a quartz against the character's t_orb element-locked slot."""
    item_code = int(item_code)
    required = required_slot_element(character, slot_index)
    if not item_code or not required:
        return True
    return quartz_primary_element(item_code) == required
