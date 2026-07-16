"""Discover NISA Ao save slots without depending on Tkinter."""

from __future__ import annotations

import ctypes
import os
import re
import uuid
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


_SLOT_PATTERN = re.compile(r"^data(\d{4})$", re.IGNORECASE)
_SAVED_GAMES_FOLDER_ID = uuid.UUID("4c5c32ff-bb9d-43b0-b5b4-2d72e54eaaa4")


class _Guid(ctypes.Structure):
    _fields_ = (
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    )

    @classmethod
    def from_uuid(cls, value: uuid.UUID) -> "_Guid":
        raw = value.bytes_le
        return cls(
            int.from_bytes(raw[0:4], "little"),
            int.from_bytes(raw[4:6], "little"),
            int.from_bytes(raw[6:8], "little"),
            (ctypes.c_ubyte * 8)(*raw[8:]),
        )


@dataclass(frozen=True)
class SaveSlotEntry:
    slot: int
    path: Path
    size: int
    modified: float
    status: str

    @property
    def slot_name(self) -> str:
        return f"data{self.slot:04d}"

    @property
    def modified_text(self) -> str:
        return datetime.fromtimestamp(self.modified).strftime("%Y-%m-%d %H:%M")

    @property
    def size_text(self) -> str:
        return f"{self.size / 1024:.1f} KiB"


def saved_games_folder() -> Path:
    """Return the Windows Saved Games known folder, with a portable fallback."""
    fallback = Path.home() / "Saved Games"
    if os.name != "nt":
        return fallback

    path_ptr = ctypes.c_wchar_p()
    folder_id = _Guid.from_uuid(_SAVED_GAMES_FOLDER_ID)
    try:
        shell32 = ctypes.windll.shell32
        shell32.SHGetKnownFolderPath.argtypes = (
            ctypes.POINTER(_Guid),
            wintypes.DWORD,
            wintypes.HANDLE,
            ctypes.POINTER(ctypes.c_wchar_p),
        )
        shell32.SHGetKnownFolderPath.restype = ctypes.c_long
        result = shell32.SHGetKnownFolderPath(
            ctypes.byref(folder_id), 0, None, ctypes.byref(path_ptr)
        )
        if result != 0 or not path_ptr.value:
            return fallback
        return Path(path_ptr.value)
    except (AttributeError, OSError):
        return fallback
    finally:
        if path_ptr.value:
            try:
                ctypes.windll.ole32.CoTaskMemFree(
                    ctypes.cast(path_ptr, ctypes.c_void_p)
                )
            except (AttributeError, OSError):
                pass


def default_ao_save_root(saved_games: Path | str | None = None) -> Path:
    base = Path(saved_games) if saved_games is not None else saved_games_folder()
    return base / "FALCOM" / "Ao"


def discover_save_slots(
    root: Path | str,
    validator: Callable[[Path], bool] | None = None,
) -> list[SaveSlotEntry]:
    """Find ``dataNNNN/savedata.dat`` entries, sorted by numeric slot ID."""
    root_path = Path(root)
    if not root_path.is_dir():
        return []

    entries: list[SaveSlotEntry] = []
    try:
        children = tuple(root_path.iterdir())
    except OSError:
        return []

    for folder in children:
        match = _SLOT_PATTERN.fullmatch(folder.name)
        if match is None or not folder.is_dir():
            continue
        save_path = folder / "savedata.dat"
        if not save_path.is_file():
            continue
        try:
            stat = save_path.stat()
        except OSError:
            continue

        status = "unchecked"
        if validator is not None:
            try:
                status = "valid" if validator(save_path) else "invalid"
            except (OSError, RuntimeError, ValueError):
                status = "invalid"
        entries.append(
            SaveSlotEntry(
                slot=int(match.group(1)),
                path=save_path,
                size=stat.st_size,
                modified=stat.st_mtime,
                status=status,
            )
        )

    return sorted(entries, key=lambda entry: entry.slot)


SAVE_BROWSER_TRANSLATIONS = {
    "zh_cn": {
        "存档列表": "存档列表", "选择目录": "选择目录", "刷新列表": "刷新列表",
        "加载选中": "加载选中", "槽位": "槽位", "状态": "状态",
        "修改时间": "修改时间", "大小": "大小", "有效": "有效",
        "无效": "无效", "未校验": "未校验", "未找到存档": "未找到存档",
        "已识别 {count} 个存档": "已识别 {count} 个存档",
        "隐藏存档列表": "隐藏存档列表", "显示存档列表": "显示存档列表",
        "选择 Ao 存档目录": "选择 Ao 存档目录",
        "请先选择一个存档": "请先选择一个存档", "切换存档": "切换存档",
        "切换存档会放弃当前尚未保存的界面修改。是否继续？": "切换存档会放弃当前尚未保存的界面修改。是否继续？",
    },
    "en": {
        "存档列表": "Save Slots", "选择目录": "Choose Folder", "刷新列表": "Refresh",
        "加载选中": "Load Selected", "槽位": "Slot", "状态": "Status",
        "修改时间": "Modified", "大小": "Size", "有效": "Valid",
        "无效": "Invalid", "未校验": "Unchecked", "未找到存档": "No saves found",
        "已识别 {count} 个存档": "Found {count} saves",
        "隐藏存档列表": "Hide Save List", "显示存档列表": "Show Save List",
        "选择 Ao 存档目录": "Choose the Ao save folder",
        "请先选择一个存档": "Select a save first", "切换存档": "Switch Save",
        "切换存档会放弃当前尚未保存的界面修改。是否继续？": "Switching saves discards any unsaved UI changes. Continue?",
    },
    "ja": {
        "存档列表": "セーブ一覧", "选择目录": "フォルダー選択", "刷新列表": "更新",
        "加载选中": "選択データを開く", "槽位": "スロット", "状态": "状態",
        "修改时间": "更新日時", "大小": "サイズ", "有效": "有効",
        "无效": "無効", "未校验": "未確認", "未找到存档": "セーブデータが見つかりません",
        "已识别 {count} 个存档": "{count} 件のセーブを検出",
        "隐藏存档列表": "一覧を隠す", "显示存档列表": "一覧を表示",
        "选择 Ao 存档目录": "Ao のセーブフォルダーを選択",
        "请先选择一个存档": "セーブデータを選択してください", "切换存档": "セーブ切替",
        "切换存档会放弃当前尚未保存的界面修改。是否继续？": "セーブを切り替えると未保存の画面上の変更は失われます。続行しますか？",
    },
}
