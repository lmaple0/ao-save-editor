# CLE PC Kai Save Format Research

Date: 2026-07-05

## 中文结论

当前这个 CLE PC Kai 版 `039_save.bin` 不能直接适配现有 NISA `savedata.dat` 编辑逻辑，也暂时不能实现 NISA/CLE 双向转换。

关键原因不是偏移表缺失，而是 CLE 样本看起来是加密或封包后的高熵数据：它没有 NISA 的 zstd magic，无法 zstd 解压，直接按 NISA 明文偏移读取时校验和不成立，也找不到 NISA 明文中的典型字段模式。

值得注意的是：`0x27450 - 0x1014 = 0x2643C`，刚好等于 NISA 解压后的明文存档大小。这说明 CLE 文件可能是 `0x1014` 字节头/元数据加一个 `0x2643C` 字节的存档主体。但这个主体仍然是高熵状态，说明还需要解密或逆向封包算法。

本轮已给编辑器加入 BZH checksum 校验，避免把 CLE `.bin` 误识别成 raw NISA 存档并写坏。

Sample: `tools/ao_save_editor/data/samples/039_save.bin`
Companion image: `tools/ao_save_editor/data/samples/039_save.ico`

## Summary

The provided CLE PC Kai save sample is not directly compatible with the current NISA `savedata.dat` loader.

The NISA PC save used by this editor is a zstd-compressed stream. After decompression it is `0x2643C` bytes and validates with the BZH additive checksum at `0x26434` and `0x26438`.

The CLE sample is `0x27450` bytes, has no zstd magic, has near-random entropy across the whole file, and does not contain recognizable NISA plaintext offsets or checksum fields. It should be treated as an encrypted/containerized save, not as a raw NISA save.

## Observations

| Item | NISA sample | CLE sample |
|---|---:|---:|
| File | `ao_savedata.dat` | `039_save.bin` |
| File size | about 4.6 KB compressed | `160,848` bytes (`0x27450`) |
| Magic | zstd `28 B5 2F FD` | none |
| Decompressed/plain size | `156,732` bytes (`0x2643C`) | not available yet |
| Entropy | compressed high entropy | `~7.9989`, high entropy across blocks |
| BZH checksum validation | passes after zstd decompression | fails if interpreted as raw NISA data |
| Known NISA offset patterns | present after decompression | not found |

A notable size relation exists:

- `0x27450 - 0x1014 = 0x2643C`

This suggests the CLE file may contain a `0x1014`-byte header/metadata region plus a `0x2643C`-byte save payload. However, the possible payload region is still high entropy and does not validate as plaintext. This points to encryption or another transformation over the payload.

## Safety Fix Added

The editor now validates the BZH checksum before accepting any non-zstd/raw candidate. This prevents encrypted CLE `.bin` files from being accidentally opened as raw NISA saves and then overwritten as zstd NISA saves.

## Conversion Feasibility

Current status: not implementable from this single sample alone.

Likely conversion pipeline if CLE encryption/container is solved:

1. Decode/decrypt CLE `039_save.bin` into a `0x2643C` plaintext payload.
2. Confirm whether the plaintext payload uses the same BZH/NISA offsets.
3. For CLE -> NISA: recalculate BZH checksum, zstd-compress plaintext, write as `savedata.dat`.
4. For NISA -> CLE: zstd-decompress NISA save, recalculate checksum, re-encrypt/repack using the CLE container format.

Step 1 and step 4 are currently missing.

## What Is Needed Next

To continue, one of the following is needed:

- CLE executable reverse engineering to locate save load/save routines and encryption keys or algorithms.
- Multiple CLE saves from the same slot with controlled small changes, for differential analysis.
- A known decrypted CLE plaintext save, if available.
- Any community documentation or tooling that can already unpack/repack CLE Kai PC save `.bin` files.

Until then, the editor should reject CLE `.bin` files instead of attempting conversion.
