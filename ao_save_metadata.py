"""Ao conversion sidecars: retain source metadata and label clear slots exactly."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import struct

from ao_save_layout import DIFFICULTY_OFFSET

CLE_INFO_SIZE = 0x2889C
TITLES = ("英雄伝説 碧の軌跡：改", "영웅전설 벽의 궤적: Kai", "英雄傳說 碧之軌跡：改")
CHAPTERS = ("序章", "第一章", "第二章", "间章", "第三章", "第四章", "断章", "终章", "通关资料")
DIFFICULTIES = ("Normal", "Hard", "Nightmare", "Easy")
DIFFICULTIES_ZH = ("普通", "困难", "噩梦", "简单")
CHARACTERS = ("罗伊德", "艾莉", "缇欧", "兰迪", "瓦吉", "莉夏", "蔡特", "亚里欧斯", "诺艾尔", "达德利", "加尔西亚")


@dataclass
class SaveMetadata:
    chapter: str
    subtitle: str
    location: str
    timestamp: datetime
    clear: bool = False
    icon: bytes | None = None


def _text(raw, encoding):
    return raw.split(b"\0", 1)[0].decode(encoding)


def _put_text(buf, start, size, text, encoding="utf-8"):
    raw = text.encode(encoding, errors="replace")[:size - 1]
    raw = raw.decode(encoding, errors="ignore").encode(encoding)
    buf[start:start + size] = raw.ljust(size, b"\0")


def _systemtime(when):
    return struct.pack("<8H", when.year, when.month, (when.weekday() + 1) % 7,
                       when.day, when.hour, when.minute, when.second, when.microsecond // 1000)


def source_metadata(path, data, edition):
    path = Path(path)
    when = datetime.fromtimestamp(path.stat().st_mtime)
    chapter_code = data[0x19C78]
    chapter = CHAPTERS[chapter_code] if chapter_code < len(CHAPTERS) else ""
    meta = SaveMetadata(chapter, "", "", when)
    if edition == "cle_kai":
        match = re.fullmatch(r"(\d{3})_save\.bin", path.name, re.IGNORECASE)
        index_path = path.parent / "info.bin"
        if match and index_path.is_file():
            index = index_path.read_bytes()
            slot = int(match[1])
            if not 1 <= slot <= 100:
                raise ValueError("CLE 列表槽位应为 001..100")
            if len(index) != CLE_INFO_SIZE:
                raise ValueError("CLE info.bin 大小错误")
            base = 0x1BC + (slot - 1) * 0x678 + 2 * 0x228
            if struct.unpack_from("<I", index, base)[0]:
                meta.chapter = _text(index[base + 0x84:base + 0x104], "utf-8")
                meta.subtitle = _text(index[base + 0x104:base + 0x184], "utf-8")
                meta.location = _text(index[base + 0x184:base + 0x204], "utf-8")
                year, month, _, day, hour, minute, second, ms = struct.unpack_from("<8H", index, base + 0x214)
                meta.timestamp = datetime(year, month, day, hour, minute, second, ms * 1000)
                meta.clear = bool(struct.unpack_from("<I", index, base + 0x224)[0])
        icon = path.with_suffix(".ico")
    else:
        match = re.fullmatch(r"data(\d{4})", path.parent.name, re.IGNORECASE)
        meta.clear = bool(match and 201 <= int(match[1]) <= 210)
        info_path = path.parent / "info.txt"
        if info_path.is_file():
            raw = info_path.read_bytes()
            title = _text(raw[:0x80], "cp936")
            parts = re.split(r"[　\s]+", title.strip())
            meta.chapter = parts[0]
            meta.subtitle = "　".join(parts[1:-1]).strip("～~")
            detail = _text(raw[0x80:0x480], "cp936")
            meta.location = detail.split("PlayTime", 1)[0].strip()
            meta.timestamp = datetime.strptime(_text(raw[0x480:0x491], "ascii"), "%Y/%m/%d %H:%M")
        icon = path.parent / "icon0.png"
    if icon.is_file():
        meta.icon = icon.read_bytes()
    return meta


def nisa_info(data, meta):
    buf = bytearray(0x491)
    difficulty = DIFFICULTIES_ZH[data[DIFFICULTY_OFFSET]]
    subtitle = f"～{meta.subtitle}～" if meta.subtitle else ""
    title = f"{meta.chapter}　{subtitle}　{difficulty}"
    seconds = struct.unpack_from("<I", data, 0x19C84)[0]
    detail = f"{meta.location}  PlayTime {seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"
    for character in struct.unpack_from("<8H", data, 0x1AFE0):
        if character < len(CHARACTERS):
            level = struct.unpack_from("<H", data, 0x9C + character * 0x34)[0]
            detail += f"\n  {CHARACTERS[character]}        Lv{level:3d}"
    _put_text(buf, 0, 0x80, title, "cp936")
    _put_text(buf, 0x80, 0x400, detail, "cp936")
    _put_text(buf, 0x480, 0x11, meta.timestamp.strftime("%Y/%m/%d %H:%M"), "ascii")
    return bytes(buf)


def cle_info(existing, slot, data, meta):
    if not 1 <= slot <= 100:
        raise ValueError("CLE 目标槽位应为 001..100")
    if existing is not None and len(existing) != CLE_INFO_SIZE:
        raise ValueError("CLE info.bin 大小错误")
    buf = bytearray(existing) if existing is not None else bytearray(CLE_INFO_SIZE)
    for language, title in enumerate(TITLES):
        if existing is None:
            base = language * 0x94
            struct.pack_into("<I", buf, base, 1)
            _put_text(buf, base + 4, 0x80, title)
            buf[base + 0x84:base + 0x94] = _systemtime(meta.timestamp)
        base = 0x1BC + (slot - 1) * 0x678 + language * 0x228
        struct.pack_into("<I", buf, base, 1)
        _put_text(buf, base + 4, 0x80, title)
        _put_text(buf, base + 0x84, 0x80, meta.chapter)
        _put_text(buf, base + 0x104, 0x80, meta.subtitle)
        _put_text(buf, base + 0x184, 0x80, meta.location)
        _put_text(buf, base + 0x204, 0x10, DIFFICULTIES[data[DIFFICULTY_OFFSET]])
        buf[base + 0x214:base + 0x224] = _systemtime(meta.timestamp)
        struct.pack_into("<I", buf, base + 0x224, int(meta.clear))
    return bytes(buf)
