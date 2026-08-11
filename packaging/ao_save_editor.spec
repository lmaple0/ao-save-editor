# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for the Windows GUI release."""

import os
from pathlib import Path


PACKAGE_ROOT = Path(SPEC).resolve().parent.parent
BUILD_MODE = os.environ.get("AO_SAVE_EDITOR_BUILD_MODE", "onefile").casefold()
if BUILD_MODE not in {"onefile", "onedir"}:
    raise ValueError(f"Unsupported AO_SAVE_EDITOR_BUILD_MODE: {BUILD_MODE}")

# Only files read by the runtime are bundled. Research, generator, and test
# assets deliberately stay out of the executable.
RUNTIME_DATA_FILES = (
    "ao_achievement_i18n.json",
    "ao_chest_reference.json",
    "ao_item_i18n.json",
    "ao_item_index.json",
    "ao_monster_details.json",
    "ao_monster_reference.json",
    "ao_reference_graph.json",
)

datas = [(str(PACKAGE_ROOT / name), ".") for name in RUNTIME_DATA_FILES]
ICON_PATH = PACKAGE_ROOT / "packaging" / "kea.ico"

a = Analysis(
    [str(PACKAGE_ROOT / "ao_save_editor.py")],
    pathex=[str(PACKAGE_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe_options = dict(
    name="AoSaveEditor",
    icon=str(ICON_PATH),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if BUILD_MODE == "onefile":
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], **exe_options)
else:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **exe_options)
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="AoSaveEditor",
    )
