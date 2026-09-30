# StarOcean2-SaveTools

PS1 memory-card save tools for **Star Ocean: The Second Story (US)**. Started as a format-ingestion
tool (bringing GME/VGS/DexDrive/raw card images into a usable form) and grew into full save-format
reverse engineering — there's no published spec for this format, so every field documented here was
found by diffing real save files, matching numbers against the game's own screens, or disassembling
the actual PS1 code that reads and writes it.

## What's solved

Grouped by subsystem — every fact and doc link below was previously scattered across a flat 29-row
table with real duplication (skills/SP/talents and "the secondary array" were 4 rows describing one
208-byte struct; two "chunk accounting" rows mostly restated content already given its own row). Nothing
here was cut, just merged where multiple rows described the same underlying record.

### Party members

The secondary record (`0x4A0 + slot*0xD0`, 208 bytes) is **100% mapped with zero gaps**. The primary
record (`0x1A0 + slot*0x60`, 96 bytes) has every named stat (ID, EXP, HP/MP/level, STR/CON/AGL/DEX/INT/
GUTS, the now-fully-solved status-ailment condition byte) mapped, but still has 18 genuinely opaque
bytes per slot (`+0x04..0x0F`, `+0x5A..0x5F`) plus a 12-byte "Unknown A/B" region with a real but
unproven lead (looks tied to which characters have been forced into the field-leader role — see
`docs/SO2-PARTY-MEMBER-INVESTIGATION.md`'s 2026-09-29 follow-up). Both cross-checked against all 15
real saves in the repo:

| Field | Decoded offset | Notes |
|---|---|---|
| Level, HP, MP, STR/CON/AGL/DEX/INT | `0x1A0 + slot*0x60` | 3-stage stat triplets (base/intermediate/final) via resident accessors `80033218`/`800332F8`; recalculation rules mapped, write safety uncapped |
| SP (skill points) | `+0x1A` (u16, slot 0 `0x4BA..0x4BB`) | Clamped 0..999; script opcode `0xFE0A`/`0xFE8A`, level-up UI in Overlay 3014 |
| Talents (all 10) | `+0x20` (u32) | Bits 0..11; corrects an earlier wrong `u16` assumption |
| All 46 skill levels & names/order | `+0x5D..0x8A` (slot 0 `0x4FD..0x52A`) | 1 byte per skill (IDs 1..46), resident getter/setter `80033CB4`/`80033CE0` |
| Name buffer, combat-strategy bytes, battle-ability proficiency counts | rest of the 208-byte record | Fully mapped alongside the above |

[Full secondary-record map](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#secondary-record-complete-208-byte-map-sp-opcode-u32-talent-word-and-46-skill-levels-2026-09-27) ·
[primary record](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#primary-record-complete-byte-coverage-partial-semantic-map-2026-09-27)

Everything else party-related:

| Area | Status |
|---|---|
| Checksums, party list, character ID swaps | ✅ Verified |
| Adding/recruiting a party member | ✅ Mapped and disassembly-verified (via `so2_party.py`) — two parallel per-slot arrays, identity is a numeric ID not the name string; real initializer code executed under bounded MIPS execution, **not yet booted in an emulator** — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md) |
| Field leader / walking sprite mechanism | ✅ Resolved — graphics consumer located (`8003F518`/`80042E4C`); full 12-character selector space mapped (`ID - 1`, Dias = 4); party archive streaming solved (`80061888`); save-edit forced-leader swap ruled out (strictly requires code mod) — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#2026-09-27-third-follow-up-graphics-selection-consumer-found-12-character-selector-space-solved-save-edit-forced-leader-ruled-out) |
| Battle-ability quick-assignment slots (4 per character) | ✅ Mapped and disassembly-verified — decoded `0x56C-0x56F` per character — [details](docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md) |
| Specialties (Skill Shop tiers: Knowledge/Sensibility/Technique/Combat ×3) | ✅ Verified — full 12-tier bit table (`0x1A3F`/`0x1A40`) confirmed by executing the real purchase code; one clean live purchase would close the last loose end — [details](docs/SO2-SPECIALTY-INVESTIGATION.md) |
| Status ailments (condition byte, primary `+0x02`) | ✅ Solved & live-confirmed — 4-bit mask: `0x01` Dead, `0x02` Paralysis, `0x04` Stone, `0x08` Poison, freely combinable (tested all four simultaneously on one character); mirrored at header `0x0234 + slot*4 + 0x01`; disassembly-verified against Overlay 2986/2985 — [details](docs/SO2-STATUS-AILMENT-SOURCES.md) |

### Items & equipment

| Area | Status |
|---|---|
| Item ID table, inventory counts for items already owned (max 20) | ✅ Verified |
| Giving a character an item type they've **never** owned before | ✅ Mapped and disassembly-verified (via `so2_inventory.py`) — Seraphic Garb 0→20 candidate for save 15 reproduces the real add routine and serializer exactly under bounded MIPS execution; **not yet booted in an emulator** — [details](docs/SO2-INVENTORY-ADD-INVESTIGATION.md) |
| Inventory word bit-15 flag meaning | ✅ Verified — transient "new acquisition / pending auto-equip evaluation" flag; set by all 14 item grant paths (`8003C594`), checked by the field auto-equip evaluator (`800310A0`), mass-cleared across all 1,024 slots (`80030F84`), excluded from the runtime checksum (`8003C8A0`) — [details](docs/SO2-INVENTORY-ADD-INVESTIGATION.md#2026-09-28-follow-up-investigation-meaning-and-lifecycle-of-inventory-bit-15) |
| Equipment — full 7-slot characters (incl. Noel, Chisato) & compressed 6-slot (missing one accessory) | ✅ Verified |
| Fol (money) | ✅ Verified in-game (via `so2_fol.py` — see Tools) |
| Item-creation recipes | ✅ Solved — Disc Archive 2990: 119 Customization recipes + 108 Cooking/Master Cooking dishes across 16 ingredient groups (Overlay 3012). Disc Archive 3008: Art (39 recipes, 5 tiers, 12 portraits) and Compounding (21 herb pairs / 84 medicine variants, 6x6 matrix) — e.g. Minus Sword + Mithril → Eternal Sphere (80% success) — [details](docs/SO2-CHUNK1-MAPPING.md#2026-09-28-follow-up-disc-2-ending-threshold-system--item-creation-recipes) |

### Map & world state

| Area | Status |
|---|---|
| Map position (X/Y/Z, facing, area ID + real scene selector) and area/scene → name lookup | ✅ Verified in-game — tool: `so2_location.py`. 8 areas / 24 sightings recorded, incl. all 13 floors of Cave of Trials plus 2 in-cave escape points — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Same-area repositioning & cross-area teleport | ✅ Verified in-game — cross-area also copies a 48-byte region (`0x1B58-0x1B88`) from a reference save; `so2_location.py teleport` implements both — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| The "stuck area ID" mystery | ✅ Resolved — decoded `0x1769` (long assumed a location ID) is actually a saved sprite drawing-order value; the real location selector is `0x1762` ("scene"). `so2_location.py` uses scene throughout — [details](docs/SO2-MAP-LOCATION-CHECK.md#2026-09-27-disassembly-follow-up-0x1769-is-saved-drawing-order-not-an-area-id) |
| Map terrain / collision (dungeon + overworld) | ✅ Solved — dungeon: 88-byte triangle records, plane-equation height formula. Overworld: 9-slot streaming cache, 4×4 sub-cell mesh per world cell, packed triangle/quad polygons, PS1 GTE point-in-polygon test, exact plane-equation elevation — Area-0 height cross-check is an exact integer match against disc assets — [details](docs/SO2-MAP-TERRAIN-INVESTIGATION.md) |
| Required disc (Disc 1 vs Disc 2) | ✅ Verified — decoded byte `0x4C`, confirmed by executing the real disc-check code against both actual disc images — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |
| Psynard (flying mount) teleport | ✅ Verified in-game — editing parking coordinates (`0x19B4-0x19D8`) moves it, confirmed live twice — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |

### Story & social systems

| Area | Status |
|---|---|
| Private Actions / emotion levels | ✅ Solved — Matrix A = Friendship, Matrix B = Romance/Affection (both `0xFF10-13`), proven via named PAs (Leon's confession, the Arlia rescue scene) |
| Ending thresholds | ✅ Solved — Disc 2 Archive 3788 (`0xBE80..0xC600`) confirms the fan hypothesis: opposite-sex pairs need mutual Matrix B ≥ 10, same-sex pairs need mutual Matrix A ≥ 10, pairs sorted by combined score and assigned greedily, unpaired characters get solo endings; all 3 hardcoded special pairs enumerated (Celine+Chris, Ashton+Eleanor, Opera+Ernest) — [details](docs/SO2-CHUNK1-MAPPING.md#2026-09-28-follow-up-disc-2-ending-threshold-system--item-creation-recipes) |
| Story/event flags — global 368-byte bitmap (`0x19E8..0x1B58`) | ✅ Solved — every byte accounted for: 99 mapped to real plot/game systems (Expel prologue, Lacour tournament, Nede Four Fields quest, Skill Guild tiers, Battle Stadium, Cave of Trials bosses, and more), 269 exhaustively proven silent (scripts, overlays, and resident code all audited) and confirmed as genuine unused padding, not a gap — [details](docs/SO2-CHUNK5-MAPPING.md#script-vm-flag-opcodes-and-named-story-milestones--part-3--final-2026-09-28) |
| Voice Collection save data & cross-slot merge | ✅ Solved & Verified — raw `0x0280..0x031F` (160 bytes / 1,280 bits), 1,278 voice quotas across all 12 characters (`0x8009C138` in RAM). Zero-decompression multi-save bitwise OR on boot; `so2_voice_collection.py` audits, merges, and unlocks 50% (Universe) or 100% — [details](docs/SO2-VOICE-COLLECTION.md) |

### Full byte-range accounting

Beyond the named systems above, two full save-block regions have been swept byte-by-byte so nothing
is left unexamined: **chunk 1** (`0x000..0x1A0`, 416 bytes — 96.4% mapped, remainder confirmed
alignment padding, [details](docs/SO2-CHUNK1-MAPPING.md#resolution-of-final-remaining-chunk-1-gaps-2026-09-28))
and **chunk 5** (`0x1748..0x1B88`, 1,088 bytes — includes the story-flag bitmap above plus 12
character names, 48 clock snapshots, pending deliveries, and the minimap-mode cycler (`800889A4`);
remainder confirmed operational parameters or proven-silent padding, [details](docs/SO2-CHUNK5-MAPPING.md#resolution-of-remaining-miscellaneous-chunk-5-gaps-2026-09-28)).
0 unknown bytes in either.

### Menu settings — verified

Found by extracting the real Options overlay (disc archive entry 3016) and executing its actual
menu-construction, input-callback, and save-serializer code — not by diffing saves, which is why
three earlier attempts at this found nothing. All offsets are **decoded**, not raw card-block
offsets. In-game save/reload has not yet been tested for any of these.
**[Full evidence](docs/SO2-OPTIONS-MENU-INVESTIGATION.md)**

| Setting | Decoded offset | Values |
|---|---|---|
| Message speed | `0x1860` | u8 `0..7`, displayed `1..8` (fast → slow) |
| Sound output | `0x44` | `0` Surround, `1` Stereo, `2` Monaural |
| Message window color | `0x30` / `0x34` / `0x38` / `0x3C` | Four `0x00BBGGRR` words: UL, UR, LL, LR corners |
| Targeting mode | `0x49` | `2` Auto, `0` Semi-Auto, `1` Manual |
| Camera work | `0x4A` | `0` Normal, `1` Leader-Centered |
| Combat motion mode | `0x4B` | `0` button + direction icon, `1` direction icon only |
| Key customization | `0x00..0x0F` | Eight u16 button masks, one per assignable action |
| Vibration | `0x46` | `0` OFF, `1` ON |

Full byte-level reference, including every offset and the exact SP/equipment encoding rules:
**[docs/SAVE-FORMAT.md](docs/SAVE-FORMAT.md)**

**Game-mechanic reference docs** (fan-sourced, cross-validated against real saves/equip attempts
where noted — see each doc's own Status section): [master item architecture overview](docs/SO2-ITEMS.md)
covering the [full item database](docs/SO2-ITEM-DATABASE.md) and equip restrictions
([weapons/armor/accessories](docs/SO2-ITEM-RESTRICTIONS.md)), [Skills](docs/SO2-SKILLS-FULL.md) and
their derived [Specialties](docs/SO2-SKILL-SPECIALTIES.md)/[Super Specialties](docs/SO2-SUPER-SPECIALTIES.md),
[Talents](docs/SO2-TALENTS.md), [Private Actions](docs/SO2-PRIVATE-ACTIONS.md),
[Emotional Levels](docs/SO2-EMOTIONAL-LEVELS.md), [story/precious items](docs/SO2-STORY-ITEMS.md),
[status ailment sources](docs/SO2-STATUS-AILMENT-SOURCES.md), [spells](docs/SO2-SPELLS.md),
[Fun City](docs/SO2-FUN-CITY.md), and the [dialogue/story script bytecode engine](docs/SO2-STORY-SCRIPTS.md)
(scene container format, opcode ISA — in-game text itself is not reproduced).

**2026-09-25 — important structural correction:** part of every save block (starting at `0x0380`) is
**zero-run compressed**, not raw bytes — `00 00 N` means "N+2 zero bytes." Earlier notes in this repo
describe fixed offsets and "01 &lt;value&gt; 00 00"-shaped records in that region; those were compression
artifacts, not real field boundaries, and don't generalize as raw-offset editing rules. The checksum
formula was also wrong (an old `[0x206,0x281)` byte-sum rule that only worked by coincidence on
late-game saves) and has been corrected in `so2_sign()`. Both were confirmed by disassembling the
actual PS1 game code — see
[docs/SO2-CHECKSUM-INVESTIGATION.md](docs/SO2-CHECKSUM-INVESTIGATION.md) and
[docs/SO2-FOL-INVESTIGATION.md](docs/SO2-FOL-INVESTIGATION.md). Any tool that edits inside the
compressed region must decode → edit → re-encode → re-sign (see `so2_fol.py` for the pattern) —
never poke raw bytes there directly.

### Game asset & graphics formats — disassembly-verified

Separate from the save format above: the PS1 disc's own game-data and graphics formats, reverse
engineered the same way (disassembly and real disc bytes, not fan-wiki guessing).

| Area | Status |
|---|---|
| Combat monster graphics (2D texture-atlas format) | ✅ Solved — not a 3D model; a real texture-atlas + palette format traced through the resident renderer (`8007344C`/`80042990`). All 564 combat archives (`1405..1968`) extracted; archive→monster name reference and archive→sprite-file database both built and cross-verified — [details](docs/SO2-COMBAT-GRAPHICS-INVESTIGATION.md) |
| Enemy stat database (92-byte record) | ✅ Solved — 184 unique species, real names/HP/stats/drops/elemental affinities decoded straight from the 92-byte struct on both discs; a per-archive name-collapsing bug (was silently dropping 69% of archives) found and fixed |
| Combat sprite piece compositing (body/head/attachment pieces → full poses) | ✅ Solved — traced the real animation-record and sub-piece-attachment struct layout (primary record at `anim_bank+0x14+8i`, 28-byte attachment records) and a **524-byte custom palette container format** (magic `0x11000000 0x02000000 0x0C020000`, 16 rows × 16 BGR555 colors) present in 138 of 184 enemy archives that the compositor was silently ignoring — recoloring is real in-game data, not a coincidence (e.g. Coldlizard/Weirdbeast/Salamander share one body shape in 3 disc-verified distinct colors) |
| Item struct (48-byte record) & real item 3D model format | ✅ Solved — full 823-item database (stats, equip restrictions, elemental resistances, buy/sell) from the 48-byte struct; separately, the in-game item-inspection "3D spin" presentation is a **genuine 3D triangle mesh + PS1 GTE hardware transform** (not a flat sprite), traced through the real resident renderer (RTPT/NCLIP/AVSZ3 GTE opcodes at `0x80088BA8..0x80088F40`) with its own dedicated model container (Archive 4489, separate from the item stat archive) — all 823 models extracted and rendered |
| Scene/field sprite format (hero + NPC/field-object sprites) | ✅ Solved — 47,228 frames across 626+ archives; multi-row palette selection mechanism (frame's flags byte selects a CLUT row) disassembly-verified at `0x80042908`/`0x80042974` |

A from-scratch, fully static fan reference site (item gallery, bestiary, equipment lookups) built on
top of this data lives outside this repo at `C:\Webpages\StarOcean2ndStory` — not itself under version
control here, ask if you want that folder git-initialized too.

**A note on process, since it happened more than once building the above:** several early attempts at
the item-icon and monster-sprite work fabricated addresses/struct fields to justify copying images
from an external fan-wiki mirror instead of the real disc. All of that was caught, reverted, and
quarantined (`artifacts/_QUARANTINE_fabricated_item_icons/`, `artifacts/_QUARANTINE_external_psf_music/`)
before it reached this table — everything listed above was independently re-derived from real disc
bytes and cross-checked (hash comparisons, direct visual inspection, or both) before being accepted.

## Ongoing tasks

"Disassembly" = disc image + disassembly + existing save files only, no emulator run required.
"In-game testing" = the result has to actually be booted and observed in-game to confirm it.

### Open items

Genuinely unresolved work — fully resolved items live in "What's solved" above, not here.

Ordered so every pure-disassembly task (no boot/live test required to make progress) comes before
anything that needs in-game or live testing to advance further.

| # | Task | Status | Validation | Notes |
|---|---|---|---|---|
| 1 | Party primary array — full byte-by-byte map | 69% mapped, static leads exhausted, one live-testable lead identified | Disassembly exhausted + live stat-change test needed | All 96 bytes covered; 66 named (ID/EXP/HP/MP/level/STR/CON/AGL/DEX/INT/GUTS, incl. the now-solved status-ailment byte), 12 are two unnamed stat triplets ("Unknown A/B"), 18 fully opaque. Generic-accessor lead (selectors 1-17), stat recalculation pipeline, all 12 initializers, and script VM opcodes all audited and ruled out for standalone resident/menu accessors — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#2026-09-28-second-disassembly-retry-standalone-accessors-recalculation-pipeline-all-12-initializer-tables-and-script-vm-opcodes-disassembly-only--verified). **2026-09-29:** mining all 15 real saves found Unknown A/B diverge from their init values only for characters ever forced into the field-leader role (Claude near-universally; Bowman/Chisato/Rena sometimes; never Ashton/Dias/Ernest/Opera/Leon/Precis) — a real correlation, not yet causally confirmed; the 18 fully-opaque bytes remain untouched by this lead — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#2026-09-29-follow-up-mining-all-15-real-saves-resolves-the-apparent-contradiction-with-the-confirmed-scaled-during-stat-recalculation-claim-below). Next step: grab a before/after save pair around the next story segment that forces a normally-flat character into field-leader |

## Layout

```
saveconv.py, saveconv.bat    core library + launcher (double-click opens savemanager)
area_data.json                map/location database (so2_location.py's data)
scripts/                      every other user-facing tool (see table below)
tools/                        disassembly/evidence scripts behind each investigation doc
tests/                        unit tests (python -m pytest, from the repo root)
docs/                         investigation write-ups and the byte-level reference
```

## Tools

All of these live in `scripts/` and are run from the repo root, e.g. `python scripts/so2_fol.py ...`.

| File | What it does |
|---|---|
| `saveconv.py` *(repo root)* | Core library (checksums, card format detection/conversion) + a CLI: `convert`, `list`, `extract`, `import`. No arguments opens `scripts/savemanager.py`'s picker window. |
| `savemanager.py` | Two-card-side-by-side GUI: copy/move/rename/delete saves, import/export single saves, combine cards, convert formats, install as DuckStation's card 1/2. `python scripts/savemanager.py` |
| `so2_refill_sp.py` | Sets every character's SP to max, handling every internal encoding form. `python scripts/so2_refill_sp.py <slot> <box1> [box2]` — e.g. `python scripts/so2_refill_sp.py 1 1 2` |
| `so2_equip.py` | View/edit equipment. `python scripts/so2_equip.py show [box]` or `python scripts/so2_equip.py set <box> <Character> <slot> "<Item>"` |
| `so2_anatomy.py` | Labels every byte of one save block by confidence (verified/decoded/unknown) and writes a full map to disk. `python scripts/so2_anatomy.py [box]` |
| `so2_coverage.py` | Static knowledge map of the decoded save state — what fraction is mapped/partial/runtime/unknown, region by region. `python scripts/so2_coverage.py` |
| `so2_fol.py` | Sets Fol (money) through the real zero-run codec — decodes the compressed state, edits the value, re-encodes, re-signs. `python scripts/so2_fol.py <card> --save S13 --fol 5000 --out <new card>` (writes a new card file; never overwrites the source) |
| `so2_party.py` | Adds/recruits a party member into a genuinely empty slot pair by executing the game's own initializer code (both the primary and secondary arrays, correctly paired). `python scripts/so2_party.py <card> --save S15 --id 9 --out <new card>` (id is the character ID, 1-12; writes a new card file) |
| `so2_inventory.py` | Gives a character an item type they've never owned before (or tops up one they have) by executing the game's actual add-item routine — the only correct way to create a brand-new inventory entry. `python scripts/so2_inventory.py <card> --save S15 --id 364 --count 20 --out <new card>` (count is an increment; writes a new card file) |
| `so2_location.py` | Reads/records/names map locations and teleports between recorded ones. `python scripts/so2_location.py show [box]`, `name`, `list`, `map`, `map-html`, `teleport` — see the script's own docstring for full usage. |
| `so2_voice_collection.py` | Audits, merges, and unlocks the Voice Collection (50% Universe mode, 75% Music Test, 100% Master) across memory card save slots, recomputing both checksums via `so2_sign()`. `python tools/so2_voice_collection.py <card> [--slot N] [--unlock PCT] [--merge] [--out <new card>]` |
| `so2_sprite_extract.py` | Extracts authentic 16-color BGR555 combat and hero sprites (Hero Roster 3026, party combat banks 3111..3206, summons/extras 4035..4050) into transparent PNG frames across all animation banks. `python tools/so2_sprite_extract.py [--archive <id>] [--all] [--scale N]` |
| `so2_scene_npc_extract.py` | Extracts 2D sprite banks from the `tag==2` section of town/dungeon scene containers (3207..4154). Batch mode scanned all 948 scene archives: 484 contained sprite banks, 42,694 frames extracted, 0 decode failures. What specific content each archive depicts (NPCs, field creatures, item icons, etc.) is not catalogued — that needs a deliberate content pass, not assumed from archive IDs. `python tools/so2_scene_npc_extract.py [--archive <id>] [--all] [--scale N]` |
| `so2_extract_item_models.py` | Renders all 823 items' real in-game 3D models (Archive 4489, disassembly-verified GTE triangle renderer) to 128x128 PNG icons + a manifest, matched to the item database by ID. `python tools/so2_extract_item_models.py [--disc <path>] [--out-dir <dir>] [--size N]` |

`saveconv.py` (repo root) also has built-in Star Ocean 2 subcommands, no `scripts/` prefix needed:
`python saveconv.py voice <card> [--slot N] [--unlock PCT] [--merge] [--out <new card>]`
`python saveconv.py so2-edit <card> [--slot N] [--fol N] [--sp N] [--talents] [--skills] [--out <new card>]`
`python saveconv.py so2-sprites [--archive <id>] [--all] [--scale N] [--out <dir>]`
`python saveconv.py so2-scene-npc [--archive <id>] [--all] [--scale N] [--out <dir>]`
(Fol/SP/Talents/Skill-Shop-tier editing and combat/hero/scene sprite extraction).

**Not committed (local-only by design):** the FMV/audio/character-art media-ripping toolchain
(`so2_audio_extract.py`, `so2_video_convert.py`, `so2_duckstation_pack.py`, `so2_sync_cutscenes.py`,
`so2_fullbody_extract.py`, `so2_media_extract.py`) and its pipeline doc. These rip actual copyrighted
game assets via third-party tools (jPSXdec/FFmpeg) and are kept offline rather than pushed to this
public repo; extracted sprite/media output under `artifacts/` is gitignored for the same reason.

## Usage notes

- **Close DuckStation before writing any card** — it rewrites the card file on exit and will clobber your changes.
- These tools always back up a card before writing to it.
- After any manual edit, both checksums must be recomputed (`so2_sign()` in `saveconv.py` does this automatically in every tool above).
- Character identity inside a save is tracked by the name string embedded in each entry, not by slot position — characters can be freely reordered between party slots.

## Card formats supported

| Ext | Format |
|---|---|
| `.mcd` `.mcr` `.mc` `.mem` `.bin` `.srm` `.ps1` | Raw 131,072-byte card image |
| `.gme` | DexDrive |
| `.vgs` | Virtual Game Station |
| `.vmp` | PSP virtual card (read-only — writing needs Sony signing keys) |
| `.mcs` | Single save (128-byte directory frame + block) |
