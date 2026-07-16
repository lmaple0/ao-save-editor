"""Validated Ao NISA PC fishing-notebook records.

The visible notebook contains 31 records at 0x19CC0.  Each 0x74-byte record
ends with a little-endian u16 maximum size.  Other history fields are exposed
read-only until their exact UI meaning is proven; maximum-size edits preserve
every byte outside that u16.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct


FISH_RECORDS_OFFSET = 0x19CC0
FISH_RECORD_SIZE = 0x74
FISH_RECORD_COUNT = 31
FISH_MAX_SIZE_OFFSET = 0x72
FISH_ITEM_FIRST = 0x015E

# Falcom/NISA data/text/t_fish._dt records 0..30, fields +0x08/+0x0A.
FISH_SIZE_RANGES = (
    (6, 16), (8, 18), (10, 20), (12, 22), (14, 24), (16, 26),
    (18, 38), (22, 42), (26, 46), (30, 50), (36, 56), (38, 58),
    (42, 62), (70, 90), (46, 66), (50, 70), (58, 78), (62, 82),
    (74, 104), (78, 108), (90, 120), (104, 134), (125, 155),
    (98, 128), (112, 142), (86, 116), (192, 192), (215, 215),
    (227, 227), (248, 248), (392, 392),
)

# Falcom/NISA t_fish._dt reward entries. Each pair is (item_id, quantity),
# ordered exactly like save bits 1..4. The table is embedded so packaged builds
# do not depend on a local game installation.
FISH_REWARD_ITEMS = (
    ((304, 1), (995, 10), (996, 20), (994, 50)),
    ((302, 1), (996, 5), (302, 2), (996, 30)),
    ((996, 5), (991, 10), (996, 20), (991, 50)),
    ((330, 1), (995, 5), (330, 3), (995, 30)),
    ((330, 1), (993, 10), (993, 20), (993, 50)),
    ((302, 1), (995, 5), (302, 2), (995, 30)),
    ((992, 10), (992, 25), (992, 50), (992, 150)),
    ((990, 10), (990, 25), (990, 50), (990, 150)),
    ((997, 5), (997, 10), (997, 20), (997, 50)),
    ((301, 1), (993, 25), (301, 2), (993, 150)),
    ((500, 1), (507, 1), (501, 1), (508, 1)),
    ((525, 1), (526, 1), (910, 1), (85, 1)),
    ((996, 10), (994, 25), (996, 40), (994, 100)),
    ((990, 10), (991, 25), (992, 50), (993, 150)),
    ((991, 10), (991, 25), (991, 50), (991, 150)),
    ((306, 1), (993, 25), (993, 50), (993, 150)),
    ((301, 1), (390, 1), (301, 2), (390, 5)),
    ((301, 1), (992, 25), (992, 50), (992, 150)),
    ((523, 1), (994, 15), (994, 30), (994, 100)),
    ((302, 1), (301, 2), (302, 3), (301, 10)),
    ((992, 20), (992, 40), (992, 80), (110, 1)),
    ((995, 15), (996, 30), (995, 60), (996, 200)),
    ((990, 20), (990, 40), (990, 80), (114, 1)),
    ((995, 15), (995, 30), (995, 60), (148, 1)),
    ((306, 2), (991, 40), (991, 80), (991, 300)),
    ((500, 1), (501, 1), (502, 1), (503, 1)),
    ((838, 1),), ((837, 1),), ((839, 1),), ((836, 1),), ((511, 1),),
)

FISH_BAIT_ITEM_BASE = FISH_ITEM_FIRST
FISH_BAIT_FLAG_COUNT = 64


@dataclass(frozen=True)
class FishNotebookRecord:
    index: int
    item_id: int
    min_size: int
    natural_max_size: int
    maximum_size: int
    recent_location_ids: tuple[int, ...]
    location_counts: tuple[int, ...]
    bait_flags: int
    reward_flags: int

    @property
    def registered(self) -> bool:
        return self.maximum_size != 0

    @property
    def caught_count(self) -> int:
        return sum(self.location_counts)


def reward_items_for_flags(index: int, flags: int) -> tuple[tuple[int, int], ...]:
    """Return discovered reward (item_id, quantity) pairs for one fish."""
    if not 0 <= index < FISH_RECORD_COUNT:
        raise IndexError(f"fish index out of range: {index}")
    return tuple(
        reward
        for tier, reward in enumerate(FISH_REWARD_ITEMS[index])
        if flags & (1 << (tier + 1))
    )


def known_reward_flags(index: int) -> int:
    if not 0 <= index < FISH_RECORD_COUNT:
        raise IndexError(f"fish index out of range: {index}")
    return sum(1 << (tier + 1) for tier in range(len(FISH_REWARD_ITEMS[index])))


def bait_item_ids_for_flags(flags: int) -> tuple[int, ...]:
    """Map the 64-bit save bitmap to fish/bait item IDs."""
    return tuple(
        FISH_BAIT_ITEM_BASE + bit
        for bit in range(FISH_BAIT_FLAG_COUNT)
        if flags & (1 << bit)
    )


def _record_offset(index: int) -> int:
    if not 0 <= index < FISH_RECORD_COUNT:
        raise IndexError(f"fish index out of range: {index}")
    return FISH_RECORDS_OFFSET + index * FISH_RECORD_SIZE


def read_fishing_notebook(data: bytes | bytearray) -> tuple[FishNotebookRecord, ...]:
    required = FISH_RECORDS_OFFSET + FISH_RECORD_COUNT * FISH_RECORD_SIZE
    if len(data) < required:
        raise ValueError(f"save data is too short for fishing notebook: {len(data):#x} < {required:#x}")
    rows = []
    for index, (minimum, maximum) in enumerate(FISH_SIZE_RANGES):
        offset = _record_offset(index)
        rows.append(
            FishNotebookRecord(
                index=index,
                item_id=FISH_ITEM_FIRST + index,
                min_size=minimum,
                natural_max_size=maximum,
                maximum_size=struct.unpack_from("<H", data, offset + FISH_MAX_SIZE_OFFSET)[0],
                recent_location_ids=tuple(data[offset : offset + 4]),
                location_counts=struct.unpack_from("<50H", data, offset + 4),
                bait_flags=int.from_bytes(data[offset + 0x68 : offset + 0x70], "little"),
                reward_flags=struct.unpack_from("<H", data, offset + 0x70)[0],
            )
        )
    return tuple(rows)


def write_fish_maximum_size(data: bytearray, index: int, value: int) -> None:
    """Write one proven u16 field, preserving the remaining 0x72 record bytes."""
    minimum, maximum = FISH_SIZE_RANGES[index]
    if value != 0 and not minimum <= value <= maximum:
        raise ValueError(
            f"fish {index} maximum size must be 0 or {minimum}..{maximum}, got {value}"
        )
    offset = _record_offset(index) + FISH_MAX_SIZE_OFFSET
    if len(data) < offset + 2:
        raise ValueError("save data is too short for fishing notebook")
    struct.pack_into("<H", data, offset, value)


def register_all_fish(data: bytearray, *, use_natural_maximum: bool = True) -> None:
    """Register all visible fish by changing only their proven maximum-size fields."""
    for index, (minimum, maximum) in enumerate(FISH_SIZE_RANGES):
        write_fish_maximum_size(data, index, maximum if use_natural_maximum else minimum)


# UI translations and internal reward pseudo-item names owned by fishing.
FISHING_UI_TRANSLATIONS = {
    "zh_cn": {
        "钓鱼手册": "钓鱼手册", "登记进度: 0/31": "登记进度: 0/31",
        "登记进度: {count}/31": "登记进度: {count}/31", "选中 → 登记": "选中 → 登记",
        "全部登记": "全部登记", "最大尺寸:": "最大尺寸:", "应用最大尺寸": "应用最大尺寸",
        "0 表示未登记；登记尺寸必须位于自然范围内": "0 表示未登记；登记尺寸必须位于自然范围内",
        "序号": "序号", "最大尺寸": "最大尺寸", "自然范围": "自然范围", "累计次数": "累计次数",
        "奖励资料": "奖励资料", "鱼饵资料": "鱼饵资料", "已登记": "已登记",
        "请先选择鱼类记录": "请先选择鱼类记录", "已登记选中鱼类: {count}": "已登记选中鱼类: {count}",
        "已设为未登记: {count}": "已设为未登记: {count}", "全部鱼类已登记": "全部鱼类已登记",
        "修改最大尺寸时只能选择一项": "修改最大尺寸时只能选择一项",
        "最大尺寸必须为 0 或 {minimum} 到 {maximum}": "最大尺寸必须为 0 或 {minimum} 到 {maximum}",
        "最大尺寸已设为 {value}": "最大尺寸已设为 {value}",
    },
    "en": {
        "钓鱼手册": "Fishing Notebook", "登记进度: 0/31": "Registered: 0/31",
        "登记进度: {count}/31": "Registered: {count}/31", "选中 → 登记": "Selected → Registered",
        "全部登记": "Register All", "最大尺寸:": "Maximum size:", "应用最大尺寸": "Apply Maximum Size",
        "0 表示未登记；登记尺寸必须位于自然范围内": "0 means unregistered; registered sizes must be within the natural range",
        "序号": "No.", "最大尺寸": "Maximum", "自然范围": "Natural Range", "累计次数": "Caught",
        "奖励资料": "Reward Data", "鱼饵资料": "Bait Data", "已登记": "Registered",
        "请先选择鱼类记录": "Select a fish record first", "已登记选中鱼类: {count}": "Registered selected fish: {count}",
        "已设为未登记: {count}": "Set selected fish to unregistered: {count}", "全部鱼类已登记": "All fish registered",
        "修改最大尺寸时只能选择一项": "Select exactly one fish to edit its maximum size",
        "最大尺寸必须为 0 或 {minimum} 到 {maximum}": "Maximum size must be 0 or {minimum} to {maximum}",
        "最大尺寸已设为 {value}": "Maximum size set to {value}",
    },
    "ja": {
        "钓鱼手册": "釣り手帳", "登记进度: 0/31": "登録: 0/31",
        "登记进度: {count}/31": "登録: {count}/31", "选中 → 登记": "選択 → 登録",
        "全部登记": "すべて登録", "最大尺寸:": "最大サイズ:", "应用最大尺寸": "最大サイズを適用",
        "0 表示未登记；登记尺寸必须位于自然范围内": "0は未登録。登録サイズは自然範囲内にしてください",
        "序号": "番号", "最大尺寸": "最大サイズ", "自然范围": "自然範囲", "累计次数": "釣獲回数",
        "奖励资料": "報酬データ", "鱼饵资料": "エサデータ", "已登记": "登録済み",
        "请先选择鱼类记录": "魚の記録を選択してください", "已登记选中鱼类: {count}": "選択した魚を登録しました: {count}",
        "已设为未登记: {count}": "未登録に設定しました: {count}", "全部鱼类已登记": "すべての魚を登録しました",
        "修改最大尺寸时只能选择一项": "最大サイズの編集では1件だけ選択してください",
        "最大尺寸必须为 0 或 {minimum} 到 {maximum}": "最大サイズは0または{minimum}～{maximum}です",
        "最大尺寸已设为 {value}": "最大サイズを{value}に設定しました",
    },
}


# t_fish._dt uses these internal reward IDs for currencies rather than normal
# inventory items, so they are intentionally localized outside ao_item_i18n.json.
FISH_REWARD_PSEUDO_NAMES = {
    0x03DE: {"zh_cn": "地之耀晶片", "en": "Earth Sepith", "ja": "地のセピス"},
    0x03DF: {"zh_cn": "水之耀晶片", "en": "Water Sepith", "ja": "水のセピス"},
    0x03E0: {"zh_cn": "火之耀晶片", "en": "Fire Sepith", "ja": "火のセピス"},
    0x03E1: {"zh_cn": "风之耀晶片", "en": "Wind Sepith", "ja": "風のセピス"},
    0x03E2: {"zh_cn": "时之耀晶片", "en": "Time Sepith", "ja": "時のセピス"},
    0x03E3: {"zh_cn": "空之耀晶片", "en": "Space Sepith", "ja": "空のセピス"},
    0x03E4: {"zh_cn": "幻之耀晶片", "en": "Mirage Sepith", "ja": "幻のセピス"},
    0x03E5: {"zh_cn": "耀晶片块", "en": "Sepith Mass", "ja": "セピス塊"},
}


def fishing_reward_item_name(item_id: int, lang: str, item_name) -> str:
    localized = FISH_REWARD_PSEUDO_NAMES.get(item_id, {}).get(lang)
    return localized or item_name(item_id, lang)
