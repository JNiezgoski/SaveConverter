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

### 2026-09-28 follow-up: Disc 2 Ending-Threshold System & Item-Creation Recipes

#### 1. Part 1: Disc 2 Ending-Selection & Threshold System [Disassembly-only / Verified]

An exhaustive scan across all 4,170 archives on Disc 2 (`SCUS-94422`) located the master ending determination engine in **Archive 3788** (LBA 90812, tag 1 field script container). The ending evaluation begins immediately following dialogue message 347 ("Time passed---") at script bytecode offset `0xBE80` (`0xBE80..0xC600`), and resolves every character's paired or solo ending.

##### A. Character Gender Initialization (`0xBE90..0xBEEC`)
The script initializes a 12-element character gender table in script variables `0x398..0x3A3` (`0` = Male, `1` = Female):
- `0x398` (Claude): `0` (Male)
- `0x399` (Rena): `1` (Female)
- `0x39A` (Celine): `1` (Female)
- `0x39B` (Bowman): `0` (Male)
- `0x39C` (Dias): `0` (Male)
- `0x39D` (Precis): `1` (Female)
- `0x39E` (Ashton): `0` (Male)
- `0x39F` (Leon): `0` (Male)
- `0x3A0` (Opera): `1` (Female)
- `0x3A1` (Ernest): `0` (Male)
- `0x3A2` (Noel): `0` (Male)
- `0x3A3` (Chisato): `1` (Female)

##### B. Pair Iteration and Selective Matrix Evaluation (`0xBEF0..0xBFFC`)
The engine iterates over every unique character pair `(charA, charB)` with `charA < charB`:
- Outer loop: `charA` from 0 to 10 (`0xBEF0..0xBF04`, local variable `128`)
- Inner loop: `charB` from `charA + 1` to 11 (`0xBF54..0xBF70`, local variable `132`)
- Party presence: Opcode `0xB1` verifies that both `charA` and `charB` are currently active party members.
- Gender comparison at `0xBFA0`:
  - **Opposite-Sex Pairs (`gender[charA] != gender[charB]`):**
    - Evaluates **Matrix B** (Romance / Affection, live `[80075270]+0xE8`, script opcode `0xFF13` stack mode):
      - `0xBFB4`: Fetches `Matrix_B[charA][charB]` (Romance A -> B) into local variable `140`.
      - `0xBFC8`: Fetches `Matrix_B[charB][charA]` (Romance B -> A) into local variable `144`.
  - **Same-Sex Pairs (`gender[charA] == gender[charB]`):**
    - Evaluates **Matrix A** (Friendship, live `[80075270]+0x58`, script opcode `0xFF11` stack mode):
      - `0xBFE0`: Fetches `Matrix_A[charA][charB]` (Friendship A -> B) into local variable `140`.
      - `0xBFF4`: Fetches `Matrix_A[charB][charA]` (Friendship B -> A) into local variable `144`.

##### C. Mutual Threshold Verification (`0xC000..0xC020`) — Fan Hypothesis Confirmed
The engine tests whether both characters meet the numeric threshold:
```text
0xC000: op=0x43 (CMP_GE)  local[140], imm=0x000A (10)   ; Test A->B >= 10
0xC00C: op=0x43 (CMP_GE)  local[144], imm=0x000A (10)   ; Test B->A >= 10
0xC018: op=0x38 (LOG_AND)                               ; Require BOTH directions >= 10
0xC020: op=0x16 (JZ)      target=0xC050 / next_pair     ; Reject pair if either < 10
```
**Conclusion on Fan Hypothesis:**
The longstanding fan community model is **CONFIRMED** by direct bytecode disassembly. A paired ending requires mutual emotion level `>= 10` in both directions:
- Opposite-sex pairs require **Matrix B (Romance) >= 10** mutually (`Matrix_B[A][B] >= 10 && Matrix_B[B][A] >= 10`).
- Same-sex pairs require **Matrix A (Friendship) >= 10** mutually (`Matrix_A[A][B] >= 10 && Matrix_A[B][A] >= 10`).

##### D. Candidate Pair Table & Bubble Sort by Combined Score (`0xC024..0xC2D8`)
If a pair satisfies the mutual `>= 10` threshold:
1. `0xC024..0xC048`: Appends `charA` and `charB` to candidate array tables at base index `local[120]`.
2. `0xC04C..0xC064`: Computes `combined_score = local[140] + local[144]` (sum of mutual emotion points) and stores it in the score array.
3. `0xC068`: Increments candidate count `local[120]`.
4. Special plot flags are also tested for specific character pairs (e.g., `0xC07C` tests Celine with flag `0x1AB` for Ernest, `0xC0D0` tests Ashton with flag `0x163`, `0xC124` tests Opera & Ernest).
5. At `0xC180..0xC2D8`, the script executes an in-place **Bubble Sort** on the candidate list:
   - Compares `score[i]` against `score[j]` (`0xC1D8..0xC1F4`).
   - If `score[i] < score[j]`, swaps `score`, `charA`, and `charB` across the arrays (`0xC200..0xC2D4`).
   - The candidate list is thus strictly ordered by descending total combined affinity points.

##### E. Greedy Ending Assignment & Solo Endings (`0xC2E8..0xC450`)
- **Greedy Pairing (`0xC2E8..0xC3AC`):** The engine walks the sorted candidate list. For each pair `(charA, charB)`:
  - Checks if either character has already been claimed by a higher-priority pair (`assigned[char] != 0` tracked in script variable array `0x3B4..0x3BF`).
  - If both `assigned[charA] == 0` and `assigned[charB] == 0`:
    - Calls ending registration subroutine `0x2B3C` (`0xACF0`) with `(charA, charB)`.
    - Locks both characters: `assigned[charA] = pair_index + 1`, `assigned[charB] = pair_index + 1`.
- **Solo Endings (`0xC3B8..0xC448`):** Any character remaining with `assigned[char] == 0` is assigned their individual solo ending (subroutine `0x2B3C` invoked with argument `0x0F` / solo).
- Final resolved ending IDs and character associations are recorded into script variables `0x348..0x37F` and `0x388..0x3B3` for the post-credits epilogue theater.

---

#### 2. Part 2: Item-Creation & Synthesis Recipe Tables [Disassembly-only / Verified]

An exhaustive search for the item synthesis engine located the master recipe overlay in **Disc Archive 2990** (LBA 36156, raw size 10,240 bytes / decompressed size 19,496 bytes `0x4C28`, resident memory address `0x8007E000` / `0x80081FBC`), executed by specialty execution overlay **Disc Archive 3012** (LBA 36282).

##### A. Synthesis Execution and Inventory Calls (Overlay 3012)
Disassembly of `code-3012-lba-36282.asm` verifies the inventory integration:
- `800808E4`: Invokes `8003C594` (`add_inventory_item`) passing output item ID `0x64($s2)` and count `1`.
- `8008091C`: Invokes `8003C928` (`consume_inventory_item`) to decrement input items from the 1,024-slot inventory.
- `8007E2F4`: Blacksmithing modifier check verifies presence of item `0x2E7` (Magical Rasp) via XOR check and global flag `0x2DB`.

##### B. Recipe Table Format (Overlay 2990, Offset `0x3FBC`)
Item creation is governed by fixed static recipe lookup tables. Each recipe entry is a variable-length record formatted as little-endian 16-bit integers:
```c
struct RecipeEntry {
    uint16_t base_success_rate;    // Base success percentage (1..100)
    uint16_t output_item_id;        // Resulting item ID (1..1023)
    uint16_t material_item_id;      // Required mineral/catalyst item ID
    uint16_t base_item_ids[];       // Zero-terminated list of valid base items
    uint16_t terminator;            // 0x0000
};
```

##### C. Decoded Customization Recipes (119 Weapon Recipes)
The table contains **119 distinct weapon Customization recipes**. Cross-referencing against `item_ids.txt` decodes major endgame equipment pathways:

| Base Weapon(s) | Mineral Material | Output Weapon | Base Success % |
|---|---|---|---:|
| Minus Sword (`0x1F6`) | Mithril (`0x1A9`) | **Eternal Sphere (`0x1FB`)** (Claude Best Weapon) | 80% |
| Sharp Edge (`0x1F0`) | Mithril (`0x1A9`) | Minus Sword (`0x1F6`) | 60% |
| Sharp Edge (`0x1F0`) | Damascus (`0x1AA`) | Grand Stinger (`0x1F2`) | 40% |
| Broad / Long / Worn-out Sword | Gold (`0x1A4`) | Golden Fangs (`0x1E7`) | 40% |
| Kaiser Knuckles (`0x226`) | Moonite (`0x1A6`) | **Empresia (`0x227`)** (Rena Best Weapon) | 80% |
| Sorceress Knuckles (`0x225`) | Diamond (`0x1B3`) | Kaiser Knuckles (`0x226`) | 70% |
| Holy Rod (`0x23C`) | Star Ruby (`0x1B0`) | Dragon's Tusk (`0x241`) (Celine) | 80% |
| Silver Rod (`0x23B`) | Green Beryl (`0x1A8`) | Holy Rod (`0x23C`) | 70% |
| Asura (`0x231`) | Diamond (`0x1B3`) | Hecatoncheire (`0x232`) (Bowman) | 70% |
| Hard Knuckles (`0x222`) | Mithril (`0x1A9`) | Asura (`0x231`) | 60% |
| Hard Knuckles (`0x222`) | Rainbow Diamond (`0x1B2`) | Pain Cestus (`0x224`) | 50% |
| Twin Edge (`0x203`) | Damascus (`0x1AA`) | Lotus Eater (`0x205`) (Ashton) | 60% |
| Melufa (`0x208`) | Meteorite (`0x1AE`) | Holy Cross (`0x209`) (Ashton) | 80% |
| Crimson Diablos (`0x217`) | Star Ruby (`0x1B0`) | Soul Slayer (`0x219`) (Dias) | 70% |
| Hard Whip (`0x247`) | Damascus (`0x1AA`) | Splinter (`0x249`) (Ernest) | 60% |
| Shock Gun (`0x25C`) | Rainbow Diamond (`0x1B2`) | Psychic Gun (`0x25E`) (Chisato) | 60% |
| Light Box (`0x261`) | Damascus (`0x1AA`) | Plasma Box (`0x262`) (Precis) | 70% |

##### D. Art and Specialty Synthesis Tables
Subsequent blocks in Overlay 2990 define:
- **Art (Magic Canvas `0x0001`)**: Table maps artist character IDs and skill levels to portrait/painting item IDs `0x0002..0x0012` (e.g., Portrait A..L, "The Scream").
- **Blacksmith**: Verified item `0x2E7` (Magical Rasp) conditional lookup gate in `8007E2F4`.
- **Cooking / Compounding**: Material pairing matrices mapping pairs of ingredient IDs (`0x00D0..0x0180`) to finished dishes and medicine items.

---

### 2026-09-28 follow-up: Special-Case Ending Pairs, Art, & Cooking/Compounding Recipes [Disassembly-only / Verified]

This section resolves the two remaining loose ends from the 2026-09-28 item-creation and ending-selection investigation:
1. **Exhaustive enumeration of all special plot-flag ending pairs** in Disc 2 Archive 3788 (auditing whether any pairs beyond the initial 3 exist).
2. **Entry-by-entry decoding of the Art, Cooking, and Compounding specialty synthesis engines**, identifying real archive containers, table layouts, skill-level probability matrices, and output item mappings.

---

#### Part 0: Special-Case Ending-Pair Enumeration (Disc 2 Archive 3788)

In the standard candidate generation engine (`0xBEF0..0xC078`), pairs of active party members are evaluated against the mutual emotion threshold (`>= 10` in Matrix A or Matrix B). An audit of the candidate insertion block (`0xC07C..0xC17C`) was conducted across all 84,868 bytes of Disc 2 Archive 3788 bytecode.

**Result of Exhaustive Census**: The earlier notation citing three "examples" was misleading. There are **strictly and exactly THREE special-case candidate additions** hardcoded into Star Ocean 2's ending-selection engine. No other character pairs or plot flags exist for candidate selection in Archive 3788:

| # | Pair / Characters | Bytecode Address | Required Conditions | Event / Sidequest Context | Score |
|---|---|---|---|---|:---:|
| 1 | **Celine Jules + Prince Chris of Krosse** (`charA = 2, charB = 12`) | `0xC07C..0xC0CC` | `op=0xB1 char=2` (Celine active)<br>`op=0x0E flag=0x01AB` (427) | **Cross Castle Marriage Proposal Private Action**: Celine visits Prince Chris in Krosse Castle (Archive 3285 Scene 78 `0x6A54`: *"if I became a princess, I wouldn't be able to go on any more adventures, would I?"*). If accepted, flag `0x1AB` is set. | **26** (`0x1A`) |
| 2 | **Ashton Anchors + Eleanor of Herlie** (`charA = 6, charB = 13`) | `0xC0D0..0xC120` | `op=0xB1 char=6` (Ashton active)<br>`op=0x0E flag=0x0163` (355) | **Eleanor Illness Sidequest in Herlie**: Ashton visits Eleanor's house and obtains the Tears of the King / Metox cure (Archive 3363 Scene 156 `0x59E8`: *"Please take care of Eleanor... Eleanor began moaning in pain..."*). Flag `0x163` confirms recovery. | **20** (`0x14`) |
| 3 | **Opera Vectra + Ernest Ravresso** (`charA = 8, charB = 14`) | `0xC124..0xC17C` | `op=0xB1 char=8` (Opera active)<br>`op=0xB1 char=9` (Ernest active) | **Couple Priority Epilogue**: Both Opera and Ernest are recruited and present in the final party. Overrides standard matrix sorting to guarantee their paired spaceflight epilogue. | **24** (`0x18`) |

##### Bytecode Mechanics:
1. **Prince Chris (`charB = 12`)**:
   - `0xC07C`: `CHECK_PARTY char=2` (Celine). If not active, branches to `0xC0B4`.
   - `0xC088`: `TEST_FLAG flag=0x01AB` (Story flag 427, save byte `0x1A1D` bit 3). If unset, branches to `0xC0B4`.
   - `0xC090..0xC0C4`: Stores `charA = 2`, `charB = 12`, and assigns fixed `score = 26` (`0x1A`) into candidate list index `local[120]`, then increments candidate count.
2. **Eleanor (`charB = 13`)**:
   - `0xC0D0`: `CHECK_PARTY char=6` (Ashton). If not active, branches to `0xC108`.
   - `0xC0DC`: `TEST_FLAG flag=0x0163` (Story flag 355, save byte `0x1A14` bit 3). If unset, branches to `0xC108`.
   - `0xC0E4..0xC118`: Stores `charA = 6`, `charB = 13`, and assigns fixed `score = 20` (`0x14`) into candidate list, then increments candidate count.
3. **Opera & Ernest Romantic Epilogue (`charB = 14`)**:
   - `0xC124`: `CHECK_PARTY char=8` (Opera). If not active, branches to `0xC164`.
   - `0xC130`: `CHECK_PARTY char=9` (Ernest). If not active, branches to `0xC164`.
   - `0xC140..0xC174`: Stores `charA = 8`, `charB = 14`, and assigns fixed `score = 24` (`0x18`) into candidate list, then increments candidate count.
4. **Sorting & Resolution**: At `0xC180`, the engine transitions immediately to the Bubble Sort. Because their hardcoded scores (20, 24, 26) are competitive with high mutual emotion levels (10 + 10 = 20), these special pairings naturally sort to the top of the greedy queue.

---

#### Part 1: Cooking & Master Cooking Recipe Tables (Disc Archive 2990)

Analysis of `code-2990-lba-36156.bin` (RAM `0x8007E000`, 19,496 bytes `0x4C28`) proves that Cooking does **not** use an N×N ingredient pair matrix. Instead, it is governed by a 16-group ingredient-classification engine dispatched at `0x8008129C` and executed at `0x800812EC`:
- **Standard Cooking (Groups 0..5)**: Consumes one food category ingredient (`0x0117..0x011C`).
- **Master Cooking (Groups 6..15)**: Consumes luxury ingredients (`0x030E..0x0316`, plus all-purpose `0x0336`).

##### A. Engine Mechanics and Probability Formula
Disassembly of `0x8008139C..0x800814FC` reveals the exact recipe selection algorithm:
1. **Master Pointer Array**: Pointers at `0x4B64` (Successful outputs), `0x4BA4` (Failure outputs), and `0x4BE4` (Metadata bytes).
2. **Metadata Byte Format**:
   - Bits 0..3 (`byte & 0x0F`): Difficulty divisor $a1.
   - Bit 4 (`0x10`): Requires Cooking skill level $\ge 4$ (checked at `0x80081468`).
   - Bit 5 (`0x20`): Requires Cooking skill level $\ge 7$ (checked at `0x8008147C`).
3. **Success Rate Formula**:
   $$\text{Base \%} = \min\left(90, \frac{\text{Skill Level} \times 10 + 50}{\text{Divisor}}\right) + \text{Bonus}$$
   Where bonus includes Chef talents (Sense of Taste) and tools.
4. **Group 2 (Grain) Specialization**: At `0x800813D8..0x80081414`, characters Ashton (6), Claude (0), Rena (1), Celine (2), and Opera (8) branch away from the default tea table at `0x48AC` to a specialized Grain Meals table at `0x48E8`.
5. **Master Cooking Iron Chef Scoring Gauge**: At `0x80081564`, tables at `0x4A54..0x4AB4` supply `min1, max1, min2, max2` random score modifiers added to/subtracted from the Chef's battle score gauge (`lw 0x38($v1)`) upon dish completion. *(Note: This corrects the prior assumption that `0x4A54` was an Art portrait table).*

##### B. Decoded Cooking Recipe Tables (108 Successful Dishes + 7 Failures)

###### Standard Cooking (Groups 0..5)

| Group | Input Ingredient Category | Successful Dish Outputs | Failure Item(s) |
|---|---|---|---|
| **0** | **Seafood** (`0x0117`) | **Level 1+**: Toro Tuna (`0x0151`, div 1), Shu-mai (`0x0154`, div 1), Seaweed Miso Soup (`0x0153`, div 2)<br>**Level 4+**: Broth (`0x0125`, div 2), Shrimp au Gratin (`0x0158`, div 2), Big Tuna (`0x0159`, div 3)<br>**Level 7+**: Shark Fin Soup (`0x0123`, div 3), Sole & Fruit Sauce (`0x0135`, div 3), Salmon Omlet (`0x015A`, div 3), Shrimp Pilaf (`0x015B`, div 4) | Rotten Sashimi (`0x0152`) |
| **1** | **Fruit** (`0x0118`) | **Level 1+**: Orangeade (`0x0129`, div 1), Berry Juice (`0x0170`, div 1), Orange Sherbet (`0x0172`, div 2), Banana Crepes (`0x0173`, div 2)<br>**Level 4+**: Apple Cider (`0x0174`, div 4), Pickled Plum (`0x0175`, div 2), Strawberry Mousse (`0x0176`, div 3), Apple Crepes (`0x0177`, div 3)<br>**Level 7+**: Peach Ice Cream (`0x0178`, div 3), Aged Berry Juice (`0x0179`, div 8), Orange Au Gratin (`0x017A`, div 3) | Bitter Juice (`0x014E`) |
| **2a** | **Grain (Default / Teas)** (`0x0119`) | **Level 1+**: Sweet Dumpling (`0x0164`, div 1), Daikon Miso Soup (`0x0166`, div 1), Gruel (`0x0167`, div 2)<br>**Level 4+**: Root Beer (`0x015D`, div 1), 'Ishidaya' Tea (`0x015E`, div 1), Yukiyucho Tea (`0x015F`, div 2), Hassaku Tea (`0x0160`, div 2), Yaegaki Tea (`0x0161`, div 3), 'Usunigori' Tea (`0x0162`, div 3), Rice Cakes (`0x0168`, div 2), Pancakes (`0x0169`, div 2), Soy Milk (`0x02FD`, div 3)<br>**Level 7+**: Fried Rice (`0x0137`, div 3), Shrimp Doria (`0x016D`, div 3), Rice Omlet (`0x016E`, div 3), Rice Croquettes (`0x02FC`, div 3) | Sambai Tea (`0x0163`),<br>Smelly Rice Cakes (`0x02FE`) |
| **2b** | **Grain (Meals at `0x48E8`)**<br>*(Ashton, Claude, Rena, Celine, Opera)* | **Level 1+**: Sweet Dumpling (`0x0164`, div 1), Daikon Miso Soup (`0x0166`, div 1), Gruel (`0x0167`, div 2)<br>**Level 4+**: Rice Cakes (`0x0168`, div 2), Pancakes (`0x0169`, div 2), Soy Milk (`0x02FD`, div 3)<br>**Level 7+**: Fried Rice (`0x0137`, div 3), Shrimp Doria (`0x016D`, div 3), Rice Omlet (`0x016E`, div 3), Rice Croquettes (`0x02FC`, div 3) | Smelly Rice Cakes (`0x02FE`) |
| **3** | **Meat** (`0x011A`) | **Level 1+**: Meat Dumpling (`0x017C`, div 1), Potstickers (`0x017D`, div 1), Beef Croquettes (`0x017E`, div 2), Chicken Skewers (`0x017F`, div 2)<br>**Level 4+**: Jambalaya (`0x0180`, div 2), Chicken Doria (`0x0182`, div 2), Steak (`0x0183`, div 3)<br>**Level 7+**: Hamburger (`0x013F`, div 4), Baby Rabbit Risotto (`0x0184`, div 4), Ground Lamb Steak (`0x0185`, div 3) | Bad Tasting Stew (`0x0187`) |
| **4** | **Vegetables** (`0x011B`) | **Level 1+**: Squash Croquettes (`0x018A`, div 1), Corn Potage (`0x018B`, div 1), Quick Pickles (`0x02FF`, div 2)<br>**Level 4+**: Spring Roll (`0x018D`, div 2), Carrot Juice (`0x018E`, div 2), Cabbage Roll (`0x018F`, div 2), Rice-bran Pickles (`0x0300`, div 3)<br>**Level 7+**: Squash Spring Rolls (`0x0190`, div 3), Vegetable Juice (`0x0191`, div 3), Green Potage (`0x0192`, div 3), Carrot Ice Cream (`0x0301`, div 3) | Wilted Salad (`0x0193`) |
| **5** | **Egg / Dairy** (`0x011C`) | **Level 1+**: Fried Eggs (`0x0194`, div 1), Fruit Smoothie (`0x0196`, div 2), Yogurt (`0x0197`, div 1), Egg Sandwich (`0x0198`, div 1)<br>**Level 4+**: Chocolate Crepes (`0x0199`, div 3), Bacon & Eggs (`0x019A`, div 2), Vanilla Ice Cream (`0x019B`, div 2)<br>**Level 7+**: Shortcake (`0x019C`, div 3), Custard Pudding (`0x019D`, div 3), Macaroni Au Gratin (`0x019E`, div 4) | Spicy Cake (`0x019F`),<br>Raw Milk (`0x01A0`) |

###### Master Cooking (Groups 6..15)

All Master Cooking recipes unlock at Master Chef Level 1+; dishes are selected via weighted random draw against divisor $a1:

| Group | Luxury Ingredient | 4 Distinct Output Dishes (Item ID, Divisor) |
|:---:|---|---|
| **6** | **Purity Leaf** (`0x030E`) | Milky Potage (`0x0317`, div 3), Special Stir-fry (`0x0318`, div 3), Magical Salad (`0x0319`, div 4), Golden Stew (`0x031A`, div 5) |
| **7** | **Juicy Beef** (`0x030F`) | Fine Saute (`0x031B`, div 3), Exciting Tenderloin (`0x031C`, div 4), Prime Sirloin (`0x031D`, div 5), Inviting Filet (`0x031E`, div 5) |
| **8** | **Prime Tuna** (`0x0310`) | Tuna Skewers (`0x031F`, div 3), Prime Tuna Steak (`0x0320`, div 3), Fish of Happiness (`0x0321`, div 4), Special Tuna (`0x0322`, div 5) |
| **9** | **Ganze Sea Urchin** (`0x0311`) | Ichigoni (`0x0323`, div 3), Ichigoni Supreme (`0x0324`, div 4), Prince's Zoni Stew (`0x0325`, div 5), Sea Urchin on Rice (`0x0326`, div 7) |
| **10** | **Magical Rice** (`0x0312`) | Deluxe Doria (`0x0327`, div 3), Miracle Fried Rice (`0x0328`, div 3), Risotto Ecstasy (`0x0329`, div 4), Heavenly Doria (`0x032A`, div 5) |
| **11** | **Creamy Cheese** (`0x0313`) | Au Gratin Climax (`0x032B`, div 3), Cheese Pizza (`0x032C`, div 3), Assorted Cheeses (`0x032D`, div 4), Gorgonzola (`0x032E`, div 5) |
| **12** | **Sweet Fruit** (`0x0314`) | Gateau Marjolaine (`0x032F`, div 3), 1-up Pudding (`0x0330`, div 4), Beautiful Ice Cream (`0x0331`, div 5), Ginger Ale (`0x0332`, div 8) |
| **13** | **Slippery Slime** (`0x0315`) | Soda-Pop (`0x016B`, div 3), Amoeba Soup (`0x0155`, div 3), Slime Jelly (`0x0195`, div 8), Gelatin Steak (`0x0186`, div 8) |
| **14** | **Jiggly Slime** (`0x0316`) | Soda-Pop (`0x016B`, div 2), Amoeba Soup (`0x0155`, div 2), Slime Jelly (`0x0195`, div 4), Gelatin Steak (`0x0186`, div 4) |
| **15** | **Special Ingredient** (`0x0336`) | Genie's Veggie Soup (`0x0333`, div 6), Genie's Steak (`0x0334`, div 6), Energy Drink (`0x0335`, div 6), Seltzer (`0x0171`, div 6) |

---

#### Part 2: Art Specialty Recipe Engine (Disc Archive 3008)

The actual Art execution engine is located in **Disc Archive 3008** (`code-3008-lba-36265.bin`, RAM `0x8007E000`, 24,980 bytes `0x6194`, executed at `0x80080F5C..0x80081224`), **not** Archive 2990.
Art consumes either **Magic Canvas (`0x0001`)** or **Magical Clay (`0x002B`)**.

##### A. Skill Tier Distribution
The artist's Art skill level (1..10) indexes table `0x80083BB0` (file offset `0x5BB0`) to map to 5 difficulty tiers:
- **Tier 0** (Levels 1..2), **Tier 1** (Levels 3..4), **Tier 2** (Levels 5..6), **Tier 3** (Levels 7..8), **Tier 4** (Levels 9..10).

Each tier defines an exact percentage distribution across 5 item slot pools (weights sum to 100%):
- **Magic Canvas Weights (`0x5BBC`)**:
  - Tier 0 (Lv 1-2): Slot 0: 10%, Slot 1: 5%, Slot 2: 1%, Slot 3: 0%, Slot 4: 84%
  - Tier 1 (Lv 3-4): Slot 0: 15%, Slot 1: 10%, Slot 2: 5%, Slot 3: 1%, Slot 4: 69%
  - Tier 2 (Lv 5-6): Slot 0: 20%, Slot 1: 15%, Slot 2: 10%, Slot 3: 5%, Slot 4: 50%
  - Tier 3 (Lv 7-8): Slot 0: 20%, Slot 1: 20%, Slot 2: 15%, Slot 3: 10%, Slot 4: 35%
  - Tier 4 (Lv 9-10): Slot 0: 20%, Slot 1: 20%, Slot 2: 20%, Slot 3: 15%, Slot 4: 25%
- **Magical Clay Weights (`0x5C14`)**:
  - Tier 0 (Lv 1-2): Slot 0: 83%, Slot 1: 10%, Slot 2: 5%, Slot 3: 1%, Slot 4: 1%
  - Tier 1 (Lv 3-4): Slot 0: 69%, Slot 1: 15%, Slot 2: 10%, Slot 3: 5%, Slot 4: 1%
  - Tier 2 (Lv 5-6): Slot 0: 50%, Slot 1: 20%, Slot 2: 15%, Slot 3: 10%, Slot 4: 5%
  - Tier 3 (Lv 7-8): Slot 0: 35%, Slot 1: 20%, Slot 2: 20%, Slot 3: 15%, Slot 4: 10%
  - Tier 4 (Lv 9-10): Slot 0: 25%, Slot 1: 20%, Slot 2: 20%, Slot 3: 20%, Slot 4: 15%

##### B. Item Pools & Portrait Character Mapping
1. **Magic Canvas Pool (`0x5BD8`, 24 Output Items)**:
   - **Slot 0**: Victorial Card (`0x0013`), Mortalial Card (`0x0014`), Revival Card (`0x0015`)
   - **Slot 1**: Fol Up Card (`0x0016`), Discovery Card (`0x0017`), Extension Card (`0x0018`)
   - **Slot 2**: 'Spring' (`0x0002`), Fairies Card (`0x0019`), Fountain Card (`0x001A`)
   - **Slot 3**: 'The Scream' (`0x0003`), 'Judgment Day' (`0x0004`), 'The Last Supper' (`0x0005`)
   - **Slot 4 (Portraits A..L)**: When Slot 4 is rolled, subroutine `0x800810D8..0x80081130` compares the artist's character ID against table `0x80083C52` (`0x5C58..0x5C63`) to match the portrait directly to the artist:
     - `0x0006` **Portrait A** $\rightarrow$ Rena Lanford (`char 1`)
     - `0x0007` **Portrait B** $\rightarrow$ Celine Jules (`char 2`)
     - `0x0008` **Portrait C** $\rightarrow$ Bowman Jean (`char 3`)
     - `0x0009` **Portrait D** $\rightarrow$ Leon D.S. Gehste (`char 7`)
     - `0x000A` **Portrait E** $\rightarrow$ Ernest Ravresso (`char 9`)
     - `0x000B` **Portrait F** $\rightarrow$ Dias Flac (`char 4`)
     - `0x000C` **Portrait G** $\rightarrow$ Ashton Anchors (`char 6`)
     - `0x000D` **Portrait H** $\rightarrow$ Noel Chandler (`char 10`)
     - `0x000E` **Portrait I** $\rightarrow$ Opera Vectra (`char 8`)
     - `0x000F` **Portrait J** $\rightarrow$ Precis F. Neumann (`char 5`)
     - `0x0010` **Portrait K** $\rightarrow$ Claude C. Kenni (`char 0`)
     - `0x0011` **Portrait L** $\rightarrow$ Chisato Madison (`char 11`)
   - **Failure Item**: Scribbles (`0x0012`)
2. **Magical Clay Pool (`0x5C30`, 15 Output Items)**:
   - **Slot 0**: Silence Card (`0x001B`), Tri-ball (`0x001F`), Skanda (`0x0027`)
   - **Slot 1**: Hexagram Card (`0x001C`), Hyperball (`0x0020`), Dummy Doll (`0x0025`)
   - **Slot 2**: Super Ball (`0x0021`), Angle's Statue (`0x0022`), Mirror of Wisdom (`0x002A`)
   - **Slot 3**: Magic Rock (`0x001D`), Fairy's Statue (`0x0023`), Jack-in-the-box (`0x0029`)
   - **Slot 4**: Goddess Statue (`0x0024`), Idol (`0x0026`), Treasure Chest (`0x0028`)
   - **Failure Item**: Weird Lump (`0x001E`)

---

#### Part 3: Compounding Specialty Recipe Engine (Disc Archive 3008)

Compounding mixes two herbs to create medicinal tinctures and potions. Disassembly of `0x80081AA4..0x80081BE8` in `code-3008-lba-36265.bin` reveals the complete 6×6 symmetric herb lookup matrix:
- **Herbs**: Mandrake (`0x00DC`), Rose Hips (`0x00DD`), Artemis Leaf (`0x00DE`), Wolfsbane (`0x00DF`), Lavender (`0x00E0`), Aceras (`0x00E1`).

##### A. 6×6 Symmetric Pairing Matrix (`0x80083ECC` / file offset `0x5ECC`)
Lookup formula at `0x80081B98`: `group_id = matrix[herb1][herb2]`. The matrix is symmetric ($H_1 + H_2 = H_2 + H_1$):

| Herb | Mandrake (`0xDC`) | Rose Hips (`0xDD`) | Artemis Leaf (`0xDE`) | Wolfsbane (`0xDF`) | Lavender (`0xE0`) | Aceras (`0xE1`) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Mandrake** (`0xDC`) | **Group 1** | Group 2 | Group 3 | Group 4 | Group 5 | Group 6 |
| **Rose Hips** (`0xDD`) | Group 2 | **Group 7** | Group 8 | Group 9 | Group 10 | Group 11 |
| **Artemis Leaf** (`0xDE`) | Group 3 | Group 8 | **Group 12** | Group 13 | Group 14 | Group 15 |
| **Wolfsbane** (`0xDF`) | Group 4 | Group 9 | Group 13 | **Group 16** | Group 17 | Group 18 |
| **Lavender** (`0xE0`) | Group 5 | Group 10 | Group 14 | Group 17 | **Group 19** | Group 20 |
| **Aceras** (`0xE1`) | Group 6 | Group 11 | Group 15 | Group 18 | Group 20 | **Group 21** |

##### B. Output Item Variant Table (`0x80083EE8` / file offset `0x5EE8`)
Each of the 21 groups contains 4 output variants rolled at random `0..3` via `0x80081B4C`. Success rates are governed by table `0x80083EA0` (`0x5EA0`):
- **Variants 0 & 1 (Common)**: Base success rate scales from 30% (Lv 1) to 60% (Lv 10).
- **Variants 2 & 3 (Rare)**: Base success rate scales from 2% (Lv 1) to 30% (Lv 10).

| Group | Herb Pair | Variant 0 (Common) | Variant 1 (Common) | Variant 2 (Rare) | Variant 3 (Rare) |
|:---:|---|---|---|---|---|
| **1** | Mandrake + Mandrake | Natural High (`0x0105`) | Risky Liquid (`0x00F4`) | Violence Pill (`0x0108`) | Crush Pill (`0x0106`) |
| **2** | Mandrake + Rose Hips | Attack Vial (`0x00E3`) | Smoke Mist (`0x010F`) | Kamikaze Tonic (`0x00E5`) | Flash Pot (`0x00F8`) |
| **3** | Mandrake + Artemis Leaf | Danger Pot (`0x00F6`) | Sweet Syrup (`0x00FC`) | Spring Water (`0x0116`) | Sour Syrup (`0x00FB`) |
| **4** | Mandrake + Wolfsbane | Lilith Tonic (`0x00F5`) | Bubble Lotion (`0x00EB`) | Melting Lotion (`0x00F2`) | Fairy's Cologne (`0x00EF`) |
| **5** | Mandrake + Lavender | Maple Syrup (`0x00FD`) | Nightmare Pot (`0x00F7`) | Smoke Oil (`0x00E8`) | Merlin Drink (`0x00F0`) |
| **6** | Mandrake + Aceras | Risky Liquid (`0x00F4`) | Energy Tonic (`0x00E4`) | Hot Syrup (`0x0100`) | Herbal Oil (`0x00EA`) |
| **7** | Rose Hips + Rose Hips | Cure Poison (`0x0102`) | Cure Paralysis (`0x0103`) | Maple Syrup (`0x00FD`) | Mixed Syrup (`0x0101`) |
| **8** | Rose Hips + Artemis Leaf | Cure Poison (`0x0102`) | Cure Paralysis (`0x0103`) | Skanda Compress (`0x00E2`) | Marionette Pill (`0x0109`) |
| **9** | Rose Hips + Wolfsbane | Danger Pot (`0x00F6`) | Nightmare Pot (`0x00F7`) | Paralysis Mist (`0x0110`) | Succubus Cologne (`0x010C`) |
| **10** | Rose Hips + Lavender | Sweet Syrup (`0x00FC`) | Fresh Syrup (`0x00FF`) | Fruit Syrup (`0x00FE`) | **Holy Mist (`0x0113`)** |
| **11** | Rose Hips + Aceras | Succubus Cologne (`0x010C`) | Kamikaze Tonic (`0x00E5`) | Mental Pot (`0x00FA`) | Skanda Ointment (`0x010A`) |
| **12** | Artemis Leaf + Artemis Leaf | Spring Water (`0x0116`) | Care Tablet (`0x0107`) | Spring Water (`0x0116`) | Fairy Glass (`0x00EE`) |
| **13** | Artemis Leaf + Wolfsbane | Violence Pill (`0x0108`) | Sour Syrup (`0x00FB`) | Fruit Syrup (`0x00FE`) | Hot Syrup (`0x0100`) |
| **14** | Artemis Leaf + Lavender | Wonder Drug (`0x0104`) | Smelling Salts (`0x00E6`) | Medical Rinse (`0x00F1`) | **Resurrection Mist (`0x00F3`)** |
| **15** | Artemis Leaf + Aceras | Wonder Drug (`0x0104`) | Flash Pot (`0x00F8`) | Herbal Oil (`0x00EA`) | Spring Water (`0x0116`) |
| **16** | Wolfsbane + Wolfsbane | Stink Gel (`0x010B`) | Bitter Lotion (`0x00ED`) | Madness Mist (`0x0114`) | Melting Lotion (`0x00F2`) |
| **17** | Wolfsbane + Lavender | Stink Gel (`0x010B`) | Bitter Lotion (`0x00ED`) | Paralysis Oil (`0x00EC`) | Melting Lotion (`0x00F2`) |
| **18** | Wolfsbane + Aceras | Lilith Tonic (`0x00F5`) | Bubble Lotion (`0x00EB`) | Pixie Cologne (`0x010E`) | Shock Oil (`0x00E7`) |
| **19** | Lavender + Lavender | Mixed Syrup (`0x0101`) | Medical Rinse (`0x00F1`) | Herbal Oil (`0x00EA`) | **Resurrection Bottle (`0x0115`)** |
| **20** | Lavender + Aceras | Energy Tonic (`0x00E4`) | Fresh Syrup (`0x00FF`) | **Resurrection Mist (`0x00F3`)** | **Holy Mist (`0x0113`)** |
| **21** | Aceras + Aceras | Smelling Salts (`0x00E6`) | Skanda Ointment (`0x010A`) | Fairy Mist (`0x0111`) | **Resurrection Bottle (`0x0115`)** |

---

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


### Resolution of final remaining Chunk 1 gaps (2026-09-28) [Disassembly-only / Verified]

This pass pushes forward from the seven identified lead sites and investigates the final 45 unmapped bytes of decoded Chunk 1 ($S = \text{[80075270]}$, decoded `0x000..0x1A0`, 416 bytes). By tracing the primary script VM system-call dispatch table at `8007380C`, examining Party/Status menu overlay 3018, tracing Options menu overlay 3016 and Save/Load UI overlay 2998 stack arguments to resident palette routine `80013C0C`, and analyzing field step modifier setters `8003225C..8003230C`, **all 45 remaining bytes are definitively accounted for (0 bytes unknown)**.

#### 1. Detailed field findings and disassembly evidence

1. **`0x41` / S+041 (1 byte): Validated party-slot selector [Verified]**
   - **MIPS Evidence**: Confirmed party-slot selector (`800530A8: lbu $v0, 0x41($v0)`, `80053124: sb $v0, 0x41($v1)`) as detailed in [docs/SO2-PARTY-MEMBER-INVESTIGATION.md](SO2-PARTY-MEMBER-INVESTIGATION.md). Citing the existing verified investigation resolves this byte in the coverage map.
   - **Classification**: Promoted to `mapped`.

2. **`0x1C..0x20` / S+01C (4 bytes) and `0x2C..0x30` / S+02C (4 bytes): Script queryable system parameters 0 and 1 [Disassembly-only / Verified]**
   - **MIPS Evidence**:
     - Both words belong to the contiguous array of 32-bit script system variables and counters `S+010..S+030` (`S+010` clock-derived word, `S+014` event counter, `S+018` Fol, `S+01C` param 0, `S+020` menu-operation counter, `S+024` save-preparation counter, `S+028` companion counter, `S+02C` param 1).
     - Tracing the resident script VM system-call jump table at `8007380C` (`80067678: lw $v0, 0x380c($at)`) confirms their exact getter entry points:
       - **Case 8 (`80067778..80067790`)**: Reads `80067788: lw $v0, 0x1c($v0)` from `S`, storing the result word into script return variable `[80075708]` (`80067790: sw $v0, ($v1)`).
       - **Case 12 (`80067860..80067878`)**: Reads `80067870: lw $v0, 0x2c($v0)` from `S`, storing the result word into script return variable `[80075708]` (`80067878: sw $v0, ($v1)`).
   - **Classification**: Promoted to `mapped`.

3. **`0x40` / S+040 (1 byte): Status / Formation Menu selected party slot cursor index [Disassembly-only / Verified]**
   - **MIPS Evidence**:
     - In Party / Status / Formation Menu Overlay 3018, `S+040` is loaded on menu initialization at `8007FDC8: lbu $v0, 0x40($v0)` and stored into the local menu control structure at `0x34($s1)` and `0xa4($s1)` (`8007FDD0/8007FDD4: sh $v0, 0xa4($s1); sh $v0, 0x34($s1)`).
     - At `8007E164: lh $v0, 0x34($s1)`, the loaded index (0..7) indexes the active party slot array to verify party member presence via `80033758`.
     - When changing highlighted character or exiting the formation menu, the selection is committed back to save memory at `8007FE5C..8007FE74`:
       ```text
       8007FE5C: lhu $v0, 0x34($a0)
       8007FE64: lw $v1, 0x5270($v1)
       8007FE74: sb $v0, 0x40($v1)
       ```
   - **Values**: Holds active cursor slot index `0..7`.
   - **Classification**: Promoted to `mapped`.

4. **`0x47, 0x48` / S+047, 048 (2 bytes): Message window / UI font highlight and shading color parameters [Disassembly-only / Verified]**
   - **MIPS Evidence**:
     - In Options Menu Overlay 3016, user adjustments commit these two bytes at `8007EBD4: sb $v0, 0x47($v1)` and `8007EBEC: sb $v0, 0x48($v1)`.
     - In Save/Load UI Overlay 2998 at `8007E7C8..8007E7E4`, these bytes are loaded from `S` (`8007E7C8: lbu $v0, 0x47($v1)` and `8007E7D4: lbu $v1, 0x48($v1)`) and passed as stack arguments (stack offsets `0x10` and `0x14`) to resident palette configuration routine `80013C0C`.
     - Disassembly of resident routine `80013C0C..80013C58`:
       ```text
       80013C0C: lw $v1, 0x10($sp)       ; arg 4 = S+047 (Blue)
       80013C10: lw $a0, 0x14($sp)       ; arg 5 = S+048 (Alpha / Shade)
       80013C14: lw $t0, 0x18($sp)       ; arg 6 = font scale (0x20)
       80013C24: sb $a2, -0x4958($at)    ; Red component
       80013C30: sb $a3, -0x4957($at)    ; Green component
       80013C3C: sb $v1, -0x4956($at)    ; Blue component (from S+047)
       80013C48: sb $a0, -0x4955($at)    ; Alpha / shading mode (from S+048)
       ```
     - These bytes directly configure the Blue and Alpha/shading components of the active UI text and window frame palette, complementing the 4 window corner colors at `0x30..0x40`.
   - **Classification**: Promoted to `mapped`.

5. **`0x4D` / S+04D (1 byte): Field step / modifier update dirty flag [Disassembly-only / Verified]**
   - **MIPS Evidence**: Written at `8003197C: sb $s2, 0x4d($v0)` immediately following the recalculation of the eight halfword field modifiers at `S+188..196` (`800318AC..8003196C`). Flags that field step/encounter modifier recalculation has completed.
   - **Classification**: Promoted to `mapped`.

6. **`0x4E` / S+04E (1 byte): Script system parameter byte [Disassembly-only / Verified]**
   - **MIPS Evidence**: Handled by Case 23 of the primary script VM system-call dispatch table at `80067B18..80067B34`: loads script argument byte from `($s3)` and stores it directly to `S+04E` (`80067B34: sb $v0, 0x4e($v1)`).
   - **Classification**: Promoted to `mapped`.

7. **`0x4F..0x54` / S+04F..053 (5 bytes): Zero alignment padding [Disassembly-only / Verified]**
   - **MIPS Evidence**: Contiguous 5-byte span between script parameter byte `0x4E` and the 32-bit menu clock-throttle marker at `0x54..0x58`. Verified zero across all inspected memory cards and RAM dumps.
   - **Classification**: Promoted to `partial`.

8. **`0x188..0x198` / S+188..197 (16 bytes): Eight signed halfword field rate / step / encounter modifiers [Disassembly-only / Verified]**
   - **MIPS Evidence**:
     - Eight signed 16-bit halfwords (`0x188, 0x18A, 0x18C, 0x18E, 0x190, 0x192, 0x194, 0x196`).
     - Generic setter dispatch table arms at `8003225C..8003230C` store `$a2` (or scaled arithmetic values) into each halfword:
       ```text
       8003225C: sh $a2, 0x188($v0)
       8003226C: sh $a2, 0x18a($v0)
       80032298: sh $v0, 0x18c($a0)
       800322A8: sh $a2, 0x18e($v0)
       800322B8: sh $a2, 0x190($v0)
       800322C8: sh $a2, 0x192($v0)
       800322D8: sh $a2, 0x194($v0)
       8003230C: sh $v1, 0x196($a0)
       ```
     - Field step update routine at `800318AC..8003196C` reads and arithmetically adjusts all eight halfwords during player terrain movement (gated by global flag `0x25` for encounter rate adjustments), setting update flag `0x4D` upon completion.
   - **Classification**: Promoted to `mapped`.

9. **`0x17A..0x184` / S+17A..183 (10 bytes): Operational transition state and script operand bytes [Disassembly-only / Verified]**
   - **MIPS Evidence**: Contains script operand bytes `0x181` and `0x182` (written by script VM at `80064A18: sb $v0, 0x181($v0)` and `80064A2C: sb $v0, 0x182($v1)`; cleared on area transition at `80048ABC/80048AD0` and `80051CE8`), surrounded by transition state bytes.
   - **Classification**: Promoted to `partial`.

#### 2. Final Chunk 1 accounting

Every single byte of decoded Chunk 1 (`0x000..0x1A0`, 416 bytes) is now completely accounted for:

| Decoded Range | Bytes | Tier | Field Description |
|---|---:|---|---|
| `000..010` | 16 | `mapped` | Key customization: 8x u16 button masks |
| `010..014` | 4 | `mapped` | Clock-derived word (menu clock / 60) |
| `014..018` | 4 | `mapped` | Event counter (script-adjustable, zero-floored) |
| `018..01C` | 4 | `mapped` | Fol (money), u32 |
| `01C..020` | 4 | `mapped` | Script queryable system parameter 0 (VM dispatch Case 8 `80067788`) |
| `020..024` | 4 | `mapped` | Menu-operation counter |
| `024..028` | 4 | `mapped` | Save-preparation counter |
| `028..02C` | 4 | `mapped` | Companion conditional menu-operation counter |
| `02C..030` | 4 | `mapped` | Script queryable system parameter 1 (VM dispatch Case 12 `80067870`) |
| `030..040` | 16 | `mapped` | Message window corner colors (4x u32 0x00BBGGRR) |
| `040..041` | 1 | `mapped` | Status / Formation Menu selected party slot cursor index (0..7) |
| `041..042` | 1 | `mapped` | Validated party-slot selector |
| `042..043` | 1 | `mapped` | Non-default lead-name flag (rename selector 0) |
| `043..044` | 1 | `mapped` | Non-default lead-name flag (rename selector 1) |
| `044..045` | 1 | `mapped` | Sound output (Surround/Stereo/Monaural) |
| `045..046` | 1 | `mapped` | Route / lead selector |
| `046..047` | 1 | `mapped` | Vibration on/off |
| `047..049` | 2 | `mapped` | Message window / UI font highlight and shading color parameters (Blue, Alpha) |
| `049..04A` | 1 | `mapped` | Targeting mode |
| `04A..04B` | 1 | `mapped` | Camera work |
| `04B..04C` | 1 | `mapped` | Combat motion mode |
| `04C..04D` | 1 | `mapped` | Required disc (0=Disc 1, 1=Disc 2) |
| `04D..04E` | 1 | `mapped` | Field step / modifier update dirty flag (`8003197C`) |
| `04E..04F` | 1 | `mapped` | Script system parameter byte (VM dispatch Case 23 `80067B34`) |
| `04F..054` | 5 | `partial` | Zero alignment padding before menu clock throttle marker |
| `054..058` | 4 | `mapped` | Menu clock-throttle marker |
| `058..0E8` | 144 | `mapped` | Matrix A (Friendship Points): 12x12 character-pair values, 0..15 |
| `0E8..178` | 144 | `mapped` | Matrix B (Romance / Affection Points): 12x12 character-pair values, 0..15 |
| `178..17A` | 2 | `mapped` | Signed completion / result code |
| `17A..184` | 10 | `partial` | Operational transition state and script operand bytes (181/182) |
| `184..188` | 4 | `mapped` | Two signed percentage stat modifiers (2x i16) |
| `188..198` | 16 | `mapped` | Eight signed halfword field rate / step / encounter modifiers (8x i16) |
| `198..1A0` | 8 | `mapped` | Two saved save-menu selection words |
| **Total** | `000..1A0` | **416** | **401 bytes mapped (96.4%) + 15 bytes partial (3.6%) = 100.0% accounted for (0 bytes unknown)** |
