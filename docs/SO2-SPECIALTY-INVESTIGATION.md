# SO2 Specialties

Investigation started 2026-09-25; purchase-code verification completed 2026-09-27.
The twelve party-wide skill-shop flags are now **code-verified**, including their skill-group
assignments, prices, and execution through the extracted resident MIPS interpreter. The earlier
mapping was correct. The historical purchase labeled "Sensibility 2" that changed bit 2 remains
an unexplained observation: the code establishes that this unlocks Technique 2, but cannot
establish why that purchase was reported under another name. See the reconciliation below.

These are the twelve Skill Shop tiers in [SO2-SKILLS-FULL.md](SO2-SKILLS-FULL.md), not the
separately derived character specialties. Each tier enables SP investment in a group of skills.

## Method

Every earlier attempt at this (the "33-byte flag run" and specialty-purchase diffs from earlier
in this session) used raw-byte diffing and produced 100-200+ changed bytes per test, dominated by
zero-run re-compression noise (see [SAVE-FORMAT.md](SAVE-FORMAT.md)'s compression note) — not
usable signal. Decoding both saves first with `so2_fol.py`'s `state()`/`decode()` and diffing the
*decoded* bytes instead dropped that to single digits. **All future before/after tests on this
save format should decode first.**

## VERIFIED: the specialty system

There are exactly **4 specialties**, each purchasable at **3 levels**, for **12 fixed flags total**
— confirmed by Codex tracing the actual purchase script in the game's MIPS code. The flags use
fixed IDs assigned by the game, not acquisition order (an early theory, now disproved by the code).

- **Decoded offset `0x1A3F`, bits 4-7**: "has reached level 1" (i.e. unlocked) for the 4
  specialties. Bits 0-3 unused (always 0 in every sample seen).
- **Decoded offset `0x1A40`, bits 0-3**: "has reached level 2" for the same 4 specialties, in the
  **same order** as `0x1A3F`'s bits 4-7 (just shifted down by 4 bit positions).
- **Decoded offset `0x1A40`, bits 4-7**: "has reached level 3" for the same 4 specialties, same
  order again.

The complete mapping below is verified against the script's fixed IDs, the independent
skill-availability table, and execution of the real purchase commit instructions. These are
independent purchased-tier flags, not a numeric level or an acquisition-order counter. Buying
one tier does not itself set the lower-tier flags.

| Tier | Global flag | Decoded byte | Bit | Mask | Base Fol cost |
|---|---|---|---:|---|---:|
| Knowledge 1 | `0x2bc` | `0x1a3f` | 4 | `0x10` | 300 |
| Sensibility 1 | `0x2bd` | `0x1a3f` | 5 | `0x20` | 400 |
| Technique 1 | `0x2be` | `0x1a3f` | 6 | `0x40` | 400 |
| Combat 1 | `0x2bf` | `0x1a3f` | 7 | `0x80` | 400 |
| Knowledge 2 | `0x2c0` | `0x1a40` | 0 | `0x01` | 1,500 |
| Sensibility 2 | `0x2c1` | `0x1a40` | 1 | `0x02` | 1,600 |
| Technique 2 | `0x2c2` | `0x1a40` | 2 | `0x04` | 1,600 |
| Combat 2 | `0x2c3` | `0x1a40` | 3 | `0x08` | 1,600 |
| Knowledge 3 | `0x2c4` | `0x1a40` | 4 | `0x10` | 2,700 |
| Sensibility 3 | `0x2c5` | `0x1a40` | 5 | `0x20` | 2,700 |
| Technique 3 | `0x2c6` | `0x1a40` | 6 | `0x40` | 3,600 |
| Combat 3 | `0x2c7` | `0x1a40` | 7 | `0x80` | 4,500 |

The prices above are read from the extracted shop scripts. The current local "Skill Shops"
table in SO2-SKILLS-FULL.md lists skills and towns, **not prices**. Its general reference to a
purchase counter is also superseded by the save-counter finding below.

```python
# Apply to the fully decoded state; re-encode and sign before writing a save.
TIER_BITS = {
    f"{name} {level}": (0x19E8 + flag // 8, flag % 8)
    for level in range(1, 4)
    for index, name in enumerate(("Knowledge", "Sensibility", "Technique", "Combat"))
    for flag in (0x2BC + 4 * (level - 1) + index,)
}
offset, bit = TIER_BITS[tier_name]
decoded[offset] |= 1 << bit
```

## Corrected: earlier wrong guesses

Two fields we guessed were specialty-related turned out not to be, once Codex traced the actual code:

- **Decoded offset `0x24`** is a general **save counter** (increments every time the game saves),
  not a specialty-purchase counter. It only *looked* correlated because we happened to save once
  per purchase in testing.
- **Decoded offset `0x10`** is used to **display playtime**, unrelated to specialties.
- **Decoded offset `0x198`** is the game's remembered **cursor position for which save box was last
  selected** in the load/save menu (UI state, not game data) — it tracked our own box navigation
  during testing (S14→S11), nothing to do with any purchase.

## LIKELY (strong evidence, not fully closed out)

- **Decoded offsets `0x1B58`-`0x1B82`** (~48 bytes near the very end of the `0x1B88`-byte decoded
  state): Codex traced the save serializer and confirmed this range is **saved beyond the portion
  the snapshot routine actually populates** — i.e. it's very likely genuinely unused/uninitialized
  trailing data, consistent with what the old raw-offset docs already flagged for this same region.
  Codex was still checking allocation/load behavior to fully close this out when it ran out of
  usage credits a second time; treat as LIKELY rather than fully VERIFIED.
- **Decoded offset `0x1880`**: appeared alongside `0x198` starting with the third test onward.
  Not yet traced in code — plausibly another UI/navigation counter given its correlation with
  `0x198`, but unconfirmed.
- Several bytes near Claude's character entry (`0x1750`, `0x1758`, `0x1760`, `0x1761`, `0x1769`,
  occasionally `0x1340`/`0x1341`) shift by small amounts on every specialty purchase test so far —
  presumed to be a recalculated derived stat (something like an effect total that changes once a
  character has access to a new specialty), not the unlock flag itself. Not traced in code.

## Reconciliation: mapping resolved, historical label discrepancy remains

The old SAVE-FORMAT open item called this a "Knowledge-vs-Sensibility" conflict. The actual
recorded conflict is **Sensibility 2 versus Technique 2**:

- Earlier "Knowledge lvl 2", S14 -> S13: `0x1A40: 00 -> 01`; matches Knowledge 2.
- Earlier "Sensibility lvl 2", S13 -> S12: `01 -> 03`; matches Sensibility 2.
- Later "Sensibility 2", S10 -> S09: `03 -> 07`; sets **Technique 2**, not Sensibility 2.
- Combat 2, S09 -> S08: `07 -> 0F`; matches Combat 2.
- Knowledge 3, S15 -> S14: `0F -> 1F`; matches Knowledge 3.
- Technique 3, S14 -> S13: `1F -> 5F`; matches Technique 3.

The real Technique 1 observation is reproduced exactly: flag `0x2BE` sets bit 6 at `0x1A3F`,
changing `30 -> 70`, with a 400-Fol deduction. The skill table identifies `0x2C1` with Danger
Sense/Playfulness/Perseverance/Poker Face and `0x2C2` with Craft/Writing/Animal Training/Mech
Knowledge. There is no acquisition-order remapping in the traced commit or availability check.
Controlled execution starting from `0x1A40=03` gives `03 -> 03` for `0x2C1` and `03 -> 07` for
`0x2C2`. Thus the earlier bit-1 interpretation agrees with the code; interpreting the later
bit-2 change as the Sensibility-2 unlock does not.

**We cannot honestly identify a data-entry error from this evidence.** The player explicitly
maintained the labels were accurate. The saved byte observations are preserved below, including
the anomaly. A menu/text mismatch, a different selected row, or a before/after pairing problem
cannot be distinguished without the original transaction context. The trace proves the flag's
meaning, not what was displayed or selected during that historical test. It does not justify
calling that observation disproven or silently relabeling it.

One clean test would settle the remaining discrepancy: at the **same guild as the anomalous
purchase**, load a save where `0x1A40` bits 1 and 2 are both clear; record the highlighted
**Sensibility 2** row and confirmation, buy only that tier, and save immediately to a new slot.
Decode the before/after pair. Expect bit 1 (`+02`) and availability of Danger Sense/Playfulness/
Perseverance/Poker Face. If bit 2 (`+04`) changes instead, preserve the town, menu recording,
card pair and RAM state: that would demonstrate a shop-specific selection/text mismatch and
identify the exact script/text variant to trace. Price alone cannot distinguish these tiers;
both have base cost 1,600 Fol.

## Disc and disassembly evidence (2026-09-27)

All binaries were **reused**, not newly extracted. Entry 2986 is the ordinary inventory shop:
its commit loop calls inventory insertion `0x8003C594`, and its Fol commit at `0x8007E900` is
not the skill-shop transaction. The latter is event bytecode interpreted by resident entry 2576.
Existing specialty artifacts supplied its script and the independent availability table.

| Source | Disc LBA | Load / location | Decoded size | SHA256 |
|---|---:|---|---|---|
| Resident entry 2576 | 30736 | `0x8002F810` | `0x4C7FC` | `6dec3950348b57068a85759f472ea7d5c92241d28b00ff4ea139ddd8dc1587cf` |
| Inspected shop entry 2986 | 36126 | `0x8007E000` | `0x3E2C` | `577a2482dc4532bdc70d9a7c6708f4133e6ae589c4e2704b39ac45909ff6b466` |
| Entry 3207, script part | 38691 | SLZ1 at archive-entry byte offset `0x1137C`; runtime pointer, not fixed RAM | `0xF000` | `30923618f001a29e257b02fa06762e16a16c7542fa90d42a821b4018dadc5ce8` |
| Skill availability entry 3014 | 36286 | `0x8007E000` | `0x31A5` | `3e345c0ab652387a23c3a8da259f3372a6c8ef6adaa0d793d36d0fdf4bc86c53` |

Entry 3207's cached script and entry 3014 were compared byte-for-byte with read-only Disc 1
SLZ decompression during this run. LBA refers to the ISO user-data stream inside raw 2352-byte
sectors (2048 bytes starting at sector byte 24), using tools/so2_disc_code.py. Entry 3207 starts
with a three-part container; its script is the second part, not an executable overlay.

The script contains repeated per-guild initialization records rather than a single twelve-row
MIPS item table. Each record stores a fixed flag in a local slot, pushes a base price, and calls
the price helper (`1400066A`, script offset `0x19C4`). That helper consults flags `0x2DF/0x2E0`
and can adjust the price; the commit receives the resulting price. Direct representative dump
(offsets are within the **decompressed script**, words are little-endian):

| Tier | Flag-word offset | Flag word | Following push-price word |
|---|---|---|---|
| Knowledge 1 | `0x4d04` | `000002BC` | `1200012C` |
| Sensibility 1 | `0x4d1c` | `000002BD` | `12000190` |
| Technique 1 | `0x4d34` | `000002BE` | `12000190` |
| Combat 1 | `0x4e18` | `000002BF` | `12000190` |
| Knowledge 2 | `0x4eb4` | `000002C0` | `120005DC` |
| Sensibility 2 | `0x4ecc` | `000002C1` | `12000640` |
| Technique 2 | `0x4fc8` | `000002C2` | `12000640` |
| Combat 2 | `0x4fe0` | `000002C3` | `12000640` |
| Knowledge 3 | `0x5190` | `000002C4` | `12000A8C` |
| Sensibility 3 | `0x507c` | `000002C5` | `12000A8C` |
| Technique 3 | `0x51a8` | `000002C6` | `12000E10` |
| Combat 3 | `0x50c4` | `000002C7` | `12001194` |

For example, `0x4D30: 21800010; 0x4D34: 000002BE; 0x4D38: 12000190` stores Technique 1's
flag and pushes 400. The shared purchase function is called by `140012FC`; script call targets
are word indices relative to the script body at `+0x1C`, so its entry is `0x4C0C`.
It accepts the selected fixed flag and computed price. `0x4C1C..0x4C58` checks ownership;
`0x4C5C..0x4CA0` obtains Fol (`D3`) and checks affordability before reaching the commit:

```text
script offset  word       operation
4CA4           0B800000   push local flag ID
4CA8           09800001   indirect addressing, stride 1
4CAC           0A000000   select global flag operand using that ID
4CB0           21030000   write flag operand
4CB4           00000001   value = 1
4CB8           51800004   multiply local price by following immediate
4CBC           FFFFFFFF   -1
4CC0           0B800004   push negative price
4CC4           D4800000   add signed amount to Fol
```

The flag is set **before** Fol is deducted. These are bytecode words, not MIPS instructions.
The real MIPS fetch/dispatch is `0x8006C358..0x8006C398`, using the opcode jump table at
`0x800739A0`. Opcode `21` enters `0x8006CD48`; its flag-write arm executes:

```text
8006CE54 lw    v0,10(s1)      ; pointer to immediate value
8006CE5C lw    v0,0(v0)
8006CE64 beqz  v0,8006CED4    ; clear arm for zero, set arm otherwise
8006CE68 and   v0,s0,s4      ; local/global operand selection, delay slot
...
8006CEB0 lui   a0,8007
8006CEB4 lw    a0,5704(a0)   ; global flag-buffer pointer
8006CEB8 sra   v0,v0,3       ; flag ID / 8
8006CEBC addu  a0,a0,v0
8006CEC0 andi  v0,s0,7       ; flag ID % 8
8006CEC4 lbu   v1,0(a0)
8006CEC8 sllv  v0,s7,v0      ; s7 = 1
8006CECC j     8006CF40
8006CED0 or    v1,v1,v0      ; delay slot
8006CF40 sb    v1,0(a0)
```

Extended opcode dispatch `0x8006241C` uses table `0x8007359C`; `D3` maps to `0x80063F1C`
(Fol read), `D4` to `0x80063F38` (signed addition). `D4800000` pops its amount through
`0x80068DB8` into scratchpad, then executes:

```text
80063F78 lui   t0,8007
80063F7C lw    t0,5270(t0)
80063F80 lw    v1,0(s2)      ; signed amount from script
80063F84 lw    v0,18(t0)
80063F8C addu  a3,v0,v1
80063F90 bgez  a3,80063FA0   ; otherwise store zero
...
80063FC0 j     80064F08      ; after upper-bound checks
80063FC4 sw    a3,18(t0)     ; commit full-word Fol, delay slot
```

Global flag RAM is separate from the first decoded chunk. Snapshot routine `0x80055FC8`
gets resource `0xE`, copies `0x2A0` bytes of context, then at `0x80056090..0x80056128` copies
`0x170` bytes from `[0x80075704]` to resource-E `+0x2A0`. The save serializer places resource E
at decoded `0x1748` (see Fol/inventory investigations). Thus flags begin at `0x1748+0x2A0 =
0x19E8`, and ID `0x2BE` gives `0x19E8+0x57 = 0x1A3F`, bit 6.

### Independent name/group cross-check

Entry 3014's availability routine `0x8007E6BC` searches five-byte skill groups at `0x80081168`
(file offset `0x3168`); `0x8007E700..0x8007E718` computes group index `floor(position/5)` and
calls resident flag reader `0x80055ECC` with `0x2BC+group`. The table contains one-based skill
IDs (subtract one for SAVE-FORMAT's skill index); zero pads short groups:

```text
flag   raw five bytes (hex)       group identified by contained skills
2BC    06 05 11 00 00             Knowledge 1
2BD    12 08 0C 1C 00             Sensibility 1
2BE    1E 10 13 01 00             Technique 1
2BF    21 22 29 2B 00             Combat 1
2C0    04 02 0E 00 00             Knowledge 2
2C1    0D 1A 0B 1D 00             Sensibility 2
2C2    07 09 14 1F 00             Technique 2
2C3    23 2C 25 26 00             Combat 2
2C4    17 0F 19 00 00             Knowledge 3
2C5    1B 18 0A 00 00             Sensibility 3
2C6    16 03 15 20 00             Technique 3
2C7    2A 27 24 28 2D             Combat 3
```

This supplies names independently of the disputed purchase labels; the full correspondence
matches the skill groups already listed in SO2-SKILLS-FULL.md. It is a skill-availability lookup,
not the purchase price table. The historical guild's exact rendered menu text was not recovered.

### Execution and reproduction

```powershell
python tools/so2_specialty_evidence.py
python -m unittest discover -s tests -v
```

The helper executes the original script bytes `0x4CA4..0x4CC8` through the extracted resident
MIPS opcode dispatch, OR/store, price-negation and Fol instructions. It supplies a selected
flag and base price read from the script records, and stops at the next bytecode boundary after
the commit. No flag/Fol operation is replaced by a Python hook. Hooks only initialize registers
and resume/stop at interpreter boundaries; dialogue, selection, price adjustment, ownership
and affordability checks are outside this isolated successful-tail execution. Branch delay
slots execute; loads are immediate. Scratchpad is aliased to unused harness memory at zero.
This is a bounded instruction test, not a new emulator/game-load test.

Results: **38 executions passed**, comparing the whole reconstructed decoded state and
checking the allowed write regions:

- Twelve runs against the preserved real `S15.decoded` state, independently reset each time:
  SHA256 `8f457cf6feac4fd96fe8fb2cef99b8e1698f23f43921db3b0ebf86d020c2ce40`, flags `30 00`,
  Fol 999,999,999. This is the earlier captured artifact, not an assertion about today's live S15.
- Twelve runs against the checksum-valid S13 Fol candidate documented in the Fol investigation
  (5,000 Fol, flags `30 00`). Its card/block/decoded hashes are in the report.
- Twelve controlled runs with only the twelve tier flags cleared in a copy, to expose every bit.
- Two controlled runs from `0x1A40=03`: Sensibility 2 leaves `03`; Technique 2 produces `07`.

For the real snapshot: Technique 1 `30 00 -> 70 00`, Combat 1 `30 00 -> B0 00`, Knowledge 2
`30 00 -> 30 01`, Sensibility 2 `30 00 -> 30 02`, Technique 2 `30 00 -> 30 04`, Knowledge 3
`30 00 -> 30 10`, Technique 3 `30 00 -> 30 40`. Knowledge/Sensibility 1 were already present,
so their real-state runs are idempotent flag writes; the cleared-copy runs separately expose
bits 4/5. Only Fol and the expected flag byte change. All 28 existing unit tests also pass.

Machine-readable rows, prices, all per-run byte changes, script offsets and hashes:
[report.json](../artifacts/so2-specialty/verified/report.json). Instruction bytes and focused
listings: [evidence.asm](../artifacts/so2-specialty/verified/evidence.asm).
All writes stayed in SaveConverter; nothing under StarOcean2/SaveGames was modified.

## Bonus lead for future work

Codex located the game's general flag storage while tracing this: **global flags start at decoded
offset `0x19E8`**, and these specialty purchases correspond to global flag IDs starting at `0x2BC`.
This is very likely the same flag system the still-open **story/event flags** investigation
(see [SAVE-FORMAT.md](SAVE-FORMAT.md)'s open items) has been looking for — worth pointing a future
Codex investigation at `0x19E8`+ directly instead of diffing raw save-file regions.

## Raw test data

| Test | Before → After box | Fol Δ | `0x1A3F` | `0x1A40` |
|---|---|---:|---|---|
| Technique 1 (new) | S15 → S14 | −400 | `0x30`→`0x70` (bit 6) | — |
| Knowledge lvl 2 | S14 → S13 | (paid) | — | `0x00`→`0x01` (bit 0) |
| Sensibility lvl 2 | S13 → S12 | (paid) | — | `0x01`→`0x03` (bit 1) |
| Combat 1 (new) | S12 → S11 | (paid) | `0x70`→`0xF0` (bit 7) | — |
| "Sensibility 2" (player-labeled) | S10 → S09 | (paid) | — | `0x03`→`0x07` (bit 2 — see contradiction above) |
| Combat lvl 2 | S09 → S08 | (paid) | — | `0x07`→`0x0F` (bit 3, matches) |
| Knowledge 3 | (new session) S15 → S14 | (paid) | — | `0x0F`→`0x1F` (bit 4, matches) |
| Technique 3 | S14 → S13 | (paid) | — | `0x1F`→`0x5F` (bit 6, matches) |

These eight recorded purchases were made on the same card during this session; box contents get reorganized
often during play, so check `saveconv.py list` for current state rather than assuming these box
numbers still hold this data.
