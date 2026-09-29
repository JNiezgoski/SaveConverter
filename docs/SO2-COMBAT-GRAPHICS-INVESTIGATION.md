# SO2 combat encounter graphics: code-traced atlas format

Investigation: 2026-09-28, Task 3a. US Disc 1. **Archive 1427's embedded
block is a 2D animation/texture-atlas resource, not a vertex/face model.**
Its graphics are decoded successfully using the real combat loader and
renderer. This result does not establish that every enemy in the game uses
this branch, or how the original artwork was authored.

Evidence is static disassembly plus extraction and personal image inspection;
no PS1 instructions were executed in an emulator or interpreter in this pass.
No git commands were run. All binaries, images, and investigation scripts are
under `artifacts/so2-monster-format/`.

## Reproduction and evidence files

```powershell
python artifacts/so2-monster-format/write_evidence.py
python artifacts/so2-monster-format/dump_combat_graphics.py --entries 1427
# The additional samples inspected structurally in this pass:
python artifacts/so2-monster-format/dump_combat_graphics.py --entries 1405 1416 1427 1450 1508 1696 1942 1968
```

The dumper uses the existing archive-table and SLZ decoder in
`tools/so2_disc_code.py`, plus Pillow. The evidence writer uses Capstone.
The default source is the local US Disc 1 image; the dumper accepts `--disc`.
The dumper refuses output paths outside this workspace's `artifacts/`.

- `evidence.asm`: cited instructions with **RAM address, source file offset,
  and raw instruction word**, separated by source overlay.
- `source-manifest.json`: source identities and SHA-256 hashes.
- `decoded/report.json`: exact per-archive/block/bank offsets, dimensions,
  palette words, descriptor values, and unresolved cases.
- `decoded/archive-1427/block-00/bank-00/contact.png`: personally viewed;
  coherent teal creature poses, stretched poses, and small separate components.
- `decoded/archive-1416/block-00/bank-00/contact.png`: personally viewed;
  coherent armored figures holding an axe and shield. No species identification
  is inferred from that appearance.
- `decoded/archive-1450/block-00/bank-00/contact.png`: personally viewed;
  green outlined body pieces and separate rounded pieces. These are slices,
  not a reconstruction of their in-game composition.

The small proof scripts are local artifacts for manager review, not an
integration into the existing hero/scene extractor.

## Finding the actual code image

The prior `SO2-DAMAGE-FORMULAS.md` describes Archive 1 at `80040000`.
That is not the executable's load address. Executable instructions
`80010718/8001071C` select Archive 1; `8001076C` calls `800105B0`.
At `800105D0/800105D4`, `lui a2,8003; addiu a2,a2,-7F0` gives
**8002F810** as the decompression destination, and `80010604` calls that
address. Starting with the old address generated misleading disassembly;
it was corrected before the following conclusions. The old damage claims
were not re-audited here.

The field overlay supplies a better combat entry point:

| Source | Address | Instruction/effect |
|---|---|---|
| Archive 2576 | `80051A74/80051A78` | `jal 80011B98; addiu a1,zero,851`: obtain size for archive **2129** |
| Archive 2576 | `80051BE8` | `addiu a1,zero,851`, then queue that archive at `80051C0C` |
| Archive 2576 | `800521A8/800521AC` | load the queued buffer from global `80075350`; call `800105B0` |
| Executable | `800105D0..80010604` | decompress to and enter `8002F810` |

Archive **2129**, Disc 1 LBA **24323**, decompresses to **381148 bytes**
(`0x5D0DC`), SHA-256
`7ae7d12caf8146249bbaeb904f34a7b982fa928f72e3af624c438ef790ece722`.
All combat addresses below are in that image at base **8002F810**, unless
explicitly identified as executable addresses. File offset is
`RAM_address - 0x8002F810`; for example `8007344C` is file `+0x43C3C`.
Overlay identity matters: the same RAM address in Archive 1 or 2576 can contain
unrelated instructions.

## Encounter selection and embedded block loader

Archive 2576 `80078998` computes `encounter_selector + 0x57D` and stores
it at preload record `+0x58`. Archive 2129 has the corresponding code at
`800754A4/800754A8`. `0x57D` is decimal **1405**. Its loop
`800754FC..8007551C` copies the preload archive IDs from `+0x3C` to `+8`.
Thus the encounter archive occupies index 7 of this resource list.

At combat initialization, `800716E4` retrieves resource 5, and
`800716FC..80071724` copies its preload record. The resource loop at
`80071924` uses the preloaded buffer or reads the selected archive through
`80071950/80071974`. The dispatch table at `80078F38`, entry 7 at
**80078F54**, contains **80071A74**. That case calls **8007344C** at
`80071A78`, passing the archive buffer in `a1`.

Loader `8007344C` processes the encounter's initial table as pairs:

```text
80073500 lw    v1,0(t5)        ; archive-relative embedded SLZ offset
80073504 addiu v0,zero,-1
80073508 beq   v1,v0,80073BCC  ; sentinel
80073510 lw    t4,0(t5)        ; second word, after delay-slot t5 += 4
8007352C addu  s0,t5,v1        ; here t5 has been reloaded with archive base
80073534 jal   80012154        ; allocate decompressed-size buffer
80073564 jal   800121A8        ; decompress embedded SLZ
```

The second word controls repeated runtime setup using the same decompressed
block (`800735A0..800735AC`, `80073A78`, `80073BB4..80073BC8`). It is not
a vertex count. For Archive 1427 the initial pair is **(0xF0, 1)** followed
by `FFFFFFFF`. Its source archive is already an uncompressed container;
there is no outer SLZ to decompress for this sample. The embedded SLZ at
`+0xF0` decompresses to **32948 bytes / 0x80B4**.

## Decompressed resource header

Let `B` be the decompressed block base. All pointer values below are little
endian byte offsets relative to `B`.

| Offset | Meaning traced in code | Evidence |
|---|---|---|
| `+0x00` u32 | primary bank count with an additional high-value flag | `80073574..80073594`: signed comparison with `0x80`; values >=128 masked with `0x7F` |
| `+0x04` u32 | additional bank-pair count; texture-page reuse path | `8007357C`, `80073668..800736E8`, `80073A14..80073A74` |
| `+0x08` u32 | direction/action mapping table | `800735C8..800735D4`; installed in graphics state `+0` at `80073F18` |
| `+0x0C` u32 | animation sequence pointer table | `800735E0..800735EC`; installed in graphics state `+0x44` at `80073F28` |
| `+0x10 + 8*i` u32 | bank `i` animation-record table | `80073618..8007363C` |
| `+0x14 + 8*i` u32 | bank `i` graphics/atlas container | `80073640..80073658` |

For Archive 1427 the six words are **1, 0, 0x18, 0x38, 0x1A4, 0x744**.
The table-looking bytes at the start really are mapping/animation data.
Applying the hero section-header layout to them cannot locate this graphics
container correctly.

The flag at `B+0` also enables extra zero-terminated relative pointers
(`800736F4..8007374C`); their full semantics are not solved here.

## Graphics container and atlas upload

Let `G = B + u32(B+0x14)` for the first primary bank.

| Offset from G | Meaning | Evidence |
|---|---|---|
| `+0x00` u32 | relative offset to palette block | `80073898..800738A8` |
| `+0x04` u32 | relative offset to first packed texture page | `800738EC..8007391C` |
| `+0x08` u8 | graphics flags; bit `2` selects another rendering/storage branch | `8004285C..80042868` |
| `+0x09` u8 | additional texture-page count, total = byte + 1 | `80073790..8007379C`, `8007393C..800739F8` |
| `+0x0A` u16 | observed descriptor-slot count in these eight samples | Matches the palette-bounded descriptor region; **no count-reading instruction identified** |
| `+0x0C..0x0F` u8[4] | rectangle bounds used to initialize runtime texture allocation | `80073810..80073894`; X divided by four for VRAM words |
| `+0x10...` | 8-byte atlas descriptors for the branch decoded here | `80042990..80042A84` |

The descriptor start depends on the corresponding animation table byte `+2`:
zero selects `G+0x10`, nonzero `G+0x0C`. Graphics flag bit `2` selects
12-byte streamed descriptors instead. These are real code branches,
not guessed alternate layouts. The proof tool only renders the zero-byte,
bit-2-clear branch exercised by the sampled primary banks.

Palette block: `u32 color_count`, then that many little-endian BGR555 words.
`800738A4` reads the count; `800738B0` calls `80084A84`, which copies at
most 128 colors and creates an additional version with bit 15 set for nonzero
colors. `800738C0` uploads that palette through executable `80012EC4`.
The first primary bank supplies the palette for the block in this loader.
The tool preserves palette words and previews their RGB values, but does not
simulate blending against a game background.

Each texture page is `u16 width_pixels, u16 height, packed_4bpp_pixels`.
The loader passes the two halfwords at `800738FC/80073908` to executable
**80012E04**, with `a1=0` (`800738E0`). That executable function shifts the
width right by **2** at `80012E44`, calls the image-upload wrapper at
`80012E64`, and returns a packed texture-page value. This establishes the
four indexed pixels per VRAM word upload, not a vertex array.
Bytes decode low nibble first, then high nibble. The next page follows
`4 + width*height/2` bytes, aligned to four bytes
(`8007396C..800739AC`).

## Eight-byte graphics slice descriptor

This describes the ordinary atlas branch, not the separate 12-byte streaming
branch. These are **graphics slices**: a timed animation can reuse them or
compose additional pieces.

| Byte | Type | Meaning | Renderer instruction |
|---|---|---|---|
| 0 | u8 | palette row offset, added to runtime CLUT identifier | `80042A14`, `80042A50..80042A58` |
| 1 | u8 | texture-page selector | `800429B8..80042A0C` adjusts runtime page ID |
| 2 | u8 | U minimum | `80042A10` |
| 3 | u8 | V minimum | `80042A20` |
| 4 | u8 | U endpoint | `80042A2C` |
| 5 | u8 | V endpoint | `80042A38` |
| 6 | i8 | horizontal pivot | **`lb`** at `80042A48` |
| 7 | i8 | vertical pivot | **`lb`** at `80042A54` |

The eight-byte stride and `+0x10` start are explicit at
`8004299C..800429AC`. Endpoint differences determine the rectangular extent
at `80042AE8..80042B18`; crops use `[u0,u1)` and `[v0,v1)`.
The renderer builds textured quadrilateral packets (`0x2C/0x2D/0x2F` command
paths at `80042BD8`, `80042C38`, `80042C70`), writes CLUT at packet `+0x0E`
and texture page at `+0x16` (`800433AC/800433BC`), and links the packet into
the ordering table (`800433C0..80043408`). That is the traced drawing path
for these atlas slices; it is not proof of a monster vertex/face mesh.

In Archive 1427: `G=0x744`, palette relative offset `0x148`, pixels relative
offset `0x16C`, flags `0`, one page, observed slot count **39**.
The palette is at decompressed `0x88C` with **16 colors**; the texture header
is at `0x8B0`, dimensions **256x240**, followed by **30720 pixel bytes**.
Descriptor 0 at `0x754` is `00 00 C1 89 DB B5 0E 29`: palette/page 0,
UV rectangle `(193,137)..(219,181)`, pivot `(14,41)`, yielding **26x44**.
This slice is visible in the personally viewed contact sheet cited above.
Slots **36, 37, 38** have zero-area rectangles. They are retained in JSON;
no image is fabricated for them.

## Animation selection connects the index table to those images

The runtime state installed by the loader holds the mapping table at `+0`,
animation-record bank pointers at `+0x24`, graphics banks at `+4`, and the
sequence pointer table at `+0x44` (`80073E94..80073F70`).

`80042158..80042170` selects a four-byte mapping record using the object's
`+0x4C` state. `800455D8..80045660` chooses a sequence byte using direction
and records mirroring. `80045688..8004569C` resolves sequence `i` as
`sequence_base + u32(sequence_base + 4*(i+1))`.

A sequence starts with a u16 step count (`800421C8`), followed by control
bytes and four-byte steps beginning at `+4` (`80042324..80042330`): u16
animation-record index, u8 bank selector (`800423B4`), and u8 duration
(`80042334`, zero treated as one). No real-time unit is established here.
For the zero-byte branch the selected animation record is
`animation_bank + 0x14 + 8*index` (`800423D4..800423F8`); its first byte is
the graphics slice index (`800424C0`). Other bytes drive mirroring, offsets,
and optional additional pieces; the proof tool does not implement composition.

Concrete Archive 1427 chain: mapping record 0 at `0x18` is `04 06 07 05`.
Sequence 6 resolves to `0x110`, has six steps with bank 0, duration 8, and
animation-record indices **36..41**. Those records reside at
`0x2D8, 0x2E0, 0x2E8, 0x2F0, 0x2F8, 0x300`; their first bytes select
graphics slices **0..5**, respectively. This supplies a code-derived link
from the initial index/mapping data to the extracted images. No behavior
name such as idle or attack is assigned to that state.

## Scope of checks and unresolved work

| Archive | Embedded blocks | Primary banks | Decoded slices | Zero-area slots | Unresolved slots |
|---|---:|---:|---:|---:|---:|
| 1405 | 1 | 4 | 27 | 6 | 1 |
| 1416 | 2 | 2 | 49 | 0 | 0 |
| 1427 | 1 | 1 | 36 | 3 | 0 |
| 1450 | 1 | 1 | 56 | 1 | 0 |
| 1508 | 1 | 1 | 36 | 3 | 0 |
| 1696 | 1 | 1 | 31 | 0 | 0 |
| 1942 | 2 | 4 | 65 | 38 | 0 |
| 1968 | 1 | 1 | 56 | 1 | 0 |

These are **eight structural samples**, totaling 356 decoded slices, 52
zero-area slots, and one unresolved slot. Personal visual inspection is
limited to the three contact sheets named above; successful bounds checks
on the other outputs are not a claim of visual verification.

The unresolved Archive 1405 descriptor is block 0, primary bank 0, slot 4,
decompressed offset `0x1A370`: raw fields palette row 255, page 0, UV
`(62,168)..(0,0)`, pivots `(34,80)`. Its meaning is not established. The tool
reports it instead of converting it into a guessed frame or content label.

Remaining work: the flagged additional pointer list; shared-bank VRAM reuse;
the alternate descriptor/streaming branches; complete animation effects and
composition; accurate scene-dependent semi-transparency; and coverage of
the rest of `1405..1968`, including Disc 2. No OBJ or invented vertex counts
are provided because the tested format supplies sprite atlases. This pass
does not resolve Task 3b's named bosses or Task 3c's field NPC identities.
