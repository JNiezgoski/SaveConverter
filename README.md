# StarOcean2-SaveTools

PS1 memory-card save tools for **Star Ocean: The Second Story (US)**. Started as a format-ingestion
tool (bringing GME/VGS/DexDrive/raw card images into a usable form) and grew into full save-format
reverse engineering — there's no published spec for this format, so every field documented here was
found by diffing real save files, matching numbers against the game's own screens, or disassembling
the actual PS1 code that reads and writes it.

## What's solved

| Area | Status |
|---|---|
| Checksums, party list, character ID swaps | ✅ Verified |
| Level, HP, MP, STR/CON/AGL/DEX/INT | ✅ Mapped & resident-verified — decoded `0x1A0 + slot*0x60`, 3-stage stat triplets (base, intermediate, final) via resident accessors `80033218`/`800332F8`; stat recalculation rules mapped in code, in-game write safety uncapped — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#primary-record-complete-byte-coverage-partial-semantic-map-2026-09-27) |
| All 46 skill levels **and** all 46 skill names/order | ✅ Verified — decoded `0x4A0 + slot*0xD0 + 0x5D..0x8A` (slot 0 `0x4FD..0x52A`), 1 byte per skill (IDs 1..46), resident getter/setter `80033CB4`/`80033CE0` — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#secondary-record-complete-208-byte-map-sp-opcode-u32-talent-word-and-46-skill-levels-2026-09-27) |
| SP (skill points) — every internal form, all 12 characters | ✅ Verified — decoded `0x4A0 + slot*0xD0 + 0x1A` (slot 0 `0x4BA..0x4BB`), u16 clamped 0..999, script opcode `0xFE0A` / `0xFE8A` and level-up UI in Overlay 3014 — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#secondary-record-complete-208-byte-map-sp-opcode-u32-talent-word-and-46-skill-levels-2026-09-27) |
| Talents (all 10) | ✅ Verified — decoded `0x4A0 + slot*0xD0 + 0x20` (slot 0 `0x4C0..0x4C3`), 32-bit u32 word, bits 0..11 — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#secondary-record-complete-208-byte-map-sp-opcode-u32-talent-word-and-46-skill-levels-2026-09-27) |
| Item ID table, inventory counts for items already owned (max 20) | ✅ Verified |
| Giving a character an item type they've **never** owned before | ✅ Mapped and disassembly-verified (via `so2_inventory.py`) — Seraphic Garb 0→20 candidate for save 15 reproduces the real add routine and serializer exactly under bounded MIPS execution; **not yet booted in an emulator** — [details](docs/SO2-INVENTORY-ADD-INVESTIGATION.md) |
| Inventory word bit-15 flag meaning | ✅ Verified — transient "new acquisition / pending auto-equip evaluation" flag; set to 1 by all 14 item grant paths (`8003C594`), checked by field auto-equip upgrade evaluator (`800310A0`), mass-cleared to 0 across all 1,024 slots (`80030F84`), excluded from runtime integrity checksum (`8003C8A0`) — [details](docs/SO2-INVENTORY-ADD-INVESTIGATION.md#2026-09-28-follow-up-investigation-meaning-and-lifecycle-of-inventory-bit-15) |
| Equipment — full 7-slot characters (incl. Noel, Chisato) | ✅ Verified |
| Equipment — compressed 6-slot (missing one accessory) | ✅ Verified |
| Fol (money) | ✅ Verified in-game (via `so2_fol.py` — see below) |
| Specialties (shop-bought Skill Shop tiers: Knowledge/Sensibility/Technique/Combat ×3 levels) | ✅ Verified — mechanism explained and full 12-tier bit table (`0x1A3F`/`0x1A40`) confirmed by executing the real purchase code; one clean live purchase would close out the last loose end — [details](docs/SO2-SPECIALTY-INVESTIGATION.md) |
| Adding/recruiting a party member | ✅ Mapped and disassembly-verified (via `so2_party.py`) — two parallel per-slot arrays, identity is a numeric ID not the name string; real initializer code executed under bounded MIPS execution, **not yet booted in an emulator** — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md) |
| Battle-ability quick-assignment slots (4 per character) | ✅ Mapped and disassembly-verified — decoded `0x56C-0x56F` per character, real candidate/read/write code executed against real saves — [details](docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md) |
| Map position (X/Y/Z, facing, area ID + real scene selector) and area/scene → name lookup | ✅ Verified in-game — tool: `so2_location.py`. 8 areas / 24 sightings recorded, including all 13 floors of Cave of Trials plus 2 in-cave escape points — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Same-area repositioning (teleport within your current area) | ✅ Verified in-game — first successful save-edit teleport in this project |
| Cross-area teleport | ✅ Verified in-game — copying position/area plus a newly-found 48-byte region (`0x1B58-0x1B88`) from a real reference save works; `so2_location.py teleport` implements it — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Required disc (Disc 1 vs Disc 2) | ✅ Verified — decoded byte `0x4C` (0=Disc 1, 1=Disc 2), confirmed by executing the real disc-check code against both actual disc images — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |
| Psynard (flying mount) teleport | ✅ Verified in-game — editing its parking coordinates (`0x19B4-0x19D8`) moves it to the new spot, confirmed live twice — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |
| Options menu — all 8 settings (see table below) | ✅ Mapped and disassembly-verified — [details](docs/SO2-OPTIONS-MENU-INVESTIGATION.md) |
| The "stuck area ID" mystery | ✅ Resolved — decoded `0x1769` (long assumed to be a location ID) is actually a saved sprite drawing-order value; the real location selector is decoded `0x1762` ("scene"), confirmed by real code. `so2_location.py` uses scene throughout — [details](docs/SO2-MAP-LOCATION-CHECK.md#2026-09-27-disassembly-follow-up-0x1769-is-saved-drawing-order-not-an-area-id) |
| Field leader / walking sprite mechanism | ✅ Resolved — graphics consumer located (`8003F518` / `80042E4C`); full 12-character selector space mapped (`ID - 1`, Dias = 4); party archive streaming solved (`80061888`); save-edit leader forced swap ruled out (strictly requires code mod) — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#2026-09-27-third-follow-up-graphics-selection-consumer-found-12-character-selector-space-solved-save-edit-forced-leader-ruled-out) |
| Map terrain / collision data (dungeon + overworld) | ✅ Solved — dungeon: 88-byte triangle records, plane-equation height formula. Overworld: 9-slot streaming cache, 4×4 sub-cell mesh per world cell, packed triangle/quad polygons, PS1 GTE hardware point-in-polygon test, exact plane-equation elevation. Real Area-0 height cross-check verified against disc assets — exact integer match — [details](docs/SO2-MAP-TERRAIN-INVESTIGATION.md) |
| Party secondary array (SP, talents, skill levels — full 208-byte record) | ✅ Solved — decoded `0x4A0..0xB20`, all 8 slots, 100% mapped with zero gaps. SP is a `u16` at `+0x1A` (script opcode `0xFE0A`/`0xFE8A`); talents a `u32` word at `+0x20` (corrects an earlier `u16` assumption); all 46 skill levels at `+0x5D..0x8A` via canonical getter/setter `80033CB4`/`80033CE0`; plus name buffer, combat-strategy bytes, and battle-ability proficiency counts. Cross-checked against all 15 real saves in the repo — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#secondary-record-complete-208-byte-map-sp-opcode-u32-talent-word-and-46-skill-levels-2026-09-27) |
| Private Actions / emotion levels / ending thresholds / item-creation recipes | ✅ Solved — Matrix A = Friendship, Matrix B = Romance/Affection (both `0xFF10-13`), proven via named PAs (Leon's confession, the Arlia rescue scene). **Ending thresholds**: Disc 2 Archive 3788 (`0xBE80..0xC600`) confirms the fan hypothesis — opposite-sex pairs need mutual Matrix B ≥ 10, same-sex pairs need mutual Matrix A ≥ 10, qualifying pairs sorted by combined score and assigned greedily, unpaired characters get solo endings; follow-up fully enumerates all 3 hardcoded special ending pairs (Celine+Chris, Ashton+Eleanor, Opera+Ernest). **Item-creation recipes**: Disc Archive 2990 holds a static recipe table (119 Customization recipes, plus 108 Cooking/Master Cooking dishes across 16 ingredient groups), executed via Overlay 3012; Disc Archive 3008 holds Art (39 item recipes across 5 skill tiers with 12 character portraits) and Compounding (21 herb pairs / 84 medicine variants across a 6x6 matrix) — e.g. Minus Sword + Mithril → Eternal Sphere (Claude's best weapon, 80% success) — [details](docs/SO2-CHUNK1-MAPPING.md#2026-09-28-follow-up-disc-2-ending-threshold-system--item-creation-recipes) |
| Decoded chunk 1 (`0x000..0x1A0`, 416 bytes) | ✅ 100% accounted for — 401 bytes (96.4%) mapped, 15 bytes partial, 0 unknown. Two 12×12 emotion matrices (Friendship/Romance, 288 bytes), script system-call return words (`S+01C`/`02C` via VM dispatch table `8007380C`), Formation-menu cursor byte, window/palette shading bytes, field step-rate modifiers, and route/rename/counters all mapped; remaining 15 bytes are confirmed alignment padding and transition-state operands — [details](docs/SO2-CHUNK1-MAPPING.md#resolution-of-final-remaining-chunk-1-gaps-2026-09-28) |
| Decoded chunk 5 (`0x1748..0x1B88`, 1,088 bytes) | ✅ 100% accounted for — 549 bytes (50.5%) mapped, 539 bytes partial, 0 unknown. Includes the fully-solved 368-byte story/event flag bitmap (99 named, 269 confirmed silent), 12 character names, 48 clock snapshots, pending deliveries, Object-14/Psynard coordinates, and the overworld minimap-mode cycler (`800889A4`); remaining partial bytes are confirmed operational parameters or exhaustively-proven-silent padding capacity, not unexamined gaps — [details](docs/SO2-CHUNK5-MAPPING.md#resolution-of-remaining-miscellaneous-chunk-5-gaps-2026-09-28) |
| Story/event flags — global 368-byte bitmap (`0x19E8..0x1B58`) | ✅ Solved — every byte accounted for: 99 bytes mapped to real plot/game systems (Expel prologue, Lacour tournament, Nede Four Fields quest, Skill Guild tiers, Battle Stadium, Cave of Trials bosses, and more), 269 bytes exhaustively proven to hold zero references anywhere — disc scripts, overlays, and resident code all audited, not just script VM opcodes. The remaining 269 bytes are genuine unused padding capacity in the allocation, not an unexamined gap — [details](docs/SO2-CHUNK5-MAPPING.md#script-vm-flag-opcodes-and-named-story-milestones--part-3--final-2026-09-28) |
| Voice Collection save data & cross-slot merge | ✅ Solved & Verified — raw `0x0280..0x031F` (160 bytes / 1,280 bits capacity), 1,278 total voice quotas mapped across all 12 characters (`0x8009C138` in RAM). Zero-decompression multi-save bitwise OR on boot; tool `so2_voice_collection.py` audits, merges, and unlocks 50% (Universe mode) or 100% — [details](docs/SO2-VOICE-COLLECTION.md) |

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

## Ongoing tasks

"Disassembly" = disc image + disassembly + existing save files only, no emulator run required.
"In-game testing" = the result has to actually be booted and observed in-game to confirm it.

### Open items

Genuinely unresolved work — fully resolved items live in "What's solved" above, not here.

Ordered so every pure-disassembly task (no boot/live test required to make progress) comes before
anything that needs in-game or live testing to advance further.

| # | Task | Status | Validation | Notes |
|---|---|---|---|---|
| 1 | Party primary array — full byte-by-byte map | 69% mapped, static leads exhausted | Disassembly exhausted + live stat-change test needed | All 96 bytes covered; 66 named (ID/EXP/HP/MP/level/STR/CON/AGL/DEX/INT/GUTS), 12 are two unnamed stat triplets, 18 unresolved. Generic-accessor lead (selectors 1-17), stat recalculation pipeline, all 12 initializers, and script VM opcodes all audited and ruled out for standalone resident/menu accessors — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#2026-09-28-second-disassembly-retry-standalone-accessors-recalculation-pipeline-all-12-initializer-tables-and-script-vm-opcodes-disassembly-only--verified). Live in-game combat testing required to establish remaining semantics |

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
| `so2_sprite_extract.py` | Extracts authentic 16-color BGR555 combat and hero sprites (Hero Roster 3026, Claude 3111..3173, Ashton/monsters 3176..3206, summons 4035..4050) into transparent PNG frames across all animation banks. `python tools/so2_sprite_extract.py [--archive <id>] [--all] [--scale N]` |

`saveconv.py` (repo root) also has three built-in Star Ocean 2 subcommands, no `scripts/` prefix needed:
`python saveconv.py voice <card> [--slot N] [--unlock PCT] [--merge] [--out <new card>]`
`python saveconv.py so2-edit <card> [--slot N] [--fol N] [--sp N] [--talents] [--skills] [--out <new card>]`
`python saveconv.py so2-sprites [--archive <id>] [--all] [--scale N] [--out <dir>]`
(Fol/SP/Talents/Skill-Shop-tier editing and authentic 16-color combat/hero sprite extraction).

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
