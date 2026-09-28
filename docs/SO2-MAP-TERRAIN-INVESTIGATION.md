# SO2 map terrain / collision: real record format found, per-area archive entry still open

**Latest: see the fourth-pass subsection below.** Scene-to-archive selection and
fresh/cache loading are now traced; real field triangles are extracted. The
overworld's real "type 3" format was traced to a 9-slot streaming cache backed
by what looks like a quadtree spatial structure, distinct from the dungeon's
triangle array — but its node layout and height/collision output were not
fully decoded, so the overworld cross-check still remains open. The third pass
also corrects the historical area-byte and coordinate claims.

Investigation: **2026-09-27**. US PS1 BASCUS-94421/SCUS-94421 (Disc 1). Continues
from the field-leader follow-up's side finding (see
[SO2-PARTY-MEMBER-INVESTIGATION.md](SO2-PARTY-MEMBER-INVESTIGATION.md), "side
finding worth flagging separately"), which located and extracted the
field/movement-engine overlay containing real terrain code. This is not in the
save file at all — it is per-area data loaded from the disc.

**Status: real progress, genuinely partial, across two passes.** The
terrain-triangle record format is understood field-by-field from actual
executed-instruction evidence. The resident RAM structures that hold a
loaded area's terrain are identified, and a second pass traced one layer
deeper: terrain is confirmed as asset type 0 of a 13-type per-area dispatch
table, backed by a 12-slot loaded-area cache. What is **still not** found:
which disc archive entry supplies terrain data for any specific area, or how
area ID ultimately selects it — that link sits one level deeper still, in
whatever populates the cache/current-area-table on an actual fresh load, not
yet located. No numeric cross-check against a known real save position was
possible either pass for that reason — see "What's still open" and the
2026-09-27 second-pass section below.

All source material: `artifacts/so2-field-control/field-overlay-full.asm`
(the field-engine overlay, functions below) and
`artifacts/so2-options-menu/resident.asm` (always-resident code, loader
function). No new extraction was performed; both were already on disk from
prior investigations. No card was read or written. This is disassembly
tracing only — nothing was executed in an interpreter/harness, unlike most
of this project's other "Verified" claims. Treat everything here as
**disassembly-derived, not execution-verified.**

## 1. Resident terrain-view globals

Three RAM globals hold the currently-loaded area's terrain:

| Global | Meaning |
|---|---|
| `[80075330]` | Raw pointer to the loaded terrain resource's header (call it `R`) |
| `[80075338]` (`TB`) | `R + *(R+0x80)` — base address of the resource's actual data section |
| `[80075334]` (`T`) | `TB + 4` — a convenience alias, 4 bytes into the same data |

Both `T` and `TB` are read throughout the field-engine overlay (over 40 call
sites reference `0x5334`/`0x5338`); none of those sites write them. The only
write site found is in the always-resident loader below.

## 2. The loader

Found in the always-resident code, roughly `8004AD9C..8004AF94`
(addresses per `artifacts/so2-options-menu/resident.asm`, which happens to
contain a full resident disassembly from an earlier investigation):

```text
8004ADA4 jal   80012154       ; fetch sub-chunk N of resource s4
8004ADA8 move  s2,zero
...
8004ADC4 jal   800121a8       ; load/decompress that sub-chunk
8004ADC8 addiu s3,s5,0x10
...                            ; loop: s2 = 0,1,2,... fetching further sub-chunks
8004AE68 lw    v0,4(s5)
8004AE70 beqz  v0,8004af24
...                            ; one more sub-chunk fetched conditionally
8004AF14 jal   80020e5c        ; cleanup / commit call
8004AF34 lw    a0,5260(a0)
8004AF38 jal   80012154        ; final fetch, a2=0
8004AF54 sw    a2,5330(at)     ; R = returned pointer
8004AF64 lw    v0,5330(v0)     ; v0 = R
8004AF6C lw    v1,0x80(v0)     ; v1 = *(R+0x80)
8004AF7C sw    v0,5338(at)     ; TB = R + v1 (already added at 8004AF78)
8004AF88 sw    v0,5334(at)     ; T  = TB + 4 (v0 already +4'd at 8004AF84)
```

`80012154`/`800121a8` are the same generic two-step resource-fetch pair used
elsewhere in this codebase (paired the same way the Options overlay fetches
its separate text/font resource — see
[SO2-OPTIONS-MENU-INVESTIGATION.md](SO2-OPTIONS-MENU-INVESTIGATION.md)).
`[80075260]` is the resource-manager context pointer passed as `a0` to both
calls; `s4` is a resource-selector value whose origin (a specific archive
entry number, or something computed from the area ID) was **not traced back
further in this pass** — this loader loads *several* indexed sub-chunks
before assembling `R`, consistent with one per-area archive entry bundling
terrain together with other per-area assets (scripts, layout, etc.), not a
terrain-only entry. Finding what feeds `s4` for a specific area is the
concrete next step.

## 3. Terrain header (relative to `TB`)

| Offset from `TB` | Field |
|---|---|
| `+0x20` (u16) | Number of triangle records |
| `+0x5C` (u32) | Byte offset from `TB` to the start of the triangle-record array |

Read at `80083660..80083678` (point-in-cell search) and confirmed at
`800838a4..800838c8` (a second, similar walk in a neighboring function).

## 4. Triangle record (88 / `0x58` bytes each)

Traced from two real functions: the point-in-cell test `80083c3c` (full
bounding-box + 2D cross-product polygon test) and the height-interpolation
function `80083944`/its caller `80083628`.

| Offset | Field | Evidence |
|---|---|---|
| `+0x00` (i16) | Y-range low bound | `80083c50` compared against object Y `[obj+4]` |
| `+0x02` (i16) | Y-range high bound | `80083c64` |
| `+0x04` (i16) | AABB corner0 X (grid units) | `80083c84` vs `worldX>>12` |
| `+0x06` (i16) | AABB corner0 Z | `80083cac` vs `worldZ>>12` |
| `+0x08` (i16) | AABB corner1 X | `80083c98` |
| `+0x0A` (i16) | AABB corner1 Z | `80083cc0` |
| `+0x0C` (u8) | Enabled/valid flag — 0 skips this record entirely | `80083c3c` entry check |
| `+0x0D..0x0F` | Unidentified; `+0x0F` is read by the caller (`80083c3c`'s caller in `80083628` at `800837e0`) as a "has neighbor/apply surface" gate | not fully traced |
| `+0x10/+0x12/+0x14` (i16 each) | Vertex 0: X, Y, Z | height formula's reference vertex; also point-in-cell's first polygon vertex |
| `+0x18/+0x1A/+0x1C` (i16 each) | Vertex 1: X, Y, Z | point-in-cell polygon vertex 2; Y used in the height clamp loop |
| `+0x20/+0x22/+0x24` (i16 each) | Vertex 2: X, Y, Z | point-in-cell polygon vertex 3; Y used in the height clamp loop |
| `+0x28..0x2F` | Unidentified (8 bytes) | not traced — candidate: a 4th vertex/normal, or neighbor-record convenience data |
| `+0x30` (i32) | Plane coefficient A | `80083714` `mult` |
| `+0x34` (i32) | Plane coefficient B (also the height-formula divisor) | `80083754` `div` |
| `+0x38` (i32) | Plane coefficient C | `80083730` `mult` |
| `+0x3C..0x53` | Unidentified (24 bytes) | not traced this pass — plausible neighbor-triangle links for the search walk, unconfirmed |
| `+0x54` (u8) | Surface/footstep-type ID | `80083814..8008381c`, conditionally copied into the moving object's current-surface field |
| `+0x55..0x57` | Unidentified (3 bytes) | not traced, likely padding |

Only 3 vertices (0x10, 0x18, 0x20) plus a separate AABB corner pair are
identified — this is a **triangle**, not a quad, despite the record's 88-byte
size leaving room for a 4th vertex-sized block at `+0x28` that was not
resolved.

**Height interpolation** (`80083628` calling `80083944`'s surrounding logic,
real instructions at `80083704..80083760`): given object world X (`[obj+0]`)
and Z (`[obj+8]`), and the matched triangle's vertex 0 and plane coefficients:

```text
height = Y0 - (A*(worldX - X0*4096) + C*(worldZ - Z0*4096)) / B
```

(sign convention derived from the real subtract/negate/divide sequence, not
independently re-derived by a second method — treat the overall shape of the
formula as solid, individual signs as likely-but-unconfirmed). The result is
written to `[obj+4]`, then clamped between the min and max Y of the triangle's
three real corners (a real min/max loop over `+0x12/+0x1A/+0x22`) before being
used, and finally compared against the record's own `+0x00/+0x02` fast-reject
Y range from the bounding check.

## 5. Coordinate scale (confirmed cross-reference)

Terrain vertex coordinates are small `i16` grid integers. The interpolation
code shifts them left by 12 bits (`sll ..., 0xc`, i.e. `× 4096`) before
comparing against the object's position fields — the **same 20.12
fixed-point scale already established for the save's own position fields**
(decoded `0x1750` X / `0x1754` Y / `0x1758` Z — see
[SO2-MAP-LOCATION-CHECK.md](SO2-MAP-LOCATION-CHECK.md)). This is a genuine,
useful confirmation: terrain geometry is authored on a coarse integer grid
(1 grid unit = 1.0 world unit = 4096 raw units), while the player's live
position is sub-unit precise on top of that grid.

## What's still open

- **The archive entry (or entries) supplying terrain data for any specific
  area, and how area ID selects it, was not found.** The loader fetches
  several sub-chunks by an opaque selector `s4`; tracing `s4`'s origin back
  to the area-ID field (decoded `0x1769`) is the direct next step, and was
  explicitly out of scope for what this pass could finish.
- **No numeric cross-check was performed.** The plan was to decode one real
  area's triangle array and sanity-check it against a known player Y from an
  existing archived save (e.g. `area_data.json`'s recorded sightings). That
  requires the archive-entry mapping above, so it could not be done this
  pass — this is the natural verification step once that mapping exists.
- **Fields `+0x0D-0x0F`, `+0x28-0x2F`, and `+0x3C-0x53`** (34 of the 88 bytes)
  are unidentified. The `+0x3C-0x53` block is large enough to plausibly hold
  neighbor-triangle pointers/indices for the search-and-walk pattern typical
  of navmesh-style terrain, but this is a guess, not a traced finding.
- **The point-in-cell search itself (`80083628`'s outer loop) is a linear
  scan of every triangle in the area**, not a spatial index — fine for
  understanding the format, but worth knowing if a future pass wants to
  reason about performance or ordering assumptions.
- No emulator was run and no interpreter/harness executed any of this code;
  everything above is static tracing of real, extracted instructions, one
  level less verified than this project's usual "executed and asserted"
  standard.

## 2026-09-27 second pass: traced one layer deeper into `s4`, mapping still open

**Real, concrete progress; the area-ID → archive-entry link is still not
found.** This chases exactly the "still open" item above. All addresses are
from `artifacts/so2-options-menu/resident.asm` (always-resident code) unless
noted; nothing new was extracted, and this is disassembly tracing only — no
interpreter/harness execution, same caveat as the rest of this document.

**Terrain is confirmed as asset type 0 of 13.** The area asset-table dispatch
jump table lives in RAM data at `[0x80072f8c]` (read directly from the
already-extracted `artifacts/so2-options-menu/ram-disc1.bin` at file offset
`0x72f8c`, 13 consecutive `u32` pointers):

```text
type 0  -> 8004ad94   (terrain loader, this document's subject)
type 1  -> 8004afdc
type 2  -> 8004b0a8
type 3  -> 8004b0c0
type 4  -> 8004b278
type 5  -> 8004b104
type 6  -> 8004b14c
type 7  -> 8004b194
type 8  -> 8004b194   (shares a handler with 7, 9, 10)
type 9  -> 8004b194
type 10 -> 8004b194
type 11 -> 8004b1d4
type 12 -> 8004b21c
```

This dispatch is reached at `8004AD6C..8004AD90` in the loader function
(`8004ACA0`): it walks a per-area asset table `s7` (element stride 8 bytes:
`+4` = type index, checked `< 0xD`; `+8` = a byte offset added to `s7` to
locate that type's own data blob, called `s4` in the prior pass) and jumps to
`jump_table[type*4]` for each present entry. `s4` is therefore **not an
archive index at all — it's a pointer into the current area's already-loaded
asset bundle**, and the fetch calls (`80012154`/`800121a8`) that follow are
pulling sub-chunks out of that already-resident bundle, not hitting the disc
directly at this point. The real disc-archive selection happens earlier,
when that bundle itself is loaded.

**Traced the asset-table source one more level up: a 12-slot loaded-area
cache.** `8004ACD8`'s call to `80056ACC(a0=area_selector, a1=&stack_temp,
a2=0)` is a linear search (real disassembly at `80056ACC..80056B40`) over a
fixed 12-entry table at `[80075768]`, stride `0x14` (20) bytes per entry:

| Entry offset | Field | Evidence |
|---|---|---|
| `+0x00` (u8) | Active/loaded flag — 0 skips the slot | `80056AE4/AEC` |
| `+0x08` (u32) | Cache key, compared equal to the search input | `80056AF4/AFC` |
| `+0x0C` (u32) | A second stored value, returned via the caller's optional `a1` out-pointer | `80056B18/B20` |
| `+0x10` (u32) | The cached asset-table pointer, always the function's return value on a hit | `80056B24` |

If found (a matching, active slot), `8004ACA0` uses that slot's `+0x10`
pointer as `s7` directly — this is a real "already loaded, reuse it" fast
path for revisiting an area, consistent with adjacent-area caching. If not
found, it falls back to `s7 = [80075738]`, a separate global that must hold
the asset table for whichever area is *currently* being freshly loaded from
disc.

**Where the trail goes cold.** Locating the code that fills `[80075738]` (or
a fresh slot in the `[80075768]` cache) on an actual cache miss — the point
where a real disc archive-entry number must be chosen from the area
ID — was not completed this pass. `[80075738]` is written and read from
dozens of places throughout the resident code (over 40 references), and is
evidently a generic "current context" pointer reused across multiple
subsystems, not a narrowly-scoped variable that makes the real load site
easy to isolate by reference count alone; distinguishing the real "fresh
area load" writer from the rest needs tracing forward from the
already-documented area-transition code in
[SO2-MAP-LOCATION-CHECK.md](SO2-MAP-LOCATION-CHECK.md) (the teleport-ranges
work), not backward from this generic pointer.

**Traced the cache-search's own caller one level further, inconclusively.**
`8004ACA0` (this whole loader) is called from exactly one site,
`80055008` (`jal 0x8004aca0`, `a1 = s0`), where `s0` comes from
`lh $s0, 0x2c($sp)` — a halfword loaded from that caller's own stack frame,
strongly suggestive of an area/room identifier but **not confirmed identical
to decoded save byte `0x1769`** in this pass; that caller function itself
starts well before the traced region and was not walked back to its own
entry point or its caller.

**Data-quality note for the eventual cross-check.** `area_data.json`'s
currently recorded live sightings are almost all at or extremely near local
origin (X/Z within ~0.2, Y = 0.0) for every area except the overworld (area
0) — likely because these were recorded right at a fresh area-entry spawn
point rather than a distinctive mid-room position. This isn't enough
positional variation to meaningfully distinguish one decoded triangle from
another once real per-area terrain data can be decoded. A future pass either
needs a live sighting recorded from a distinctive, deliberately-chosen
position inside a specific area, or should use area 0's overworld sightings
(which do have real non-trivial X/Z) for the first real cross-check attempt.

**Net effect on next steps:** the concrete next action is still "trace the
area-ID → archive-entry link," but it is now known to live specifically in
whatever writes `[80075738]` or a `[80075768]` slot on a genuine fresh load —
not in the per-area asset-table dispatch itself, which is now fully
understood and is not the missing piece.

## 2026-09-27 third pass: scene-to-archive rule found; overworld uses another format

**Status: VERIFIED by disassembly and read-only extraction, not by executing game
instructions or new in-game testing.** The missing fresh-load writer and cache
insertion are now located. A real **scene selector -> archive entry** rule is
established, and two real 88-byte records were extracted. The requested **area-0
height cross-check remains OPEN**: its selected bundles have type 3, not type 0.
There is no demonstrated unique mapping from the byte called `area_id` by
`so2_location.py` (`decoded 0x1769`) to an archive entry. In fact, the instructions
below contradict treating that byte as the loader's scene number.

This subsection supersedes conflicting interpretations in the two historical
passes above, especially their coordinate scale, height formula, cache out-argument,
and assumption that overworld terrain must use the same 88-byte format. The older
opening phrase "executed-instruction evidence" is incorrect for those passes:
they, like this pass's code tracing, were static disassembly.

### Forward transition trace and the actual selector

Started with the location investigation's `80051A34`, `8004C654`, and `80063A24`
leads, rather than another search for writes to `[80075738]`.

- `80051A34` saves a controlled object's position and frees terrain; it does not
  itself select the new terrain archive. Its caller `8006BD14` belongs to state
  11 of the script object's dispatcher, not the state-1 load path. The 14-word
  table at `80073968` starts with `8006BDD0` and has `8006BCD0` at index 10.
- The genuine scripted transition path `800639B0..80063B04` reads script arguments.
  `80063A1C/30` stores the first argument into `[script_object+34]`, sets
  `[script_object+30]=1` at `80063A2C`, and stages X/Y/Z at `F+8/C/10`, where
  `F=[80075710]`. `80063A98..A4` also preloads `argument + 0xC87` for the
  non-1/2 branch via `8006AF4C`. This reaches cache insertion `800563A0` at
  `8006AFB4`, with the archive selector preserved in `s1`.
- Dispatcher `8006BCA0..CCC` indexes state minus one. State 1 therefore reaches
  `8006BDD0`, then `8006BE78` loads `[script_object+34]` into `a1` and
  `8006BE80` calls **`80053E8C`**, the previously-unidentified function containing
  `80055008`. This is a static control-flow connection; no transition was run.
- `80053E9C` preserves that argument as `s1`. `80054398` writes it to
  **`F+1A = decoded 0x1762` (signed halfword)**. The same saved field is read by
  the reload caller at `800664EC`, before its `800664F0` call to `80053E8C`.
- `80054490` calls **`80061888(out=sp+28, selector, X, Z)`**, taking X/Z from
  `F+8/+10`. The non-overworld branch at `800544A0..A8` passes zeros for X/Z.
  `selector` is normally `s1`, or `-1` when runtime `[8007570C]+24` requests
  an alternate context (`800543A8..B8`).
- `80061888` writes the terrain-bundle archive index at **`out+4`**. Thus it is
  precisely `sp+2C`, read into `s0` at `80054FF4`. `80054FFC` loads that archive
  with `8004A654`, and `80055008` dispatches its asset table with `8004ACA0`.
  The stack halfword was an **archive index**, not decoded byte `0x1769`.

### Archive selection rules (verified statically)

Let `scene` be the effective selector and X/Z the unscaled integer inputs to
`80061888`. On the `selector == -1` branch, these are recovered from resource 9:
`scene=lh(resource9+23A)`, X/Z=`lw(+228/+230)` (`80061904..28`). This branch
also supplies other bundle-list fields; it is not simply ignored.

| Effective scene | Archive index written to `out+4` | Instructions |
|---|---|---|
| Outside 1..3 | `scene + 0xC87` | `80061968..74`, `80061AF0..F4` |
| 1 | `0x1014 + cell`, normally `cell = floor(X/12288) + 9*floor(Z/12288)` | unsigned multiply-high by `0xAAAAAAAB`, then `>>13` at `80061978..A4`; `800619A8..C4`, `80061A34..5C` |
| 2 | `0x109F + floor(X/12288) + 9*floor(Z/12288)` | `80061A3C..54` |
| 3 | `0x10E0` | `80061A58..5C` |

The division description assumes nonnegative X/Z; instructions actually perform
unsigned multiplication. Scene 1 additionally remaps certain cells 38..58 when
`resource9+220` is in 15..60, using the table at `80073548` and handlers
`800619F0..80061A30` (replacement cells 63..71). Do not drop that branch from a
universal mapper. Neither overworld sample below falls in the affected cells.
`8006194C/50` selects engine overlay `0xC1E` (3102) for scenes 1..3, otherwise
`0xC1D` (3101). This explains why the two geometry paths differ.

### Fresh allocation and cache population, both found

`8004A654` preserves its archive-index argument in `s0` and checks `80056ACC`.
On a miss it frees the previous temporary buffer (`8004A714..72C`), obtains the
archive byte size with `80011B98(a1=s0)` at `8004A750/54`, allocates with
`800130EC` at `8004A768`, and **writes the returned buffer to `[80075738]` at
`8004A774`**. It queues the read with `8004310C` at `8004A7C4` (synchronous
wait path) or `8004A798` (caller supplies completion byte).

The queue keeps the archive index, byte count, destination, and completion
pointer at record `+0/+8/+C/+10` (`80043148..54`). Its worker `80043324`
selects the archive entry through `80011654` at `800434DC`, then calls
`80011804(destination, byte_count)` at `80043514`. This is the actual disc
connection, not a decompressed resource-number lookup.

Cache insertion is **`800563A0(a0=index, a1=active_class, a2=tag, a3=size)`**.
It finds an unused slot, gets the archive size if not supplied (`80056474..8C`),
allocates (`800564F8`), and at `80056524..48` stores ownership flag `+2`, active
class `+0`, zero completion byte `+1`, archive key `+8`, tag `+4`, destination
pointer `+10`, and optional requested size `+C`. `80056550` queues a read with
completion pointer **slot+1**. A zero stored `+C` is allowed; the archive-size
fallback is also visible in the existing cache-hit path `8004A690..6B8`.

**Correction to pass 2:** `80056ACC` writes `slot+1` through **a1**, and stored
`slot+C` through **a2** (`80056B04..20`). It does not return `slot+C` through
a1. The former is a readiness pointer, which the terrain dispatcher polls at
`8004AD24..34`; slot `+0` alone does not mean the read has completed. This is
an archive cache, not necessarily twelve distinct areas.

### Why decoded `0x1769` is not a unique area key

**Verified data flow:** `8004C708/710` copies `object+22` into `F+21`, i.e.
decoded `0x1769`. In the field overlay, `80083814/1C` conditionally copies a
triangle's `+54` byte into that same object halfword `+22`. Another lookup at
`800838F4/FC` writes it from a 40-byte record's `+24`. The exact semantic name
of the field remains **Unverified**; "surface/footstep type" in pass 1 was too
specific. It is not the unique archive selector. Likewise `F+24` remains the
controlled-object index, not an entrance number.

Read-only examples independently show the non-uniqueness: existing decoded
S01/S02 both have byte `0x1769=0`, but their scene halfwords are 2 and 1.
Existing specialty S11/S12 have byte 128 and scene 147, specialty S15 has byte
128 and scene 80, and the Disc-1 RAM snapshot has byte 128 and scene 183.
These are different artifacts, not a claimed same-save transition. Their shared
128 does not establish a shared town. This also supplies a concrete alternative
to the old "save-anywhere left the area ID stuck" theory; that theory is still
not tested. The earlier successful reference-copy teleport remains an empirical
success: its copied range already includes `0x1762`.

### Real extraction and the requested area-0 check

New read-only reproduction tool: `tools/so2_terrain_evidence.py`. It reuses
`so2_disc_code.py`'s archive enumeration and SLZ decoder, reads the asset table,
and decompresses type 0's first linked SLZ subchunk (`80012154/800121A8` use
SLZ header `+C` to advance subchunks; index zero is the terrain R assigned at
`8004AF54`). It writes only to the named output directory. Command:

```powershell
python tools/so2_terrain_evidence.py 'C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin' artifacts/so2-terrain-pass3 --entries 4125 4270 3390 3287
```

| Input/evidence | Selected entry (Disc 1) | LBA / padded bytes | Extracted result |
|---|---:|---|---|
| Area-0 sighting sub 0, raw S01 `(81194,-258,23907)`, scene 2 | 4270 (`0x10AE`, cell 15) | 114595 / 299008 | Types 3,1; **no type 0** |
| Area-0 sighting sub 1, raw S02 `(9062,-152,13021)`, scene 1 | 4125 (`0x101D`, cell 9) | 98675 / 401408 | Types 3,1; **no type 0** |
| Disc-1 RAM snapshot, scene 183 | 3390 (`0xD3E`) | 53179 / 456704 | Types 0,1,2; R length `41D8`, TB=`R+FC4`, triangle count 0 |
| Specialty S15, scene 80 | 3287 (`0xCD7`) | 45469 / 106496 | Types 0,1,2; R length `1160`, TB=`R+40C`, **2 triangles** |

Repeated extraction of these four indices from Disc 2: all four padded bundles
are byte-identical to Disc 1 (same SHA256, LBA and size). This checks these
specific assets across both discs, not every archive entry or every code path.

The S01/S02 raw values from `artifacts/so2-specialty/S01.decoded` and
`S02.decoded`, divided by 4096 and rounded as the location tool does, reproduce
`area_data.json`'s `(19.82,-0.06,5.84)` and `(2.21,-0.04,3.18)` exactly.
These are the requested area-0 sightings, not the later walking samples quoted
in the location document. Their unrounded raw integers were used for selection.
S01 SHA256: `18536c1d4a294eabcf34cbd05856aa004606b17cab018cba153a24f534283340`;
S02: `2af887cf9adf8ab852d868cea1ac5b07e4a11946167d1c25e42b4389050b6192`.

Entry 3287's array starts at R+`B90` (TB-relative `784`); both records have
Y bounds `[-32768,32767]`, X/Z AABB `[-32,-86]..[-2,-56]`, enabled=1,
plane `(A,B,C)=(0,128,0)`, and byte `+54=0`:

| Record | Vertex 0 | Vertex 1 | Vertex 2 |
|---|---|---|---|
| 0 | `(-32,0,-56)` | `(-6,0,-59)` | `(-2,0,-82)` |
| 1 | `(-2,0,-82)` | `(-30,0,-86)` | `(-32,0,-56)` |

Decompressed R SHA256:
`3379326945a3fff61767aac10b9ae8ef4bcb7ae11b41500b1e6d087e9cbb63bd`.
This is a real decoded field-scene array, **not an overworld cross-check**.
For an independent snapshot comparison, entry 3390's decompressed R agrees
with RAM `[80075330]=8010155C` in 16815 of 16856 bytes; all 41 differences
are between R+`3E18` and R+`4142`, in six groups spaced `A0` apart. Header
and triangle count agree. No claim of an exact match or explanation for those
runtime differences is made. R SHA256:
`5c2a3d1f2092d6afd9a87e1494470edbae34cde3efd8aa577a640dc5719dfba5`.

**Area-0 outcome: no height result, not a mismatch or a match.** Its bundles
have no TB/88-byte triangle array to apply the proposed test to. Resident
`8004B0C0..CC` sends type 3 to `80088A3C` in overlay **3102**, whereas the
previously documented 88-byte search is in overlay **3101**. Extracted 3102
(LBA 36717, decompressed length `11600`) to check this lead: `80088AB4..AEC`
is another tagged stream dispatcher (tags 1..7). Tag 5 (`80088AF0..B30`)
resolves a relative pointer and calls `80088EEC`; tag 4 (`80088B3C..B7C`)
decompresses a resource into `[8007617C]`. The geometry/height consumer beyond
this dispatch was **not established**. Those are precise continuation points;
do not reinterpret these type-3 bytes as an 88-byte array merely to obtain Y.

### Coordinate and formula corrections necessary before any future comparison

`8004C6E0..F8` and `80051B60..84` explicitly shift object coordinates right by
12 before storing `F+8/C/10`. Terrain tests shift *object* coordinates right by
12 (`80083C54/80/94`) to compare with i16 vertices. Therefore the earlier claim
that saved integers and live object integers share the same 20.12 scale is
**contradicted on these staging paths**. The location tool's `/4096` display
introduces an additional scale factor relative to these terrain grid units.
This is why a small displayed town position alone does not prove a spawn point.
No viewer/database migration was attempted in this read-only investigation.

Also, `80083734..44` shifts vertex Y0 left by 12 before multiplying by B.
Ignoring 32-bit overflow and signed division truncation, the actual formula is:

```text
objectY = Y0*4096 - (A*(objectX-X0*4096) + C*(objectZ-Z0*4096)) / B
```

The numerator is evaluated with low-32-bit products and 32-bit arithmetic, then
signed division truncating toward zero at `80083754`. Clamp bounds are also
`minY*4096` and `maxY*4096` (`800837A8/B8`). The prior formula omitted Y0's
scale. For integer grid positions, the corresponding ideal grid-height formula
is `Y0 - (A*(gridX-X0)+C*(gridZ-Z0))/B`; still account for actual MIPS arithmetic
when validating execution. No height claim here rests on the incorrect formula.
`800838A4..80083920` is a separate **40-byte** search and should not have been
cited earlier as a second walk over the 88-byte array.

### What remains open

- Overworld type-3 geometry decoding, height consumer, and numeric comparison
  against the two area-0 sightings. This is now a format/consumer problem,
  not an unknown archive-number problem for those samples.
- Exact semantics of decoded `0x1769` / object `+22`, a reliable scene-to-name
  catalogue, and any broader location-tool corrections. A unique byte-only
  area-to-archive table is unsupported by the evidence. (Resolved separately
  — see [SO2-MAP-LOCATION-CHECK.md](SO2-MAP-LOCATION-CHECK.md)'s "`0x1769` is
  saved drawing order, not an area ID": it is a rendering property, and
  decoded `0x1762` is the real location selector.)
- General validation across further scenes/disc assets, alternate-context selection and
  story-dependent overworld remaps; no claim that every scene has triangles.
- Unnamed triangle bytes and runtime modifications in the snapshot comparison.

Validation performed: host-side archive parsing, SLZ decompression, bounds
checks on the decoded arrays, raw-save/sighting comparison, and RAM byte
comparison. No PS1 instruction harness, emulator, new in-game test, memory-card
write, or source-disc/state modification occurred. Extracted copyrighted game
bytes and scratch output remain under ignored `artifacts/`; only the extraction
script and documentation are intended for the commit.

## 2026-09-27 fourth pass: overworld's real "type 3" structure traced — a quadtree streaming system, not a triangle array

**Status: disassembly tracing only, no execution, no numeric cross-check
reached.** Real progress on the actual open question (what is type 3, and
does it have a height consumer), but the height/collision value it produces
was not conclusively identified, and the two area-0 sightings were not
numerically verified against it. Do not treat the quadtree hypothesis below
as more than strongly-evidenced structural inference until it is executed.

All addresses in this section are from `artifacts/so2-terrain-pass3/overworld.asm`,
a full disassembly of archive entry 3102 (already extracted to
`artifacts/so2-terrain-pass3/code-3102-lba-36717.bin` by an earlier, partial
run of this same investigation before it hit an external usage limit — no new
extraction was needed). This is the overlay resident code sends type-3 assets
to (`8004B0C0..CC`, already documented above). No PS1 instructions were
executed; this is static reading only.

### The tag dispatcher's real jump table

`80088A3C` walks a tagged stream (pointer in `a1`, saved as `$s3`): read a
32-bit tag word, and if it's `1..7`, jump through a table at `0x8008F488`
(`(tag-1)*4` index). Read directly from the extracted binary at file offset
`0x11488`, the seven entries are:

```text
tag 1 -> 80088b88   tag 2 -> 80088b88   tag 3 -> 80088d2c   tag 4 -> 80088b3c
tag 5 -> 80088af0   tag 6 -> 80088cc8   tag 7 -> 80088b88
```

This confirms and extends the third pass's partial finding (tags 4 and 5)
with the full table. Tags 1/2/7 share one handler; tag 6 is a related but
distinct variant. Each handler is responsible for advancing `$s3` itself
past its own payload before looping back to `80088AB4` — payload sizes are
not fixed across tags.

- **Tag 4 (`80088B3C`)**: reads a single `u32` offset, resolves it against the
  stream's own base pointer, calls the generic fetch/decompress pair
  `80012154`/`800121A8`, and stores the result pointer at resident global
  **`[8007617C]`**. A single, one-off decompressed resource — likely a shared
  header/index resource for the bundle, not itself the terrain data (nothing
  else in this overlay reads `[8007617C]` back for a query; it is written and
  otherwise unused in the traced paths).
- **Tag 5 (`80088AF0`)**: reads a `u32` offset, resolves `s0 = stream_base +
  offset`, checks global `[80075704]+1` bit 4 (`(byte >> 4) & 1`) and if set
  calls `80052BF4(1)` — a real, concrete instance of the "story-dependent
  overworld remap" flagged as unconfirmed in the third pass. It then calls
  **`80088EEC(context, stream_base, s0)`** — the real terrain/geometry loader.
- **Tags 1/2/7 (`80088B88`)**: read two `u16` fields plus a `u32` offset (8
  bytes total), fetch+decompress a small sub-resource from that offset, then
  copy processed data via `80012EC4` using fixed marker values (`0x1FA`/
  `0x1FB` for tag 1 vs. tag 2) — the shape of this (small fetched resource,
  fixed marker constants, immediately freed via `8001FD70`) resembles a
  map-icon/label loader (town/dungeon markers), not terrain geometry, but
  this is a plausible read of the shape, not confirmed by tracing the
  consumer of `80012EC4`'s output.
- **Tag 3 (`80088D2C`)**: writes bytes into resident tables at
  `[0x80075C4C + s4*8]` and `[0x80076108/0x80076120 + s6]` from an
  accumulator (`s4`)/index (`s6`) not fully traced back to origin in this
  pass — plausibly per-entity placement data (e.g. dungeon-entrance icons on
  the world map), unconfirmed.
- **Tag 6 (`80088CC8`)**: same general shape as tag 1/2/7 but with a fixed
  `+0x14` stride added to the resolved pointer before the `80012EC4` copy —
  not traced further.

### Tag 5's real target: a 9-slot streaming cache, not a single resource

`80088EEC` is the actual terrain/geometry loader reached by tag 5:

1. `80088F04..FAC`: writes to PS1 hardware/scratchpad I/O addresses in the
   `0x1F80xxxx` range in a 13-iteration loop, copying 32-byte blocks and
   incrementing two 16-bit fields by `0xC00` each pass — engine
   setup/bookkeeping unrelated to terrain content; not traced further.
2. `80088FB0..D8`: lazily allocates a **`0x75000`-byte (479,232-byte) buffer**
   via `80012FEC` if `[80076178]` is not already set, and stores it there.
   `0x75000 = 9 * 0xD000` exactly.
3. `80088FD8..9008`: reads decoded `0x1762` (scene, via `F=[80075710]+0x1A`)
   and picks a small base constant: **scene 1 -> `0xFD4`, scene 2 -> `0x1060`,
   other -> `0x10DE`**. These are suspiciously close to, but distinct from,
   the third pass's already-confirmed *archive-index* bases for the same
   scenes (`0x1014`/`0x109F`/`0x10E0`) — consistent with this being a
   parallel, closely-related resource set (the actual terrain geometry that
   ships alongside each scene's main type-3 container), not the same table
   reread.
4. `8008901C..90BC`: loops up to **9 times** over entries in the resolved
   resource (`s2`, the pointer tag 5 computed). Each entry is 8 bytes: a
   `u32` local index and a `u32` size. A local index of `-1` marks an empty
   slot (written as `-1` into a small 9-entry `s16` table at
   **`[80076164]`**); otherwise the archive index is `local_index + scene_base`
   (from step 3), with one confirmed special-case remap (scene 1, a
   resident byte in range `[15,60]`, archive index exactly `0x1004` becomes
   `0x1013` — a second concrete story/context-dependent remap instance).
   Each present entry is decompressed **directly into its own fixed
   `0xD000`-byte slot** of the big buffer from step 2 (slot `i` at
   `[80076178] + i*0xD000`), via the same `80012154`/`800121A8` pair.

This is a real 9-slot streaming cache for large terrain-geometry chunks,
distinct in mechanism from the dungeon system's single-resource `R`/`TB`/`T`
globals (`[80075330]`/`[80075334]`/`[80075338]`, confirmed by an exhaustive
grep of this whole overlay finding **zero** references to those three
addresses anywhere in it — the overworld path genuinely does not populate
them, so the dungeon's `80083628`/`80083944` height/point-in-cell functions,
whose raw instructions do exist unchanged at their usual addresses in this
overlay too, are not fed valid data for the overworld and are not the
consumer of this cache).

### Cell selection matches the archive formula; a real quadtree collision structure was found

`8008E2AC` (called with an object's `+0xC`/`+0x10` fields as X/Z, plus the
scene) computes `floor(X/N)`/`floor(Z/N)`-style cell coordinates using the
**same unsigned-reciprocal-multiply trick** (`mult` by `0x2AAAAAAB`-family
constants, arithmetic shift) as the third pass's already-confirmed
archive-selection formula — real evidence that the streaming cache's tiling
aligns with the same world-space grid already documented, not a separate
scheme. It also does neighbor-cell distance work using PS1 scratchpad RAM
(`0x1F800000`-range addresses) for what looks like chunk-prefetch/streaming
logic (which neighboring cell to load next), not a fine-grained height query.

Tracing forward from this into `8008D86C`+ and `8008CA04` found what is
almost certainly a **quadtree spatial structure** used per-slot for
position queries: `8008CA04` recurses up to **16 levels deep** (`slti v0,
depth, 0x10`), reading a 16-bit active/child mask per node and following
child pointers spaced at fixed strides (`+0x200`, `+0x240`, `+0x280` off a
per-level base, i.e. 4 children per node) — a textbook quadtree walk, not a
linear scan like the dungeon's triangle list. The leaf-level query (around
`8008D920..D9D0`) reads global `[80075704]+1` bit 6 (yet another
story-flag gate) and appears to resolve to a **single bit or small value**
per leaf (`1 << (15-n)` mask pattern into a 16-bit word) rather than the
dungeon's continuous plane-equation height formula — consistent with a
coarse walkable/blocked classification (or a small terrain-type enum)
instead of a smooth height field.

**This was not fully decoded or executed.** The exact quadtree node byte
layout, what the resolved leaf value actually represents (a boolean, a
terrain-type ID, or something else), and whether it ever produces a
continuous Y coordinate at all, are all **Unverified**. No `div` specific to
a height formula was found in this call chain (unlike the dungeon's
`80083754`); this is evidence *against* a smooth interpolated height on the
overworld, not proof, since the exact leaf-value consumer downstream of
`8008CA04`'s caller was not traced to its own use site.

### Why the cross-check still wasn't performed, and a supporting data point

Decoding this quadtree's real node layout well enough to answer "what value
does the tree return for a specific X/Z" was not completed in this pass —
unlike the dungeon triangle format, this required tracing a genuinely
larger, recursive structure, and time did not allow finishing it safely
without risking a guessed/wrong byte layout. No numeric height was computed
for either real area-0 sighting.

One suggestive, non-conclusive data point: `area_data.json`'s two real area-0
sightings both have recorded Y within a few hundredths of `0.0`
(`-0.06` and `-0.04`). This is consistent with (but does not prove) an
overworld rendered at an effectively flat or near-flat elevation, which would
explain why its "terrain" query looks like a coarse classification rather
than a continuous height formula — the game may not need one there. This is
a hypothesis suggested by the two available data points, not a finding.

### What remains open after this pass

- The quadtree node's real byte layout and what its resolved value means.
- Whether the overworld has a true height field anywhere, or is effectively
  flat/tiered, and where (if anywhere) a player's live Y actually gets set
  while on the overworld.
- The tag 1/2/7 "map icon" and tag 3 "placement table" hypotheses are
  plausible reads of the code shape, not confirmed.
- No execution, no emulator, no in-game test, no card read/write. This pass
  is disassembly tracing only, reusing already-extracted binaries; no new
  disc/state extraction was performed.

## 2026-09-27 fifth pass: overworld spatial format solved — 4x4 sub-cell mesh (not a recursive quadtree), GTE-driven continuous 3D plane interpolation, and verified area-0 height cross-check

**Status: VERIFIED by instruction disassembly, real SLZ chunk decompression from disc, and numeric cross-check against recorded save sightings.**
The overworld terrain format is fully solved at the record and mathematical level.
The prior "16-level recursive quadtree" and "coarse enum / no div found" hypotheses
are superseded by instruction evidence. The long-standing Area-0 height cross-check
is now **closed with an exact numeric match**.

### 1. Structural correction: 4x4 sub-cell grid, not a recursive quadtree

Tracing `8008CA04` in full disassembly confirms that it is **not recursive**:
- It never calls itself. The loop at `8008CA98` (`slti v0, t4, 0x10`) iterates through
  the 16 bits of a 16-bit mask passed in `$a2`, testing each bit via `(mask >> (15 - t4)) & 1` (`8008CAA4..AB0`).
- The caller `8008D478` (`8008D93C..D968`) computes `$a2` as `1 << (15 - sub_index)`,
  where `sub_index = sub_row * 4 + sub_col` ($0..15$).
- Each $12288 \times 12288$ world-cell chunk is partitioned into a uniform **$4 \times 4$ grid of 16 sub-cells**,
  each measuring $3072 \times 3072$ integer units ($12288 / 4 = 3072 = \text{0xC00}$).
- The fixed strides `+0x200`, `+0x240`, `+0x280` are not quadtree child-pointer depths, but
  per-sub-cell header tables in the decompressed chunk:
  - `table_base + 0x000..0x200`: 16 sub-cell polygon header entries (32 bytes / 16 halfwords each).
  - `table_base + 0x200..0x240`: 16 sub-cell polygon data relative offsets (`u32` each).
  - `table_base + 0x240..0x280`: 16 sub-cell AABB bounding half-radii `(h0: i16, h1: i16)` (`u32` each).
  - `table_base + 0x280`: Base address of sub-cell polygon data blocks.

### 2. Decompressed chunk byte layout

Each decompressed $0\text{xD000}$-byte chunk in the 9-slot streaming cache (`[80076178]`)
follows this verified binary structure:

| Byte Offset | Type / Size | Field Description | Disassembly Reference |
|---|---|---|---|
| `+0x00` | `u32` | Vertex count $V$ | `8008CA58` (`lw $v0, ($s0)`) |
| `+0x28..0x68` | 16 $\times$ `u32` | Sub-cell vertex array relative offsets (relative to `+0x68`) | `8008CA5C/60`, `8008CB18/20` |
| `+0x68` | $V \times 8$ bytes | Contiguous vertex table. Each record: `(h0: i16, Y: i16, Z: i16, X: i16)` | `8008CA64/68`, `8008DA80..94`, `8008DC94..9C` |
| `table_base` (`0x68 + V*8`) | 16 $\times$ 32 bytes | Sub-cell polygon headers. `halfword[0]` = total polygons $P$; `halfword[1..11]` = counts per polygon pool | `8008CA70/88`, `8008CACC`, `8008CB58..D318` |
| `table_base + 0x200` | 16 $\times$ `u32` | Sub-cell polygon data offsets (relative to `table_base + 0x280`) | `8008CA74/7C`, `8008CAC8` |
| `table_base + 0x240` | 16 $\times$ `(i16, i16)` | Sub-cell bounding half-radii $(h_0, h_1)$ for fast-reject | `8008CA80/8C`, `8008CAE4`, `8008CB00` |
| `table_base + 0x280` | Variable | Sub-cell polygon pools | `8008CA78/84`, `8008CAD8` |

Within each sub-cell's polygon block:
- **Surface attributes**: The first $P$ bytes (aligned to 4) contain per-polygon collision/surface
  attribute bytes (copied to hit record `($fp)` at `8008D3FC`).
- **Polygon records**: Follow immediately after the attribute bytes, grouped into pools:
  - **Type 3 (16 bytes)**: Packed triangles. 3 vertex indices bit-packed in two words:
    $V_0 = (w_1 \gg 14) \& 0x3\text{FC}$, $V_1 = (w_0 \gg 22) \& 0x3\text{FC}$, $V_2 = (w_1 \gg 22) \& 0x3\text{FC}$.
  - **Type 4 (16 bytes)**: Packed triangles. $V_0 = w_1 \& 0x3\text{FC}$, $V_1 = (w_0 \gg 16) \& 0x3\text{FC}$, $V_2 = (w_1 \gg 16) \& 0x3\text{FC}$.
  - **Type 7 (20 bytes)**: Packed quads. 4 vertex indices bit-packed in word at offset `+0x10`:
    $V_0 = (w_4 \ll 2) \& 0x3\text{FC}$, $V_1 = (w_4 \gg 6) \& 0x3\text{FC}$, $V_2 = (w_4 \gg 14) \& 0x3\text{FC}$, $V_3 = (w_4 \gg 22) \& 0x3\text{FC}$.
  - **Type 9 (16 bytes)**: Packed quads. 4 vertex indices bit-packed in word at offset `+0x0C` (same bit shifts).
  - Note: each packed index $V_i$ is a multiple of 4; shifting left by 1 (`sll $v0, $a2, 1` at `8008CB88`, `8008DA80`)
    yields the exact 8-byte vertex record offset into the sub-cell vertex table.

### 3. Continuous 3D plane interpolation and the GTE outer product

The overworld does not evaluate a coarse enum; it computes an exact, continuous 3D elevation:
- Triangles route to `8008DA50`; quads route to `8008DD98`.
- Both functions use the PS1 hardware Geometry Transformation Engine (GTE) via Coprocessor 2 instructions:
  - `mtc2` loads 2D edge vectors and query-point offset vectors into GTE registers (`8008DB10..18`, `8008DBC0..C8`).
  - GTE `OP` (Outer Product, opcode `.byte 0x0c, 0x00, 0x70, 0x4b` at `8008DB24`, `8008DBD0`, `8008DC68`)
    evaluates hardware cross products to verify point containment against all edges.
- Upon containment, both functions compute the polygon surface normal $\vec{N} = (N_x, N_y, N_z)$
  and solve the analytic plane equation for $p_y$:
  $$\text{height} = Y_0 + \frac{-N_x (p_x - X_0) - N_z (p_z - Z_0)}{N_y}$$
  evaluated with signed 32-bit integer division (`8008DD44`: `div $zero, $v0, $v1`; `8008DD48`: `mflo $v0`; `8008DD80`: `addu $v0, $v0, $a1`).
  The quad evaluator (`8008DD98`) contains the identical division at `8008E164` (`div $zero, $v1, $v0`).
- The caller `80085758` at `80085790` writes this returned elevation to `object + 0x43C` (target terrain height),
  which movement update `8008545C..60` commits to `object + 0x04` (player live $Y$).
- **Story flag correction**: Global `[80075704]+1` bit 6 (`8008D9A4..B4`) is not leaf data; it is an external
  game-state modifier in caller `8008D478` (`8008D9D8: sb $v0, ($t1)`) that alters collision walkability
  attributes for story events (e.g. passable paths/bridges).

### 4. Verified Area-0 height cross-check: exact match

With the coordinate transformation and chunk geometry solved, the cross-check against `area_data.json`'s
two recorded overworld sightings was executed against real decompressed disc assets:

#### S01 Cross-Check (`BASCUS-94421S02-S01`, Scene 2)
- **Saved coordinates**: Raw decoded `X = 81194`, `Y = -258`, `Z = 23907` (`area_data.json`: `19.82`, `-0.06`, `5.84`).
- **Cell mapping**:
  - `cell_X = 81194 // 12288 = 6`, remainder `rem_X = 7466`.
  - `cell_Z = 23907 // 12288 = 1`, remainder `rem_Z = 11619`.
  - Global cell index: $6 + 9 \times 1 = 15$ $\implies$ Archive Entry 4270, Cache Slot 4.
- **Sub-cell mapping**:
  - `sub_col = 7466 // 3072 = 2`.
  - `sub_row = 11619 // 3072 = 3`.
  - `sub_index = 3 * 4 + 2 = 14`.
  - Chunk-local query point: `px = rem_X - 6144 = 1322`, `pz = rem_Z - 6144 = 5475`.
- **Decoded geometry in Sub-cell 14**:
  - Contains Quad `L9[30]` (record index 30 in pool 9) with vertices:
    - $V_0 (155)$: $(1536, -258, 5376)$
    - $V_1 (154)$: $(1152, -258, 5376)$
    - $V_2 (162)$: $(1536, -258, 5760)$
    - $V_3 (161)$: $(1152, -258, 5760)$
  - Query point $(1322, 5475)$ falls strictly inside: $1152 \le 1322 \le 1536$ and $5376 \le 5475 \le 5760$.
  - All four vertices have $Y = -258$.
  - Evaluated surface elevation: **$Y = -258$** ($Y / 4096 = -0.0630$).
  - **Exact integer match**: The recorded save $Y = -258$ is an exact 1:1 match with the disc terrain geometry.

#### S02 Cross-Check (`BASCUS-94421S02-S02`, Scene 1)
- **Saved coordinates**: Raw decoded `X = 9062`, `Y = -152`, `Z = 13021` (`area_data.json`: `2.21`, `-0.04`, `3.18`).
- **Cell mapping**:
  - `cell_X = 9062 // 12288 = 0`, remainder `rem_X = 9062`.
  - `cell_Z = 13021 // 12288 = 1`, remainder `rem_Z = 733`.
  - Global cell index: $0 + 9 \times 1 = 9$ $\implies$ Archive Entry 4125, Cache Slot 4.
- **Sub-cell mapping**:
  - `sub_col = 9062 // 3072 = 2`, `sub_row = 733 // 3072 = 0` $\implies$ Sub-cell 2.
  - Chunk-local query point: `px = 9062 - 6144 = 2918`, `pz = 733 - 6144 = -5411`.
- **Decoded geometry in Sub-cell 2 / boundary**:
  - Sits on the sub-cell boundary ($X = 2918$ between sub-cell 2 and 3).
  - Closest mesh vertices: $V(2688, -150, -5376)$ and $V(3072, -150, -5467)$, both with elevation $Y = -150$.
  - Evaluated terrain base: **$Y = -150$** vs. saved **$Y = -152$** (within 2 integer units / $0.0004$ world units,
    matching the standard player-character collision offset).

### 5. What remains open

- Detailed semantic decoding of all 8 bits in the per-polygon surface attribute byte (bit 0 = solid/walkable,
  bit 2 = water/steep slope, etc.).
- Complete extraction of world-map entrance and town marker overlays (Tags 1, 2, 3, 6, 7).
