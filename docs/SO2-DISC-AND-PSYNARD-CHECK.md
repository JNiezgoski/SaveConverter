# SO2: required disc and persistent flying-mount position

Investigation: 2026-09-27, US PS1 SCUS-94421 / BASCUS-94421.
The two questions are answered separately below. All offsets called **decoded**
are in the decompressed `0x1B88`-byte body, not the physical memory-card block.

## 1. Disc 1 versus Disc 2: explicit field found

**Decoded `0x4C` is a one-byte, zero-based required-disc selector: `0` means
Disc 1; `1` means Disc 2.** Story-flag inference is unnecessary for this question.
This describes which disc the game requests, not a guarantee that an edited save's
story/location data is consistent with that disc. Other values are not established.

Let `S=[80075270]`. The field is part of the serializer's first `0x1A0` bytes,
so it is saved and restored without a special header field. Resident code reads it
and adds one before checking the loaded archive:

```text
80054248 lui   v0,8007
8005424C lw    v0,5270(v0)
80054250 nop
80054254 lbu   a1,4C(v0)
80054258 lui   a0,8007
8005425C lw    a0,525C(a0)
80054260 jal   80011D38
80054264 addiu a1,a1,1          ; delay slot: requested disc = saved byte + 1
```

The restoration path at `80048B34..80048B78` independently does the same check;
if its result is not 1 it calls `80052CE8` with `a1=S[4C]+1`, `a2=0`.
Another call at `80054664..80054678` passes that same disc number with `a2=1`.
The script-handler block below performs the explicit Disc-2 transition:

```text
80066C3C addiu a1,zero,2
80066C40 lui   v1,8007
80066C44 lw    v1,5270(v1)
80066C48 addiu v0,zero,1
80066C4C sb    v0,4C(v1)        ; persist Disc 2
80066C50 lui   a0,8007
80066C54 lw    a0,5284(a0)
80066C58 jal   80052CE8
80066C5C addiu a2,zero,1
```

The exact story scene/script invoking this block was not identified. The reader,
writer and physical-disc check establish the field independently of that scene.

### Why these calls really concern the disc

The base executable's `80011D38` checks archive magic `34829314` at context `+4`.
With valid magic it calls `80011B98` for index `requested_disc+5` and returns
whether the resulting archive entry size is nonzero:

```text
80011D44 lw    v0,4(a0)
80011D48 ori   v1,v1,9314       ; preceding lui v1,3482
80011D4C bne   v0,v1,80011D64  ; invalid archive returns 2
80011D50 nop
80011D54 jal   80011B98
80011D58 addiu a1,a1,5
80011D5C j     80011D68
80011D60 sltu  v0,zero,v0

80011B98 addu  v0,a0,a1
80011B9C sll   a1,a1,2
80011BA0 addu  a1,a1,a0
80011BA4 lhu   v1,6(a1)
80011BA8 lbu   v0,4804(v0)
80011BAC andi  v1,v1,FF00
80011BB0 or    v0,v0,v1
80011BB4 jr    ra
80011BB8 sll   v0,v0,B          ; size in bytes, sector count * 2048
```

Both actual disc images were opened read-only. Their SO2.BIN tables at ISO LBA
300 were decrypted using the established EXE algorithm, including zero-size
entries (which `archive_table()` normally omits):

| Inserted image | Entry 6 (request 1) | Entry 7 (request 2) |
|---|---|---|
| Disc 1 | LBA 380, 2048 bytes | zero size |
| Disc 2 | zero size | LBA 380, 2048 bytes |

Executing **the actual `80011D38` and `80011B98` instructions**, with these real
decrypted tables, returned `(1,0)` for requests `(1,2)` on Disc 1 and `(0,1)`
on Disc 2. No CD-identity host stub supplied these answers.

`80052CE8` forwards its requested disc to `8006F958` (`80052E10..18`). That
routine draws its prompt resources, calls the tray-change wait `80011E24` at
`8006FB24`, refreshes/checks the media via `80011EB4`, then calls `80011D38`
with the requested disc at `8006FB64..6C`. Only result 1 exits at `8006FC00`;
the wrong-disc path displays another prompt and loops. The prompt is resource
data, not an ASCII "insert disc" string in the resident binary. The hardware/UI
loop was inspected, not emulated by the verification harness.

**Correction relevant to the earlier map note:** `80011B98` is demonstrably an
archive-entry-size getter, not a UI/object dispatcher. Its EXE instructions above
were checked against the existing Disc-2 RAM dump and both discs' EXE payloads.
The map note's contrary inference from a caller is superseded. This does not
establish the contents of any area-name resource or require another asset search.

## 2. Psynard: persistent parking state, separate from the party

**A separate, saved parking-position mechanism exists for the rideable flying
object. The resident behavior identifies it as the Psynard with high confidence:**
an interaction near object slot 13 replaces the controlled object with that object,
sets an airborne bit, animates ascent, checks terrain before landing, saves its
landing position, and later spawns object 13 from those saved coordinates.
This is behavioral identification; no text label or rendered sprite was decoded
to independently name object 13, and no new live mounting test was performed.

It is therefore not supported to describe this flying object as stateless,
fixed-position, or always spawned at the player's current position. Both the
parking writer and spawn-coordinate reader are in the **already-extracted
resident code**, not blocked behind an unidentified overlay.

Let `F=[80075710]` and `G=[80075704]`. The established staging/serializer maps
`F+[0,2A0)` to decoded `[1748,19E8)` and `G+[0,170)` to `[19E8,1B58)`.

| State | RAM-relative field | Decoded offset | Evidence/qualification |
|---|---|---|---|
| Parking bank A X/Y/Z | F+26C / F+28C / F+270 | `19B4 / 19D4 / 19B8` | signed 32-bit coordinates; chosen when F+1A is 1 |
| Parking bank B X/Y/Z | F+274 / F+290 / F+278 | `19BC / 19D8 / 19C0` | signed 32-bit coordinates; other branch |
| Bank selector | F+1A, signed halfword | `1762` | compare to 1; do not rename its other modes/worlds from this pass |
| Associated bank halfwords | F+27C / F+27E | `19C4 / 19C6` | `8004C780/7AC` copy F+21 here; broader meaning not assigned |
| Flying-object presence gate | G+1 bit 3 | `19E9`, mask `08` | controls spawn and interaction; acquisition story writer not mapped |
| Riding/airborne state | G+1 bit 4 | `19E9`, mask `10` | set during mount, cleared during dismount |

These coordinate words have the same integer scale as the saved player XYZ at
`1750/1754/1758`. Runtime object coordinates are shifted right by 12 before the
landing writer stores them. No arbitrary float or world-unit interpretation is
needed to copy/read the words.

### Interaction, object replacement and state bit

`8004CE44..8004D068` gates interaction on the field-mode byte at `[7570C]+68`,
presence bit 3, input-mask checks, and riding bit 4 being clear. It reads the
mount pointer from **`80075394 = 80075360 + 13*4`**, and the controlled object
from `table[F[24]]`. `8004CF70..8004CFC4` computes their three-dimensional
distance from fixed-point coordinates; `8004CFC8` tests distance `<0x105`.
On success, `8004D064/68` selects state 9. The state-table entry at `80073008`
points to `8004EB84`, the mount continuation.

After its animation-ready check and removal of the old controlled object:

```text
8004EBE4 lw    a0,5710(a0)      ; F
8004EBEC lbu   v0,24(a0)        ; controlled-object table index
8004EBF4 lw    v1,5394(v1)      ; object 13
8004EBF8 sll   v0,v0,2
8004EBFC addu  v0,v0,s0         ; s0 = 80075360
8004EC00 sw    v1,0(v0)         ; object 13 becomes controlled object
8004EC08 sw    zero,5394(at)    ; clear former parked-object slot
...
8004ED28 lw    v1,5704(v1)      ; G
8004ED38 lbu   v0,1(v1)
8004ED40 ori   v0,v0,10
8004ED44 sb    v0,1(v1)         ; airborne bit
```

This is a **runtime object-pointer replacement**, not a new party member or
an extended value of decoded `0x41`. No instruction in these transfer/flag
slices writes `S+41` or either party array. The existing leader validator
`80052FF4..80053154` still interprets `S+41` as a primary-record slot (`slot*60`)
and accepts character IDs 1..12. It has no Psynard special case. This does not
claim every renderer reads `0x41` directly; that consumer remains a separate issue.

The pointer table itself is used for **live objects**: `80043890` indexes it,
allocates an object, calls an overlay constructor (`80082E5C` in the field-mode
branch), and stores the resulting pointer at `80043968`. Thus the old map note's
"194 area-entrance definitions" interpretation cannot be applied to these
entries. A bounds check of 194 establishes an index limit, not an area-name list.
This explains how the table can supply moving character/mount coordinates.

### Dismount writes parking coordinates; later spawn reads them

`8004D070..8004D444` tests the alternate input mask and riding bit. It performs
terrain/proximity checks (including calls to the field overlay at `8008D478`),
prepares landing position/height, and clears the riding bit:

```text
8004D3A0 lw    a0,5704(a0)
8004D3AC lbu   v0,1(a0)
8004D3B4 andi  v0,v0,EF
8004D3B8 sb    v0,1(a0)
```

The ordinary success path selects state `0xC` at `8004D430..440`; its table
entry `80073014` points to `8004F090`. After descent, that continuation removes
object 13's old slot (`8004F174/178`), moves the controlled mount pointer back
to slot 13 (`8004F1A8/1AC`), and recreates the walking object via `80043890`.
Its parking write follows conversion of the landed XYZ to integer coordinates:

```text
8004F270 lw    a0,5710(a0)      ; F
8004F288 lh    v1,1A(a0)
8004F28C addiu v0,zero,1
8004F290 bne   v1,v0,8004F2B4
8004F294 nop
8004F298 sw    a3,26C(a0)       ; bank A X
8004F29C lw    v0,54(sp)        ; landed Y
8004F2A4 sw    v0,28C(a0)
8004F2A8 lw    v0,58(sp)        ; landed Z
8004F2AC j     8004F2D0
8004F2B0 sw    v0,270(a0)
8004F2B4 sw    a3,274(a0)       ; bank B X
8004F2B8 lw    v0,54(sp)
8004F2C0 sw    v0,290(a0)
8004F2C4 lw    v0,58(sp)
8004F2CC sw    v0,278(a0)
```

The spawn path at `8005561C..800556F4` checks presence bit 3, chooses the same
bank using `lh ...,1A(F)`, copies its XYZ to `sp+58`, and calls `80043890` with
`a1=a2=13` while dismounted and `a3=sp+58`. When riding bit 4 is set it instead
uses the current controlled-object index. It does **not** substitute the player's
saved XYZ for the parked mount. `80054404..80054478` also restores the selected
parking coordinates into the player-position fields when both bits are set.

The earlier map note's suggestion that these extra coordinate slots might be a
camera-pan pair is superseded by this writer-to-spawn trace. A script opcode also
writes the two banks (`80067B38..80067BC0`), so they need not only change on landing.

### Real save values and executed checks

S01 and S02 below match checksum-valid blocks in the existing workspace copy
`artifacts/so2-inventory/source-live-card-20260926.mcd` byte-for-byte after decoding.
The reproduction records card, block, decoded-fixture and code SHA256 hashes.

| Fixture | Disc byte | G+1 | F+1A | Player XYZ | Selected parked XYZ |
|---|---:|---:|---:|---|---|
| S01 | 1 | 08 | 2 | 81194, -258, 23907 | 81659, -258, 23764 |
| S02 | 1 | 08 | 1 | 9062, -152, 13021 | 9727, -186, 13197 |

These dismounted saves contain distinct player and parked-object positions.
Their selected bank values also differ between saves. This is consistent with
the code's persistent parking behavior, without pretending these are a controlled
before/after flight pair.

**The user states saving while riding is prohibited.** No riding save was sought
or asserted. Bit-4 execution tests explicitly modify RAM in the isolated harness;
they are not captured game saves. The bit is within a serialized region, but its
normal savable value is clear. No cheat-based riding capture is needed here.

## Reproduction, sources and limits

```powershell
python artifacts/so2-disc-psynard/verify.py
```

Outputs: [instruction listings](../artifacts/so2-disc-psynard/evidence.asm),
[assertion results and hashes](../artifacts/so2-disc-psynard/results.json),
[bounded verification source](../artifacts/so2-disc-psynard/verify.py).

| Code source | Disc location | Load |
|---|---|---|
| Existing entry 2576, `artifacts/so2-fol/disc-code/code-2576-lba-30736.bin` | Disc 1 SO2.BIN, LBA 30736 | `8002F810` |
| Existing entry 2998, `code-2998-lba-36213.bin` | Disc 1 SO2.BIN, LBA 36213 | `8007E000` |
| Base PS-X EXE, same payload on both discs | EXE LBA 24, payload LBA 25, size `1F800` | `80010000` |

No new archive overlays were extracted. The EXE payload was read to settle the
previously unverified below-resident calls; a reproducible copy is in the evidence
directory. The resident SHA256 remains
`6dec3950348b57068a85759f472ea7d5c92241d28b00ff4ea139ddd8dc1587cf`;
the EXE payload SHA256 is
`9bd6d6c52056c2a8c91633ab44900ae687a67ba51bf29ed4d8f8c87e83f96a4b`.

All checks passed: four physical-disc/request combinations, then nine existing
decoded fixtures through the real codec, disc reader/transition writer, complete
leader validator, resource-E staging routine, object-13 transfer, mount/dismount
bit tails, and both parking-write/spawn-argument branches. Synthetic branch
inputs select both banks even for early saves with no mount; this verifies code
behavior, not mount ownership in those saves. The staging test executes
`80055FC8` with only resource-E lookup supplied by a host hook. The parking-write
test asserts its entire write set is exactly the chosen three words. Spawn tests
stop before the overlay constructor, after verifying its actual arguments.

The harness executes extracted MIPS with branch delay slots and immediate loads,
using the project's bounded interpreter. Basic-block tests seed documented
registers and stop at explicit boundaries; they do not silently skip unknown
game calls. Full proximity/terrain/animation/rendering and physical disc swapping
were not executed. Remaining overlay calls limit full-game simulation, **not**
the proven existence and persistence of the parking coordinates. A live test
parking the Psynard twice would independently close the remaining visual identity
and gameplay-validation gap.

The latest cross-area teleport bundle in
[the map investigation](SO2-MAP-LOCATION-CHECK.md) remains a separate live result:
`[1750,1765)`, byte `1769`, byte `1880`, byte `1A45`, and `[1B58,1B88)`.
It includes the bank selector but not these parking banks. That test does not
establish how arbitrary cross-world edits should reconcile mount state.
No editor was added: reading the disc byte is simple; changing disc/parking state
without coherent story and location state has not been live-validated.

All writes in this investigation were confined to `C:/CodeTesting/SaveConverter`.
Nothing under `C:/CodeTesting/StarOcean2/SaveGames` was touched.

## 2026-09-27 live test: Psynard parking-position edit confirmed working in-game

Closes the "visual identity and gameplay-validation gap" noted above. Took a real
save (S01, card slot 1), read the currently-selected parking bank via the bank
selector (`0x1762`), and overwrote only that bank's X/Z words (decoded
`0x19BC`/`0x19C0` for bank B, the selected bank in this save) with a small offset
from the player's own position. Verified round-trip, checksum, and that exactly
the 4 intended bytes changed and nothing else in the save.

**First attempt (offset ~12 units, chosen without a real distance reference):
the user could not find the mount at all ("flew him somewhere I cannot reach").**
Reconciled against the earlier live-tested Hoffman-to-Linga walk, which spanned
several real towns for only ~20 units of position delta - a 12-unit offset was
therefore roughly half that entire journey's distance, almost certainly placing
the mount far outside visual/walking range rather than indicating a broken edit.

**Second attempt, offset reduced to ~1.5 units: user confirmed seeing the mount
at the new location** ("I see him... behind a red wall I cannot reach, but I see
where you moved him"). The placement landing on an impassable terrain object is
an artifact of not choosing a walkable exact coordinate, not a failure of the
edit - the mount visibly appeared exactly where a ~1.5-unit eastward shift should
put it.

**Conclusion: editing the Psynard's parking coordinates directly moves it,
confirmed live, using the same decode/edit/verify/re-encode pattern as every
other teleport in this project.** No new tool built yet; the same manual pattern
used for the player teleport applies here (edit `0x19B4`/`0x19D4`/`0x19B8` for
bank A or `0x19BC`/`0x19D8`/`0x19C0` for bank B, whichever `0x1762` currently
selects). A future `so2_location.py`-style helper could fold this in once a
convenient way to pick "somewhere walkable" is worked out (e.g. reusing an
already-recorded player-position sighting as the target, which is what both
live tests here did).
