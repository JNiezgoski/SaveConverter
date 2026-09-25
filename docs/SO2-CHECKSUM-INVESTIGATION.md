# SO2 checksum investigation — 2026-09-25

**Fol follow-up:** The checksum result below remains correct. The body is
zero-run compressed: Fol must be changed in the decoded state, not by writing
a u16/u32 at a fixed encoded offset. The genuine `28 00 00 01` decodes to 40;
the naive `88 13 00 01` edit decodes to 16,782,216 despite valid checksums.
See [Fol investigation, game-code evidence, and 5,000-Fol candidate](SO2-FOL-INVESTIGATION.md).
The 40-to-41 candidate described below happens to preserve the zero-run token;
it does not establish a general two-byte Fol setter.

## Result

The checksum formula in the older notes was incorrect. Disassembly of the actual
game's writer and both validators establishes these rules for an 8192-byte block:

```python
C = u16le(d, 0x21A)
marker = d[0x218:0x21A]       # normally 55 55
d[0x210:0x21A] = bytes(10)   # A u32, B u32, marker u16
B = sum(d[0:C])
write_u32le(d, 0x214, B)
A = sum(d[0x200:0x280])
write_u32le(d, 0x210, A)
d[0x218:0x21A] = marker
```

The game separately requires the signature and marker to be valid. `so2_valid()`
checks checksum agreement, not every condition required to load a save.

## Direct code evidence

Source: read-only inspection of `SaveGames/SCUS-94421_resume.sav` (DuckStation
state version 87). Its Zstandard frame at file offset `0x99CE` decompresses to
4,027,962 bytes. Main RAM starts at decompressed offset `0x1A62`; this was located
by matching the first 64 bytes of the disc's PS-X executable payload at RAM
`0x80010000`. The executable is ISO file `SCUS_944.21;1`, LBA 24, on Disc 1.

Relevant MIPS addresses in this state:

| Address | Behavior |
|---|---|
| `0x80081EBC` | Unsigned byte-sum helper: initializes accumulator to zero, uses `lbu`, sums exactly `a2` bytes beginning at `a1`, returns the sum in `v0`. |
| `0x80081800–0x80081834` | Writer: stores C, sums the entire buffer through C, stores B at header+`0x14`, sums 128 bytes at buffer+`0x200`, stores A with `sw` at header+`0x10`. |
| `0x80081C74–0x80081D08` | Header validator: compares 16-byte signature, requires marker `0x5555`, loads A with `lw`, zeros marker with `sh` and A with `sw`, sums exactly `0x80` header bytes, compares full-word A, restores A and marker. |
| `0x800819F4–0x80081A20` | Body validator: reads C at buffer+`0x21A`, saves B, zeros marker, A and B, sums C bytes from the beginning of the buffer, compares B. |
| `0x80037870–0x80037898` | Save I/O stage writes `0x5555` at header+`0x18`. |

Key header-validator instructions (including the call's delay slot):

```text
80081cc0 move  a1, s1          # header pointer
80081cc4 lw    s0, 0x10(s1)   # stored A, 32 bits
80081cc8 addiu a2, zero, 0x80 # 128-byte header
80081ccc sh    zero, 0x18(s1) # clear marker
80081cd0 jal   0x80081ebc     # byte sum
80081cd4 sw    zero, 0x10(s1) # clear all of A before call executes
80081cd8 addiu v1, zero, 0x5555
80081cdc sh    v1, 0x18(s1)
80081ce0 xor   v0, s0, v0
80081ce4 sltiu s2, v0, 1      # equality test
80081ce8 sw    s0, 0x10(s1)
```

## Why the old formulas appeared correct

For normal headers, the first six signature bytes (`STAR O`) sum to 425, and
the marker bytes (`55 55`) sum to 170. Thus the correct A also equals:

```text
sum(d[0x206:0x280], with A zeroed) + 255
```

The old formula instead included byte `d[0x280]`. Therefore:

```text
correct A - old A = 255 - d[0x280]
```

This explains both the old first-save discrepancy of 255 and the new discrepancy
of 252: the respective boundary bytes are 0 and 3. Late saves with `0xFF` at
that boundary conceal the error. The byte is outside the header checksum range.
No party-size-specific checksum algorithm is needed.

The old B formula omitted the first four bytes but included the marker. The
usual PS1 prefix `53 43 13 01` sums to 170, exactly equal to the marker's byte sum.
Those errors cancel for that prefix. They need not cancel for other prefixes.

A includes B's bytes. Keeping an old A after changing B does not preserve a valid
header, even if Fol itself lies outside A's range. The correction depends on the
change in the *sum of B's four bytes*, not necessarily B's numerical change.

## Save evidence

All paths below are relative to `C:/CodeTesting/StarOcean2/SaveGames`.

| Sample | Source | C | Fol u16 at `0x39A` | Stored A = corrected A | B |
|---|---|---|---:|---|---|
| A | `cards/_backup/card1-before-fol-fix4-20260925-011239.mcd`, S13 | `0x73B` | 40 | `0x242F` | `0x17D92` |
| B | `Star Ocean - The Second Story (USA)_1.mcd`, S14 | `0x711` | 90 | `0x2464` | `0x175FA` |
| C | Same live card, S15 | `0x710` | 210 | `0x245C` | `0x174F5` |

Block SHA-256 hashes, in the same order:

```text
634052bd5d7670acebb84c4040902c3daafcfeaec1c52bc07fbb48f2b200487f
fc529e2e7fa23aff8c2a257cf3b91d6ee4979cb5aa6bf2df08e40d79345353ab
ee3f800e0a0f333559b73780534a4b2d56ac5f604361c8be78e357179d08ca1e
```

The live S13 is **not the original sample A**: it now contains 5,000 Fol, B
`0x17E05`, and stale A `0x242F`. Its required A is `0x23A3`. The original 40-Fol
version survives in the backup above. This distinction matters when brute-forcing
against supposedly untouched examples.

A read-only audit of `.mcd`, `.mcs`, and `.gme` files found 159 distinct SO2 data
blocks (deduplicated by entire block). 154 match both corrected checksums. Five
fail: live S13; S13 in the `before-fol-fix5` and `before-fol-fix6` backups; and S03
in the `USA)_2.20260920-181543.mcd` and `USA)_2.20260920-182951.mcd` backups.
The two older S03 blocks fail B as well; their contents were not repaired.
This archive includes edited saves, so 154 matches are not 154 independent
game-written confirmations. The disassembly establishes the algorithm.

The live card's five active entries are single-block saves in physical slots
1, 2, 3, 4, and 6, all with size 8192, next link `0xFFFF`, and valid directory
XOR checksums. `chains()` maps the stored zero-based links correctly;
`read_saves()` extracts the correct block bytes without modifying them. No
chain or container discrepancy was found for these examples.

## Reproduction and controlled edit

```powershell
python -m unittest discover -s tests -v
python tools/audit_so2_checksums.py C:\CodeTesting\StarOcean2\SaveGames
```

The audit is read-only. A separate test card in this workspace,
`artifacts/so2-checksum/fol-41-test.mcd`, copies the original sample-A backup and
changes S13 from 40 to 41 Fol using the corrected signer. Relative to its source,
exactly three bytes change inside that block:

| Block offset | Before | After |
|---|---|---|
| `0x210` | `2F` | `30` |
| `0x214` | `92` | `93` |
| `0x39A` | `28` | `29` |

Expected A is `0x2430`, B is `0x17D93`; C and all directory bytes are unchanged.
No file under `SaveGames` was written. This candidate has not been loaded in-game;
the evidence is the game-code analysis, original-save matches, and byte-level
validation, not a claim of a completed emulator load test.
