"""Shared verified NISA PC save-layout constants.

Keep binary offsets here so read, write, and audit modules cannot silently drift.
This module deliberately contains no parsing or mutation behaviour.
"""

EXPECTED_SIZE = 0x2643C

CHECKSUM_USER_SIZE = 0x00026438
CHECKSUM_USER = 0x00026434

ITEMS_START = 0x00000E2C
ITEMS_END = 0x0000194C

TEAM_SLOTS = tuple(0x0001AFE0 + index * 2 for index in range(8))
KNOWN_TEAM_IDS = frozenset((
    *range(11), 15, 61, 82, 140, 160, 161, 0x00FF,
))
DIFFICULTY_OFFSET = 0x0001F36D

RECIPE_BOOK_OFFSETS = (0x00019C98, 0x00019C9C, 0x00019CA0)
RECIPE_BOOK_MASK = 0x01FFFFFE

ROLE_DISPLAY_OFFSETS = tuple(0x0001B358 + index * 2 for index in range(12))
KNOWN_ROLE_DISPLAY_IDS = frozenset((
    *range(11), 11, 12, 14, 15, 0x1F, 0x20,
    0x60, 0x61, 0x62, 0xA0, 0xA1, 0xA2, 0xA4,
))

MONSTER_START = 0x0001B370
MONSTER_END = 0x0001BCF0
MONSTER_RECORD_SIZE = 8
MONSTER_COMPLETE_PAYLOAD = bytes((0x08, 0xFE, 0xFF, 0xFF))
