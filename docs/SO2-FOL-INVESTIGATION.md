# SO2 Fol: zero-run compression, not a checksum problem

Investigation date: 2026-09-25. US PS1 game, Disc 1 code and supplied saves.

## Findings

Fol is a **32-bit little-endian word at decoded-state offset `0x18`**.
The pointer at RAM `0x80075270` locates that state. Its address is allocated
dynamically; Fol is not reliably at a fixed absolute RAM address.

The save payload beginning at block offset `0x382` is a zero-run-compressed
byte stream. A token `00 00 N` expands to `N + 2` zero bytes. The two bytes at
`0x380` give the compressed byte count (excluding that count itself).
The checksum end offset is `C = 0x382 + compressed_count`.

For the genuine S13, the four encoded bytes at `0x39A..0x39D` are:

```text
28 | 00 00 01  ->  28 00 00 00  ->  40
     zero run
```

`0x39D = 01` is the **count of one additional zero after the two explicit
zeros**, not the next field's tag and not a high Fol byte in the original.
The following field begins with literal `05` at `0x39E`.
Similarly, `01` at `0x395` ends the preceding zero run; `03` at `0x396` is
the next literal. This explains the misleading repeating `01 <value> 00 00`
pattern: its apparent record boundaries are one byte too early.

Replacing only `28 00` with `88 13` changes the tokenization:

```text
88 13 00 01  ->  88 13 00 01  ->  0x01001388 = 16,782,216
```

There are no longer two consecutive zeros, so `01` becomes literal data.
The decoder still emits four bytes; subsequent decoded fields stay aligned.
This is an exact explanation of the observed `5000 + 2^24`, with no checksum
fallback or alternate Fol source required. Correctly re-signing this malformed
edit makes its *checksums* valid; it does not restore the intended decoded value.

The observed low-u16 purchase values are consistent with this. A small positive
value has its low byte followed by a zero-run token, whose first byte is zero.
A value with two nonzero low bytes stores both literally. Reading the first two
encoded bytes therefore tracks these purchases, but writing those bytes can
change how the rest of the stream is interpreted.

## Sources and reproducibility

Original source (read-only throughout):

```text
C:/CodeTesting/StarOcean2/SaveGames/cards/_backup/card1-before-fol-fix4-20260925-011239.mcd
S13 / BASCUS-94421S02-S13 / physical card block 4
card SHA256  0171ea3603d777aa6e2251a65e1654dfa26037486ed745473f231e9eba3e221a
block SHA256 634052bd5d7670acebb84c4040902c3daafcfeaec1c52bc07fbb48f2b200487f
```

The current `SCUS-94421_resume.sav` differs from last round's state. Its SHA256
is `7efb22370a1956b919ab1336680d722d48708e97b8c264d657479ccd2c6ce716`.
Its RAM-containing Zstandard frame starts at `0xB749`, decompresses to
3,986,994 bytes, and RAM starts at decompressed offset `0x1A62`. The anchor is
the first 64 payload bytes of `SCUS_944.21;1`, LBA 24, loaded at `0x80010000`.
The screenshot frame at `0x11E` is a separate Zstandard frame.

In that current state:

```text
[80075270] = 8009A9C0
[8009A9D8..8009A9DB] = 88 13 00 01  (16,782,216)
```

This is observed RAM evidence from the supplied state, not a new emulator test.
`SCUS-94422_resume.sav` still contains the save overlay; its codec bytes at
`0x80081EF4..0x80082073` match Disc 1's extracted codec byte-for-byte.

The disc archive is `SO2.BIN`, ISO LBA 300. `tools/so2_disc_code.py` reproduces
the EXE's table decryption (`0x80011CCC..0x80011D1C`) and SLZ1/SLZ2 decoding
(`0x800122B4`, `0x8001275C`). Relevant archive entries:

| Entry | Disc LBA | Decoded size | Load address / role |
|---|---:|---:|---|
| 2576 | 30736 | `0x4C7FC` | `0x8002F810`, resident game code; anchored to current RAM |
| 2982 | 36099 | `0x2420` | `0x8007E000`, menu/status summary, TIME/FOL/BATTLES strings |
| 2985 | 36109 | `0xF9A8` | `0x800D1B28`, shared UI code; anchored to current RAM |
| 2986 | 36126 | `0x3E2C` | `0x8007E000`, shop transaction overlay |
| 2998 | 36213 | `0x4D28` | `0x8007E000`, save/load overlay |

Addresses in that region are overlay-specific: the same address can hold
unrelated code when another screen is active. Entry 2998 SHA256:
`f56ace2f46ff6c3d886e5f372a1e8f41db9da1d3667e65c4afb9189ddc3d9186`.

## Save reader and writer evidence

`0x80081A44` calls the state serializer with `a1=1` (load) and
`a2=save_buffer+0x380` in its delay slot. The serializer calls decoder
`0x80081FE8` at `0x80081AC0`, then copies the first `0x1A0` decoded bytes to
the state pointer from `0x80075270` (`0x80081ACC..0x80081AF0`).

The complete decoded payload has fixed size `0x1B88`, assembled from chunks
`0x1A0 + 0x300 + 0x680 + 0xC28 + 0x440`. These are memory-state chunks, not
variable-length per-field records.

Key decoder instructions:

```text
80081FF0 addiu a2,a2,2        ; skip compressed-length word
80081FF4 lh    t0,0(v0)       ; compressed byte count
80082010 lbu   v0,0(a2)       ; next encoded byte
80082014 addiu a2,a2,1
80082018 sb    v0,0(a1)       ; emit it
8008201C bnez  v0,8008205C    ; nonzero resets consecutive-zero count
80082020 addiu a1,a1,1        ; delay slot: advance output
80082024 addiu v1,v1,1
80082028 bne   v1,t1,80082060 ; t1=2: wait for second zero
80082030 lbu   v0,0(a2)       ; consume run count, NOT literal data
80082034 addiu a2,a2,1
80082038 addiu a3,a3,1
8008203C andi  a0,v0,00FF
80082040 blez  a0,8008205C
80082044 move  v1,zero
80082048 sb    zero,0(a1)     ; emit that many additional zeros
8008204C addiu v1,v1,1
80082050 slt   v0,v1,a0
80082054 bnez  v0,80082048
80082058 addiu a1,a1,1
```

Writer `0x80081EF4` emits isolated zeros literally and runs of two or more
as `00 00 (run_length-2)` (`0x80081F40..0x80081F6C`). It splits runs at 256
zeros (`0x80081F28`), despite the decoder also accepting count `FF` (257).
It writes the compressed length with `sh` at `0x80081FD4`. The existing
checksum writer then derives C from the final output pointer and signs it.
No change to `so2_sign()` was needed or made in this investigation.

## Display and transaction evidence

### Menu/status summary

Entry 2982 has two full-word Fol formatting sites:

```text
8007F250 lui   v0,8007
8007F254 lw    v0,5270(v0)    ; global state pointer
8007F258 move  a0,s0
8007F25C lw    a2,18(v0)      ; full 32-bit Fol
8007F260 jal   8003635C       ; integer-to-text formatter
8007F264 addiu a1,sp,20       ; output buffer, delay slot
```

The second site is `0x8007F618..0x8007F62C`, with `lw a2,0x18(v0)` at
`0x8007F624`. The surrounding strings include `FOL` and `%9d` at
`0x800800E8` / `0x800800F4`. Formatter `0x8003635C` processes the complete
integer with division/remainder, not a u16/u24 mask. Its digit loop allows
nine digits (`0x80036434`), enough for both 5,000 and 16,782,216.
These are the menu's Fol summaries, not character-stat fields.

### Shop

Entry 2986 uses a cached full-word balance and a computed transaction balance:

```text
8007E288 lui   v0,8007
8007E28C lw    v0,5270(v0)
8007E298 lw    v0,18(v0)      ; load current Fol
8007E2A8 sw    v0,CC(s2)      ; shop's starting-balance copy (delay slot)

8007F560 lw    v0,CC(s1)
8007F564 lw    v1,C0(s1)
8007F56C addu  v0,v0,v1
8007F574 lw    a0,BC(s1)
8007F57C subu  v0,v0,a0
8007F580 sw    v0,C4(s1)      ; projected balance = starting + credits - costs

8007F5B8 lw    a1,CC(s1)      ; display starting balance
8007F5BC jal   8007F6C4       ; clamp to +/-999,999,999
8007F5C0 ori   a2,a2,C9FF     ; with preceding lui a2,3B9A
8007F5C8 move  a1,v0
8007F5CC jal   800D7CF0       ; numeric UI output
8007F5D0 addiu a2,zero,A      ; field width 10
```

`0x8007F690..0x8007F6A8` similarly displays the full projected balance at
shop-state `+0xC4`. The clamp at `0x8007F6C4` compares signed full words;
it does not trim the high byte. `0x800D7CF0` forwards the integer to
`0x800D838C`, which calls the decimal formatter at `0x800100EC` before
rendering numeric glyphs.

The commit path reads projected balance with `lw` at `0x8007E900`, bounds
it through `0x80033ABC`, and stores the result with
`sw v0,0x18(v1)` at `0x8007E91C`, where `v1=[0x80075270]`.
Thus the shop and menu ultimately use the same 32-bit field; the shop's local
copy is ordinary transaction state, not a different save field.

## Correct edit and candidate

Decode the entire stream, set decoded bytes `0x18..0x1B` to the intended u32,
re-encode, update **both** the compressed count at `0x380` and C at `0x21A`,
then run the existing corrected signer. `so2_fol.py` implements this and
verifies that every other decoded byte is preserved. It refuses structurally
unexpected saves, invalid source checksums, values outside 0..999,999,999,
and an output that will not fit the single block. Its CLI creates a new card
file exclusively, preserving all directory bytes and all other saves.

For this exact S13, the canonical Fol encoding for 5,000 is five bytes:

```text
88 13 | 00 00 00  ->  88 13 00 00
        run of 2
```

The next field's `05` moves from `0x39E` to `0x39F`. Simply changing `0x39D`
to zero without inserting the count byte would consume the following `05`
as a zero-run count, damaging subsequent fields. A flat-u32 write is therefore
also incorrect.

Candidate: `artifacts/so2-fol/fol-5000-candidate.mcd`.
**2026-09-25 update: a save produced the same way by `so2_fol.py` (S13, 40 → 5,000 Fol) was
loaded in DuckStation and confirmed in-game — Fol displays correctly as 5,000, no corruption.
The codec-aware edit is now live-verified, not just checksum/decoder-verified.**

| Property | Original S13 | Candidate S13 |
|---|---:|---:|
| Decoded Fol | 40 | 5,000 |
| Compressed count at `0x380` | `0x03B9` | `0x03BA` |
| C | `0x073B` | `0x073C` |
| Checksum A | `0x242F` | `0x23A5` |
| Checksum B | `0x17D92` | `0x17E06` |

The candidate has 684 changed physical card bytes because the remaining
compressed stream shifts one byte. Its suffix `[0x39F,0x73C)` equals the
original suffix `[0x39E,0x73B)` exactly. After decompression, **only two bytes
change**, offsets `0x18` and `0x19`; the other 7,046 decoded bytes are identical.
Everything outside physical block 4 is byte-identical, including the directory.
Detailed byte differences are in `artifacts/so2-fol/candidate-report.json`.

```text
candidate card SHA256
312ac96b475dc408b26548c9b1b459a6f5a0a90ecf15858ce8419bf6c7499a16
candidate S13 block SHA256
ac6b2a713fd91ac5f14927c459b2050ef69c86956c0552943b3b61d96637797a
```

## Validation and commands

`python -m unittest discover -s tests -v`: 10 tests pass, including exact
reproduction of 16,782,216 from the two-byte edit, zero-run boundaries, Fol
width boundaries, and preservation of all other decoded data.

`tools/verify_so2_codec.py` independently executes the extracted game's encoder
and decoder instructions in a small bounded MIPS leaf-routine interpreter,
including branch delay slots. This is **not** a full emulator or game-load test.
The candidate also decoded to 5,000 under those actual decoder instructions.
Executing the actual encoder on its edited decoded state reproduced the
candidate's compressed bytes and length word exactly. The resident number
formatter also matched the Disc 1 extraction. Focused disassembly, including
instruction bytes, is in `artifacts/so2-fol/evidence.asm`.

Read-only archive audit: 160 distinct SO2 blocks; 131 passed structural checks
and agreed byte-for-byte between Python and MIPS for decoding and canonical
re-encoding. Of these, 126 passed checksums. Another 29 were rejected for
inconsistent encoded lengths or decoded sizes. This archive contains prior
edited/broken saves: checksum validity does not establish semantic validity,
and those 29 were neither repaired nor attributed to genuine game writes.
Eleven additional zero-run/mixed-data cases agreed with the actual MIPS codec.
The complete candidate card was also audited: all five saves matched both
MIPS codec routines, canonical encoding, and checksums.

```powershell
python tools/so2_disc_code.py "C:\CodeTesting\StarOcean2\disc\Star Ocean - The Second Story (USA) (Disc 1).bin" artifacts/so2-fol/disc-code
python tools/verify_so2_codec.py artifacts/so2-fol/disc-code/code-2998-lba-36213.bin "C:\CodeTesting\StarOcean2\SaveGames"
python -m unittest discover -s tests -v

# Choose a NEW output name; existing files are deliberately refused.
python scripts/so2_fol.py "C:\CodeTesting\StarOcean2\SaveGames\cards\_backup\card1-before-fol-fix4-20260925-011239.mcd" --save S13 --fol 5000 --out artifacts/so2-fol/fol-5000-another-copy.mcd

# Optional RAM extraction; output must not already exist. Requires zstandard.
python tools/extract_so2_ram.py "C:\CodeTesting\StarOcean2\SaveGames\SCUS-94421_resume.sav" "C:\CodeTesting\StarOcean2\disc\Star Ocean - The Second Story (USA) (Disc 1).bin" artifacts/so2-fol/new-resume-ram.bin
```

All investigation writes were confined to `C:/CodeTesting/SaveConverter`.
No file under `C:/CodeTesting/StarOcean2/SaveGames` was modified.
