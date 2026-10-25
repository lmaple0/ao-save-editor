# CLE PC Kai Ao Save Format

Updated: 2026-10-26

## Implemented format

Only Ao/Trails to Azure is supported. CLE saves are one AES-128-CBC stream
with PKCS7 padding. The plaintext is a little-endian u32 length followed by
a 0x27448-byte payload. Three SHA-256 iterations of the existing CLE seed
derive the key (first 16 bytes) and fixed IV (last 16 bytes). Game-data assets
still use their own explicit IV prefix; that asset codec is separate.

The previous dual-region container model, 48/50-actor reservation and fixed
scene-command clearing patch were incorrect and have been removed.

| Region | NISA payload | CLE payload |
|---|---|---|
| Common prefix | 0..0x4B64 | 0..0x4B64 |
| Alignment | none | 0x4B64..0x4B68 |
| Scene thread | 0x4B64..0x4C04 | 0x4B68..0x4C10 |
| 128 actors | 0x4C04..0x19C04, stride 0x2A0 | 0x4C10..0x1AC10, stride 0x2C0 |
| Common tail | 0x19C04..0x26434 | 0x1AC10..0x27440 |
| Final 8 bytes | two u32 checksums | edition-owned trailer |

Each actor is a common 0x20-byte header and four threads. NISA threads are
0xA0 bytes; CLE threads are 0xA8. Shared fields are NISA [0,0x3C) → CLE
[0,0x3C), and NISA [0x3C,0x96) → CLE [0x40,0x9A).
Cross-edition export initializes edition-only bytes to zero. Same-format CLE
writes start from the original complete payload and retain every unmapped
byte, including the prefix alignment, thread-only bytes and trailer.

## Editor integration

- ao_save_container.py decrypts/encrypts the complete file.
- ao_save_formats.py maps the complete Ao payload; SaveData.data always has
  the 0x2643C-byte NISA layout and a valid recalculated checksum on load.
- Existing character, equipment/orbment, inventory and progress editors use
  the same offsets for both editions.
- SaveData.save writes the requested container; SaveData.export additionally
  writes list metadata and available source thumbnails.
- NISA/CLE sidebar discovery remains separate and counts both sources.
- CLE difficulty comes from normalized 0x1F36D. Chapter 7 is not a clear flag.
  Clear status comes from source CLE info.bin or NISA data0201..data0210.
- Missing location metadata is left empty; the source file timestamp is used
  when no original index timestamp is supplied. No fake screenshot is made.
- Existing target CLE info.bin entries outside the exported slot are retained.
  Source message logs are retained if supplied; otherwise NISA receives an
  explicit empty message log. Conversion cannot recover missing source logs.
- Standalone system.bin/record conversion is not exposed by this editor.

## Evidence and validation

The user-supplied zero_save_converter_package v2 includes Python/C# sources
for both games. Only its Ao format was implemented here. Normal payload
mapping matches the reviewed reference in both directions.

- CLE039: Mira 97300, DP 355, difficulty 2, inventory 595 entries.
- CLE039 no-change output is byte-identical; weapon/quartz editing changes
  only the requested decoded fields and preserves all edition-only bytes.
- NISA0003/0060/0120 maps match the reference; NISA0060→CLE→NISA is exact.
- 41 focused regression checks pass, including loadout transactions,
  orbment restrictions, difficulty, sidebar discovery and package contracts.
- Runtime candidates: CLE039→NISA data0134 and NISA data0060→CLE016.
  The user tested the converted saves in both games on 2026-10-26 and
  confirmed that the functionality is basically working. This is focused
  acceptance, not exhaustive coverage of every scene and save variant.

The independent audit and candidate regeneration scripts live in the local
research/ folder; executables, supplied third-party binaries and private save
samples are not runtime package dependencies.
