# Ao monster notebook completion flags

Updated: 2026-10-26. Scope: NISA/CLE Ao only.

## Binary evidence

Each serialized notebook entry is 8 bytes: u32 monster code, then four bytes:

| Entry offset | Editor field | Meaning relevant to completion |
|---|---|---|
| +4 | flag | Defeat counter; not a completion requirement |
| +5 | resistance | Seven elemental observation flags; bit 0 is Earth |
| +6 | stats | Low seven information flags; bit 7 selects higher-element requirements |
| +7 | get_item | Bits 4/5 mark existing drops; bits 0/1 mark observed drops |

NISA executable SHA-256:
`F55840B551C5C214272F46E950922A58A57F8F91A4297F32FE99A3F786A33C61`.

- `0x1404772F1..0x140477377`: notebook checkmark branch.
- `0x140472A20..0x140472A9E`: registered/complete count using the same predicate.
- `0x140475B2A..0x140475B49`: test entry[5] against `1 << element_index`;
  if present, read the corresponding u16 attribute rate at status +0x5E.
  Missing observation branches to unknown text at `0x140475C0B`.
- The rate order is Earth, Water, Fire, Wind, Time, Space, Mirage; the loop
  begins at element_index 0. This confirms the Earth bit independently of
  the BZH editor's labels.

Retained unpacked CLE executable SHA-256:
`4D229326C4088FDF4AC4C17474E086358C2ECEE462E7D411FA897277E1A8371D`.

- `0x140183BF4..0x140183C3D`: same completion predicate.
- `0x1401C3738..0x1401C3775`: complete-count path using the same conditions.

These addresses are build-specific and are not runtime patch targets.

## Exact completion condition

Let E, S, D be entry bytes +5, +6, +7:

```text
information_ok = (S & 0x7F) == 0x7F
element_mask = 0x7F if (S & 0x80) else 0x0F
elements_ok = (E & element_mask) == element_mask
drop1_ok = not (D & 0x10) or (D & 0x01)
drop2_ok = not (D & 0x20) or (D & 0x02)
complete = information_ok and elements_ok and drop1_ok and drop2_ok
```

The previous rule ignored E and required D == 0xFF. That both accepted
missing-Earth entries and rejected complete entries without both drop types.

## Legacy write defect and corrected behavior

BZH `bzh_ank_se_savedata_manual.h` writes flag=0x08 (line 172) and clears
resistant_code bit 0 (line 206). This produces `08 FE FF FF` with Earth
unobserved under NISA/CLE. It must no longer be accepted as complete.

Completing an existing entry keeps its counter, unknown bits, higher-element
marker and drop-existence flags. It sets the seven observation bits in E/S
and both drop-observation bits in D. Already-complete entries are unchanged.
Duplicates retain separate counters/flags and their original order.

New entries start as `00 7F 7F 03`: no fabricated defeats, higher-element
marker or drop-existence flags. All element/information/drop observations
are set. The game supplies existence metadata on later encounters.

For the reported legacy value, the operation is exactly:
`08 FE FF FF` -> `08 FF FF FF` (one Earth observation bit changes).

## Verification boundary

Regression cases cover missing Earth, four/seven-element requirements,
conditional drop slots, counter/flag preservation, duplicates and the existing
audit path. Local complete CLE039 entries remain byte-identical; NISA0060
keeps its 147 existing complete entries when adding the remaining catalog.
27 focused tests pass, including the container regression. NISA/CLE fixture
round trips confirm the reported legacy payload is repaired by changing only
entry +5 bit 0. A hidden GUI check verifies the actual selected-entry button
changes Partial data to Full data for both formats and retains the counter.
Game-internal checks are statically corroborated in both editions. The
user confirmed the local repair is working before authorizing publication.
No original game save was modified by local verification.
