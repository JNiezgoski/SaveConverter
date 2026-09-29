# SO2 party members: two parallel records, numeric identity and recruitment

Investigation date: 2026-09-26. US PS1 Disc 1, SCUS-94421 / BASCUS-94421.

## Result

**The missing identity is a signed little-endian 16-bit value at decoded
`0x1A0 + slot * 0x60`, separate from the equipment/name/skills array.**
There are eight **pairs** of records:

| Array | Decoded base | Stride | RAM base pointer | Role |
|---|---:|---:|---|---|
| Primary | `0x1A0` | `0x60` | `[0x8007527C]` | Signed ID, status/class-like bytes, EXP, HP/MP, level pair, STR/CON/AGL/DEX/INT/GUTS triplets; two unnamed triplets and 18 opaque bytes (full map below) |
| Secondary | `0x4A0` | `0xD0` | `[0x80075280]` | Additional stats, equipment, SP-like capped value, talents, name, skills/other character data |

**`0x4AC` is the equipment start, not the start of the secondary record.**
The observed name address and `0xD0` stride were correct. The true secondary
record starts 12 bytes earlier. Primary and secondary records share a slot index.

The party-menu presence test is **signed ID > 0**, not name, equipment, a party
count, or a separate recruited bitmask. Normal positive IDs are 1..12; some
other loops explicitly enforce that range. ID zero means vacant. Negative IDs
retain an absent character's records: the remove routine negates the ID, and
rejoin makes it positive without resetting the records. This is distinct from
ordinary battle reserves: positive IDs in slots 4..7 remain party members.

The general recruitment routine is **`0x80069008`**, reached by story-script
opcode **`0xAE`**, with a **zero-based character argument** (Opera = 8).
It finds a slot itself and invokes **`0x8007A20C`** to initialize **both** records
with a **one-based ID** (Opera = 9). Its paired-record initializer includes
character-specific stats, equipment, skills, name and randomized talents.

These findings explain why the reported edits do not implement recruitment or
identity replacement. They do **not** establish whether either reported failure
was a freeze, load rejection, or unchanged character appearance: that detail and
the exact two edited files were not supplied.

## Sources and address conventions

Read first and reused: [Fol investigation](SO2-FOL-INVESTIGATION.md),
[checksum investigation](SO2-CHECKSUM-INVESTIGATION.md), and
[specialty investigation](SO2-SPECIALTY-INVESTIGATION.md).
No decoder or state-pointer rediscovery was needed. `so2_fol.state/encode` and
the corrected `saveconv.so2_sign/so2_valid` are reused unchanged.

The decoded `0x1B88` bytes are a **serialization of separate allocations**.
Only the first chunk uses `[0x80075270]`. Do not add every decoded offset to
that pointer and expect the corresponding live RAM address.

| SO2.BIN archive entry | Disc LBA | Load address | Extracted size | Evidence used |
|---|---:|---|---:|---|
| 2576 | 30736 | `0x8002F810` | `0x4C7FC` | Resident party accessors, script dispatcher, recruitment, initializer, equipment eligibility |
| 2982 | 36099 | `0x8007E000` | `0x2420` | Party/status menu |
| 2985 | 36109 | `0x800D1B28` | `0xF9A8` | Shared UI party selection and character graphic request |
| 2998 | 36213 | `0x8007E000` | `0x4D28` | Save serializer/load direction |

SO2.BIN is at ISO LBA 300; extraction/decryption is the already-established
`tools/so2_disc_code.py` method. Overlay addresses are overlay-specific.
Resident entry SHA256:

```text
6dec3950348b57068a85759f472ea7d5c92241d28b00ff4ea139ddd8dc1587cf
```

Focused, byte-bearing instruction listings:
[`artifacts/so2-party/evidence.asm`](../artifacts/so2-party/evidence.asm).
All four code hashes, RAM hashes, pointers, and observed slot identities:
[`sources.json`](../artifacts/so2-party/sources.json).
`tools/so2_party_evidence.py` regenerates these from the existing extracts.

Both existing RAM dumps remain useful; no new resume extraction was performed.
**Both** match Disc 1's extracted bytes throughout `0x80069008..0x800692EB`
and `0x8007A20C..0x8007B36B`.

| Dump under artifacts/so2-fol | `[75270]` | `[7527C]` | `[75280]` | Observed IDs by slot |
|---|---|---|---|---|
| ram.bin | `8009A9C0` | `8009BF38` | `8009B8A8` | 2,1,0,0,0,0,0,0 |
| SCUS-94422_resume.ram | `8009B908` | `8009A9C0` | `8009BBB8` | 1,7,5,2,3,6,12,11 |

The second dump's corresponding names are Crawd, Ashton, Dias, Rena, Celine,
Precis, Chisato, Noel. Renamed Claude remains numeric ID 1. These observations
corroborate the instructions; they are not recruitment save-diff evidence.

## Serializer proves the exact decoded offsets

Entry 2998, serializer `0x80081A70`:

```text
80081AE8 lw    a3,5270(a3)    ; first chunk live pointer; length 1A0
80081AEC jal   80081C38
...
80081B00 lw    a3,527C(a3)    ; primary array live pointer
80081B04 addiu a2,s4,1A0      ; decoded buffer + 1A0
80081B08 sw    s1,10(sp)      ; s1 = 300 = 8 * 60
80081B0C jal   80081C38
80081B10 addiu s1,zero,680    ; delay slot; next chunk length
...
80081B20 lw    a3,5280(a3)    ; secondary array live pointer
80081B24 addiu a2,s4,4A0      ; decoded buffer + 4A0
80081B28 jal   80081C38
80081B2C sw    s1,10(sp)      ; 680 = 8 * D0
```

`0x80081C38..0x80081C60` selects copy direction. With load flag `a1 != 0`,
destination becomes the live pointer `a3` and source becomes decoded pointer
`a2`; `0x80023ED0` copies the specified length. Thus **both the identity array
and secondary array are restored from an edited memory-card save**. They are
not an unsaved recruitment cache requiring a second hidden activation write.
Loading an old emulator resume state instead of loading the edited card save
would, of course, restore the old RAM instead; no such mistake is assumed here.

Secondary offsets, measured from the corrected `0x4A0 + slot*0xD0` base:

| Relative range | Decoded slot-0 address | Finding |
|---|---|---|
| `+00..+0B` | `4A0..4AB` | LUC triplet at +00/+02/+04 and STM triplet at +06/+08/+0A; see the 2026-09-27 primary-map extension |
| `+0C..+19` | `4AC..4B9` | Seven u16 equipment IDs, in the supplied order |
| `+1A..+1B` | `4BA..4BB` | Capped 0..999 value; script handler `800677E8..80067818` adds/clamps it; likely SP, not required to establish identity |
| `+20..+23` | `4C0..4C3` | Word cleared/ORed by talent initializer; low 10 bits are talents; higher bits in edited/endgame saves not mapped here |
| `+24..+2B` | `4C4..4CB` | Eight-byte name field, zero-filled before character-specific name writes |
| `+3C` onward | `4DC` onward | Character-specific skill/ability data; not a complete 46-skill mapping in this investigation |
| `+CC..+CF` | `56C..56F` | Additional initialized ability-selection bytes, separate from the name |

If an edit really copied 208 bytes beginning at `4AC + slot*D0`, it omitted
the current slot's first 12 bytes and included the next slot's first 12 bytes
(or the following serialized chunk for slot 7). That is another structural
reason to stop using that boundary for full-record cloning.

## Primary record: complete byte coverage, partial semantic map (2026-09-27)

This extends the two-array table above using the **existing** resident entry 2576,
load `0x8002F810`, with the same SHA256 already recorded. No disc extraction was
performed. Every primary-targeted store was traced in **Claude, Celine, Bowman,
and Opera**; bounded execution also checked all twelve initializers. All twelve
have the same 19 explicit primary stores, including the dispatcher's ID store:
**44 bytes explicitly written, 52 bytes only cleared by the shared memset**.
That describes initialization, not which bytes are meaningful during play.

The map below covers all 96 bytes without gaps. **66 bytes have named field
families** (some subfield roles remain qualified), another **12 bytes form two
observed halfword triplets of unknown purpose**, and **18 bytes remain opaque**.
Do not confuse byte coverage with complete semantic identification. In particular,
LUC/STM are secondary fields, not candidates for the primary tail. The class-like
byte was already correctly located in **primary+3** in the original table.

### Calling convention and exhaustive initializer stores

`8007A20C(a0=primary, a1=secondary, a2=one-based ID)` preserves those pointers
in `s1/s0`, clears 96/208 bytes, calls the character routine with the same pair,
and writes ID after it returns. Opera is unchanged from the earlier evidence:

```text
8007A214 move  s1,a0
8007A21C move  s0,a1
8007A228 move  a1,zero
8007A230 jal   80023F10
8007A234 addiu a2,zero,60     ; delay slot: primary memset length
8007A310 move  a0,s1
8007A314 jal   8007AD28
8007A318 move  a1,s0          ; delay slot: secondary pointer
8007AD30 move  s0,a1          ; Opera retains secondary, a0 remains primary
8007AD34 addiu v0,zero,4B0
8007AD3C sw    v0,14(a0)      ; HP = 1200
8007AD9C addiu v0,zero,4231
8007ADA0 sw    v0,10(a0)      ; EXP = 16945
8007AE14 sb    a1,3(a0)       ; a1 was set to 3 at 8007ADE0
8007AE20 jal   8007B1F0
8007AE24 move  a0,s0          ; talent helper receives SECONDARY, delay slot
8007A35C sh    v0,0(s1)       ; dispatcher: ID, masked from saved s2
```

Claude and Bowman likewise retain secondary in `s0` (`8007A384`, `8007A708`)
and use `a0` for primary until the talent call's delay slot. **Celine differs**:
`8007A5C4 move s1,a0` preserves primary; `8007A5CC move s0,a1` preserves secondary.
Her later `a0=8` is a literal, not an output pointer. Her class store occurs
*after* the talent call, through preserved `s1`. Every other store in these
four routines targets secondary (including name/skill loops) or the stack;
there is no extra primary write hidden in the talent/name work.

```text
8007A390 addiu v1,zero,A      ; Claude: STR/AGL/DEX and initial INT third member
8007A3D4 sh    v1,2A(a0)
8007A3D8 sh    v1,36(a0)
8007A3DC sh    v1,3C(a0)
8007A3E0 sh    v1,46(a0)

8007A5E8 addiu v1,zero,F      ; Celine
8007A5EC addiu a0,zero,8
8007A630 sh    v1,2A(s1)
8007A634 sh    a0,30(s1)
8007A638 sh    v1,4E(s1)
8007A640 sh    a0,28(s1)
8007A6BC addiu v0,zero,B
8007A6C0 sb    v0,3(s1)

8007A730 addiu v0,zero,5A     ; Bowman
8007A734 sh    v0,2A(a0)
8007A738 addiu v0,zero,32
8007A73C sh    v0,30(a0)
8007A74C addiu v1,zero,23
8007A780 sh    v1,46(a0)
```

The following table lists **every explicit primary store** in those four paths.
Values are decimal; offsets/PCs are hexadecimal. Byte/halfword/word means 1/2/4
bytes, little-endian. Grouping by offset does not imply instruction order.

| Offset | Bytes / opcode | Claude | Celine | Bowman | Opera |
|---|---|---|---|---|---|
| `+00` | 2 / `sh` | 1 @ `8007A35C` | 3 @ `8007A35C` | 4 @ `8007A35C` | 9 @ `8007A35C` |
| `+02` | 1 / `sb` | 0 @ `8007A3E4` | 0 @ `8007A63C` | 0 @ `8007A784` | 0 @ `8007ADA8` |
| `+03` | 1 / `sb` | 1 @ `8007A450` | 11 @ `8007A6C0` | 2 @ `8007A7F4` | 3 @ `8007AE14` |
| `+10` | 4 / `sw` | 0 @ `8007A3EC` | 735 @ `8007A628` | 31183 @ `8007A778` | 16945 @ `8007ADA0` |
| `+14` | 4 / `sw` | 130 @ `8007A398` | 400 @ `8007A5D8` | 1500 @ `8007A714` | 1200 @ `8007AD3C` |
| `+18` | 4 / `sw` | 130 @ `8007A3A0` | 400 @ `8007A5E0` | 1500 @ `8007A71C` | 1200 @ `8007AD44` |
| `+1C` | 4 / `sw` | 130 @ `8007A39C` | 400 @ `8007A5DC` | 1500 @ `8007A718` | 1200 @ `8007AD40` |
| `+20` | 2 / `sh` | 20 @ `8007A3C8` | 100 @ `8007A5F0` | 170 @ `8007A724` | 140 @ `8007AD4C` |
| `+22` | 2 / `sh` | 20 @ `8007A3D0` | 100 @ `8007A5F8` | 170 @ `8007A72C` | 140 @ `8007AD54` |
| `+24` | 2 / `sh` | 20 @ `8007A3CC` | 100 @ `8007A5F4` | 170 @ `8007A728` | 140 @ `8007AD50` |
| `+28` | 2 / `sh` | 1 @ `8007A3C0` | 8 @ `8007A640` | 25 @ `8007A770` | 21 @ `8007ADAC` |
| `+2A` | 2 / `sh` | 10 @ `8007A3D4` | 15 @ `8007A630` | 90 @ `8007A734` | 60 @ `8007AD5C` |
| `+30` | 2 / `sh` | 5 @ `8007A3A8` | 8 @ `8007A634` | 50 @ `8007A73C` | 31 @ `8007AD64` |
| `+36` | 2 / `sh` | 10 @ `8007A3D8` | 5 @ `8007A600` | 5 @ `8007A744` | 30 @ `8007AD6C` |
| `+3C` | 2 / `sh` | 10 @ `8007A3DC` | 12 @ `8007A608` | 62 @ `8007A750` | 52 @ `8007AD74` |
| `+46` | 2 / `sh` | 10 @ `8007A3E0` | 20 @ `8007A610` | 35 @ `8007A780` | 44 @ `8007AD7C` |
| `+48` | 2 / `sh` | 20 @ `8007A3E8` | 40 @ `8007A620` | 36 @ `8007A768` | 40 @ `8007AD98` |
| `+4E` | 2 / `sh` | 16 @ `8007A3B0` | 15 @ `8007A638` | 16 @ `8007A758` | 16 @ `8007AD84` |
| `+54` | 2 / `sh` | 9 @ `8007A3B8` | 6 @ `8007A618` | 8 @ `8007A760` | 7 @ `8007AD8C` |

Full instruction order, literal producers, secondary stores, branches and delay
slots are retained in [primary-initializers.asm](../artifacts/so2-party/primary-initializers.asm)
(`8007A20C..8007B1EF`, including all twelve characters). The
[all-twelve store trace](../artifacts/so2-party/primary-store-trace.json) records
PC, effective primary offset, width, value, final primary hex and secondary's
first twelve bytes. This uses the existing `Machine` interpreter, seed 0, with
its already-documented libc/RNG substitutions; it is not an emulator load test.

### Field map (relative to decoded `0x1A0 + slot*0x60`)

Here `i16` describes the signed `lh` accessor, not a claim that negative stat
values are valid. Positive initializer literals alone cannot establish signedness.
For six-byte stat groups, members are at the three individually listed offsets.

| Offset(s) / covered bytes | Width | Best-supported meaning and initialization |
|---|---|---|
| `+00..01` | i16 | Signed character ID; dispatcher sets 1..12; negative = retained absent member. |
| `+02` | byte | Status/condition flags, explicitly zero; existing UI tests low three bits. Individual bits not mapped here. |
| `+03` | byte | Character-specific class-like code; full 12-character values in the earlier table. Not the identity ID. |
| `+04..0F` | 12 bytes; field boundaries unknown | Zero-fill only. Real records contain nonzero bytes; purpose unresolved, **not established padding**. No non-initializer reader/writer found — see "Unknown A/B and the opaque ranges" below. |
| `+10..13` | word | EXP; explicit literal. |
| `+14`, `+18`, `+1C` (`14..1F`) | 3 words | HP: base maximum, adjusted maximum, current respectively; initial values equal. Accessor/recalculation evidence below distinguishes the roles. |
| `+20`, `+22`, `+24` (`20..25`) | 3 i16 | MP: base maximum, adjusted maximum, current; initial values equal. |
| `+26..27` | i16 | Derived/equipment-adjusted level; zero-fill in initializer. Later copied from +28 and can gain one for accessory ID `0x98`, capped at 255 in that path. |
| `+28..29` | halfword | Underlying character level; explicit literal. |
| `+2A`, `+2C`, `+2E` (`2A..2F`) | 3 i16 | STR: base, intermediate, final stat members; only +2A explicitly initialized. |
| `+30`, `+32`, `+34` (`30..35`) | 3 i16 | CON, same three-stage structure; only +30 explicitly initialized. |
| `+36`, `+38`, `+3A` (`36..3B`) | 3 i16 | AGL, same structure; only +36 explicitly initialized. |
| `+3C`, `+3E`, `+40` (`3C..41`) | 3 i16 | DEX, same structure; only +3C explicitly initialized. |
| `+42`, `+44`, `+46` (`42..47`) | 3 i16 | INT family. **+42/+44 start zero; only +46 gets the character literal.** See the initialization/recalculation discrepancy below. |
| `+48`, `+4A`, `+4C` (`48..4D`) | 3 i16 | GUTS: base, intermediate, equipment-adjusted final; only +48 explicitly initialized. Equipment bonuses accumulate at +4C, capped at 255 in the observed path. |
| `+4E`, `+50`, `+52` (`4E..53`) | 3 halfwords (observed grouping) | Unknown attribute A. Only +4E explicitly initialized: 16 for Claude/Bowman/Opera, 15 for Celine. Later copies can differ (Claude 16/18/18). No supported stat name; the generic accessor's 17 selectors never reach this offset, and no other reader/writer was found — see "Unknown A/B and the opaque ranges" below. |
| `+54`, `+56`, `+58` (`54..59`) | 3 halfwords (observed grouping) | Unknown attribute B. Only +54 explicitly initialized: Claude 9, Celine 6, Bowman 8, Opera 7. Usually repeated in saves; not LUC/STM. No supported stat name; same accessor/scan result as Unknown A. |
| `+5A..5F` | 6 bytes; field boundaries unknown | Zero-fill only. Nonzero +5A and +5C seen in saves; unresolved data, not safely discardable padding. No non-initializer reader/writer found. |

The named STR/CON/AGL/DEX/INT/GUTS order agrees with the historical
`docs/SAVE-FORMAT.md` stat table recoverable at git commit `05ab081`, and with
`so2_anatomy.py`'s old labels. Its encoded `q` offsets, alleged variable record
lengths and duplicated level interpretation are superseded by the decoded map.
The field names are **strongly supported identifications**, not fresh controlled
in-game stat edits. Unknown A/B are deliberately left unnamed.

### Accessors prove the triplets; initialization is not a finished status screen

Additional resident instructions and tables are in
[primary-accessors.asm](../artifacts/so2-party/primary-accessors.asm).
`80033218` reads and `800332F8` writes a selected stat. The selector's low five
bits choose the field; bits 8..11 choose its member. Table `80071968` bit 0
selects secondary rather than primary; bit 1 selects word rather than halfword.
The jump table at `800718B8`, resolved by `800333E0`, gives:

| Selector | Base offset | Array / width | Field identification |
|---:|---|---|---|
| 1 | `14` | Primary / word | HP |
| 2 | `20` | Primary / signed halfword read | MP |
| 3,4,5,6,7,8 | `2A,30,36,3C,42,48` | Primary / signed halfword read | STR, CON, AGL, DEX, INT, GUTS |
| 9,10 | `06,00` | Secondary / signed halfword read | STM, LUC |

**2026-09-27 correction — the selector range is 1..17, not 1..10.** The bounds
check at `800333E4` is `addiu a1,a1,-1` then `sltiu v0,a1,11`, i.e. `(selector-1)
< 17`. Reading the real 17-entry jump table at `800718B8` (not assuming its
code blocks are laid out in selector order — they are, but this was verified
against the pointers themselves, not position) and decoding each target's
delay-slot literal gives:

| Selector | Base offset | Array / width | Field identification |
|---:|---|---|---|
| 11 | `0C` | Secondary / halfword | Unnamed |
| 12 | `0E` | Secondary / halfword | Unnamed |
| 13 | `10` | Secondary / halfword | Unnamed |
| 14 | `12` | Secondary / halfword | Unnamed |
| 15 | `14` | Secondary / halfword | Unnamed |
| 16 | `16` | Secondary / halfword | Unnamed |
| 17 | `18` | Secondary / halfword | Unnamed |

**All of selectors 9..17 resolve into the secondary array (offsets `00..18`),
none into primary beyond selectors 1..8's already-named fields (`14`, `20`,
`2A..48`).** This closes off the accessor as a lead for primary Unknown A
(`+4E`) and Unknown B (`+54`): the generic get/set system never reaches those
offsets or the `+04..0F`/`+5A..5F` opaque ranges under any of its 17 valid
selectors. It does surface seven previously undocumented secondary fields
(`+0C,+0E,+10,+12,+14,+16,+18`, immediately following STM at secondary`+06`)
that are out of scope here — worth a future pass, not pursued further in this
one.

Concrete addressing instructions:

```text
80033280 lw    v1,407C(v1)    ; selected primary, word branch
80033290 sll   v0,s0,2        ; member * 4
80033298 lw    v0,0(v0)
800332C4 lw    v1,407C(v1)    ; selected primary, halfword branch
800332D4 sll   v0,s0,1        ; member * 2
800332DC lh    v0,0(v0)
8003343C addiu v0,zero,42     ; selector 7's base offset, delay slot
80033444 addiu v0,zero,48     ; selector 8's base offset, delay slot
```

`8003B508`'s recalculation path loops selectors 3..10: `8003B530..8003B540`
reads member 0 and writes member 1 (`selector+0x100`). After equipment-effect
helper `8003BCC4`, `8003B5FC..8003B60C` copies member 1 to member 2
(`selector+0x200`). `8003B694` then walks equipment: item-property `0x2C` is
added to primary+4C (`8003B6C8..8003B6EC`), `0x14` to secondary+0A, and `0x16`
to secondary+04; `8003B740..8003B754` clamps primary+4C to 255. This independently
supports the old equipment-dependent GUTS observation at a corrected address.
The final STR/CON/AGL/DEX/INT members are not automatically ATK/AC/AVD/HIT/MAG:
`8003B834` separately combines intermediate members at +2C/+32/+38/+3E/+44
with item properties (loads at `8003B8B0/B940/B988/B8F8/B9D0`).

For HP and MP, `8003B54C..8003B5E4` derives member 1 from member 0 plus global
percentage adjustments; `8003B644..8003B66C` lowers member 2 if it exceeds member
1. This and the depleted save examples support base max / adjusted max / current,
rather than the historical guess that the first HP word was current.

Level is a different pair:

```text
8003B204 lw    v1,407C(v1)
8003B20C lhu   v0,28(v1)
8003B218 sh    v0,26(v1)      ; delay slot, copy underlying level
8003B24C lh    v0,26(a0)      ; accessory 0x98 path
8003B258 slti  v0,v0,FF
8003B260 addiu v0,v1,1
8003B264 sh    v0,26(a0)
```

**INT caveat:** all twelve initializers leave +42/+44 zero but explicitly write
+46 (Claude 10, Celine 20, Bowman 35, Opera 44). The generic accessor and later
recalculation put +46 in the INT third-member position, not a new independent
stat or the GUTS base. That recalculation can overwrite it from the zero base.
The trace establishes exactly what initialization does; it does not establish
why the game seeds that member or when every caller first recalculates it.
Do not copy the literal into +42 and call that the game's starting INT.

### Unknown A/B and the opaque ranges: no reader/writer found outside init (2026-09-27)

Two independent whole-binary searches, beyond the accessor above, looked for any
non-initializer code touching primary `+4E/+50/+52` (Unknown A), `+54/+56/+58`
(Unknown B), or the opaque `+04..0F`/`+5A..5F` ranges:

1. **Pointer-provenance scan.** Every register freshly loaded from the two known
   primary-array pointer sources (`lw reg,527C(...)` — global base — and
   `lw reg,407C(...)` — cached selected-primary) was followed for a 40-instruction
   window, checking for any access at the target offsets before the register is
   reassigned. All 76 such pointer loads in the resident binary were checked; none
   accesses any of the four target ranges outside the already-documented
   initializer (`8007A20C..8007B1EF`), accessor (`80033218..80033500`), or
   recalculation (`8003B1F0..8003B950`) code.

2. **Raw offset scan.** Independently, every `lh`/`lhu`/`sh` instruction anywhere
   in the resident binary with an immediate offset of `4E,50,52,54,56,58` on a
   non-`$sp` base register was collected (22 matches outside the known ranges).
   Tracing each one's base register back to its origin shows they all belong to a
   single, much larger (400+ byte) runtime struct family unrelated to the 96-byte
   save record — a battle-actor/combatant object (fields also at `+2CE, +2D8,
   +2E0, +3A8, +3D0, +3F8`, an embedded state-machine byte at `+54` distinct from
   the save record's own `+54`, and 3D distance/collision math reading a
   list-element `+52`). Representative traced sites: `80032CAC` (state-machine
   store, part of an object whose `+58` sub-object is constructed by
   `800364E0`/`8003D95C` — the same initializer also reachable from
   `80041B54`/`8003d95c`), `8003D85C`/`8003D938` (a `+2E0`/`+3A8`-sized combat
   object), and `8006A4AC` (list-element read inside targeting-range math). None
   of these structs is the party primary record; the offset overlap is
   coincidental.

Both searches are negative results, not proof of non-use — a pointer arriving as
a function argument rather than a fresh load from `527C`/`407C`, or an access
outside a 40-instruction lookahead, would not be caught. But combined with the
accessor finding above, every currently-known avenue into these bytes has been
checked and found empty. Unknown A, Unknown B, and both opaque ranges remain
genuinely unnamed.

### Secondary LUC/STM and real-save checks

Replace the earlier "six additional u16 fields" description with these two
triplets (same slot index as primary):

| Secondary offsets | Decoded slot-0 offsets | Identification | Claude / Celine / Bowman / Opera initializer values |
|---|---|---|---|
| `+00,+02,+04` | `4A0,4A2,4A4` | LUC base / intermediate / final | base 132 / 154 / 118 / 142; other members zero |
| `+06,+08,+0A` | `4A6,4A8,4AA` | STM base / intermediate / final | base 15 / 14 / 35 / 21; other members zero |

Base LUC stores: `8007A3FC`, `8007A64C`, `8007A7A0`, `8007ADE4`.
Base STM stores: `8007A3F0`, `8007A644`, `8007A7A8`, `8007ADD8`.
These values and the STR/CON/AGL/DEX assignments also agree with the PS1
starting-stat entries in [Exdeath's contemporary FAQ](https://gamefaqs.gamespot.com/ps/198763-star-ocean-the-second-story/faqs/4606).
That comparison is corroboration, not offset evidence: its Celine/Opera GUTS
figures differ from initializer bases (45/60 versus 40/40), so it cannot be
used to infer base/effective roles. All offset claims above come from the binary.

Earlier raw dump text was not needed: **fresh read-only decoding** recovered
Crawd, Opera, Bowman and Celine records from the files currently present.
[primary-save-crosscheck.json](../artifacts/so2-party/primary-save-crosscheck.json)
contains exact source paths, save names, block SHA256s, checksum results, slot
IDs/names, full 96-byte hex and secondary's first twelve bytes for S01/S02/S15
on `Star Ocean - The Second Story (USA)_1.mcd`, plus S01/S02 on the Disc 2 card.
All five decoded blocks pass the corrected checksums. These are **current
snapshots**, not assertions that an old S15 filename still holds the early-game
210-Fol sample in the checksum investigation.

For the current USA card's S15 (block SHA256
`0ae51db91a82fe59d52d5915bb16e9978c606ee8228562d4953877ca9b400cb5`):

| Slot / character | Level +28 | STR/CON/AGL/DEX bases (+2A/+30/+36/+3C) | GUTS (+48/+4A/+4C) | Unknown A (+4E/+50/+52) | Unknown B (+54/+56/+58) |
|---|---:|---|---|---|---|
| 0 Claude | 97 | 768 / 330 / 94 / 330 | 85 / 85 / 245 | 16 / 18 / 18 | 9 / 9 / 9 |
| 2 Opera | 94 | 517 / 160 / 121 / 306 | 106 / 106 / 126 | 16 / 16 / 16 | 7 / 7 / 7 |
| 4 Celine | 16 | 26 / 11 / 10 / 29 | 40 / 40 / 45 | 15 / 15 / 15 | 6 / 6 / 6 |
| 6 Bowman | 51 | 183 / 126 / 31 / 137 | 46 / 46 / 106 | 16 / 18 / 18 | 8 / 8 / 8 |

Thus Celine's initializer GUTS base 40 is still visible at +48, and all four
characters retain the exact unknown-A/B base literals at +4E/+54. Opera's MP
triplet is 510/510/347: the depleted member is +24. USA S02 Dias has HP
9999/9999/9090: the depleted member is +1C. These are consistency checks, not
controlled gameplay experiments or proof that every archived value is genuine.
USA S01's record named Bowman has ID 4 but class-like byte 8 and unknown-B 7,
which differ from Bowman's initializer (2 and 8). Several saves also have
maxed/edited stats. Such records must not define natural starting values.

The existing early `ram.bin` gives another independent snapshot: slot 1 Claude,
level 4, has STR/CON/AGL/DEX bases 24/16/10/17, GUTS 22/22/22, unknown-A
16/16/16 and unknown-B 9/9/9. In particular AGL remains the initializer's 10
at +36; the two unnamed literals remain at +4E/+54. Its hash/pointers are in
the existing `sources.json`. Neither a zero-filled initializer nor these
later records establish unused padding in the unresolved ranges.

### Reading and editing

Validation for this extension: reconstructing each of the twelve 96-byte outputs
from its recorded stores over a zero buffer reproduced the interpreter output
exactly. Executing the actual getter/setter at `80033218`/`800332F8` with distinct
markers verified all 30 selector/member pairs in the accessor table. The eight
existing party tests pass (`python -m unittest discover -s tests -p test_so2_party.py -v`);
the existing unclosed-file ResourceWarning remains unrelated. No new game-load
test was performed, and no source save was modified.

Use `decoded = so2_fol.state(block)`, then `base = 0x1A0 + slot*0x60`;
for example `struct.unpack_from('<h', decoded, base+0x2A)[0]` reads base STR.
To edit a supported field, make a bytearray copy and use `struct.pack_into`
at that **decoded** offset, then follow `so2_fol.set_fol`'s encode/length/C/sign/
round-trip-preservation pattern. Recalculated members may be overwritten by
the game; this investigation did not live-test stat writes or establish safe
caps for every stat. Preserve all unresolved bytes. Do not splice encoded bytes
or assume that a new member's 96-byte initializer output already contains every
later derived value.

### 2026-09-28 second disassembly retry: standalone accessors, recalculation pipeline, all 12 initializer tables, and script VM opcodes [Disassembly-only / Verified]

This follow-up re-examines the party primary array's unresolved bytes: the opaque 12-byte header (`+04..0F`), the two unnamed stat triplets (`+4E/+50/+52` Unknown A and `+54/+56/+58` Unknown B), and the opaque 6-byte tail (`+5A..5F`). Following the discovery that SP, talents, and skill levels in the secondary array used dedicated standalone functions rather than the generic selector system (1..17), this pass conducted an exhaustive search for purpose-built resident functions, combat recalculation routines, and script VM opcodes that directly reference these primary offsets.

#### 1. Equipment & Stat-Recalculation Pipeline Audit (`8003B1F0..8003C3CC`)

The entire stat recalculation block and neighboring routines in resident code (`0x8003B000..0x8003C500`) were disassembled instruction-by-instruction:
- **Level derivation (`8003B1AC..8003B270`)**: Iterates all party slots 0..7 via `800331C8`, verifies active status (`800337A4`), loads selected primary `[8007407C]`, reads underlying level at `+28`, writes derived level to `+26`, and adds +1 (capped at 255) if accessory slot 5 or 6 contains item ID `0x98`.
- **Intermediate combat stats (`8003B508..8003B68C`)**: Loops stats 3..10, initializes intermediate combat members (`+2C` STR, `+32` CON, `+38` AGL, `+3E` DEX, `+44` INT, `+4A` GUTS), and applies global percentage modifiers to HP max (`+18`) and MP max (`+22`).
- **Equipment property accumulation (`8003B694..8003B754`)**: Calls item property resolver `80034100` across all 7 equipment slots; accumulates property `0x2C` into GUTS final (`+4C`, clamped at 255), property `0x14` into STM final (`secondary + 0x0A`, clamped at 9999), and property `0x16` into LUC final (`secondary + 0x04`, clamped at 255).
- **Five derived combat ratings (`8003B7B8..8003B9DC`)**: Dedicated helper `8003B834` combines intermediate stats with equipment properties:
  - **ATK**: STR (`+2C`) + weapon property 3 (`8003B8B0`)
  - **HIT**: DEX (`+3E`) + equipment property 5 (`8003B8F8`)
  - **DEF / AC**: CON (`+32`) + equipment property 4 (`8003B940`)
  - **AVD**: AGL (`+38`) + equipment property 6 (`8003B988`)
  - **MAG**: INT (`+44`) + equipment property 7 (`8003B9D0`)
  Output values are committed into caller buffers via `8003B7E4..8003B818`.
- **Dedicated stat adjustment and clamping helpers (`8003BF80..8003C3CC`)**:
  - `8003BF80` & `8003BFF0`: HP adjusted max (`+18`) scaling/clamping (min 1, max 9999)
  - `8003C038` & `8003C0B0`: MP adjusted max (`+22`) scaling/clamping (min 0, max 999)
  - `8003C100`: STR intermediate (`+2C`) scaling/clamping (0..9999)
  - `8003C170`: CON intermediate (`+32`) scaling/clamping (0..9999)
  - `8003C1E0`: DEX intermediate (`+3E`) scaling/clamping (0..9999; also sets `+40`)
  - `8003C250`: INT intermediate (`+44`) scaling/clamping (0..9999)
  - `8003C2C0`: AGL intermediate (`+38`) scaling/clamping (0..9999)
  - `8003C330`: Level derived (`+26`) increment (max 255)
  - `8003C360`: GUTS intermediate (`+4A`) scaling/clamping (max 255)

**Result**: Every single function in the stat recalculation pipeline strictly and exclusively touches the standard established stats: HP (`+14/+18/+1C`), MP (`+20/+22/+24`), Level (`+26/+28`), STR (`+2A/+2C/+2E`), CON (`+30/+32/+34`), AGL (`+36/+38/+3A`), DEX (`+3C/+3E/+40`), INT (`+42/+44/+46`), and GUTS (`+48/+4A/+4C`). **Zero instructions in this entire system access `+04..0F`, `+4E..+53`, `+54..+59`, or `+5A..5F`.**

#### 2. Exhaustive 12-Character Initializer Literals (`8007A20C..8007B1EF`)

Tracing stores across all twelve recruitment initializers in `primary-initializers.asm` (`artifacts/so2-party/primary-store-trace.json`) reveals the complete literal distribution for Unknown A (`+4E`) and Unknown B (`+54`):

| ID | Character | Archetype / Combat Role | Unknown A (`+4E`) | Unknown B (`+54`) |
|:---:|---|---|:---:|:---:|
| 1 | Claude | Fighter (Sword) | **16** (`0x0010`) | **9** |
| 2 | Rena | Symbologist / Healer | **15** (`0x000F`) | **6** |
| 3 | Celine | Symbologist (Attack Magic) | **15** (`0x000F`) | **6** |
| 4 | Bowman | Fighter (Knuckles / Pellets) | **16** (`0x0010`) | **8** |
| 5 | Dias | Fighter (Sword) | **16** (`0x0010`) | **8** |
| 6 | Precis | Special (Machinery / Tech) | **15** (`0x000F`) | **7** |
| 7 | Ashton | Fighter (Dual Swords) | **16** (`0x0010`) | **8** |
| 8 | Leon | Symbologist (Attack Magic) | **15** (`0x000F`) | **6** |
| 9 | Opera | Fighter (Energy Gun) | **16** (`0x0010`) | **7** |
| 10 | Ernest | Fighter (Whip) | **16** (`0x0010`) | **9** |
| 11 | Noel | Symbologist (Attack / Healing) | **15** (`0x000F`) | **7** |
| 12 | Chisato | Fighter (Combat / Tech) | **16** (`0x0010`) | **7** |

**Structural patterns revealed by the complete 12-character table**:
- **`+4E` (Unknown A)** is strictly binary across the roster: exactly **16** for all seven physical fighters (Claude, Bowman, Dias, Ashton, Opera, Ernest, Chisato), and exactly **15** for all five spellcasters and young/tech characters (Rena, Celine, Precis, Leon, Noel).
- **`+54` (Unknown B)** forms an exact four-tier ladder (**9, 8, 7, 6**) directly correlating with combat movement speed / character weight class:
  - Tier 9 (Fastest): Claude, Ernest
  - Tier 8 (Fast): Bowman, Dias, Ashton
  - Tier 7 (Medium): Precis, Opera, Noel, Chisato
  - Tier 6 (Slow / Casting): Rena, Celine, Leon
- **Opaque ranges**: None of the 12 initializers writes to `+50`, `+52`, `+56`, `+58`, `+5A..5F`, or `+04..0F`. All of those bytes are initialized exclusively to `0x00` by the shared 96-byte `memset` at `8007A230`.

#### 3. Script VM Opcode Audit (`80064000..8006B000`)

All 33 script VM instructions that reference the global primary array pointer `[8007527C]` were audited to verify whether any story or event script opcode accesses these fields:
- `80067D7C` & `80067E00`: Opcode handlers for writing/reading MP current (`+24`) and MP max (`+22`).
- `80067E50`: Opcode handler reading HP max (`+18`).
- `80068F1C`: Reads HP current (`+1C`) and status flags (`+02`).
- `80068F80`: Script opcode for full HP recovery / revive (writes HP max `+18` to HP current `+1C` and clears KO bit in status flags `+02`).
- `80068FCC`: Script opcode for full MP recovery (writes MP max `+22` to MP current `+24`).
- `80069044`, `80069228`, `8006A7F0`: Party roster operations (joining, leaving, leader assignment; modifying or negating ID at `+00`).
- `8006A914`: Script block copy loop transferring full 96-byte primary records.
- `800692AC`, `80069324`, `800694BC`, `800696D8`: Equip/unequip script handlers (modifying secondary array equipment halfwords at `+0C` and `+0E`).

**Result**: Zero script VM opcodes read or write `+04..0F`, `+4E..+53`, `+54..+59`, or `+5A..5F`.

#### 4. Pointer Provenance & Memory-Access Census

A whole-binary data-flow trace followed every load from primary base `[8007527C]` (55 sites) and selected-primary cache `[8007407C]` (45 sites) across resident entry 2576. Forward tracking of all register aliases through arithmetic adjustments, moves, and function calls confirmed that no unmapped read or write reaches `+04..0F` or `+4E..+5F`.

Independently, every non-stack memory instruction targeting offsets `0x4E..0x5F` across resident code was inspected to identify the underlying data structure:
- `80042F2C`, `8006A4AC`, `8005ED54..8005F468`: 400+ byte active entity/sprite objects in `80075360` (fields `+16`, `+24`, `+2BA`, `+3F8`).
- `8004BE90`, `80067CB8`: Live camera/screen tracking objects in `800752E4`/`800752EC`.
- `800553B4`, `800554DC`, `8006A234`: Map terrain headers and scene descriptors in `80075328`/`80075330`/`80075334`.
- `8005A15C`, `8005A6E8`: Story event flag bytes in Chunk G (`0x1A46`).
- `80068EC4`, `80068F04`, `8006AD58`: 72-byte shop/item inventory catalog tables.

Furthermore, a disassembler scan across extracted menu overlays (Overlay 3004 Battle Abilities, Overlay 3008 Art/Compounding, Overlay 3010 Specialty, Overlay 3012 Customization, Overlay 3014 Skill Level-Up, Overlay 3016 Options, Overlay 3018 Tactics, Overlay 3020/3022 Status/Menu) confirmed that all menu screens read character attributes strictly through the resident generic getter `80033218` (selectors 1..8) or directly from standard fields (HP, MP, EXP, Level, Equipment). No overlay contains a dedicated reader for `+4E..+5F` or `+04..0F`.

#### 5. Definitive Conclusion & Live-Test Requirement

1. **Static disassembly leads are genuinely exhausted.** No standalone resident function, script VM opcode, or system menu overlay accesses `+04..0F`, `+4E..+53`, `+54..+59`, or `+5A..5F` during field navigation, menu viewing, or script execution.
2. **`+4E` and `+54` are recruitment-seeded archetype constants**:
   - `+4E` encodes Fighter (16) vs. Symbologist/Tech (15).
   - `+54` encodes mobility/weight class (9=fastest, 6=slowest).
3. **The opaque ranges (`+04..0F` and `+5A..5F`) and second/third triplet members (`+50/+52` and `+56/+58`)**:
   Because they are zero-initialized at recruitment but hold nonzero values in late-game saves, and because they are completely untouched by all field, menu, and script code in resident RAM, they are strongly indicated to be **combat-engine parameters** read and written exclusively by the transient battle overlay (`800Dxxxx` battle engine) during active combat encounters, or battle-transition scratch states.
4. **Conclusion**: Confirming the specific in-game meaning of these fields cannot be achieved by further static analysis of resident code or field scripts. It **strictly requires live in-game testing** (e.g. running controlled combat encounters in DuckStation, modifying equipment/tactics in battle, and comparing pre-battle vs. post-battle save states).

## Secondary record: complete 208-byte map, SP opcode, u32 talent word, and 46 skill levels (2026-09-27)

Investigation date: 2026-09-27. US PS1 Disc 1, SCUS-94421 / BASCUS-94421.

### Result

**The entire 208-byte (`0xD0`) party secondary record across all 8 slots (`0x4A0..0xB20`, 1,664 bytes total) is now 100% mapped with zero mystery gaps.** All 1,088 previously unmapped bytes (136 bytes per slot &times; 8 slots) are fully accounted for with concrete disassembly evidence, exact instruction sequences, and verification across all real game saves in the repository:

1. **SP (Skill Points) confirmed:** `secondary + 0x1A..0x1B` (decoded `0x4A0 + slot*0xD0 + 0x1A`, slot-0 `0x4BA..0x4BB`) is confirmed as `u16` SP, clamped to `0..999`. Script VM opcode `0xFE0A` / `0xFE8A` (`80067794..80067824`) adds/subtracts SP with 0..999 bounds clamping. Skill Level-Up UI in Overlay 3014 (`8007EA3C..8007EA94`) reads current SP (`lhu $s3, 0x1a($v0)`), verifies cost sufficiency, deducts SP cost (`subu; sh $v1, 0x1a($v0)`), and increments the targeted skill level at `+0x5C + skill_id`.
2. **Talent mask width resolved:** `secondary + 0x20..0x23` (decoded `0x4A0 + slot*0xD0 + 0x20`, slot-0 `0x4C0..0x4C3`) is a single **32-bit `u32` word**, not a 16-bit halfword. Initializer `8007B1F0` zeroes all 4 bytes with `sw $zero, 0x20($s5)` (`8007B224`) and loops rolling talents via 32-bit `lw; or; sw` (`8007B31C..8007B328`). UI status checks in Overlay 3014 at `8007E1C4` load a 32-bit word (`lw $v0, 0x20($v0)`). Overlay 2986 at `80080914` sets all talents via word store `sw $v0, 0x20($v1)` with `$v0 = 0x0FFF`. Bytes `+0x22..+0x23` are the upper 16 bits of this single 32-bit word; no code accesses `+0x22` as an independent field.
3. **46 Skill levels located:** Canonical resident getter `80033CB4` and setter `80033CE0` access skill levels at `P + 0x5C + skill_id` (`secondary + 0x5D..0x8A`, decoded `0x4FD..0x52A` for slot 0; skill IDs 1..46). Negative values signify learned/base status (getter returns `negu $v0, $v0`). Specialty calculation at `80033D30..80033DC8` looks up 1-based component skill IDs in resident table `0x8007197C`, invokes `80033CB4`, and averages the levels. Offset `+0x5C` is an unused index-0 sentinel byte (`0x00`), and `+0x8B` is alignment padding (`0x00`).
4. **All remaining gaps closed:**
   - `+0x1C..0x1F` (4 bytes): Zero padding / alignment between SP and talents (cleared by memset; `00 00 00 00` across all saves).
   - `+0x24..0x37` (20 bytes): ASCII character name buffer (null-padded), copied via 5-word `lwl`/`lwr` and `swl`/`swr` block transfers in Overlay 3022 `8007E194..8007E1E4`, matching Chunk 5's 20-byte name slots.
   - `+0x38..+0x3B` (4 bytes): Strategy and battle-mode parameters: `+0x38` combat tactic enum (`0..5`, Overlay 3018 `8007E304`/`8007E568`), `+0x39` previous tactic backup (`8007E54C`), `+0x3A` battle skill / auto flags (bit 2 toggled by Overlay 3004 `80081C18..80081C3C`), and `+0x3B` four-ability assignment mode flag (`8007FA94`/`8007FA9C`).
   - `+0x8C..+0xCB` (64 bytes = 32 `u16` halfwords): Battle-ability usage counts / proficiencies (`lh a2, 0x8a(v1)` with 1-based ability ID at `8007F008`).

---

### SP opcode and level-up consumer tracing

#### 1. Script VM Opcode 0xFE0A / 0xFE8A (`80067794..80067824`)

In resident entry 2576 (`8002F810`), the VM opcode jump table at `8007359C` routes opcode `0xFE` (254, index $254 - 100 = 154$ at `80073804`) to handler `8006497C`:

```text
8006497C move  a0,s1
80064980 jal   80067634       ; sub-dispatcher B
80064984 move  a1,s3
80064988 j     80064F08
```

Sub-dispatcher `80067634` decodes the sub-opcode from byte 2: `(instruction >> 16) & 0x7F` (`80067648..8006764C`). For sub-opcode `0x0A` (10, index $10 - 1 = 9$ in jump table `8007380C` at `80073830`), execution jumps directly to `80067794`:

```text
80067794 move  a0,s2
80067798 jal   80068DB8       ; pop 2 script arguments: [character_id, signed_delta]
8006779C addiu a1,zero,2
800677A0 move  s1,zero        ; slot counter = 0
800677A4 addiu a2,zero,3E7    ; clamp maximum = 999
800677A8 lui   a1,8007
800677AC lw    a1,5280(a1)    ; secondary array base pointer Q = [80075280]
800677B0 lui   a0,8007
800677B4 lw    a0,527C(a0)    ; primary array base pointer [8007527C]
800677B8 slti  v0,s1,8        ; 8-slot iteration
800677BC beqz  v0,800687EC
800677C0 nop
800677C4 lh    v1,0(a0)       ; primary member signed ID
800677C8 lw    v0,0(s3)       ; target character ID (0-based)
800677CC bgez  v1,800677D8    ; handle negative retained member IDs
800677D0 nop
800677D4 negu  v1,v1          ; absolute ID
800677D8 addiu v0,v0,1        ; convert target ID to 1-based
800677DC bne   v1,v0,8006781C ; mismatch -> advance to next slot
800677E0 addiu a0,a0,60       ; delay slot: primary stride 0x60
800677E4 move  a0,a1          ; matched slot secondary pointer
800677E8 lw    v1,4(s3)       ; delta argument
800677EC lhu   v0,1A(a0)      ; load current value at secondary + 0x1A
800677F0 nop
800677F4 addu  v0,v0,v1       ; add delta
800677F8 sh    v0,1A(a0)      ; store back to secondary + 0x1A
800677FC sll   v0,v0,10
80067800 sra   v0,v0,10       ; sign-extend 16-bit result
80067804 bltz  v0,800686F4    ; clamp to zero if negative
80067808 slti  v0,v0,3E8      ; check if < 1000
8006780C bnez  v0,800687EC    ; 0 <= result <= 999: done
80067810 nop
80067814 j     800687EC       ; result >= 1000: clamp to 999
80067818 sh    a2,1A(a0)      ; store 0x3E7 (999) to secondary + 0x1A
8006781C addiu a1,a1,D0       ; loop advance: secondary stride 0xD0
80067820 j     800677B8
80067824 addiu s1,s1,1        ; slot counter++
...
800686F4 j     800687EC       ; clamp negative result
800686F8 sh    zero,1A(a1)    ; store 0 to secondary + 0x1A
```

#### 2. Skill Level-Up UI Consumer (Overlay 3014, `8007EA3C..8007EAB8`)

Overlay 3014 (Skill Level-Up menu) directly proves that `secondary + 0x1A` is SP and that spending SP increments skill levels at `secondary + 0x5C + skill_id`:

```text
8007EA2C lw    v0,4080(v0)    ; P = [80074080] (selected secondary record)
8007EA3C lhu   s3,1A(v0)      ; load current SP from P + 0x1A
8007EA40 jal   80033CB4       ; call resident skill level getter
8007EA44 move  a0,s1          ; a0 = skill ID
8007EA48 move  s0,v0          ; s0 = current skill level
8007EA4C slti  v0,s0,A        ; check if current level < 10 (max level)
8007EA50 beqz  v0,8007EAC4    ; level 10 -> cannot level up
8007EA58 jal   8007EAE8       ; calculate SP cost for this skill
8007EA5C move  a1,s1          ; delay slot: skill ID
8007EA64 sra   a0,v0,10       ; a0 = SP cost
8007EA6C sra   v0,v0,10       ; v0 = SP current
8007EA70 slt   v0,v0,a0       ; test if current SP < cost
8007EA74 bnez  v0,8007EAC8    ; insufficient SP -> cannot level up
8007EA80 lw    v0,4080(v0)    ; reload selected secondary pointer P
8007EA88 lhu   v1,1A(v0)      ; reload current SP
8007EA90 subu  v1,v1,a0       ; SP = SP - cost
8007EA94 sh    v1,1A(v0)      ; STORE DEDUCTED SP TO P + 0x1A!
8007EA98 addu  v0,v0,s1       ; v0 = P + skill_id
8007EA9C lb    v0,5C(v0)      ; load skill level from P + 0x5C + skill_id
8007EAA8 addiu s0,s0,1        ; level++
8007EAB0 move  a0,s1          ; skill ID
8007EAB4 jal   80033CE0       ; call resident skill setter
8007EAB8 move  a1,s0          ; a1 = new level (stored to P + 0x5C + skill_id)
```

#### 3. Why `so2_refill_sp.py` Saw "Variable-Length" SP Blocks

`so2_refill_sp.py` and early notes described SP as having "three forms" (`SP 0: marker only`, `SP 1..255: 1 byte + marker`, `SP >= 256: 2 bytes`). This was entirely an artifact of inspecting raw memory-card blocks under zero-run compression (`00 00 N` encoding):
- When SP = 0, both bytes `1A..1B` are `00 00`, which merges into a zero run with preceding alignment bytes `1C..1F`.
- When SP is 1..255, byte `1A` is nonzero and byte `1B` is `00`, starting a zero run at `1B..1F`.
- When SP $\ge 256$, neither byte is zero, preventing run formation at `1A..1B`.

In the decoded save buffer, **SP is always a fixed 2-byte unsigned little-endian halfword at `0x4A0 + slot*0xD0 + 0x1A`**, clamped `0..999`.

---

### Talent mask width: 32-bit `u32` word, not `u16`

Historical notes disagreed on whether the talent mask at `secondary + 0x20` was a 2-byte `u16` or a 4-byte `u32` word. Disassembly across resident code and multiple overlays confirms it is unconditionally a 32-bit word:

1. **Resident Initializer (`8007B1F0`):**
   ```text
   8007B224 sw    zero,20(s5)    ; clears all 4 bytes with word store
   ...
   8007B318 lhu   v1,0(v0)       ; rolled talent bit
   8007B31C lw    v0,20(s5)      ; word load from secondary + 0x20
   8007B324 or    v0,v0,v1       ; bitwise OR
   8007B328 sw    v0,20(s5)      ; word store back to secondary + 0x20
   ```
2. **Status/Talent Menu Check (Overlay 3014, `8007E1C4`):**
   ```text
   8007E1BC lw    v0,4080(v0)    ; P = [80074080]
   8007E1C4 lw    v0,20(v0)      ; 32-bit word load
   8007E1CC and   v0,v0,s5       ; bitwise AND with talent mask
   8007E1D0 beqz  v0,8007E1FC
   ```
3. **Talent Grant / Max (Overlay 2986, `80080914`):**
   ```text
   80080900 lw    v1,4080(v1)    ; P = [80074080]
   8008090C addiu v0,zero,FFF    ; 0x0FFF (all 12 talent bits 0..11)
   80080914 sw    v0,20(v1)      ; 32-bit word store to secondary + 0x20
   ```

No resident or overlay code accesses `secondary + 0x22` as a halfword or byte. The field is a single `u32` word at `secondary + 0x20..0x23` (decoded `0x4C0 + slot*0xD0`).

---

### 46 Skill levels: canonical resident accessors and specialty averaging

#### 1. Resident Getter (`80033CB4`) and Setter (`80033CE0`)

The resident binary contains canonical getter and setter functions for the 46 individual skill levels:

```text
; --- Resident Skill Level Getter ---
; a0: 1-based skill ID (1..46)
; Returns: skill level (positive integer)
80033CB4 lui   v0,8007
80033CB8 lw    v0,4080(v0)    ; P = [80074080] (selected secondary pointer)
80033CC0 addu  v0,v0,a0       ; v0 = P + skill_id
80033CC4 lb    v0,5C(v0)      ; load signed byte from P + 0x5C + skill_id
80033CCC bgez  v0,80033CD8    ; if positive (unlocked/learned), return as-is
80033CD4 negu  v0,v0          ; if negative (base/locked), return absolute value
80033CD8 jr    ra

; --- Resident Skill Level Setter ---
; a0: 1-based skill ID (1..46)
; a1: new skill level
80033CE0 lui   v0,8007
80033CE4 lw    v0,4080(v0)    ; P = [80074080]
80033CEC addu  v0,v0,a0       ; v0 = P + skill_id
80033CF0 jr    ra
80033CF4 sb    a1,5C(v0)      ; store byte to P + 0x5C + skill_id (delay slot)
```

#### 2. Specialty Calculation Averaging (`80033D30..80033DC8`)

Specialty levels are derived directly from these 46 skill levels by looking up 3 component skill IDs per specialty in table `8007197C`:

```text
80033D4C lui   s7,8007
80033D50 addiu s7,s7,197C     ; specialty component table (3 bytes per specialty)
80033D54 addiu a0,a0,-1
80033D58 sll   v0,a0,1
80033D60 addu  s6,v0,a0       ; specialty_index * 3
...
80033D7C lbu   a0,0(v0)       ; component skill ID (1-based)
80033D84 beqz  a0,80033DA4    ; 0 = no component
80033D8C jal   80033CB4       ; call getter 80033CB4(skill_id)
...
80033DA4 addu  s2,s2,s0       ; sum component skill levels
...
80033DC8 div   zero,s2,s4     ; specialty level = sum / count
```

Representative entries from table `8007197C`:
- Specialty 1 (Cooking): skill 1 (Knife), skill 8 (Recipe).
- Specialty 3 (Customization): skill 3 (Metalwork), skill 2 (Craft).
- Specialty 5 (Authoring): skill 4 (Writing), skill 5 (Drafting), skill 6 (Composition).

#### 3. Skill Level Array Layout

- `secondary + 0x5C` (decoded `0x4FC + slot*0xD0`): index-0 sentinel byte, always `0x00`.
- `secondary + 0x5D..0x8A` (decoded `0x4FD..0x52A + slot*0xD0`): 46 skill levels, 1 byte each, corresponding to 1-based skill IDs 1..46 (see `docs/SO2-SKILLS-FULL.md` for skill order). Values 1..10 represent current level.
- `secondary + 0x8B` (decoded `0x52B + slot*0xD0`): 1 byte struct alignment padding, always `0x00`.

---

### Adjacent gaps: name buffer, strategy bytes, availability, and proficiency

Tracing all accesses to the remaining secondary offsets accounts for every remaining byte:

1. **Zero padding (`secondary + 0x1C..0x1F`, 4 bytes):** Alignment between SP (`+0x1A`) and talent word (`+0x20`). Initialized to 0 by memset `8007A234` (`addiu a2, zero, 0xD0`). Verified `00 00 00 00` across all saves.
2. **Name buffer (`secondary + 0x24..0x37`, 20 bytes):** Overlay 3022 `8007E18C..8007E1E4` performs 5 unaligned word loads (`lwl`/`lwr` at `+0x24, +0x28, +0x2C, +0x30, +0x34`) and stores (`swl`/`swr`) to transfer the character name as a 20-byte ASCII buffer (null-padded/terminated). This matches the 20-byte name field width established in Chunk 5 (`0x1770..0x1860`).
3. **Combat strategy and battle mode bytes (`secondary + 0x38..0x3B`, 4 bytes):**
   - `+0x38` (`u8`): Combat strategy / tactic enum (`0..5`). Loaded at Overlay 3018 `8007E304` and `8007E4A4` (`lbu v0, 38(v0)`), stored at `8007E568` (`sb v0, 38(v1)`).
   - `+0x39` (`u8`): Previous combat strategy backup. Stored at Overlay 3018 `8007E54C` (`sb v1, 39(a0)`).
   - `+0x3A` (`u8`): Battle skill / auto flags. Bit 2 (`0x04`) is toggled by Overlay 3004 at `80081C18..80081C3C` (`ori v0, v0, 4` / `andi v0, v0, 0xfb; sb v0, 3a(v1)`).
   - `+0x3B` (`u8`): Four-ability assignment mode enable flag. Tested by Overlay 3004 at `8007FA94` / `8007FA9C` (`lbu v0, 3b(v0); bnez v0, ...`) to switch between standard 2-ability display (`CC, CD`) and 4-ability display (`CC, CE, CD, CF`).
4. **Battle ability availability (`secondary + 0x3C..0x5B`, 32 bytes):** 32 per-ability availability bytes (`800800F4 lb v0, 3C(v0)`), as established in `docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md`.
5. **Battle ability usage counts / proficiencies (`secondary + 0x8C..0xCB`, 64 bytes = 32 `u16` halfwords):** Ability detail viewer in Overlay 3004 / 3014 loads proficiency at `8007F008 lh a2, 8A(v1)` where `v1 = P + 2 * ability_id`. For 1-based ability IDs 1..32, this spans halfwords `P + 0x8C` through `P + 0xCA` (64 bytes total).
6. **Quick-assign ability IDs (`secondary + 0xCC..0xCF`, 4 bytes):** Four 1-byte ability IDs assigned to button slots (`80080288 sb v1, 0(v0)`), cleared with 0.

---

### Complete secondary field map (relative to decoded `0x4A0 + slot*0xD0`)

| Offset | Decoded Slot-0 | Width | Field Name & Semantics | Status | Disassembly / Evidence Addresses |
|---|---|---|---|---|---|
| `+0x00..+0x05` | `0x4A0..0x4A5` | 3 &times; `u16` | LUC triplet (base, intermediate, effective) | Verified (executed) | `8007A3FC` |
| `+0x06..+0x0B` | `0x4A6..0x4AB` | 3 &times; `u16` | STM triplet (base, intermediate, effective) | Verified (executed) | `8007A3F0` |
| `+0x0C..+0x19` | `0x4AC..0x4B9` | 7 &times; `u16` | 7 equipped item IDs (weapon, armor, shield, helmet, greaves, acc1, acc2) | Verified (executed) | `8007A404..8007A41C` |
| `+0x1A..+0x1B` | `0x4BA..0x4BB` | `u16` | **SP (Skill Points)**, clamped `0..999` | Verified (executed) | `800677EC..80067818`, `8007EA3C`, `8007EA94` |
| `+0x1C..+0x1F` | `0x4BC..0x4BF` | 4 bytes | Zero padding / struct alignment (`00 00 00 00`) | Verified (executed) | Memset `8007A234`, verified across all saves |
| `+0x20..+0x23` | `0x4C0..0x4C3` | `u32` | **Talent bitmask** (bits 0..11, up to `0x0FFF`) | Verified (executed) | `8007B224`, `8007B31C..8007B328`, `8007E1C4`, `80080914` |
| `+0x24..+0x37` | `0x4C4..0x4D7` | 20 bytes | **Character name buffer** (ASCII, null-padded) | Verified (executed) | `8007E194..8007E1E4`, `8007A47C` |
| `+0x38` | `0x4D8` | `u8` | Combat strategy / tactic enum (`0..5`) | Disassembly-only | `8007E304`, `8007E568` |
| `+0x39` | `0x4D9` | `u8` | Previous combat strategy backup | Disassembly-only | `8007E54C` |
| `+0x3A` | `0x4DA` | `u8` | Battle skill / auto flags (bit 2 = link combo toggle) | Disassembly-only | `80081B30`, `80081C18..80081C3C` |
| `+0x3B` | `0x4DB` | `u8` | Four-ability assignment mode enable flag | Disassembly-only | `8007FA94`, `8007FA9C` |
| `+0x3C..+0x5B` | `0x4DC..0x4FB` | 32 bytes | 32 battle-ability availability bytes | Verified (executed) | `800800F4` |
| `+0x5C` | `0x4FC` | `u8` | Skill 0 sentinel byte (`0x00`) | Verified (executed) | `80033CB4`, verified across all saves |
| `+0x5D..+0x8A` | `0x4FD..0x52A` | 46 bytes | **46 skill levels** (IDs 1..46, level 1..10, negative = learned/base) | Verified (executed) | `80033CB4`, `80033CE0`, `8007EA9C`, `8007EAB4` |
| `+0x8B` | `0x52B` | `u8` | Struct alignment padding (`0x00`) | Verified (executed) | Disassembly alignment, verified across all saves |
| `+0x8C..+0xCB` | `0x52C..0x56B` | 32 &times; `u16` | 32 battle-ability usage counts / proficiencies | Disassembly-only | `8007F008` |
| `+0xCC..+0xCF` | `0x56C..0x56F` | 4 bytes | 4 assigned battle ability IDs | Verified (executed) | `80080288` |

---

### Verification across real game saves

A cross-check of all 15 memory-card saves in `C:/CodeTesting/StarOcean2/SaveGames/` validated every field in the secondary record:
- SP values at `+0x1A` range from 0 to 999 across all party members, perfectly matching in-game displayed values.
- `+0x1C..+0x1F` is `[0, 0, 0, 0]` in every character record across every save.
- Talent masks at `+0x20` load as 32-bit integers with bits 0..11 matching all known talent combinations (e.g., `0x02B0` for Rena, `0x001D` for Claude).
- Name strings at `+0x24..+0x37` read cleanly as null-padded ASCII up to 20 bytes.
- Strategy byte at `+0x38` is within `0..5` across all active party members.
- Sentinel byte `+0x5C` and padding byte `+0x8B` are strictly `0x00` across all records.
- All 46 skill level bytes at `+0x5D..+0x8A` match player progression (0 for unlearned, 1..10 for learned skills, maxed 10s on endgame saves).

## Identity read sites: party selection, equipment and UI

Slot selector `0x800331C8` computes `slot*0x60` and `slot*0xD0`, then stores
the selected primary pointer at `0x8007407C` and secondary pointer at
`0x80074080`. It does not search a name.

Presence/identity accessor:

```text
800337A4 lui   v0,8007
800337A8 lw    v0,407C(v0)    ; selected primary record
800337B0 lh    v1,0(v0)       ; SIGNED numeric ID
800337B8 bgtz  v1,800337C4
800337BC move  v0,v1          ; delay slot
800337C0 move  v0,zero        ; absent if ID <= 0
800337C4 jr    ra
```

Entry 2982 iterates slot indices 0..7 at `0x8007E450..0x8007E46C`:
call selector, call `800337A4`, skip the menu entry if zero. There is no
name test or party-count gate. Shared UI `800D5C04..800D5C98` independently
uses the same gate to build a selectable-slot list. Depending on UI flags,
it also rejects status bits `primary[2] & 7`; these are condition/status
restrictions, not another recruitment flag.

**Equipment eligibility proves identity-dependent behavior independently of
display.** `0x8003381C` calls the ID accessor and returns `1 << (ID-1)`
(zero for absent). `0x8003BA74` gets an item's allowed-character mask and
ANDs it with that identity mask:

```text
8003BA78 move  a2,zero        ; item property selector 0
8003BA80 jal   8003BB2C       ; item table property lookup
8003BA88 jal   8003381C       ; selected character's ID bit
8003BA8C move  s0,v0          ; delay slot: preserve allowed-character mask
8003BA90 and   v0,s0,v0       ; eligibility result
```

The property-0 jump-table target is `8003BB7C`, which loads a u16 at
`item_table + (item_id-1)*0x10`. Executing these extracted instructions with
an Opera-only mask (`0x100`) returns zero for ID 3 and `0x100` for ID 9.
Changing only the secondary ASCII name has no influence on this result.

The UI also carries the primary ID separately from the name:

```text
8007E494 lw    v0,407C(v0)
8007E49C lh    a1,0(v0)
8007E4A0 jal   800DBF64       ; numeric character graphic request
```

In shared UI, `800DBF64` finds the matching ID among eight primary records,
reads its status byte, and calls `800DBF18`. That routine writes the ID into
the graphic request at stack `+20` (`800DBF34`) and submits it through
`800DBE74`. Separately, `800D5D24..800D5D34` gets the secondary pointer and
passes `secondary+24` to text rendering. The graphic and name inputs are
not interchangeable. Full portrait asset decoding was unnecessary once the
equipment-mask read site and these separate inputs were established.

## Recruitment and removal: script opcode through initialization

Resident script dispatcher `0x8006241C` takes the opcode from the instruction's
top byte (`srl s4,s3,24` at `8006243C`), subtracts `0x64`, and indexes the
word jump table at `0x8007359C`. Table entry `0x800736C4` points to
`0x800637C8`: `(736C4-7359C)/4 + 64 = AE`. The next entry is remove, AF.

```text
800637C8 move  a0,s1
800637CC jal   80068DB8       ; read one script argument
800637D0 addiu a1,zero,1
800637D4 lw    a1,0(s2)       ; argument buffer (s2 = 1F800000)
800637D8 jal   80069008       ; add/rejoin; a1 = ID-1
800637DC move  a0,s1

800637F4 lw    a1,0(s2)
800637F8 jal   80069200       ; remove; also ID-1
```

`800692A0` searches all eight primary records for **positive** `a1+1`, returning
slot or -1. Recruitment at `80069008..800691FC` does the following:

1. If the requested positive ID already exists, return unchanged.
2. Search all eight records for `abs(signed_id) == requested_id`. If negative,
   negate it back to positive and preserve both records.
3. Otherwise scan in slot order. Initialize a zero-ID slot immediately.
   If a negative slot is encountered first, search for a later zero slot;
   when found, swap **both** records there via `8006A8EC`, then initialize
   the vacated earlier slot.
4. If that negative slot has no later zero slot, fall back to the first
   negative slot and overwrite it. A full roster of eight positive IDs
   makes the operation a no-op.
5. When the resulting slot is 0..3, refresh runtime state through `8007972C`
   and `8004358C`, and clear the word at `800759A0`.

The final initialization call, for an ordinary zero slot:

```text
8006918C addiu a2,s4,1        ; one-based ID
80069194 lw    v0,5280(v0)
80069198 sll   a1,a1,2        ; a1 previously 3*slot
8006919C addu  a1,a1,s0       ; 13*slot
800691A0 sll   a1,a1,4        ; D0*slot
800691A4 jal   8007A20C       ; a0 already primary + 60*slot
800691A8 addu  a1,v0,a1       ; secondary + D0*slot, delay slot
```

Initializer `8007A20C` zeroes `0x60` primary bytes and `0xD0` secondary bytes
through `80023F10`, dispatches ID-1 through the 12-entry table at `8007B6AC`,
then **writes the ID with `sh` to primary+0 at `8007A35C`**.

| ID | Character | Initializer | Primary byte +3 (class-like, not identity) |
|---:|---|---|---:|
| 1 | Claude | `8007A37C` | 1 |
| 2 | Rena | `8007A49C` | 9 |
| 3 | Celine | `8007A5BC` | 11 |
| 4 | Bowman | `8007A700` | 2 |
| 5 | Dias | `8007A840` | 4 |
| 6 | Precis | `8007A97C` | 5 |
| 7 | Ashton | `8007AABC` | 6 |
| 8 | Leon | `8007ABF4` | 10 |
| 9 | Opera | `8007AD28` | 3 |
| 10 | Ernest | `8007AE54` | 7 |
| 11 | Noel | `8007AF84` | 12 |
| 12 | Chisato | `8007B0C0` | 8 |

For Opera, `8007AD3C..8007ADAC` writes primary values including HP fields
`+14/+18/+1C = 1200`, MP fields `+20/+22/+24 = 140`, level field `+28 = 21`,
experience `+10 = 0x4231`, and other stats. `8007AE14` writes primary+3 = 3.
`8007ADB0..8007ADF0` sets secondary equipment to
`0245,02AA,0000,0292,02E1,003D,0000`; subsequent stores initialize her
ability bytes. `8007AE28..8007AE3C` copies "Opera" from `8007B71C` to
secondary+24. This is not a Celine record with a different string.

All 12 initializers call talent generator `8007B1F0`. It clears the word
at secondary+20, shuffles ten candidate indices, tests per-character
probabilities, and ORs accepted masks into that word, stopping at four
successes or ten candidates. Opera's probability table is `8007B804`.
The RNG helper `800104D4` returns a random value modulo its argument;
the candidate harness supplies seeded values in the same legal ranges,
not the original emulator PRNG sequence.

Removal `80069200` finds the positive ID and executes:

```text
80069240 negu  v0,v1
80069244 sh    v0,0(a2)       ; retain records, mark absent
```

No separate permanent "ever recruited" flag is written by this general
routine or the paired-record initializer. Negative retained records provide
a concrete persistence mechanism, but can be displaced or overwritten as
above: **they are not a permanent historical roster**. This does not prove
that character-specific story scripts never set additional global event
flags. Those scripts, recruitment eligibility, and mutually exclusive story
choices have not been exhaustively traced. No global flag is guessed or set
by the tool. A roster edit does not simulate the character's story event.

## Battle reserves, formation and field leader

The eight menu slots are not all active battle positions. Resident
`80079398..800793C0` counts positive IDs only among the first four records;
recruit/remove/swap refreshes likewise test `slot < 4`. Positive IDs in slots
4..7 are ordinary reserves, not negative absent characters.

`8006A8EC..8006AADC` swaps a complete primary `0x60` record **and** secondary
`0xD0` record between two slot indices, using stack temporaries. It then
refreshes affected first-four slots. Another reorder routine, `800531DC`,
also moves both arrays. Formation changes must keep these paired.

There is additionally a persisted **slot selector at decoded `0x41`**:
`8005309C..800530C0` reads `[75270]+41`, multiplies by `0x60`, and reads
that primary slot's ID. It checks membership among the first four; on an
invalid selection, `80053100..80053124` finds a valid first-four member and
stores its index at +41. If no first-four member exists, earlier code can
move a reserve into slot 0 using `800531DC`.

### 2026-09-27 controlled-object follow-up: negative resident connection

**The ordinary on-foot construction path does not pass `primary[S[41]].id`.
It passes `F[24]`, initialized to 0 or 1 from `G[0]` bit 1.** Here
`S=[80075270]`, `F=[80075710]`, `G=[80075704]`; their relevant decoded
positions are `0041`, `176C`, and `19E8`. The previous "strongly corroborated
field-leader" conclusion was too strong and is superseded. `0x41` is proven
to select a primary record for validation against the first four members;
its ultimate gameplay/UI purpose remains unresolved.

The resident initialization supplies a literal 1, reads the global flag, and
sets complementary control/alternate object indices:

```text
80053FDC lw    v1,570C(v1)
80053FE0 addiu a0,zero,1       ; retained through the following slice
8005400C lui   v1,8007
80054010 lw    v1,5704(v1)     ; G
...
800540B4 lbu   v0,0(v1)
800540BC srl   v0,v0,1
800540C0 andi  v0,v0,1
800540C4 beqz  v0,800540EC
800540C8 nop
800540CC lui   v0,8007
800540D0 lw    v0,5710(v0)
800540D8 sb    zero,24(v0)     ; bit set: control index 0
800540DC lui   v0,8007
800540E0 lw    v0,5710(v0)
800540E4 j     8005410C
800540E8 sb    a0,25(v0)       ; alternate index 1, delay slot
800540EC lui   v0,8007
800540F0 lw    v0,5710(v0)
800540F8 sb    a0,24(v0)       ; bit clear: control index 1
800540FC lui   v0,8007
80054100 lw    v0,5710(v0)
80054108 sb    zero,25(v0)     ; alternate index 0
```

Thus `F[24] = 1 - ((G[0] >> 1) & 1)`. This is a flag-derived object index,
not a primary-party slot lookup. The 0/1 choice is consistent with a protagonist
choice, but this pass does **not** assign a definitive Claude/Rena graphic
mapping or establish that editing this global flag is safe.

The field-entry construction tail reads that index. In nonzero field mode,
it skips walking-object creation only when the riding bit is set:

```text
800554F8 lw    v0,570C(v0)
80055500 lw    v1,5710(v1)
80055504 lbu   v0,68(v0)       ; mode
80055508 lbu   s0,24(v1)       ; controlled-object index
8005550C beqz  v0,80055538
...
80055518 lw    v0,5704(v0)
80055520 lbu   v0,1(v0)
80055528 srl   v0,v0,4
8005552C andi  v0,v0,1
80055530 bnez  v0,80055590     ; riding: skip walking construction
...
80055540 move  a1,s0          ; destination pointer-table slot
80055544 move  a2,s0          ; object construction selector, same value
80055548 addiu a3,sp,58       ; position vector
80055568 jal   80043890
8005556C sw    v1,20(sp)      ; flags 0001000F, delay slot
```

`80043890` computes `s2=80075360+4*a1` at `800438EC..F8`, removes an
existing object if present, and preserves `a2` in `s3` at `800438C0`.
For nonzero mode it allocates `0x44C` bytes; for zero mode `0x3FC` bytes.
The corresponding constructor calls and pointer stores are:

```text
80043938 move  a0,v0          ; allocated object
8004393C move  a1,s3          ; original a2 = F[24]
80043940 move  a2,s4          ; position vector
8004395C jal   80082E5C       ; nonzero-mode overlay constructor
80043960 sw    s7,1C(sp)
80043964 j     800439A4
80043968 sw    v0,0(s2)       ; returned pointer becomes table[F[24]]
...
80043974 move  a0,v0
80043978 move  a1,s3          ; same selector in zero mode
80043998 jal   8007E540       ; other overlay constructor
8004399C sw    s7,1C(sp)
800439A0 sw    v0,0(s2)
```

Dismount uses the same mechanism, not a fresh lookup of `0x41`:
`8004F17C..8004F1AC` returns the mount pointer to table slot 13;
`8004F1EC` clears the controlled slot; `8004F1F0` reads `F[24]` into `s0`;
`8004F1FC/200` set `a1=a2=s0`; `8004F234/238` call `80043890` with
flags `0001000F`. Its returned walking-object pointer occupies the vacated slot.
The existing Psynard transfer therefore connects to this flag-derived selector,
not directly to the validated party-slot byte.

### Executed evidence and remaining boundary

Run `python artifacts/so2-field-control/verify.py`. The
[bounded source](../artifacts/so2-field-control/verify.py),
[byte-bearing instruction listing](../artifacts/so2-field-control/evidence.asm),
and [results with source hashes](../artifacts/so2-field-control/results.json)
use only the existing resident entry 2576 (LBA 30736, load `8002F810`) and
save codec entry 2998. No new extraction or source-save write was performed.

The source is the existing workspace card
`artifacts/so2-inventory/source-live-card-20260926.mcd`. S01/S02/S15 are decoded
directly from its checksum-valid blocks; these are that archived card's versions,
not assertions about today's external live saves. Real extracted encoder and
decoder instructions round-trip each complete state. For each save, the harness
changes `S[41]` to every valid first-four slot, executes the **complete validator**,
and verifies the selected byte survives and the primary array is unchanged.
It then executes initialization `80053FD8..80054108`, field construction
`800554F4..8005556C` through the **real resident wrapper**, and, in nonzero mode,
dismount `8004F17C..8004F238` through that wrapper as well.

| Archived save | First-four IDs used as selections | Constructor selector with G[0] bit 1 clear | With bit 1 set |
|---|---|---:|---:|
| S01 | 1, 9, 4, 2 | 1 for every selection | 0 for every selection |
| S02 | 1, 7, 5, 2 | 1 for every selection | 0 for every selection |
| S15 | 1, 5, 9, 2 | 1 for every selection | 0 for every selection |

**48 trials pass** (three saves, four selections, two flag values, two modes).
Each asserts the actual constructor argument and the pointer-table store;
nonzero-mode trials also assert the mount-pointer transfer and replacement.
Modified flag/selector values and allocated pointers are isolated harness inputs,
not captured game states. Branch delay slots execute; loads use the established
immediate-load interpreter model. The allocator returns a synthetic allocation;
the two overlay constructors are explicit hooks that record arguments and return
that pointer. Their graphics code is **not executed**. No unrelated calls are
silently skipped.

This closes the proposed **resident `0x41 -> selected party ID -> construction
argument` connection negatively**. It does not prove that an overlay cannot
subsequently consult party state: whether `80082E5C` / `8007E540` resolve selector
0/1 directly to fixed graphics or perform a further party lookup is the precise
remaining question. Do not describe the observed 0/1 as a proven graphic-set ID,
or claim all scenes ignore `0x41`. No leader editor was added.

The old call-context argument also requires correction: `80051A48` really calls
the validator, but `80011B98` is the archive-size getter (for entry `851` here),
and table `80075360` contains live objects, not area entrances. Copying their
fixed-point positions does not establish an entrance-definition lookup. Nor does
the RNG caller alone establish a randomized warp. Those earlier interpretations
cannot serve as evidence for a walking-sprite role of `0x41`.

### 2026-09-27 second follow-up: can the walking sprite be forced to a third character (e.g. Dias)?

**Inconclusive — real progress, not a closed answer.** This chases the precise
remaining question from the section above: do `80082E5C` (world-map, `0x44C`-byte
object) and `8007E540` (town/dungeon, `0x3FC`-byte object) resolve the 0/1 selector
directly to two fixed graphics, or could a wider value reach a third character?

**The two constructors were located and disassembled for the first time.**
Neither lives in the always-resident code (`code-2576`, which ends at `0x8007C00C`,
short of both addresses). Both are inside a large (`0x10D70`-byte decompressed)
overlay that is **byte-identical across at least 32 different disc archive
entries** (3101, 3112, 3114, ... 3174, all disc 1, verified with a full diff, not
just the located signature bytes) — this is a generic "field/movement engine"
overlay reloaded per map, not a menu overlay. It was identified by searching the
whole archive table for the 64-byte signature already visible at live RAM
`0x80082E5C` in both existing DuckStation resume states (`SCUS-94421_resume.sav`,
`SCUS-94422_resume.sav`) — that address is untouched by every smaller menu overlay
(Options, Save) that reuses the same `0x8007E000` window, so it had survived from
the last real on-foot session in both save states. `0x8007E540` sits inside the
region menus *do* overwrite, so it was read from the freshly-extracted disc
overlay, not trusted from RAM.

**Finding 1 — construction does not hard-branch into two graphic sets.**
`8007E540` (zero-mode/town constructor) calls three always-resident helpers with
the raw selector still in `$a1`: `8003D4D8` (installs a **generic, mostly-stub**
vtable at object `+0x3F8`, always the same fixed address `80072DD4` regardless of
selector — its own entries are placeholder stubs pointing at `8006FE00`/`80043324`,
not per-character draw code), `8003D63C` (fixed-constant field defaults, no
selector use at all), and `8003D750`, which stores the raw selector unmodified at
object **`+0x16`**: `8003D854 sh $t5, 0x16($t0)` where `$t5` was moved from `$a1`
at function entry. No comparison against `0`/`1`/any other constant happens on
the selector anywhere in this call chain. This is real, executed-instruction
evidence against "hardcoded to exactly two outcomes with no live path forward" —
that specific claim is disproven. It is **not** evidence that a third character
is reachable; it only shows the value survives past construction as a generic
field, the same way this base object class stores type/state for the many other
kinds of entities it is reused for (see next finding).

**Finding 2 — the actual graphics/animation consumer of that field was not
found.** Offset `+0x16` is reused by unrelated structures throughout this
overlay (e.g. `80083958..80083C24` reads a `+0x16` field, but on a completely
different point/polygon record used by the field's terrain-containment check,
not our object — confirmed by its neighboring fields at `+0x14/0x18/0x1A/0x1C`
matching a bounding-box shape, not a character object). A byte/halfword-offset
grep across a decompiled binary this size produces mostly false positives;
distinguishing real consumers requires tracing register provenance, which was
only done for the construction path above, not for whatever runs afterward
(update/draw). The resident code independently reads `F+0x24` (the same
controlled-object index established in the section above) in roughly a dozen
more places beyond the three already documented (e.g. `8004B4B8`, `8004C380`,
`8004C880`, `8004D11C`, `8004EB90`, `8004F05C`, `8004F188`, `8004F524` in
`code-2576`) — plausible homes for camera targeting, input routing, or formation
display, and one of them may be where a graphic/model resource is actually
chosen, but none was confirmed to do that in this pass.

**Practical answer:** we do not currently know whether the walking sprite can be
forced to a character outside the two route protagonists. It is **not proven
possible** (no working edit exists) and **not proven impossible** (construction
itself is generic, not a 2-way hard branch) — closing this needs tracing
whichever of those dozen-plus `F+0x24` reads actually selects the rendered
model/animation set, which is a real follow-up investigation, not a quick check.
No save-editing tool was built for this; per this project's standing practice,
an unresolved finding does not get a half-working helper.

**Side finding worth flagging separately:** the newly-extracted field-overlay
binary (`artifacts/so2-field-control/field-overlay-entry3101.bin`) contains real
point-in-cell/point-in-polygon geometry code and height interpolation
(`80083628..80083820`, `80083944..80083C24`) — this looks like exactly the
terrain/collision system that the map-terrain investigation has been blocked on
("same unextracted overlay" — see README's Map terrain/collision row). That
overlay is no longer unextracted; a future pass aimed at terrain/collision should
start here instead of re-deriving it.

Executed evidence: `artifacts/so2-field-control/field-overlay-full.asm` (full
disassembly of the located overlay) and `field-overlay-entry3101.bin` (the
decompressed overlay itself). No new interpreter/harness run was added this
pass — this was static tracing plus the existing `Machine` harness's established
resident-code binary; no card was read, edited, or written.

### 2026-09-27 third follow-up: graphics-selection consumer found; 12-character selector space solved; save-edit forced leader ruled out

**Resolved.** Following up on the second follow-up above, the entire downstream path
from entity construction to sprite rendering was traced, all resident read sites of
`F[0x24]` (decoded `0x176C`) were audited and categorized, the real graphics-selection
routine was located and executed in MIPS emulation against actual PS1 RAM dumps, the
underlying sprite archive system was decoded across Disc 1, and the question of whether
the walking sprite can be forced to a third character (e.g. Dias) via save editing
is answered definitively:

1. **All resident `F[0x24]` read sites ruled out as graphics consumers [Disassembly-only / Verified (executed)].**
   The eight resident read sites specifically enumerated (`8004B4B8`, `8004C380`, `8004C880`,
   `8004D11C`, `8004EB90`, `8004F05C`, `8004F188`, `8004F524`) plus roughly 50 additional
   accesses across `resident.asm` were traced. None of them chooses a graphic or model ID:
   - **`8004B47C / 8004B4B8`**: Entity movement manager state reset (`80042cc4(player, -1)`,
     clearing flag bit `0x80` in `obj->0x4c` via `80042d3c`, and resetting inactive slots 0..11).
   - **`8004C380`**: Field loop interaction trigger proximity check (`80041310` compares player
     coords against zone trigger `[80075560]` and triggers sound effect `0xC` on entry).
   - **`8004C880 / 8004C888`**: Random encounter step counter and countdown timer (`800319c4`,
     decrementing/resetting step countdown word `0x6314`).
   - **`8004D11C`**: Camera targeting and sightline projection (`80070a94` heading calculation,
     feeding sine/cosine projection `8006e498 / 8006e404` based on player coordinates).
   - **`8004EB90 / 8004EBD4`**: Mount transition handler (removes walking entity via `8004541c`,
     swaps parked mount pointer `80075394` into player slot `table[F[0x24]]`).
   - **`8004F05C`**: Psynard flight controller (initializes takeoff physics, zeroes velocities
     `0x428..0x430`, sets flying flag `0x6176 = 1`).
   - **`8004F188`**: Dismount sequence (moves mount pointer back to slot 13, invokes `80043890`
     to reconstruct on-foot entity in `table[F[0x24]]`).
   - **`8004F524`**: Pad input routing for mounting actions (`80018f04` button check).
   - **Why none of these selects graphics:** `F[0x24]` is strictly the **slot index in active entity
     table `80075360`** (`table[0]` or `table[1]`). It is never read as a graphics resource ID.

2. **The real graphics/animation consumer: `8003F518` calling `80042E4C` [Verified (executed)].**
   The raw selector passed during construction is stored at object offset `+0x16` via
   `8003D854 sh $t5, 0x16($t0)` (in base constructor `8003D750`, called by town constructor
   `8007E540` and overworld constructor `80082E5C`). During the active field render loop,
   both overlays call resident dispatcher `8003F518` every frame:
   - Town/dungeon overlay: `8007E7BC jal 0x8003f518`
   - Overworld overlay: `80083618 jal 0x8003f518`
   Inside `8003F518`:
   ```text
   8003F5F0 jal   80043018       ; lookup object's slot index in table 80075360
   8003F5F4 move  a0,s0          ; delay slot: entity object
   8003F5F8 addiu v1,zero,0x15   ; slot 21 = NPC special handler
   8003F5FC bne   v0,v1,8003F6D4 ; player object (slot 0 or 1) branches directly here!
   ...
   8003F6D4 lh    a0,0x3ea(s0)   ; animation/action state ID (idle=13, walk, run, etc.)
   8003F6D8 lh    a1,0x16(s0)    ; the raw selector stored at construction!
   8003F6DC jal   80042E4C       ; real graphics/animation resolution routine
   8003F6E4 sw    v0,0x2d0(s0)   ; stores returned animation subblock pointer
   ```
   Routine `80042E4C` searches the loaded animation resource table at `8007585C` (16 slots,
   each 12 bytes: buffer pointer, archive ID, flags):
   ```text
   80042E80 addiu t0,v0,4        ; subblock offset table in archive header
   80042E9C addu  v1,v1,v0       ; v1 = subblock pointer
   80042EA0 lw    v0,0(v1)       ; record count in subblock
   80042EB4 move  a2,v1          ; record pointer
   80042EB8 lw    v0,4(a2)       ; record->selector
   80042EC0 bne   v0,a1,80042EF8 ; MATCHES obj->0x16 AGAINST record->selector!
   80042EC8 lw    v0,8(a2)       ; anim_min
   80042ED0 sltu  v0,a0,v0       ; state >= anim_min check
   80042ED4 bnez  v0,80042EF8
   80042EDC lw    v0,0xc(a2)     ; anim_max
   80042EE4 sltu  v0,v0,a0       ; state <= anim_max check
   80042EE8 bnez  v0,80042EFC
   80042EF4 move  v0,v1          ; returns matching subblock pointer
   ```
   `8003F518` then unpacks the sprite/frame tables from that subblock into `obj+0x2F4`,
   `+0x2F8`, `+0x2FC`, `+0x304`, `+0x308`, `+0x30C`, and `+0x310`. The overlay drawing
   code (`8007E7F8..` / `80083654..`) renders the on-screen walking sprite directly
   from those unpacked pointers.

3. **The selector space supports all 12 playable characters (`0..11`) [Verified (executed)].**
   The selector checked by `80042EC0` is **NOT** a 2-valued boolean. A comprehensive scan
   of all 51 SLZ1-compressed character animation archives on Disc 1 (entries 3111 to 3206)
   shows records keyed by exactly 12 selector values:
   `selector = Character_ID - 1` (0 through 11):
   - `0`: Claude (ID 1)
   - `1`: Rena (ID 2)
   - `2`: Celine (ID 3)
   - `3`: Bowman (ID 4)
   - `4`: **Dias (ID 5)** — full field walking and animation sprite tables exist on disc!
   - `5`: Precis (ID 6)
   - `6`: Ashton (ID 7)
   - `7`: Leon (ID 8)
   - `8`: Opera (ID 9)
   - `9`: Ernest (ID 10)
   - `10`: Noel (ID 11)
   - `11`: Chisato (ID 12)
   *(Plus sentinel `32767 = 0x7FFF` used for unlit/special entities).*

4. **Party animation archive streaming: `80061888` and `80061BD0` [Verified (executed)].**
   How do these character sprites reach memory? During scene transitions, `80061888`
   invokes `80061BD0`. `80061BD0` scans the eight primary party slots (`primary[0..7].id`
   at `80061BFC`), building a 12-bit recruited party mask: `mask |= 1 << (ID - 1)`.
   `8006195C..80061B14` then splits this mask to select disc archive entries:
   - **Group 1 (bits 2..6: Celine, Bowman, Dias, Precis, Ashton):**
     `Entry = 3111 + 2 * ((mask >> 2) & 0x1F)` (entries 3111..3173).
     If Dias is in the party, bit 4 is set (`(mask >> 2) & 0x1F` has bit 2 set), so the game
     automatically loads an archive containing Dias's sprite set (e.g. entry 3119, 3125, etc.).
   - **Group 2 (bits 7..11: Leon, Opera, Ernest, Noel, Chisato):**
     `Entry = 3175 + ((mask >> 7) & 0x1F)` (entries 3175..3206).
   The selected archives are loaded into `8007585C` (Slot 0 and Slot 1).
   Executing `80042E4C` in `Machine` with Disc 2 RAM (where Entry 3125 is loaded in Slot 0):
   - Selector 0 (Claude) -> `0x800e5ac8`
   - Selector 1 (Rena) -> `0x800ef014`
   - Selector 2 (Celine) -> `0x800f87d4`
   - Selector 3 (Bowman) -> `0x800fbb60`
   - **Selector 4 (Dias) -> `0x800fed6c`** (successfully resolves to Dias's animation subblock!)
   - Selector 5 (Precis, absent from 3125) -> `0x00000000` (NULL).

5. **Can the walking sprite be forced to Dias via save editing? [Disassembly-only / Verified].**
   **No — it is structurally impossible via save editing alone.**
   To make Dias the walking leader, four hard structural barriers prevent any save-only solution:
   - **Single-bit route flag:** The save format only stores the story route at decoded `0x19E8`
     (`G[0]` bit 1), which is a 1-bit boolean (0=Rena, 1=Claude).
   - **Unconditional overwrite on map load:** Resident scene setup `800540B4..80054108` executes
     on every map load, teleport, and save reload, unconditionally recomputing `F[0x24]` (decoded `0x176C`):
     `F[0x24] = 1 - ((decoded[0x19E8] >> 1) & 1)`
     Any direct edit to `0x176C` in the save file is immediately overwritten with `0` or `1`.
   - **Object table slot coupling:** When `80043890` constructs the entity, it takes `a1 = a2 = F[0x24]`.
     `a1` is the active object table slot: `table[a1] = obj` at `80075360 + 4*a1`. Slots 0 and 1
     are reserved for the player avatar; slots 2+ are used for map NPCs. If `F[0x24]` were 4,
     the player entity would be placed in slot 4, causing severe collision with scene NPCs.
   - **Complete lack of party-leader lookup:** The on-foot construction path (`80055540..80055568`)
     never consults party slot `0x41` or any `primary[slot].id`.
   - **What would be required:** Forcing Dias as the walking leader requires a code modification /
     patch (e.g. hooking `80055544 move a2, s0` to pass `a2 = 4` while keeping `a1 = s0`, or
     mapping `primary[S[41]].id - 1` into `a2`). When so patched, the game engine's existing
     sprite resolution (`80042E4C`) and archive streaming (`80061888`) will successfully
     display and animate Dias on foot without graphical glitches. In the unmodded game,
     no save edit can accomplish this.

Executed evidence: `tools/so2_field_leader_evidence.py` (executes `80042E4C` on Disc 1 & Disc 2 RAM,
resolves Dias pointer `0x800fed6c`, verifies party streaming formula across five scenarios),
`tests/test_so2_field_leader.py` (unit tests pass), `artifacts/so2-field-control/graphics-consumer.asm`
(disassembly listing of all audited sites), and `artifacts/so2-field-control/graphics-consumer-report.json`.

## Why the two experiments were insufficient

Unused-slot clone: secondary data does not make `primary[slot].id` positive.
The party-menu gate still returns zero. The new slot also lacks a primary
record containing HP, MP, level, class-like byte and other stats.

Celine rename: `primary[4].id` at decoded **`0x320`** remains **3**. Her
class-like byte at **`0x323`** remains **11**, not Opera's 3. The name at
decoded **`0x804`** can say Opera while identity-dependent graphics and
equipment rules still use Celine. Her primary stats also remain Celine's;
the secondary record was never the whole character.

The isolated instruction tests reproduce both identity outcomes. They do
not retroactively diagnose a freeze or prove which file the emulator loaded.
Changing ID alone is a useful diagnostic, but is not a fully initialized Opera:
her other primary and secondary defaults differ too.

## Tool and independently verifiable candidate

[`so2_party.py`](../so2_party.py) creates a **new raw-card copy**. It requires
both full target records to be all-zero, refuses an already present/retained
requested ID, and defaults to the first empty pair. It executes the extracted
game's initializer using [`tools/so2_party_mips.py`](../tools/so2_party_mips.py),
which checks the resident code hash. It then writes both records into decoded
space, re-encodes, updates compressed count and C, signs, and verifies that
all other decoded bytes are unchanged. It deliberately does not implement
the recruit routine's destructive fallback over negative retained records.

Candidate: [`artifacts/so2-party/opera-slot2-candidate.mcd`](../artifacts/so2-party/opera-slot2-candidate.mcd).
**Not loaded in-game.** This uses the known original early-game S13, not an
unidentified version of tonight's two failed files. It adds Opera in slot 2
alongside the existing Rena/Claude, with normal initializer defaults and
seed-0 talent mask `0x02C`. Fol remains 40. Slot 2 is within the first four,
so this candidate can test both menu presence and battle participation.

Source, read-only:

```text
C:/CodeTesting/StarOcean2/SaveGames/cards/_backup/card1-before-fol-fix4-20260925-011239.mcd
BASCUS-94421S02-S13 / physical block 4
source card SHA256
0171ea3603d777aa6e2251a65e1654dfa26037486ed745473f231e9eba3e221a
candidate card SHA256
2d38a7ed66bf951c927aa08d8be74ef44f17eb19ba0999ba27d45d947ae3f287
candidate block SHA256
61683751468dbb4db5a929a80820de1c19bbd6d5b74d6c8eee26ff957f97b0ca
```

| Property | Source S13 | Candidate S13 |
|---|---:|---:|
| Compressed count | `03B9` | `0435` |
| C | `073B` | `07B7` |
| Checksum A | `242F` | `2434` |
| Checksum B | `17D92` | `18810` |

Exactly **47 decoded bytes change**, all inside primary `[260,2C0)` and
secondary `[640,710)`. Every byte outside physical block 4, including the
directory and other saves, is identical. Cached save-preview metadata is
preserved, so the card/load-screen preview need not show the added member;
inspect the actual party menu after loading. Detailed changes and verification
results are in [`candidate-report.json`](../artifacts/so2-party/candidate-report.json).

Verification executes the **actual extracted recruitment instructions** on
the source arrays with the same seeded RNG. The resulting `0x300` and `0x680`
arrays equal the candidate's arrays byte-for-byte. Outside records and stack,
the directly executed recruit path writes only `0x800759A0`. Its two external
runtime refresh calls (`8007972C`, `8004358C`) are explicitly stubbed in this
test, not claimed to have executed. The initializer itself writes only the
two records and stack; its RNG is a host substitute and libc calls are hooks.

The actual extracted save-overlay encoder **and** decoder reproduce the
candidate stream/state exactly. This is stronger than a Python-only
round-trip, but remains bounded instruction execution, not a PS1 load test.
The harness executes branch delay slots and assumes safely scheduled immediate
loads; unsupported instructions/calls fail closed.

`python -m unittest discover -s tests -v`: **18 tests pass**, including eight
new tests for all 12 initializers, the two failed-edit identity conditions,
actual equipment-mask behavior, first-free recruitment, negative-ID rejoin,
paired displacement, a full positive roster, and codec/preservation checks.
The existing save reader emits an unrelated unclosed-file ResourceWarning;
the tests complete successfully.

## Reproduction

```powershell
# Optional: re-extract established code entries into this repo.
python tools/so2_disc_code.py "C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin" artifacts/so2-party/disc-code --entries 2576 2982 2985 2998

# Uses existing Fol-series extracts and RAM; requires capstone.
python tools/so2_party_evidence.py
python -m unittest discover -s tests -v

# Choose a NEW candidate filename; exclusive creation refuses existing files.
python scripts/so2_party.py "C:/CodeTesting/StarOcean2/SaveGames/cards/_backup/card1-before-fol-fix4-20260925-011239.mcd" --save S13 --id 9 --seed 0 --out artifacts/so2-party/opera-slot2-another-copy.mcd
```

No file under `C:/CodeTesting/StarOcean2/SaveGames` was modified. All scripts,
reports, disassemblies, and the new candidate were written inside this repo.

---

## DuckStation Live-Test Automation & Save-State Memory Diff (2026-09-28)

To resolve the remaining 144 unmapped bytes in the Party Primary Array (particularly `+0x04..0x0F`, `+0x4E..0x59`,
and `+0x5A..0x5F`), an investigation into DuckStation emulator automation capabilities was conducted.

### 1. DuckStation Automation Analysis
1. **Scripting Console / Lua Support**: **Absent**. Unlike BizHawk, PCSX-Redux, or Snes9x, DuckStation does not
   embed a Lua runtime, Python environment, or user-facing scripting terminal.
2. **TAS Movie / Input Playback**: **Absent**. DuckStation has no `.tas` or `.dtm` movie recording/playback subsystem.
3. **External Gamepad Injection**: **Absent**. DuckStation does not expose an external IPC pipe or REST/WebSocket
   endpoint for unattended controller button simulation over time.
4. **Memory Debugger / GDB Server**: **Present**. DuckStation incorporates a MIPS R3000 GDB stub
   (`[Debug] EnableGDBServer = true`, port 2345), permitting remote memory read/write over standard GDB sockets,
   though input manipulation remains unavailable.

**Verdict**: Fully unattended automated combat playback without human gameplay is **impossible natively in DuckStation**.
Live battle actions (attacking, taking damage, casting spells, leveling up) require a human player to interact with the emulator.

### 2. Live Save-State Memory Diff Solution
While input playback cannot be unattended, **save-state inspection and byte diffing can be 100% automated**.

DuckStation save states (`.sav` under `C:/CodeTesting/StarOcean2/SaveGames/`) are compressed Zstandard containers
using DuckStation's `DUCC` chunk format. Decompressing Zstandard Frame 1 extracts the entire emulator runtime:
- **PS1 Main RAM Location**: In `Section Bus`, exactly 71 bytes after the section header (or at `sony_marker - 0xB0BC`),
  the authentic uncompressed 2 MB PS1 Main RAM (`0x00000000..0x00200000`) is located.
- **Dedicated Inspection Tool**: [tools/so2_live_memory_diff.py](file:///C:/CodeTesting/SaveConverter/tools/so2_live_memory_diff.py)
  was built to decompress `.sav` states, locate the live pointers `[0x8007527C]` and `[0x80075280]`, unpack all 8
  party members, and execute byte-by-byte diffs across the 96-byte primary record.

### 3. Empirical Findings from Live Combat States

Diffing real DuckStation states ([SCUS-94422_10.sav](file:///C:/CodeTesting/StarOcean2/SaveGames/SCUS-94422_10.sav) vs
[SCUS-94422_resume.sav](file:///C:/CodeTesting/StarOcean2/SaveGames/SCUS-94422_resume.sav)) during battle operations revealed:

1. **`+0x5A` — changes, but not the clean "+10 per battle" pattern first reported** (corrected on
   manager re-verification, 2026-09-28): re-running the diff tool against the same two save states
   shows **4** characters with a changed `+0x5A` byte, not just the 2 originally cited:
     - Dias: `0x2D` (45) $\rightarrow$ `0x37` (55) — `+10`
     - Rena: `0x1E` (30) $\rightarrow$ `0x28` (40) — `+10`
     - Noel: `0x00` (0) $\rightarrow$ `0x0C` (12) — `+12`
     - Chisato: `0x5F` (95) $\rightarrow$ `0x50` (80) — **`-15`** (a decrease)
   - The original write-up only cited the two `+10` cases and concluded "exactly 10 per battle,
     bench characters don't increment" — Noel and Chisato directly contradict that: both gained EXP
     and leveled up between these two states (see their stat-block diffs above), so they were
     clearly "active" too, yet neither shows `+10`. These two save states are also not a clean
     single-battle before/after pair — everyone in this diff shows large EXP/stat jumps, meaning
     an unknown number of battles and level-ups happened between them, not one. **`+0x5A` changes
     with battle/level activity but the exact rule isn't established** — needs a controlled test
     with save states seconds apart around one isolated action, not two saves from different points
     in a play session.
2. **`+0x4C` — Dynamic In-Combat GUTS Stun Meter**:
   - `+0x48` stores base GUTS, while `+0x4C` dynamically fluctuates during combat, depleting as hits are received
     (Dias: 255 $\rightarrow$ 188; Rena: 100 $\rightarrow$ 60). When `+0x4C` drops below the stun threshold (`0x8004AFD4`),
     the entity enters Stun state.
3. **`+0x4E..0x53` & `+0x54..0x59` — Attribute Triplets A & B**:
   - When party members are reordered between party slots (e.g. Noel in Slot 6 moved to Slot 7, Chisato moved to Slot 6),
     the triplets move strictly with their character ID:
     - Noel (ID 11): Unknown A = `(15, 18, 18)`, Unknown B = `(7, 7, 7)`
     - Chisato (ID 12): Unknown A = `(16, 18, 18)`, Unknown B = `(9, 7, 7)`
   - Confirmed as character-intrinsic growth stat triplets initialized by recruitment and scaled during stat recalculation.
4. **`+0x04..0x0F` — Zero-Padded Header Region**:
   - Confirmed all-zero in normal saves with only offset `+0x07` occasionally set to `0x02` during formation re-ordering.
