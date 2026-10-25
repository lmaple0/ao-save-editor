"""Ao-only full-payload mapping; editor data always uses NISA offsets.

Layout corroborated by the CLE/NISA executables and the supplied converter v2.
CLE thread-only bytes are retained through the original payload on same-format
writes. Cross-edition exports contain the fields represented by both editions.
"""

import struct

from ao_save_layout import EXPECTED_SIZE

CLE_PAYLOAD_SIZE = 0x27448
NISA_SCENE_THREAD = 0x4B64
CLE_SCENE_THREAD = 0x4B68
NISA_ACTORS = 0x4C04
CLE_ACTORS = 0x4C10
ACTOR_COUNT = 128
NISA_ACTOR_SIZE = 0x2A0
CLE_ACTOR_SIZE = 0x2C0
NISA_THREAD_SIZE = 0xA0
CLE_THREAD_SIZE = 0xA8
NISA_TAIL = 0x19C04
CLE_TAIL = 0x1AC10


def checksums(data):
    words = struct.unpack(f"<{(len(data) - 8) // 4}I", data[:-8])
    total = sum(words)
    return total & 0xFFFFFFFF, (-len(words) - total) & 0xFFFFFFFF


def update_checksum(data):
    struct.pack_into("<II", data, len(data) - 8, *checksums(data))


def thread_pairs():
    yield NISA_SCENE_THREAD, CLE_SCENE_THREAD
    for actor in range(ACTOR_COUNT):
        for thread in range(4):
            yield (NISA_ACTORS + actor * NISA_ACTOR_SIZE + 0x20 + thread * NISA_THREAD_SIZE,
                   CLE_ACTORS + actor * CLE_ACTOR_SIZE + 0x20 + thread * CLE_THREAD_SIZE)


def cle_to_nisa(payload):
    if len(payload) != CLE_PAYLOAD_SIZE:
        raise ValueError(f"碧 CLE 明文大小错误: {len(payload):#x}")
    result = bytearray(EXPECTED_SIZE)
    result[:NISA_SCENE_THREAD] = payload[:NISA_SCENE_THREAD]
    for actor in range(ACTOR_COUNT):
        n = NISA_ACTORS + actor * NISA_ACTOR_SIZE
        c = CLE_ACTORS + actor * CLE_ACTOR_SIZE
        result[n:n + 0x20] = payload[c:c + 0x20]
    for n, c in thread_pairs():
        result[n:n + 0x3C] = payload[c:c + 0x3C]
        result[n + 0x3C:n + 0x96] = payload[c + 0x40:c + 0x9A]
    result[NISA_TAIL:-8] = payload[CLE_TAIL:-8]
    update_checksum(result)
    return result


def nisa_to_cle(data, original=None):
    if len(data) != EXPECTED_SIZE:
        raise ValueError(f"碧 NISA 明文大小错误: {len(data):#x}")
    if original is not None and len(original) != CLE_PAYLOAD_SIZE:
        raise ValueError("原始 CLE 明文大小错误")
    result = bytearray(original) if original is not None else bytearray(CLE_PAYLOAD_SIZE)
    result[:NISA_SCENE_THREAD] = data[:NISA_SCENE_THREAD]
    for actor in range(ACTOR_COUNT):
        n = NISA_ACTORS + actor * NISA_ACTOR_SIZE
        c = CLE_ACTORS + actor * CLE_ACTOR_SIZE
        result[c:c + 0x20] = data[n:n + 0x20]
    for n, c in thread_pairs():
        result[c:c + 0x3C] = data[n:n + 0x3C]
        result[c + 0x40:c + 0x9A] = data[n + 0x3C:n + 0x96]
    result[CLE_TAIL:-8] = data[NISA_TAIL:-8]
    return result
