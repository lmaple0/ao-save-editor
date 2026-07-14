# Ao no Kiseki / Trails to Azure Save Editor

[中文说明 / README_CN.md](README_CN.md)

A Python/Tkinter save editor for the NISA PC release of **Ao no Kiseki / Trails to Azure**.

This project adapts the offset tables and item definitions from [`424778940z/BZH_AO_NO_KISEKI_Savedata_Editor`](https://github.com/424778940z/BZH_AO_NO_KISEKI_Savedata_Editor) to NISA `savedata.dat` files. The key discovery is that the NISA save is zstd-compressed, not encrypted. After decompression it is `0x2643C` bytes and is compatible with the original BZH offsets.

## Important Version And Translation Notes

This editor was built and tested for the NISA PC release, **Trails to Azure**, whose executable/save layout differs from the older mainland Chinese PC release.

The in-editor Chinese item names and labels use the Joyoland/欢乐百世 Simplified Chinese PC release of **碧之轨迹** as the default runtime layer, alongside the original BZH editor data. The structured item index also preserves conservative CLE/Clouded Leopard Chinese variants for reference, but the GUI does not currently switch to them. The GUI supports a global Chinese/English/Japanese language switch for tabs, buttons, character labels, sepith labels, battle counters, achievements, appearance names, quick actions, and item/achievement names where matching localization data exists. Missing translations fall back to Chinese. These names may still differ from the NISA English text or community Simplified Chinese localization produced with [`J31why/zeroTool`](https://github.com/J31why/zeroTool). If you are playing NISA Trails to Azure with a zeroTool-based Chinese patch, treat this editor as a save-format tool first and a name database second.

## Features

- Directly open and save zstd-compressed NISA `savedata.dat` files.
- Edit Mira, DP, medals, sepith, play time, and difficulty.
- Edit character stat snapshots for 11 characters.
- Edit party slots and 12 bonding values.
- Switch the GUI globally between Chinese, English, and Japanese for implemented labels and data names.
- Browse and search the full 713-item inventory table, replace an item by ID/name, and set any quantity from 0 to 65,535, with Chinese/English/Japanese item-name display where available.
- Toggle the 7-byte achievement bitmap, with all-unlock/all-lock buttons and Chinese/English/Japanese achievement-name display.
- Batch-fill consumables, ingredients, books, fish, quartz, and equipment.
- Edit battle manual counters.
- Change 12 character display model slots.
- Unlock all monster manual records using the real BZH monster code table.
- Recalculate the BZH 32-bit additive save checksum before writing.
- Create a `.bak` backup when saving over an existing file.

## Current Implementation Notes

The latest review fixed several data-safety and localization bugs:

- Character stat edits now write `u32` only for HP/EXP fields and `u16` for level, EP, CP, STR, DEF, ATS, and ADF.
- Character stat entry edits now read the active entry value directly instead of looking up an invalid Tk variable name.
- Quick actions, item refresh, achievement lock/unlock, and monster-manual unlock now report a clear status when no save file is loaded.
- The global language switch no longer uses duplicate translation keys for sepith Time and play-time hours.
- Party slot labels and quick-action character names are refreshed through the global language selector.

Validation performed on the publish package:

- `py_compile` passes for both workspace and publish copies.
- Localization dictionaries were checked for duplicate keys.
- A sample save was loaded, item data was read/written, saved as zstd, and loaded again.
- CLI quick edit was tested on a temporary save copy with `--mira`, `--dp`, `--sepith max`, and `--max-like`.

GUI launch was not verified inside the Codex bundled Python runtime because that runtime lacks Tcl/Tk. Use a normal Windows Python installation with Tkinter for GUI use.

## Localization Data

- `ao_item_i18n.json`: item names/descriptions matched by save item ID.
- `ao_item_index.json`: structured item metadata; `zh_joyoland` is the runtime Chinese default and `zh_cle` is a conservative reference layer.
- `ao_achievement_i18n.json`: achievement names/descriptions matched by save bitmap position and supplied game achievement ID.
- `ao_magic_i18n.json`: English craft/orbal art rows from the supplied magic CSV. Its CSV row number is a reference row, not a confirmed save skill-slot ID; Japanese CSV text is preserved but marked for encoding review where needed.

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
