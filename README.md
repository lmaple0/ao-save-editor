# Ao no Kiseki / Trails to Azure Save Editor

[中文说明 / README_CN.md](README_CN.md)

A Python/Tkinter save editor for the NISA PC release of **Ao no Kiseki / Trails to Azure**.

This project adapts the offset tables and item definitions from [`424778940z/BZH_AO_NO_KISEKI_Savedata_Editor`](https://github.com/424778940z/BZH_AO_NO_KISEKI_Savedata_Editor) to NISA `savedata.dat` files. The key discovery is that the NISA save is zstd-compressed, not encrypted. After decompression it is `0x2643C` bytes and is compatible with the original BZH offsets.

## Important Version And Translation Notes

This editor was built and tested for the NISA PC release, **Trails to Azure**, whose executable/save layout differs from the older mainland Chinese PC release.

The in-editor Chinese item names and labels are taken from the Joyoland/欢乐百世 Simplified Chinese PC release of **碧之轨迹** and the original BZH editor data. They may not perfectly match the NISA English text, nor the community Simplified Chinese localization produced with [`J31why/zeroTool`](https://github.com/J31why/zeroTool). If you are playing NISA Trails to Azure with a zeroTool-based Chinese patch, treat this editor as a save-format tool first and a name database second.

## Features

- Directly open and save zstd-compressed NISA `savedata.dat` files.
- Edit Mira, DP, medals, sepith, play time, and difficulty.
- Edit character stat snapshots for 11 characters.
- Edit party slots and 12 bonding values.
- Browse, search, and rewrite the full 713-item inventory table.
- Batch-fill consumables, ingredients, books, fish, quartz, and equipment.
- Toggle the 7-byte achievement bitmap, with all-unlock/all-lock buttons.
- Edit battle manual counters.
- Change 12 character display model slots.
- Unlock all monster manual records using the real BZH monster code table.
- Recalculate the BZH 32-bit additive save checksum before writing.
- Create a `.bak` backup when saving over an existing file.

## Save Format Notes

- NISA compressed save size seen in testing: around 4.6 KB.
- Decompressed size: `156,732` bytes (`0x2643C`).
- User save checksum fields:
  - `0x26434`: savedata additive checksum.
  - `0x26438`: size checksum.
- The checksum is not CRC32. It follows the BZH additive algorithm from `bzh_ank_se_savedata_checksum.h`.
- Character HP/STR/DEF/ATS/ADF values are save snapshots and may be recalculated by the game after loading.

Typical NISA save path:

```text
C:/Users/<you>/Saved Games/FALCOM/Ao/dataXXXX/savedata.dat
```

## Requirements

- Python 3.10+
- `zstandard`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

GUI mode:

```bash
python ao_save_editor.py
```

CLI quick edits:

```bash
python ao_save_editor.py savedata.dat --mira 9999999 --sepith max --dp 400 --max-chars all --max-like
```

## Credits

Special thanks to [`424778940z/BZH_AO_NO_KISEKI_Savedata_Editor`](https://github.com/424778940z/BZH_AO_NO_KISEKI_Savedata_Editor), the original Qt/C++ save editor whose offset tables, checksum reference, item IDs, and monster manual code data made this NISA adaptation possible.

Also thanks to [`J31why/zeroTool`](https://github.com/J31why/zeroTool) for the localization tooling used by the community around the NISA Crossbell releases.

## Safety

Make a manual backup before editing game saves. Real save files (`*.dat`) are ignored by default and should not be committed.

See `ao_save_editor_roadmap.md` for implemented modules and future ideas.
