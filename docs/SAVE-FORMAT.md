# Star Ocean: The Second Story (PS1, US) — Save Format Reference

Everything below was reverse-engineered directly from real save files and the game's own screens —
no published spec exists for this format. Every field is tagged with how confident we are in it.

*(The anatomy diagram that used to live here was removed 2026-09-25 — it depicted the old raw-offset
byte map, which the compression discovery below made misleading. Redo it once the compressed region
is more fully mapped.)*

## Status tags

| Tag | Meaning |
|---|---|
| **VERIFIED** | Matched against a number the game displayed, or a controlled before/after diff of a real in-game save |
| **LIKELY** | Fits every sample seen, but not directly confirmed by the game |
| **OPEN** | Located but not understood, or not located at all — do not write to it |

## Layout at a glance

**2026-09-25 compression correction:** The body at `0x382` is a zero-run
compressed stream, prefixed by its u16 compressed length at `0x380`.
`00 00 N` means `N+2` zeros. Many apparent record tags and variable field
widths in the historical observations below are compression artifacts.
Fixed encoded offsets must not be used as general editing rules.
Fol is a u32 at **decoded-state offset `0x18`**, as established from the
loader, menu, and shop code. See [the Fol investigation](SO2-FOL-INVESTIGATION.md)
and use `so2_fol.py` to decode, edit, re-encode, and sign.

One memory card block is **8,192 bytes**. `q` below means "the start of a given character's HP block
inside the party records"; `name` means "the start of that character's name string inside the character
entries." Both vary per save — they're found by scanning, not fixed offsets.

| Offset | Field |
|---|---|
| `0x0000–0x01FF` | PS1 save header, title, 3 icon animation frames (not game data) |
| `0x0200` | Game data starts — ASCII signature `STAR OCEAN 03/01` |
| `0x0210` u32 | Checksum A |
| `0x0214` u32 | Checksum B |
| `0x021A` u16 | `C` — end-of-data offset |
| `0x0234–0x0253` | Party list: 8 × (u16 character ID, u16 level) — **this drives the load-screen portrait**, independent of the party record itself |
| `0x0380–0x04FF` | Options and misc. state (see table below) |
| `0x0500–0x082F` | Party records — up to 8 members, variable length, in party order |
| `0x0830–0x0EFF` | Character entries — one per character, variable length |
| `0x0EEC–0x0F67` | Default name table (shared, not per-save) |
| `C`–`0x1FFF` | Trailing buffer — uninitialized, not real data |

### Checksums (recompute after any edit)

```
zero A (4 bytes), B (4 bytes), and marker at 0x218 (2 bytes)
B = sum of bytes [0, C) as u32
A = sum of bytes [0x200, 0x280) as u32   (includes B; compute B first)
restore marker (0x5555)
```
Implemented as `so2_sign()` in `saveconv.py`. Confirmed from the game's MIPS checksum
writer and validators on 2026-09-25; see [investigation and evidence](SO2-CHECKSUM-INVESTIGATION.md).
The older `[0x206, 0x281)` rule was an accidental match when byte `0x280` was `0xFF`.

## The 12 character IDs

| ID | Character | ID | Character |
|---|---|---|---|
| 1 | Hero slot (Claude or Rena, by route) | 7 | Ashton |
| 2 | The other lead (Rena or Claude) | 8 | Leon |
| 3 | Celine | 9 | Opera |
| 4 | Bowman | 10 | Ernest |
| 5 | Dias | 11 | Noel |
| 6 | Precis | 12 | Chisato |

Route exclusivity (enforced by story scripts, not the save file): Leon is Claude-route only, Dias is
Rena-route only; Ashton excludes Opera and Ernest; Precis excludes Bowman; Chisato needs a free slot.
The save's own string for Claude is literally `Crawd` (both in his name entry and the default name table).

## Party record — two parallel arrays, not one

**Corrected 2026-09-26 by actual game-code execution.** Everything in this section used to describe
a single per-member record at raw, pre-compression offsets (`q`). That was wrong in an important way,
not just an addressing-scheme mixup: there are **two separate fixed-size arrays**, both indexed by
the same 0..7 slot number, and identity/party-membership is carried by a **signed numeric character ID**
in the first array — not by the ASCII name string, and not derivable from name/equipment alone. See
[SO2-PARTY-MEMBER-INVESTIGATION.md](SO2-PARTY-MEMBER-INVESTIGATION.md) for full disassembly evidence,
RAM pointers, and the recruitment routine; summary:

| Array | Decoded base | Stride | Contents |
|---|---:|---:|---|
| Primary | `0x1a0` | `0x60` | Signed 16-bit character **ID** at `+0` (this is the real "is this slot a party member" test: `id > 0`; `id == 0` is vacant; a **negative** ID means the character was removed but their records are retained, not deleted), plus EXP (+10), HP (+14/+18/+1C), MP (+20/+22/+24), level (+28, adjusted +26), STR/CON/AGL/DEX/INT/GUTS triplets (+2A/+30/+36/+3C/+42/+48); unknown triplets +4E/+54 |
| Secondary | `0x4a0` | `0xd0` | LUC triplet at +00/+02/+04, STM triplet at +06/+08/+0A; 7×u16 equipment IDs at `+0xc` (absolute `0x4ac + slot*0xd0` — weapon/armor/shield/helmet/greaves/acc1/acc2, `0`=empty), a capped 0-999 value, the 10-bit talent mask at `+0x20`, an 8-byte null-padded ASCII name at `+0x24`, then skill/ability data |

Only slots 0-3 are the active battle formation; slots 4-7 are ordinary reserves (still real party
members, just not in combat). Renaming or cloning the **secondary** record alone (what earlier,
pre-investigation attempts in this project tried) does nothing observable in-game, because the
primary array's numeric ID is what every identity-dependent system actually checks — equipment
eligibility, portraits, and the party-menu presence test all read the primary ID, never the name
string. Use `so2_party.py` to add a party member correctly: it executes the game's actual
initializer code for both arrays together rather than hand-splicing either one.

A separate, purely cosmetic **load-screen preview table** lives in the *uncompressed* header at raw
offset `0x234` (8 × u16 ID, u16 level pairs, one per slot, same slot indexing as the arrays above) —
this is what the memory-card load menu reads to show a quick party portrait without decompressing
the save. It is a cached snapshot, **only refreshed by an actual in-game save**, so a save produced
by external tooling will show the old party on the load screen until the game itself saves again.
It's plain, uncompressed data (no zero-run codec involved) so it's safe to patch directly with
`so2_sign()` afterward — just keep it in sync with whatever the primary/secondary arrays actually say.

**2026-09-27 primary-map extension:** [Full field map and instruction evidence](SO2-PARTY-MEMBER-INVESTIGATION.md#primary-record-complete-byte-coverage-partial-semantic-map-2026-09-27)
now covers all 96 bytes: 66 bytes assigned to named field families, 12 bytes in two
unnamed halfword triplets, and 18 opaque bytes. Four complete initializer store
walks (Claude/Celine/Bowman/Opera), all-twelve execution checks and current
S01/S02/S15 decoded records support the map. This is code/record evidence, not
new live verification of stat editing. INT is a notable exception: initialization
writes only +46, leaving +42/+44 zero; later recalculation uses the normal triplet.
LUC/STM have been relocated to the secondary array's first 12 bytes. The old
encoded offsets below remain superseded.

Everything below this point (per-field stat offsets, GUTS base/effective test, EXP/HP/MP field
widths) described the *old*, pre-compression, single-record model and has not been re-verified
against the corrected two-array layout — treat these old sub-offsets as superseded, not wrong per se,
until someone re-locates each field inside the real primary/secondary arrays above.

## Character entry (relative to `name`, the start of the character's name string)

### Extended stats

| Field | Layout | Status |
|---|---|---|
| LUC | u16 ×3: (base, base, effective) | VERIFIED |
| STM | u16 ×3: (base, base, effective) | VERIFIED |

"Effective" is what the Status screen shows (includes equipment). Both sit roughly 25–40 bytes before
`name`; writing here blind is unsafe — locate them by walking backward from the SP block instead.

### Talent mask

One u16 bitmask, immediately before the SP block:

| Entry ends in | Mask offset |
|---|---|
| `... 00 01` (class-1) | `name - 4` |
| `... 00 00 00` (class-0) | `name - 5` |

| Bit | Talent | Bit | Talent |
|---|---|---|---|
| 0 | Originality | 5 | Sense of Rhythm |
| 1 | Sense of Taste | 6 | Pitch |
| 2 | Dexterity | 7 | Love of Animals |
| 3 | Sense of Design | 8 | Sixth Sense |
| 4 | Writing Ability | 9 | The Blessing of Mana (normally unobtainable in play) |

`0x3FF` = all ten. **VERIFIED** on all 16 tested character-slots across both classes; a fixed-width u16
write in place, no length shift. Gaining a talent normally also awards 100 SP — writing the mask directly
does not award that SP.

### SP (skill points to spend) — variable-width block

SP is **not** a fixed 2-byte field. It's a variable-width block that the game itself resizes as SP
crosses 0 and 256:

```
zero  (SP = 0)     :  00 00 <marker>                                    no SP bytes at all
small (SP 1-255)   :  00 00 <prefix> <SP u8> 00 00 <marker=0x03>
large (SP >= 256)  :  00 00 <prefix> <SP u8 lo> <SP u8 hi> 00 00 <marker=0x02>   (+1 byte vs. small)
```
followed by `<talent mask u16>` then the trailer (`00 00 00` for class-0, `00 01` for class-1) then `name`.

| Form | SP u16 location |
|---|---|
| Class-1 large (Claude, Opera, Ernest, Ashton, Dias, Bowman, Precis, Chisato ≥256) | `name - 9` |
| Class-0 large (Rena, Celine, Leon, Noel) | `name - 10` |

**Rules, all VERIFIED in-game:**
- small → large: replace `[prefix, lo, 00, 00, 0x03]` with `[prefix, lo, hi, 00, 00, 0x02]` (**+1 byte**, `C += 1`)
- zero → value: **replace** the marker byte in place with `[prefix, SP bytes, 00, 00, marker]` — do **not** cut or insert around the existing `00 00` before it
- the game switches form by itself as SP crosses 0/256 — only ever convert a form the game has actually written for that character; if unsure, trigger one real level-up first and read what it wrote
- prefix byte is character/slot-specific and must be preserved as-is (values seen: `0x02`, `0x05`, `0x0A`, others)
- zero-form marker byte is also character/slot-specific (values seen: Leon `0x08`, Bowman `0x04`, Noel `0x0B`, Chisato `0x10`)

Tool: `so2_refill_sp.py` implements this for all 12 characters, all forms, both classes.

### Equipment

Two known layouts, both immediately before the SP block:

**Full (7 slots, no marker)** — the common case:
```
[weapon][armor][shield][helmet][greaves][acc1][acc2]   <- ends right at the SP block
```

**Compressed (6 slots, missing one item) — one accessory slot absent:**
```
[acc1][weapon][armor][shield][helmet][greaves]  00 00 <prefix>   <- then the SP block
```
Confirmed for Celine, Leon, Noel (in the save where he's missing accessory 2), Precis. Reordering
(accessory1 moves to the front) plus 2 bytes, not just a shorter version of the 7-slot block.

The trailing `00 00 <prefix>` is **not a special equipment marker** — it's just the SP block's own
leading bytes (see the SP section above), sitting with no separator right after the item list. The
byte is whatever that character's personal SP prefix happens to be (`0x02` for most, but `0x05` for
Noel in some saves, `0x0A` for Chisato). An earlier version of this code only recognized literal
`0x02`, which silently misread any character with a different prefix as a full 7-slot entry — fixed,
detection is now `d[sp0-3:sp0-1] == 00 00` regardless of the third byte.

| Status | Detail |
|---|---|
| VERIFIED | Full 7-slot layout; the 6-slot missing-accessory-2 layout above; Noel (full 7 slots in the current Game 2 save — confirmed exact match: Serpent's Tooth / Valiant Mail / Rare Gauntlets / Banded Helm / Bunny Shoe / Tri-emblem ×2); Chisato (also full 7 slots in the current save — confirmed exact match: Stun Gun / Bloody Armor / Star Guard / Bloody Helm / Mud Boots / Angle Hair / Atlas Ring) |
| OPEN (edge case only, not currently blocking) | The compressed layout for a genuinely **empty armor slot** was seen once (Chisato's marker was `0x0A`, armor showed "(None)") but never solved before she re-equipped armor — if a future save has any character missing armor specifically, that byte order is still unmapped |

Tool: `so2_equip.py`. Item ID table: `item_ids.txt` (save ID = published CodeBreaker code − `0x5000`).

**Weapon type per character** (use to sanity-check any decoded weapon — a mismatch means the read is wrong):

| Type | Characters |
|---|---|
| Sword | Claude, Dias |
| Dual-Sword | Ashton |
| Knuckles | Bowman, Rena, Noel |
| Kaleidoscope | Opera |
| Whip | Ernest |
| Book | Leon |
| Staff/Rod | Celine |
| Hand | Precis |
| Gun | Chisato |

Universal items that appear on multiple different-type characters' lists (don't use these to infer
type): All-Purpose Knife, Funny Slayer, Million Staff, Weird Slayer.

### Name

ASCII, no terminator, followed by `00 00`, followed by one byte = `20 - len(name)`. A different-length
name shifts every following byte and changes `C` — rename in-game rather than by hand.

### Skill levels

46 consecutive bytes after the name and a 33-byte flag run (purpose of the flag run: OPEN), one byte per
skill, `0`–`10` (10 = maxed). **VERIFIED** on all 16 tested character-slots.

| # | Skill | # | Skill | # | Skill | # | Skill |
|---|---|---|---|---|---|---|---|
| 0 | Sketching | 12 | Danger Sense | 24 | Piety | 36 | Feint |
| 1 | Musical Notation | 13 | Biology | 25 | Playfulness | 37 | Mental Training |
| 2 | Music Instrument | 14 | Mental Science | 26 | Functionality | 38 | Motormouth |
| 3 | Tool Knowledge | 15 | Kitchen Knife | 27 | Courage | 39 | Body Control |
| 4 | Mineralogy | 16 | Recipe | 28 | Poker Face | 40 | Spirit Force |
| 5 | Herbal Medicine | 17 | Good Eye | 29 | Copying | 41 | Parry |
| 6 | Craft | 18 | Whistling | 30 | Mech Knowledge | 42 | Cancel |
| 7 | Esthetic Sense | 19 | Animal Training | 31 | Mech Operation | 43 | Gale |
| 8 | Writing | 20 | Metal Casting | 32 | Below the Belt | 44 | Provocation |
| 9 | Effort | 21 | Scientific Ability | 33 | Strong Blow | 45 | Float |
| 10 | Perseverance | 22 | Fairyology | 34 | Flip | | |
| 11 | Patience | 23 | Radar | 35 | Counterattack | | |

## Inventory

**Corrected 2026-09-26 by actual game-code execution.** See
[SO2-INVENTORY-ADD-INVESTIGATION.md](SO2-INVENTORY-ADD-INVESTIGATION.md)
for disassembly, RAM pointers, first-time addition tool, and Seraphic Garb x20 candidate.

The decoded inventory is a **fixed 1,024-slot u16 array at `[0xB20,0x1320)`**,
within the `0xC28`-byte allocation pointed to by RAM `[0x80075278]`.
These decoded offsets do not vary with party size. Compressed card offsets do.

```python
item_id = word & 0x3ff
count = (word >> 10) & 0x1f  # max normal stack 20
flag = word >> 15            # separate flag, set by shop/script add callers
```

General add routine `0x8003C594` updates an existing occupied type or overwrites
the first count-zero slot. It scans through holes; no sorted insertion, item-count
counter, sentinel relocation, or decoded-byte shifting is required. Removal clears
the fixed word when its count reaches zero. The formerly described three-byte
"tombstone" is a zero-run compression token, not an inventory record.

The routine also maintains 16 recent IDs at decoded `[0x1320,0x1340)` and runtime
integrity bytes at `[0x1344,0x1744)`. The serializer saves those integrity bytes as
zeros and rebuilds them on load. It does not sort/compact the inventory on save.

Use `so2_inventory.py` for a new item type: decode, execute the actual add routine,
re-encode, update compressed length and C, sign, and verify preservation. Never
splice a word into the compressed stream or insert bytes into the decoded state.
The new candidate has passed actual add/serializer instruction execution and all
unit tests; it has not yet been loaded in-game. The exact two historical failed
files were not analyzed, so their individual corruption causes remain unproven.

## Options / misc. state (`0x0380`–`0x04FF`)

| Offset | Field | Status |
|---|---|---|
| `0x0382` / `0x0384` / `0x0386` / `0x0388` | u16 button codes: confirm / cancel / menu / move (`0x40` X, `0x20` Circle, `0x10` Triangle, `0x80` Square) | VERIFIED |
| `0x021C` / `0x0392` | u16 playtime in minutes (two copies) | VERIFIED |
| `0x0220` | u8, save counter (increments every save) | VERIFIED |
| `0x0254` | u8, a second independent save counter | VERIFIED |
| Decoded state `0x18` | u32 LE Fol; encoded location and length vary with zero-run compression | GAME-CODE VERIFIED; see [evidence](SO2-FOL-INVESTIGATION.md) |
| `0x04EC` | u16(?), counts down — likely steps-until-next-random-encounter | LIKELY |
| `0x0280`–`0x0290` | Grows in small bursts per save — likely tied to the "discovered areas" list | LIKELY |
| `0x0380` | Changes unpredictably — likely an RNG seed | LIKELY |

**Message speed and audio mode (Mono/Stereo/Surround) — attempted, not solved, and the attempt itself
revealed something important.** Both were tested with tight, controlled, single-variable before/after
saves (only that one setting changed each time):

- **Audio mode** gave a real, reproducible partial signal: `0x03CB` read `1` for Stereo, `2` for
  Surround, and `1` again for Mono — consistent with a "Surround enabled" flag rather than a 3-way
  channel value (Stereo and Mono share the same reading; only Surround differs). Not confirmed further.
- **Message speed** gave nothing at all in this region — comparing saves at speed 2, 8, and 1, no byte
  in `0x0380`–`0x04FF` held those values in any form (exact match or otherwise).
- Both tests turned up a much bigger, unexplained finding: a large cascade of scattered byte changes
  elsewhere in the file on *every* save tested, even when only one setting was deliberately changed -
  once inside `0x0380`+ near the audio test, and once deep in the inventory/name-table region
  (`0x0FC9`–`0x113B`) during the message-speed test. This isn't noise localized to one known counter
  (RNG seed, step counter, etc.) - it's a broader background drift that can reach far into the file on
  a normal save, independent of user action, and it swamps simple before/after diffing for anything
  that doesn't produce a large, obvious signal like inventory counts or equipment IDs did.
- **Takeaway for next time:** don't expect a clean single-byte diff for a setting like this. Either the
  signal is a small flag buried among a lot of coincidental noise (as with the audio 0x03CB candidate,
  which took an exact-value table across 3 saves to even notice), or it needs many repeated trials to
  separate real signal from this drift statistically, rather than 2-3 saves and a byte-by-byte diff.
- **Third confirmation, different region again:** a third attempt (message speed, Level 4 saves this
  time to reduce complexity) hit the exact same wall - 72 differing bytes, no exact 8/1 match anywhere,
  and the cascade landed a *third* place: inside the party records region (`0x06D5`+) this time, not
  the two previous locations. Three tight, controlled, single-variable save pairs, three completely
  different cascade locations. This is no longer "probably noise" - it's a confirmed, general property
  of this save format: **a large, unrelated variable-width shift (almost certainly the same mechanism
  as SP-form changes, equipment slot markers, and inventory tombstones - see those sections) can be
  triggered by something incidental between nearly any two saves**, landing wherever that particular
  structure happens to sit in the file that time. It is not localized to one region and cannot be
  assumed absent just because a test was tightly controlled.
- **This affects every future before/after diff on this project, including the story/event-flags test.**
  When that test is finally run, expect a real chance of an unrelated large cascade showing up somewhere
  else in the diff. Treat only actual changes inside the documented `0x02B4`–`0x02E3` range as evidence
  of story flags; do not assume every difference found elsewhere in that diff is meaningful.
- **2026-09-25 update — likely root cause found:** the zero-run compression discovered during the Fol
  investigation (see the note at the top of this doc) is almost certainly *why* every raw-byte diff
  test all session showed a large, unexplained cascade regardless of how tightly controlled the
  before/after pair was. Any edit that changes a zero-run's length re-tokenizes every byte after it in
  the compressed stream, without any real semantic change. A repeat of the specialty-purchase diff,
  done against the *decoded* state instead of raw bytes, dropped from 100–200+ changed bytes down to 8
  — confirming this. **Every future diff test on this format should decode first (see `so2_fol.py`'s
  `decode()`) and diff the decoded bytes, not the raw compressed bytes.** This likely obsoletes the
  "many more controlled trials" advice above — the real fix is decoding, not more samples.

## Specialty unlock flag (decoded-state offset `0x1A3F`)

**2026-09-25, decoded-diff test (real "Technique 1" specialty purchase, 400 Fol):** diffing the
*decoded* state (see the compression note above — raw byte diffs are unreliable here) between a save
immediately before and after the purchase showed only 8 changed bytes total, a dramatic improvement
over every raw-byte diff attempted earlier this session (100–200+ changed bytes each, dominated by
compression re-tokenization noise, not real signal).

Of those 8 bytes: Fol dropped by exactly 400 (confirms the transaction), a byte at `0x24` incremented
by 1 (likely a specialties-purchased counter), a handful of bytes near Claude's character entry shifted
by small amounts (likely a computed/derived stat recalculating, not the flag itself), and — the real
find — **the byte at decoded offset `0x1A3F` changed `0x30` → `0x70`: exactly one bit set (bit 6,
`0x40`), in an otherwise all-zero region.** That's the classic shape of a bitmask flag.

Confirmed against real gameplay behavior: buying a specialty makes it available to **every** character
at once (not per-character) — each character's actual progress in it is still tracked separately via
the already-VERIFIED per-character SP/skill-level system. A single global bit flip, rather than eight
separate per-character copies, is exactly consistent with that — buying the specialty flips one
party-wide "can now invest SP in this" flag; how far each character has leveled it stays governed by
the existing SP mechanism.

**LIKELY, not yet fully VERIFIED**: bit 6 = "Technique" specifically needs one more data point (a
different specialty purchase producing a different bit) to confirm the full bit-to-specialty mapping.
This is very plausibly the answer to the old "33-byte flag run, purpose unknown" open item below,
once re-expressed in decoded-state offsets rather than the old (compression-confused) raw addressing.

## Known open items (not mapped)

- **Party primary array — full byte map**: byte coverage is complete; semantic mapping remains partial.
  Named families cover 66/96 bytes; +4E/+50/+52 and +54/+56/+58 are two unnamed
  halfword triplets (12 bytes). +04..0F and +5A..5F remain opaque (18 bytes),
  with nonzero real-save data, so they are not established padding. INT initialization
  versus recalculation and the unnamed fields' consumers still need explanation.
  See [the detailed map](SO2-PARTY-MEMBER-INVESTIGATION.md#primary-record-complete-byte-coverage-partial-semantic-map-2026-09-27).

- **Story/event flags** - raw `0x02B4`-`0x02E3`: checked, inconclusive as story flags; save/load copies this range to/from live state `+0x1D4..+0x203` ([code evidence](SO2-STORY-FLAGS-HEADER-CHECK.md)); no story-specific writer established.
- **Map/location — real coordinates found 2026-09-27, but likely coarse, not free-roam.** Decoded
  `0x1750/0x1754/0x1758` (chunk-5 relative `+8/+0xC/+0x10`) hold three signed 32-bit words that read
  as real X/Y/Z position data — confirmed against S01/S02/S15: values differ meaningfully between
  saves (tens of thousands for an outdoor-scale area in S01/S02, single digits near origin for S15,
  consistent with a small interior room), plus a facing/orientation halfword at `+0x18` (decoded
  `0x1760`) and an area-sub-index byte at `+0x21` (`0x1769`) and area ID byte at `+0x24` (`0x176C`).
  Multiple resident write sites confirmed (not just the one warp handler that led here) — all are
  gated behind story-script state checks or an area-ID table lookup (20.12 fixed-point source values
  right-shifted by 12 before storing), consistent with **scripted area-entry/transition placement**,
  not a per-frame movement update. No per-frame, controller-input-driven writer to this structure was
  found in resident entry 2576; if ordinary walking also updates it, that code likely lives in an
  unextracted field-movement overlay (same boundary the field-leader investigation hit). Practical
  upshot: the save very likely records *where you last warped/entered from*, not your exact live
  position after walking around — a teleport edit would probably work for entrance-to-entrance jumps,
  not for placing you at an arbitrary point mid-room. **2026-09-27 follow-up:** the area-ID table at
  `0x80075360` is confirmed as a 194-entry pointer array (bounds-checked `sltiu v0,a0,0xc2` at a third,
  independent write site), so valid area IDs are `0..193` with a known per-entry struct layout — but no
  area/zone **name** strings were found anywhere in the three most relevant already-extracted files.
  **2026-09-27 follow-up:** targeted a 3-entry sample of the full 4,155-entry disc archive, chosen from
  direct evidence (the exact resource ID the area-entry handler loads) rather than heuristics — all
  three decoded to pure graphics/tile data, no text at all. **2026-09-27 correction:** that "no text"
  result is now known to be uninformative — the function assumed to be "the resource loader consuming
  that ID" (`0x80011b98`) is actually a generic UI/object dispatch function, not an archive-index
  loader, so the resource ID traced here was never shown to relate to the disc archive at all. No
  second resource-load call exists in either known area-entry handler. Disassembly-based name hunting
  via this thread is exhausted; **live-testing (visit a known location, read decoded `0x176C`) is the
  clearly most efficient remaining path**, not a fallback. See [code evidence](SO2-MAP-LOCATION-CHECK.md).
  **2026-09-27 live-test results:** built `so2_location.py` (reads a save's area ID/position, records
  into `area_data.json`, lets you attach real names). Real gameplay confirmed area ID only changes on
  crossing an actual area-entry trigger, not from walking — five saves spanning real outdoor travel
  (Hoffman → Hilton → Lacour → Linga outskirts) all read the same area, and it changed the instant the
  user crossed into Linga proper. **Area 128 = Linga, confirmed** (also where the user's real save 15
  currently sits). Tested writing one save's position/area fields to exactly match another known-good
  save: same-area repositioning (new X/Z, same area ID) **worked correctly in-game**; a full cross-area
  edit (area 0 → area 128, all six fields copied exactly from a working save) **produced a black screen
  with the old area's music still playing** — area ID + position alone are not sufficient for a working
  cross-area warp; something else (likely background/tileset or active-music state, probably in the
  still-mostly-unmapped chunk 1) must also be synced. **Also flagged, unresolved:** live data suggests
  `0x1769`, not `0x176C`, may be the byte that actually discriminates areas — contradicts the disassembly
  citation above; see the doc's "open discrepancy" note. Practical takeaway: a "reposition within your
  current area" tool is safe to build today; a real cross-area teleport tool is not, yet.
  **2026-09-27, more live-testing:** two more real areas confirmed (118 = Cave of Trials, 148 = Love
  Alley). A real anomaly found: deeper dungeon floors saved via the save-anywhere cheat all read the
  same stale area ID (Linga) instead of updating — checked chunk 1 for a correlated difference and
  found none, ruling that out as the cause. Leading unconfirmed theory: the cheat may bypass normal
  area-tracking where no real save point exists. See [code evidence](SO2-MAP-LOCATION-CHECK.md).
- **The 33-byte flag run** inside each character entry, just before the skill levels — likely related to
  the specialty-unlock bitmask found at decoded offset `0x1A3F` above; not yet cross-referenced.
- **Specialty shop tiers - mapping resolved 2026-09-27:** twelve fixed flags `0x2BC..0x2C7`,
  ordered Knowledge/Sensibility/Technique/Combat within each level. Level 1 uses `0x1A3F`
  bits 4-7; level 2 uses `0x1A40` bits 0-3; level 3 uses bits 4-7. Verified by extracted
  purchase bytecode, skill-availability table and 38 real-MIPS commit executions. Technique 1
  reproduces `30 -> 70` exactly. The old "Knowledge-vs-Sensibility" note misstated the conflict:
  a later purchase labeled Sensibility 2 set Technique 2's bit 2, whereas the earlier test
  set Sensibility 2's bit 1. Flag meanings are resolved; why that historical label disagreed
  remains unproven. A recorded Sensibility-2 purchase at the same guild, from both bits clear,
  is the remaining clean test. See [specialty evidence and full table](SO2-SPECIALTY-INVESTIGATION.md).
- **Global flags** — located but not explored: they start at decoded offset `0x19E8`, inside the
  still-mostly-unmapped fifth decoded chunk (found while investigating specialties). **Not** the
  same system as the raw `0x2B4` story-flags candidate below — that candidate lives in the
  uncompressed header, before the compressed body even starts, while `0x19E8` is deep inside the
  compressed/decoded state; the two are architecturally separate storage, confirmed by the
  2026-09-27 story-flags check. Worth a future investigation pointed directly at this decoded
  region instead.
- **Message speed and audio mode** — see the note above the options table. Audio has a partial lead
  (`0x03CB`); message speed has none. Both need many more controlled trials, not another 2-3-save diff.
- **Private Actions / emotion levels, item-creation recipes** — not located.
- **Field-leader / walking-sprite slot (decoded state `+0x41`)** — 2026-09-27: the validator that
  reads/repairs this byte (`0x80052FF4..0x80053154`) is confirmed to run as part of a field/area-entry
  routine (`0x80051A34`, which loads a map resource and writes fixed-point coordinates into the
  known chunk-5 source `[0x80075710]`), itself triggered by story-script opcodes. This substantially
  corroborates the field-leader theory but does not close the loop to the exact instruction that
  picks the walking character's graphic/sprite-set - no second read of `+0x41` exists in the resident
  code, so that consumer likely lives in an unextracted field-movement overlay. **Status: strongly
  corroborated, not fully closed** — do not edit `+0x41` directly yet. See
  [the party investigation's 2026-09-27 follow-up](SO2-PARTY-MEMBER-INVESTIGATION.md#2026-09-27-follow-up-validators-call-context-strongly-corroborates-the-theory-sprite-consumer-still-not-closed).
- The reported 9-slot "Special Attack/Magic Max" cheat list was **checked; its save correspondence remains inconclusive**. The actual assignment UI uses four one-byte ability IDs at decoded `0x56C..0x56F + slot*0xD0` (secondary `+CC..CF`), with 32 candidate availability bytes at `+3C..5B`; extracted candidate/read/write instructions were executed on S01/S02/S15. This does not identify the historical nine cheat addresses. See [special-attack list check](SO2-SPECIAL-ATTACK-LIST-CHECK.md).
- The early-save checksum-A discrepancy is resolved; see the checksum investigation linked above.
