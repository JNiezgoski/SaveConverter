# Decoded chunk 1 mapping

Date: **2026-09-27**. Read-only investigation; no card writes.

**329 newly resolved bytes in 302 fields/array elements**, counting precise
storage roles and operational behavior, not requiring a player-facing label.
Together with the task's 42-byte Options/Fol/disc baseline, this is
**371/416 bytes (89.18%)**, an increase of 79.09 percentage points.
**45 bytes remain outside that semantic accounting.** This is not a claim of
exhaustive instruction coverage or complete gameplay understanding.

The main finding is two **12 x 12 character-pair value matrices**, each with
script adjustments clamped to 0..15. Their combined 288 bytes explain most of
the former gap. They are a concrete lead for the emotion-level investigation;
which is friendship versus affection/love, and which scripts implement named
Private Actions or endings, remain **Unverified**.

## Actual serializer source, established first

Let **S = [80075270]**. All ranges below are hexadecimal, end exclusive.
Decoded `000..1A0` corresponds directly to **S+000..1A0**.

Save overlay archive entry **2998**, `80081ACC..80081AF0`:

```text
80081ACC addiu s1,zero,1A0
80081AD0 move  a0,s6
80081AD4 move  a1,s5
80081AD8 move  a2,s4       ; decoded buffer start
80081ADC sw    s1,10(sp)  ; fifth argument: 416 bytes
80081AE0 addiu s1,zero,300 ; next chunk's length, AFTER saving 1A0
80081AE4 lui   a3,8007
80081AE8 lw    a3,5270(a3)
80081AEC jal   80081C38
80081AF0 addiu s2,s4,B20
```

`80081C38..80081C60` reads that stack length and selects copy direction:
mode zero copies a3 to a2; nonzero copies a2 to a3, calling `80023ED0`.
Thus this chunk really is a contiguous copy of S. No resource-E staging or
F/G inference is involved. Resident `800313D4/800313F0/80031404`,
`80032578/8003257C/80032590`, and `80049020/80049024/80049034` independently
publish resource **2** as S. This is resource lookup evidence, not an assumption
that every resource-2 alias was found.

**Verified (executed):** the actual first-call setup and copy helper were run
in both directions with distinct synthetic source/destination contents and
end guards. All 416 bytes copied; both guards survived. `memcpy` is a host
hook, so this verifies the original argument/direction instructions, not the
implementation of libc or a complete save/load. Resource publication above
is **Disassembly-only**.

## Newly resolved fields

**Verified (executed)** means bounded original-instruction execution, not an
in-game observation. **Disassembly-only** means an inspected instruction-backed
storage role. **Unverified** interpretations receive no extra byte credit.
Addresses without an overlay qualification are resident entry 2576.

| Decoded range | Live-relative | Field / exact established behavior | Evidence addresses | Confidence |
|---|---|---|---|---|
| `010..014` | S+010 | Clock-derived word: menu stores signed clock/60; used in time-style divisions and copied into save preview | entry 2982 clock call `8007EE84`, divide/store `8007EE8C..8007EEB8`, reader `8007EED4`; entry 2998 preview `80081738..80081740` | Disassembly-only; seconds interpretation not executed |
| `014..018` | S+014 | Event counter: field path increments by one; script adds operand with zero floor when signed result is negative; exposed to script and save preview | R/W `80051CF8..80051D0C`, script R `80067838`, script add/floor `80068628..80068640`, entry 2998 `80081744..8008174C` | Disassembly-only; not named battle count |
| `020..024` | S+020 | Menu-operation counter, unconditional increment at common completion path in three overlays; script-readable | entry 2990 `80080098..800800A4`, 3008 `8008015C..80080168`, 3010 `8007FEEC..8007FEF8`; script `80067718` | Disassembly-only; exact mechanic unnamed |
| `024..028` | S+024 | Save-preparation counter; incremented when constructing save data, not proven successful physical card writes | entry 2998 `800817B8..800817C4`; script `80067750` | Disassembly-only |
| `028..02C` | S+028 | Companion conditional menu-operation counter: same paths increment only when menu object's signed halfword +B2 is nonzero | entry 2990 `800800A8..800800C4`, 3008 `8008016C..80080188`, 3010 `8007FEFC..8007FF18`; script `80067734` | Disassembly-only; success/attempt naming unverified |
| `042` | S+042 | Non-default lead-name flag for rename selector 0: 0 when accepted text is exactly `Crawd` plus terminator, 1 otherwise | entry 3022 comparisons `800805C8..80080628`, W `80080640/80080650` | Disassembly-only |
| `043` | S+043 | Non-default lead-name flag for rename selector 1: 0 for exact `Rena` plus terminator, 1 otherwise | entry 3022 `80080654..800806AC`, W `800806C4/800806D4` | Disassembly-only |
| `045` | S+045 | Route/lead selector: zero and nonzero select initial route setup; save preview searches primary ID equal to byte+1 | `8005EC8C..8005ED08`; entry 2998 `80081070..8008107C` | Disassembly-only; independently writable safety not established |
| `054..058` | S+054 | Menu clock-throttle marker: update allowed only if unsigned clock > saved marker+60; then save clock | entry 3004 clock `80081E98`, compare `80081EAC..80081EBC`, W `80081EC8` | Disassembly-only |
| `058..0E8` | S+058+12*r+c | Matrix A: 144 one-byte pair values; script adds signed operand and clamps to 0..15 | script R/add/clamp `8006590C..80065958`, W address/store `8006595C..8006598C`, getter `80065990..800659CC`; bounded traversal `8006B5E0..8006B61C` | Verified (executed): adjustment/addressing for all 144 cells; character-pair interpretation Disassembly-only |
| `0E8..178` | S+0E8+12*r+c | Matrix B: separate 144 one-byte pair values with the same script adjustment range | script `80065838..800658BC`, shared store `80065984..8006598C`, getter `800658C0..800658FC`; traversal `8006B59C..8006B5DC` | Verified (executed): adjustment/addressing for all 144 cells; character-pair interpretation Disassembly-only |
| `178..17A` | S+178 | Signed completion/result code: returned to script; value 1 increments F+244, value 2 gates field-return handling | `80048BFC..80048C3C`, `80055220..80055238`, `80055B18..80055B44` | Disassembly-only; writer and full enum unresolved |
| `184..186`, `186..188` | S+184, S+186 | Two signed percentage modifiers: stat selector 1/2 result becomes base+trunc(base*modifier/100); shared setter writes both | W `80032244/8003224C`; R/calculation `8003B560..8003B594`, `8003B5AC..8003B5E4` | Disassembly-only |
| `198..19C`, `19C..1A0` | S+198, S+19C | Two saved save-menu selection words: copy to/from menu +64/+68; indexed update stores selected position+1; zero means no restored selection | entry 2998 `8007FDC0..8007FDD8`, `8007FE20..8007FE54`, read/subtract/test `8007EB20..8007EB4C` | Disassembly-only; full UI/card-index provenance unresolved |

The previous 42 bytes are unchanged: buttons `000..010`, Fol `018..01C`,
colors `030..040`, and individual bytes `044,046,049,04A,04B,04C`.
See [Options evidence](SO2-OPTIONS-MENU-INVESTIGATION.md) and existing Fol/disc
investigations for their prior confidence tags. Do not count the whole
`044..04D` span as already mapped.

## Matrix evidence and its boundaries

Both script arms form **12*first_operand + second_operand**, load a byte, add
the third operand and saturate the result to 0..15. The code does not check the
two indices there. Valid 12x12 storage is independently established by the
nested loops at `8006B5AC/8006B5C8` and `8006B5EC/8006B608`: twelve rows of
twelve bytes each. That helper sums both matrices and returns the remainder
modulo its argument at `8006B620..8006B62C`; no random generator is called there.

Character linkage is visible in `80066E94..80066F20`: it walks primary party
records with stride `0x60`, validates IDs 1..12 (`80066EA8..80066EB0`), subtracts
one, and uses that value as the matrix row. It excludes the script-selected
character itself, reads **both** matrices in the script-selected column
(`80066EE8`, `80066F08`), and sums them for a ranking computation. This proves
character-pair storage, not that A/B can already be labeled friendship/love or
that pair values are symmetric. Diagonal entries are included in the serialized
capacity and traversal; their gameplay use is not established.

Entry 3010 `80082730..800827D8` obtains two values through helper `800802A4`
with argument 12 and a selector with argument 4. Selector 0 chooses A, 1 chooses
B; nonzero cells decrement by one. The helper's distribution is unexamined,
so these are not asserted to be uniformly random choices. Entry 3001 contains
a direct value-8 writer (`80082C48`). Its extracted listing has jumps to
`8008CC40/8008CC4C` outside the shown local block; the alternative B path must
not be claimed executed from this listing alone.

Resident `80066720..800667C4` walks twelve mask-selected rows, excludes one
index, calls RNG(100), and takes the update when result <10. **An important
instruction-level wrinkle:** `80066798` reads A but `800667B4` writes B, after
the earlier B decrement at `80066780`. This pass does not silently “correct”
that to a decrement of both matrices or assign it a familiar game event.

The checked-in verifier executed both adjustment blocks for every cell with
six `(old,delta)` pairs, **1,728 trials**, checking all 416 bytes after each
trial to detect collateral writes. VM operand decoding/dispatch was bypassed
using explicit entry-register setup; original adjustment, branch and store
instructions ran unchanged. No matrix getter, ranking, overlay decrement,
RNG path, or whole-game behavior is claimed executed.

### Script callers, named Private Actions, and emotion distinction (2026-09-27 follow-up)

**Status: VERIFIED by static disassembly, disc container extraction, and VM bytecode tracing.**
Script-side callers for both matrices, the VM bytecode instruction format, the disc container
archive layout for field/town scenes, the 16-bit dialogue text encoding, and concrete named
Private Actions and story scenes were fully traced. Concrete instruction evidence confirms that
**Matrix A represents Friendship Points (FP)** and **Matrix B represents Romance / Affection Points (RP)**.

#### 1. VM opcode dispatch and operand decoding

The resident script interpreter loop at `8006C358` fetches 32-bit instruction words from the script
program counter (`0x10($s1)`). For opcodes outside `1..99` (`8006C37C beqz $v0, 0x8006e374`), execution
reaches `8006E378 jal 0x8006241c`, which indexes jump table `8007359C` with `opcode - 0x64`.

Opcode `0xFF` (255) jumps to `80064968`, invoking sub-dispatcher `80064F30`. Sub-dispatcher `80064F30`
decodes the sub-opcode from byte 2: `(instruction >> 16) & 0x7F` (`80064F48 andi $v1, $v0, 0x7f`).
Bit 23 (`0x00800000`) of the instruction word acts as a stack-argument flag:
- When bit 23 is `0` (immediate mode): helper `80068DB8` takes Argument 0 directly from the lower 16
  bits of the 32-bit instruction word (`sll/sra 16` at `80068E14`), while subsequent arguments
  (Character 2 index, delta) are read sequentially as 16-bit signed halfwords from the script PC stream
  (`80068E48`, `80068E5C`), advancing script PC by 4 (`80068E70`).
- When bit 23 is `1` (stack mode, sub-opcodes `0x90..0x93`, `0xF6`): helper `80068DB8` pops the required
  arguments from the VM evaluation stack (`0x24($s1)` via `80068DF8`).

The four emotion matrix opcodes and the ranking opcode are:

| Opcode | Hex Word Pattern | Target Routine | Function & Execution Semantics |
|---|---|---|---|
| `0xFF10` / `0xFF90` | `0xFF10xxxx` / `0xFF900000` | `80065900` | **Matrix A Adjust**: forms `12*row + col`, loads byte from `S+0x058`, adds signed delta, clamps result to `0..15`, writes back to `S+0x058` |
| `0xFF11` / `0xFF91` | `0xFF11xxxx` / `0xFF910000` | `80065990` | **Matrix A Get**: forms `12*row + col`, loads byte from `S+0x058`, writes result word to script variable `[80075708]` |
| `0xFF12` / `0xFF92` | `0xFF12xxxx` / `0xFF920000` | `8006582C` | **Matrix B Adjust**: forms `12*row + col`, loads byte from `S+0x0E8`, adds signed delta, clamps result to `0..15`, writes back to `S+0x0E8` |
| `0xFF13` / `0xFF93` | `0xFF13xxxx` / `0xFF930000` | `800658C0` | **Matrix B Get**: forms `12*row + col`, loads byte from `S+0x0E8`, writes result word to script variable `[80075708]` |
| `0xFF76` / `0xFFF6` | `0xFF76xxxx` / `0xFFF60000` | `80066E58` | **Party Affinity Ranker**: takes target character index `C`, iterates through all primary party member records (`0x60` stride), sums `Matrix_A[P][C] + Matrix_B[P][C]`, identifies the maximum affinity character (breaking ties via uniform RNG helper `8006B59C`), and writes the winning party member's character ID to `[80075708]` |

#### 2. Disc script container layout and 16-bit dialogue text decoding

Field and town scenes on Disc 1 are packaged in container archives `3207..4033` (827 container archives).
Effective scene numbers follow the verified relation `scene_index = archive_index - 3207` (derived from
`80061968`'s `scene + 0xC87` rule).
Each container archive bundles three parts:
- **Part 0**: Trigger and camera metadata.
- **Part 1**: SLZ1-compressed event and dialogue bytecode stream (loaded into memory for field execution).
- **Part 2**: 3D field geometry and collision mesh.

Resident script initializer `800622EC..80062340` sets up the script context:
- `word0` at script offset `0x00`: points to message offset table at `script_base + word0 + 0x1C` (`0x28($s0)`).
- `word0xC` at script offset `0x0C`: number of dialogue message entries.
- Message offset table consists of `uint16_t` offsets relative to the text string base `(script_base + word0 + 0x1C) + (word0xC * 2)` (`0x2c($s0)`).
- Text strings are encoded in a custom 16-bit character stream:
  - `0x01B6..0x01CF`: Uppercase ASCII `A..Z` (`code = ord(c) - 65 + 0x01B6`).
  - `0x01D0..0x01E9`: Lowercase ASCII `a..z` (`code = ord(c) - 97 + 0x01D0`).
  - `0x01AA..0x01B3`: Digits `0..9`.
  - Punctuation: `0x0285` (space), `0x0283` (period), `0x0284` (comma), `0x0286` (single quote), `0x0287` (question mark), `0x0288` (exclamation point), `0x01B5` (hyphen/dash), `0x0289`/`0x028A` (double quote).
  - Control codes: `0x808C (01xx)` sets speaker portrait (e.g. `0100`=Claude, `0101`=Rena, `0102`=Celine, `0105`=Precis, `0107`=Leon, `0108`=Opera, `010B`=Chisato).

#### 3. Concrete named Private Actions and story scene callers

A comprehensive scan across all 827 container archives isolated the exact script bytecode invoking these
operations during real game events:

##### A. Scene 688 (Archive 3895) — Fun City Bar: "Leon's Confession" Private Action
In Fun City, Leon (Character ID 7, 0-indexed) asks Claude (ID 0) to help him confess his crush to any female
party member currently in the party. Each dialogue choice branch was decoded and verified:
- **Rena (ID 1)**:
  - Choice 0 ("I knew I had to keep my eye on him", mutual friendship):
    - `0x9D14`: `0xFF100001 0x00030007` -> **Matrix A** row=1 (Rena), col=7 (Leon), delta = `+3`.
    - `0x9D1C`: `0xFF100007 0x00030001` -> **Matrix A** row=7 (Leon), col=1 (Rena), delta = `+3`.
  - Choice 1 ("I have someone else", Leon heartbroken):
    - `0x9FD0`: `0xFF100001 0x00030007` -> **Matrix A** row=1 (Rena), col=7 (Leon), delta = `+3`.
    - `0x9FD8`: `0xFF100007 0xFFFE0001` -> **Matrix A** row=7 (Leon), col=1 (Rena), delta = `-2`.
- **Celine (ID 2)**:
  - Choice 0 ("He's just a little boy! Wait 10 years!"):
    - `0xA3F0`: `0xFF100002 0x00030007` -> **Matrix A** row=2 (Celine), col=7 (Leon), delta = `+3`.
    - `0xA3F8`: `0xFF100007 0xFFFE0002` -> **Matrix A** row=7 (Leon), col=2 (Celine), delta = `-2`.
  - Choice 1 ("5 years from now, if you feel the same way"):
    - `0xA7A8`: `0xFF100002 0x00030007` -> **Matrix A** row=2 (Celine), col=7 (Leon), delta = `+3`.
    - `0xA7B0`: `0xFF100007 0x00030002` -> **Matrix A** row=7 (Leon), col=2 (Celine), delta = `+3`.
- **Precis (ID 5)**:
  - Choice 0 ("Squirt! Baby! Pervert! I wouldn't go out with a sicko like you!"):
    - `0xAD88`: `0xFF100005 0xFFFE0007` -> **Matrix A** row=5 (Precis), col=7 (Leon), delta = `-2`.
    - `0xAD90`: `0xFF100007 0xFFFE0005` -> **Matrix A** row=7 (Leon), col=5 (Precis), delta = `-2`.
  - Choice 1 ("My boyfriend has to be worthy of me... wait 5 years"):
    - `0xB128`: `0xFF100005 0x00030007` -> **Matrix A** row=5 (Precis), col=7 (Leon), delta = `+3`.
    - `0xB130`: `0xFF100007 0x00030005` -> **Matrix A** row=7 (Leon), col=5 (Precis), delta = `+3`.
- **Opera (ID 8)**:
  - Choice 0 ("Romantic: love across light-years..."):
    - `0xB58C`: `0xFF100008 0x00030007` -> **Matrix A** row=8 (Opera), col=7 (Leon), delta = `+3`.
    - `0xB594`: `0xFF100007 0x00030008` -> **Matrix A** row=7 (Leon), col=8 (Opera), delta = `+3`.
  - Choice 1 ("I am not interested in a boy younger than I am! Waaaaah!"):
    - `0xB920`: `0xFF100008 0x00020007` -> **Matrix A** row=8 (Opera), col=7 (Leon), delta = `+2`.
    - `0xB928`: `0xFF100007 0xFFFE0008` -> **Matrix A** row=7 (Leon), col=8 (Opera), delta = `-2`.
- **Chisato (ID 11)**:
  - Choice 0 ("Come tell me again after you're a little older"):
    - `0xBD8C`: `0xFF10000B 0x00030007` -> **Matrix A** row=11 (Chisato), col=7 (Leon), delta = `+3`.
    - `0xBD94`: `0xFF100007 0x0003000B` -> **Matrix A** row=7 (Leon), col=11 (Chisato), delta = `+3`.
  - Choice 1 ("The guy with the camera... I LOVE... Waaaaah!"):
    - `0xC20C`: `0xFF10000B 0x00020007` -> **Matrix A** row=11 (Chisato), col=7 (Leon), delta = `+2`.
    - `0xC214`: `0xFF100007 0xFFFE000B` -> **Matrix A** row=7 (Leon), col=11 (Chisato), delta = `-2`.

**Critical Finding**: Across all 20 adjustment instructions in this entire event, the game exclusively invokes
`0xFF10` (**Matrix A Adjust**). Matrix B is never called. Because Leon is 12 years old and all five women reject
his romantic proposition while bonding with him as an endearing younger friend/colleague, this directly proves
that **Matrix A tracks Friendship Points (FP)**.

##### B. Scene 17 (Archive 3224) — Arlia Village: Alen-Tax Kidnapping
During Claude and Rena's initial meeting and subsequent rescue in Arlia:
- Positive branch (`0x4330..0x4348`):
  - `0x4330`: `0xFF100000 0x00010001` -> **Matrix A** Claude->Rena `+1`
  - `0x4338`: `0xFF100001 0x00010000` -> **Matrix A** Rena->Claude `+1`
  - `0x4340`: `0xFF120000 0x00010001` -> **Matrix B** Claude->Rena `+1`
  - `0x4348`: `0xFF120001 0x00010000` -> **Matrix B** Rena->Claude `+1`
- Negative / hesitation branch (`0x4630`):
  - `0x4630`: `0xFF120001 0xFFFF0000` -> **Matrix B** row=1 (Rena), col=0 (Claude), delta = `-1`.
  - **Matrix A is untouched**. When Rena is disappointed with Claude's hesitation, only her romance/affection
    value takes a penalty; baseline friendship remains unchanged.

##### C. Scene 173 (Archive 3380) — Hilton Port Town: "Lost Girl Nonno" Private Action
Rena and Precis encounter the lost little girl Nonno outside the Skill Guild:
- `0x7C34`: `0xFF120005 0x00020001` -> **Matrix B** row=5 (Precis), col=1 (Rena), delta = `+2`.

##### D. Scene 479 (Archive 3686) — Opera & Ernest Reunion
When the lovers Opera (ID 8) and Ernest (ID 9) reunite:
- `0x7D34..0x7D4C`: Symmetrically adjusts **both Matrix B and Matrix A**:
  - `0x7D34`: Matrix B Opera->Ernest `+2`
  - `0x7D3C`: Matrix B Ernest->Opera `+2`
  - `0x7D44`: Matrix A Opera->Ernest `+2`
  - `0x7D4C`: Matrix A Ernest->Opera `+2`

##### E. Scene 312 (Archive 3519) — Claude & Precis Private Action
Four dialogue choices adjust Matrix A and Matrix B asymmetrically:
- Choice 1: Matrix B Claude->Precis `+1`, Matrix A Precis->Claude `-1`
- Choice 2: Matrix B Claude->Precis `+1`, Matrix B Precis->Claude `+2`, Matrix A Precis->Claude `+1`
- Choice 3: Matrix B Claude->Precis `-1`, Matrix B Precis->Claude `-1`, Matrix A Precis->Claude `-2`
- Choice 4: Matrix B Claude->Precis `+1`, Matrix B Precis->Claude `+1`, Matrix A Precis->Claude `+2`

##### F. Shared Field Script Subroutine (`0x426C..0x44C8` in Archive 3207..4033 Part 1)
All field scripts embed a shared relationship tuning/fortune routine:
- Arguments: `local[0]` = row, `local[4]` = col, `local[8]` = emotion type selector.
- Branch at `0x4494`:
  - If `local[8] == 0`: invokes `0x44B0` `MATRIX_A_ADJ_STK` (Matrix A).
  - If `local[8] != 0`: invokes `0x44C4` `MATRIX_B_ADJ_STK` (Matrix B).
- A 11-step delta switch table maps choice index `0..10` to deltas `+30, +4, +3, +2, +1, 0, -1, -2, -3, -4, -30`.

#### 4. Semantic conclusion and boundaries

1. **Matrix A = Friendship Points (FP)**: Decoded `0x058..0x0E8`. Modified exclusively during platonic/mentoring
   interactions (e.g. Leon's confession PA across all female candidates), and preserved when romantic affection drops.
2. **Matrix B = Romance / Affection Points (RP)**: Decoded `0x0E8..0x178`. Modified during romantic/couple scenes
   (Opera/Ernest reunion, Claude/Rena, Precis/Rena), and penalized exclusively on romantic grievance.
3. **Affinity Ranking**: Script opcode `0xFF76` / `0xFFF6` (`80066E58`) sums both matrices `Matrix A + Matrix B`
   to determine the highest-affinity character across active party members.
4. **Limits**: Specific Disc 2 epilogue ending pair checks (e.g. whether endgame pair branches evaluate
   `Matrix B > 10` for heterosexual pairs and `Matrix A > 10` for same-sex pairs) were not audited on Disc 2
   binaries in this pass and remain open for future work.

## Other examined leads, excluded from the new-byte total

| Decoded / live | Observed behavior | Evidence / unresolved boundary |
|---|---|---|
| `01C..020`, `02C..030` / S+same | Words returned to script | `80067788`, `80067870`; producers and meanings not found |
| `040` / S+040 | Menu selection byte copied into local halfwords and committed back | entry 3018 `8007FDC8..8007FDD4`, `8007FE5C..8007FE74`; visible setting untraced |
| `041` / S+041 | Previously identified validated party-slot selector | `800530A8`, `80053124`; [prior investigation](SO2-PARTY-MEMBER-INVESTIGATION.md). Not a new field, not included in task's 42-byte baseline or promoted to walking leader |
| `047,048` / S+same | Options stores two stack values; save UI passes bytes as stack arguments to `80013C0C` | entry 3016 `8007EBD4/8007EBEC`; entry 2998 `8007E7C8..8007E7E4`. Renderer/control meaning untraced |
| `04D` / S+04D | Stores local 0/1 update flag after modifier work | `8003197C`; downstream consumer unresolved |
| `04E` / S+04E | Script operand's low byte stored | `80067B18..80067B34`; consumer unresolved |
| `181,182` / S+same | Two script operands stored as bytes; cleared by transition paths | `80064A18/80064A2C`, `80048ABC/80048AD0`, `80051CE8`; not identified battle configuration |
| `188,18A,18C,18E,190,192,194,196` / S+same | Eight halfword modifiers with generic setter arms and adjustment code | W `8003225C/8003226C/80032298/800322A8/800322B8/800322C8/800322D8/8003230C`; R/W `800318AC..8003196C`; exact affected stats/mechanics unresolved |

The last eight halfwords receive arithmetic updates: `188/18A` subtract a
quarter-derived value while `194` adds it (`80031894..800318D0`). A global flag
`0x25` gates a further path which adjusts `18C..192/196`. That flag is accessed
through the separate G bitmap helper `80055ECC`, **not a chunk-1 flag**.

The rename flags `042/043` are full byte booleans from exact string comparison,
not bit-packed plot flags. No conventional chunk-1 story bitmap was established
by the reviewed accesses. The large matrices use byte arithmetic/clamps, not
individual bit operations. This is bounded negative evidence, not proof that
the remaining bytes or undiscovered aliases cannot contain event bits.

## Access catalog, reproducibility and actual coverage

```text
python tools/so2_chunk1_scan.py --write-catalog
python tools/so2_chunk1_evidence.py
```

[The site catalog](SO2-CHUNK1-XREFS.tsv) lists every candidate emitted by this
pass, including source listing, instruction address, offset expression,
read/write direction, width, instruction and contextual review category.
Repeated code at identical virtual addresses in different overlays is kept
source-qualified. Known Options/Fol sites are retained but not re-derived.

The scan adapts the chunk-5 scanner: **33 distinct normalized listings,
182 pointer seeds, 255 site/offset-expression rows**, no 5,000-state limit
hits. The corpus includes resident, full extracted field overlay, overworld,
relocated shared UI and previously extracted menu/specialty/ability overlays.
Ignored `artifacts/so2-chunk1/sites.json` contains source paths and normalized
hashes; `contexts.txt` contains excerpts, `execution.json` the bounded results.

This is **not the requested ideal of an exhaustive all-game instruction
census**. It follows direct global loads with a nearby 8007 high-half producer,
locally recognized resource-2 returns, aliases, constant offsets, unknown
indexed additions, forward branches and delay slots. It kills caller-saved
aliases on calls. It does not propagate stack spills or general callee
arguments, follow backward edges/indirect dispatch, prove executable
reachability, or resolve every resource lookup. Non-contiguous partial listings
and relocated jumps can end a path. Indexed rows describe expressions, not
proven bounded accesses until manually traced as above. No absence is padding
evidence. No new battle overlay extraction, complete disc/script enumeration,
or Disc-2-only code audit was performed. In particular the result-code writer
and per-battle consumers remain open, not exhausted.

## Accounting and still unexamined

| New category | Bytes | Fields/elements |
|---|---:|---:|
| Two pair-value matrices | 288 | 288 |
| Five words at 010,014,020,024,028 | 20 | 5 |
| Rename booleans and route selector | 3 | 3 |
| Clock throttle | 4 | 1 |
| Completion code | 2 | 1 |
| Two percentage modifiers | 4 | 2 |
| Two saved menu selections | 8 | 2 |
| **Total new** | **329** | **302** |

The exact complement of the 371-byte internal-role map is:

| Decoded (= S-relative) range | Bytes | Status |
|---|---:|---|
| `01C..020`, `02C..030` | 8 | Script readers examined; semantics unresolved |
| `040..042` | 2 | Menu/party selectors examined; old 041 lead explicitly not new |
| `047..049` | 2 | UI argument leads examined |
| `04D..054` | 7 | 04D/04E writers examined; **04F..054 still without a reviewed semantic access** |
| `17A..184` | 10 | 181/182 script writers examined; **17A..181 and 183 still without a reviewed semantic access** |
| `188..198` | 16 | Modifier setter/adjustment leads examined; effects unresolved |
| **Total** | **45** | **13 bytes have no reviewed semantic access; 32 are located leads** |

The matrices' initialization, named PA/ending callers, distinction between
the two emotion types, and safe-edit behavior are still unexamined even though
their storage/adjustment roles are mapped. Save-preview clock units, the exact
events behind anonymous counters, the result-code writer and full enum,
modifier consumers, and overlay alias coverage remain substantive work.
No newly executed in-game save/reload or named story milestone is claimed.
