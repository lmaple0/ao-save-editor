# Ao no Kiseki / Trails to Azure Save Editor

[中文说明 / README_CN.md](README_CN.md)

A Python/Tkinter save editor for the NISA PC release of **Ao no Kiseki / Trails to Azure**.

This project adapts the offset tables and item definitions from [`424778940z/BZH_AO_NO_KISEKI_Savedata_Editor`](https://github.com/424778940z/BZH_AO_NO_KISEKI_Savedata_Editor) to NISA `savedata.dat` files. The key discovery is that the NISA save is zstd-compressed, not encrypted. After decompression it is `0x2643C` bytes and is compatible with the original BZH offsets.

## Important Version And Translation Notes

This editor was built and tested for the NISA PC release, **Trails to Azure**, whose executable/save layout differs from the older mainland Chinese PC release.

The in-editor Chinese item names and labels use the Joyoland/欢乐百世 Simplified Chinese PC release of **碧之轨迹** as the default runtime layer. Item names are keyed by save item ID and follow [Ouroboros/Falcom ItemNameMap.py](https://github.com/Ouroboros/Falcom/blob/master/ED7/Decompiler/GameData/ItemNameMap.py), alongside the original BZH editor data. The structured item index also preserves conservative CLE/Clouded Leopard Chinese variants for reference, but the GUI does not currently switch to them. The GUI supports a global Chinese/English/Japanese language switch for tabs, buttons, character labels, sepith labels, battle counters, achievements, appearance names, quick actions, and item/achievement names where matching localization data exists. Missing translations fall back to Chinese. These names may still differ from the NISA English text or community Simplified Chinese localization produced with [`J31why/zeroTool`](https://github.com/J31why/zeroTool). If you are playing NISA Trails to Azure with a zeroTool-based Chinese patch, treat this editor as a save-format tool first and a name database second.

## Features

- Directly open and save zstd-compressed NISA `savedata.dat` files.
- Automatically locate FALCOM/Ao through the Windows Saved Games known folder and list dataNNNN/savedata.dat slots with checksum status, modification time, size, folder switching, and safe single-save loading. The sidebar can be collapsed, and compact locale-specific tab titles avoid high-DPI truncation.
- Edit Mira, DP, medals, sepith, play time, and difficulty.
- Edit character stat snapshots for 11 characters.
- Edit character equipment and seven orbment slots with inventory-synchronized transactional writes. Dropdowns enforce weapon/slot categories, core uniqueness, duplicate-normal-quartz rules, and the NISA `t_orb` element locks derived from `t_quartz` primary elements.
- Edit party slots and 12 bonding values.
- Switch the GUI globally between Chinese, English, and Japanese for implemented labels and data names.
- Browse and search the full 713-item inventory table, replace an item by ID/name, and set any quantity from 0 to 99, with Chinese/English/Japanese item-name display where available.
- Edit all 24 learned-recipe flags through individual checkboxes or Select All/Clear All, with globally switched Joyoland Chinese, NISA English, and Falcom Japanese recipe names.
- View all 31 fishing-notebook entries with registration, maximum/natural size, catch count, and localized reward/bait names; edit registration or maximum size while reward and bait history remain read-only.
- Edit the NISA per-slot 56-bit achievement bitmap at `0x1F454-0x1F45A`, with unlocked-count display, all-unlock/all-lock buttons, and Chinese/English/Japanese achievement names.
- Batch-fill consumables, ingredients, books, fish, quartz, and equipment.
- Edit battle manual counters.
- Edit 12 fixed character appearance-resource slots with corrected raw NISA IDs, including early/late Wazy, Yin/Rixia, and intermission swimsuit variants.
- Browse and edit a 305-entry localized monster catalog with 75 location filters and diagnostics. A new read-only detail panel shows HP/EP/CP, full battle stats, elemental efficacy, status resistance, sepith and item drops, localized craft names/descriptions, and `ms/as` provenance. Details are generated from all 333 installed NISA `ms*.dat` files in each language, with identical numeric structures verified across locales.
- Use a save-independent, read-only Resource Index to search characters, monsters, `ms*.dat`, `as*.dat`, crafts, and action entries in Chinese, Japanese, or English. The index covers 36 characters, 305 save monsters, 333 status files, 276 action scripts, 1,052 crafts, and 4,171 non-empty action entries; every relation retains provenance/confidence, while unresolved craft references remain explicitly unclaimed.
- View read-only progress for 280 treasure chests across 44 maps; search localized map/item names, filter by map or missing status, and inspect chest coordinates, trigger coordinates, and trigger range. Localized locations are generated from installed NISA scenario MapIndex values and the three local 	_town._dt tables.
- Run a Chinese/English/Japanese read-only save audit covering size, checksum, difficulty, items, party IDs, appearance IDs, recipe mirrors, monster records, and reference-edition compatibility. It reports anomalies without repairing or writing them.
- Recalculate the BZH 32-bit additive save checksum before writing.
- Create a `.bak` backup when saving over an existing file.

## Current Implementation Notes

The latest review fixed several data-safety and localization bugs:

- Character stat edits now write `u32` only for HP/EXP fields and `u16` for level, EP, CP, STR, DEF, ATS, and ADF.
- Character stat entry edits now read the active entry value directly instead of looking up an invalid Tk variable name.
- Quick actions, item refresh, achievement lock/unlock, and monster-manual unlock now report a clear status when no save file is loaded.
- The global language switch no longer uses duplicate translation keys for sepith Time and play-time hours.
- Party slot labels and quick-action character names are refreshed through the global language selector.
- Monster records are parsed and rewritten as complete 8-byte records. Unknown and unselected records are preserved, and writes fail safely if capacity is insufficient. The four payload bytes are only classified against the verified full-data value `08 FE FF FF`; sub-bit meanings are not guessed.

Validation performed on the publish package:

- `py_compile` passes for both workspace and publish copies.
- Localization dictionaries were checked for duplicate keys.
- A sample save was loaded, item data was read/written, saved as zstd, and loaded again.
- CLI quick edit was tested on a temporary save copy with `--mira`, `--dp`, `--sepith max`, and `--max-like`.
- Recipe-book reads were verified against nine real progression saves with 0/1/6/8/12/13/15/18/18 recipes; a temporary copy also passed a 24-recipe write, checksum, zstd save, and reload roundtrip.
- A Windows Python 3.13 GUI smoke test verified all 24 checkboxes plus Chinese/English/Japanese tab and recipe-name switching.
- The monster catalog generator verifies 305/305 save codes, localized `ms*.dat` names, and localized locations (283 active and 22 commented upstream mappings; 302 scenario-derived and 3 local-town-name supplements); 23 unit tests cover localization, name/location search, location provenance, partial/duplicate/unknown diagnostics, selected writes, full-capacity protection, and the final record boundary.
- The monster-detail generator parses and numerically compares 333/333 files in all three locales, links 305/305 save monsters, and resolves action-script sources for 333/333 entries. Unexplained extensions in `ms60000/ms60001` are recorded only by size and hash. The 2.3 MB detail JSON is now loaded on first use.
- The reference-index generator independently and bounds-safely parses the three `t_name._dt` tables and effective `as*.dat` headers/action tables without disassembling or executing action instructions. It emits 6,173 nodes, 6,835 relations, and seven same-name candidate-variant groups. The 5.4 MB graph is lazy-loaded and an empty GUI search is capped at 500 rows.
- The chest generator verifies all 280 flags, 44 localized maps, and 93 NISA scenario files. Two local NISA sample saves both report 117/280 obtained chests, and the feature never writes save flags.
- All 125 unit tests pass, including four layout-contract checks for the `tools/` and `docs/` structure. Achievement regressions cover the known 47/56 bitmap, complete/unique IDs, localized-name matching, and the exact seven-byte write boundary. Eight user-identified party samples match their raw slot order; 122 valid local saves have no unknown party/appearance IDs, and validation leaves their hashes unchanged. Element-lock validation found zero conflicts across 128 valid local saves, and a hidden Windows Python 3.13 Tk smoke test confirmed that the GUI filters a locked slot to compatible quartz. The local save browser found 134 slots: 133 passed full decompression/checksum validation and the 80-byte data0255 entry was correctly marked invalid; scanning took about 530 ms.

The Codex bundled Python runtime lacks Tcl/Tk; GUI construction and language switching were instead smoke-tested with Windows Python 3.13.

## Localization Data

- `ao_item_i18n.json`: item names/descriptions matched by save item ID.
- `ao_item_index.json`: structured item metadata; `zh_joyoland` is the runtime Chinese default and `zh_cle` is a conservative reference layer.
- `ao_achievement_i18n.json`: localized achievement rows keyed by `game_achievement_id`; its `bitmap_part`/`bit` fields retain Joyoland system-save provenance and are not NISA per-slot positions. NISA bits follow `ao.exe` platform-table entries 1–56 (entry 0 is the aggregate achievement), then join to these IDs.
- `ao_magic_i18n.json`: English craft/orbal art rows from the supplied magic CSV. Its CSV row number is a reference row, not a confirmed save skill-slot ID; Japanese CSV text is preserved but marked for encoding review where needed.
- `ao_monster_reference.json`: generated by `tools/build_monster_reference.py`, which joins the save-code table and Ouroboros/Falcom identity layer with installed NISA `ms*.dat` names and localized scenario locations, without executing the upstream Python file. `tools/build_monster_locations.py` owns scenario scanning and localized MapIndex lookup.
- `ao_monster_details.json`: generated by `tools/build_monster_details.py` with an independent bounds-checked, read-only parser over all 333 installed NISA `ms*.dat` files per locale. It records source SHA-256 values and neither executes generated upstream Python nor redistributes raw game files.
- `ao_reference_graph.json`: generated by `tools/build_reference_graph.py` by joining the monster catalog, localized `t_name._dt`, 333 `ms` files, and effective localized `as` action tables. It keeps relative provenance paths and SHA-256 values; craft references that cannot be proven local remain unresolved research records.
- `ao_chest_reference.json`: generated by `tools/build_chest_reference.py` from the Ouroboros/Falcom RecordViewer flag/coordinate table, installed NISA scenario MapIndex values, localized `t_town._dt` tables, and the item-ID index. Original Joyoland labels and source line numbers remain as provenance.

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

Also thanks to [`Ouroboros/Falcom`](https://github.com/Ouroboros/Falcom/tree/master/ED7/Decompiler) for traceable ED7 formats, monster-status metadata, and decompiler tooling, and to [`J31why/zeroTool`](https://github.com/J31why/zeroTool) for the community localization tooling.

## Safety

Make a manual backup before editing game saves. Real save files (`*.dat`) are ignored by default and should not be committed.

See `docs/ao_save_editor_roadmap.md` for implemented modules and future ideas.
