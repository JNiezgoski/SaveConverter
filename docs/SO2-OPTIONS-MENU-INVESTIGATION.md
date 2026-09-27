# SO2 Options menu: per-save fields and actual menu writers

Investigation: **2026-09-27**. US PS1 BASCUS-94421 / SCUS-94421 (Disc 1),
SCUS-94422 (Disc 2).

## Result and confidence

**All eight requested settings are located in the per-save decoded body.**
The Options overlay imports them, changes local menu values in input callbacks,
and writes them back on menu destruction; button remapping writes immediately.
The established save serializer includes all these fields. No separate global
memory-card configuration record is involved in this demonstrated path.

**Verified — Disassembly / bounded execution. Unverified — In-game save/reload
and sensory/gameplay effects.** No card was edited, no emulator was driven,
and no before/after save diff was used. “Verified” here means actual extracted
instructions and their menu labels, not newly observed gameplay.

All offsets below are **decoded**, never offsets in the compressed card block.
`S=[80075270]`, `F=[80075710]`, `G=[80075704]`; `M` is the Options menu object.
Only chunk 1 is based at S. F is a separate allocation, as established in the
[disc/Psynard investigation](SO2-DISC-AND-PSYNARD-CHECK.md).
The live object-pointer table at `80075360` is not an Options storage array.

| Setting | Decoded bytes | Encoding |
|---|---|---|
| Message speed | `0x1860` | u8 `0..7`, displayed `1..8`, fast to slow |
| Sound output | `0x44` | u8 `0` Surround, `1` Stereo, `2` Monaural |
| Window color | `0x30..0x3F` | Four little-endian `0x00BBGGRR` words: UL, UR, LL, LR |
| Targeting mode | `0x49` | u8 `2` Auto, `0` Semi-Auto, `1` Manual |
| Camera work | `0x4A` | u8 `0` Normal, `1` Leader-Centered |
| Combat motion mode | `0x4B` | u8 `0` button + direction icon, `1` Only direction icon; details below |
| Key customization | `0x00..0x0F` | Eight u16 button masks in action order |
| Vibration | `0x46` | u8 `0` OFF, `1` ON |

## Sources, identification, and reproduction

Both supplied resume states were extracted afresh with `tools/extract_so2_ram.py`,
using their matching discs as EXE anchors. Both contain `S=8009BF98` in these
captures. Neither contains the Options constructor's first 128 bytes or its
complete scalar input loop (`8007EC28..8007EE37`), searched across all 2 MB.
**The identifiable Options overlay is not resident in either snapshot.**
This is a bounded negative match, not proof that no fragment survives anywhere.

However, archive scanning for the established S-pointer loads and button-setter
calls found **entry 3016**, so a fresh Options-open state is **not needed to
resolve the offsets**. Entry 3017 supplies its actual text and font. All five
entries below were independently extracted from both discs and are identical.

| Entry | ISO LBA, both discs | Decompressed bytes | Address/use |
|---|---:|---:|---|
| 2576 | 30736 | `4C7FC` | `8002F810`, resident state accessors and staging |
| 2985 | 36109 | `F9A8` | `800D1B28`, shared menu/text code |
| 2998 | 36213 | `4D28` | `8007E000`, save/load overlay |
| 3016 | 36294 | `2884` | `8007E000`, Options overlay |
| 3017 | 36297 | `1C74` | Options text/font resource |

The resident overlay manager initializes its destination to `8007E000`
(`80034DEC..80034E04`). Its selection branch `80034F2C/30` selects archive ID
`BC8` (3016); `80034F98..80034FA4` also requests the following entry.
Internal absolute pointers corroborate the load: Options construction installs
vtable `80080764`, whose destructor entry at `80080770` is `8007E3CC` and
adjustment callback at `80080800` is `8007EC28`.
The save overlay uses the same address at a different time; do not confuse them.

The labels are **not guessed from row order**. Resource 3017 begins with offsets
to its text table (`+10`) and font (`+A08`). Real shared-code execution of
`800D7BD0` resolves group/index to each string:

```text
800D7BDC lh    v0,E6(a0)       ; text group
800D7BE0 lw    v1,E0(a0)       ; text-table base
800D7BE4 sll   v0,v0,2
800D7BE8 addu  v0,v0,v1
800D7BEC lw    a1,0(v0)        ; relative group offset
800D7BF4 jal   800D863C        ; skip index zero-terminated strings
800D7BF8 addu  a1,v1,a1
```

`800D92CC..800D92DC` decodes two-byte glyph IDs as `(first&7F)|(second<<7)`;
`800D92EC` subtracts one to index the font. `800D7B70..800D7BA8` establishes
the width/bitmap pointers and height; `800D9640..800D96A8` reads 12 halfword rows
per glyph. The reproduction renders this **extracted bitmap font**, and the
visible Latin glyphs were transcribed into a local index table. `labels.json`
records the executed string addresses and decoded text; control tokens remain
explicit rather than being silently invented as letters.

Run from the repository root:

```powershell
python artifacts/so2-options-menu/verify.py
```

Requires `capstone`, `Pillow`, `zstandard`, and the supplied local discs/states.
The verification script, results, and labels live at
`artifacts/so2-options-menu/verify.py`, `results.json`, and `labels.json`, but
like every other `artifacts/` output in this repo they are **not committed**
(the whole directory is gitignored — see `.gitignore`) — regenerate them
locally with the command above if needed. It regenerates extracted binaries,
both RAM snapshots, `glyphs.png`, and byte-bearing `evidence.asm` in that
directory. Source and RAM SHA256 hashes are recorded in `results.json`.

## Shared input, commit, and serialization evidence

`8007EC28` is the adjustment callback. It reads the active column from
`[M+14]+34`, then the row from `M+BC/BE/C2`, and updates a menu halfword.
Argument `a1=1` subtracts one; the tested opposite event `a1=2` adds one.
The real helper wraps in `0..count-1` and retains the menu-only bit `8000`:

```text
8007EE00 andi  v0,a1,7FFF
8007EE04 addu  v1,v0,a2        ; delta
8007EE08 bgez  v1,8007EE18
8007EE0C slt   v0,v1,a3        ; count
8007EE10 addu  v1,v1,a3
8007EE14 slt   v0,v1,a3
8007EE18 bnez  v0,8007EE24
8007EE1C andi  v0,a1,8000
8007EE20 subu  v1,v1,a3
8007EE24 beqz  v0,8007EE30
8007EE28 nop
8007EE2C ori   v1,v1,8000
8007EE30 jr    ra
8007EE34 move  v0,v1
```

The Options destructor at `8007E3CC` commits the local fields. It stores bytes,
so the transient highlight bit is discarded; targeting explicitly masks before
conversion. This is a menu lifecycle callback, not a card-write routine.

The **save overlay** serializer `80081A70` proves persistence:

```text
80081ACC addiu s1,zero,1A0
80081AD8 move  a2,s4           ; decoded +0
80081ADC sw    s1,10(sp)       ; length
80081AE8 lw    a3,5270(a3)     ; S
80081AEC jal   80081C38
...
80081BA4 addiu s1,zero,440
80081BB0 jal   80012108
80081BB4 addiu a1,zero,E       ; chunk-5 staging resource
80081BC0 move  a2,s2           ; decoded +1748 after preceding chunks
80081BC4 move  a3,v0
80081BC8 jal   80081C38
80081BCC sw    s1,10(sp)
```

`80081C38..80081C60` copies live→decoded when `a1=0`, decoded→live when
`a1!=0`, through `80023ED0`. `80081BE8` invokes the real zero-run encoder;
`80081AC0` invokes its decoder on load. For F, resident `80055FC8` gets resource
E; `80055FF0` loads F and `80056060..8005608C` copies its first `2A0` bytes
there, followed by G's `170` bytes. Thus **F+118 = decoded 1748+118 = 1860**.
The interpreter executes this staging copy, both serializer-copy directions,
and the real codec; it does not execute the complete card transaction.

## 1. Message speed

**Verified — Disassembly / execution. Unverified — In-game.**
Decoded **`1860`, u8**, is the zero-based selection for displayed **1..8**.
Group 6 strings at resource `2A4..2B3` are the numbers; group 5 is Fast/Slow.
Rendering binds `M+C4` to eight choices at `8007EFE8..8007EFF0`.

```text
8007E314 lw    v0,5710(v0)     ; F, constructor import
8007E320 lbu   v0,118(v0)
8007E328 sh    v0,C4(s3)
8007ECE0 lh    a1,C4(s0)       ; selected-row adjustment
8007ECE4 jal   8007EE00
8007ECE8 addiu a3,zero,8
8007ECF0 sh    v0,C4(s0)
8007E3DC lw    a0,5710(a0)     ; destructor commit
8007E3E8 lhu   v1,C4(s0)
8007E404 sb    v1,118(a0)
```

The menu preview also reads `M+C4` at `8007E7A4` and advances its sample using
that delay (`8007E7AC..8007E808`). This establishes a speed selector rather
than an arbitrary byte resembling one. Exact dialogue timing in frames was
not measured; do not equate displayed 8 with stored 8.

## 2. Sound output

**Verified — Disassembly / execution. Unverified — In-game audio.**
Decoded **`44`, u8: 0=Surround, 1=Stereo, 2=Monaural**. The three strings
are group 8 at resource `30E/317/31E`; drawing selects group 8 at `8007F038/3C`
and binds `M+C6`, count 3, at `8007F054..8007F05C`.

```text
8007E32C lbu   v0,44(v1)       ; v1=S, import
8007E334 sh    v0,C6(s3)
8007ECF8 lh    a1,C6(s0)
8007ECFC jal   8007EE00
8007ED00 addiu a3,zero,3
8007ED08 sh    v0,C6(s0)
8007E410 lhu   v0,C6(s0)       ; v1=S, commit
8007E418 sb    v0,44(v1)
8007E4CC lbu   a1,44(v0)       ; v0=S
8007E4D0 jal   8001AAF0        ; a0=[80075274], sound context
8007E4D4 nop
8001AAF0 addiu v0,zero,1
8001AAF4 sb    a1,11(a0)
8001AAF8 jr    ra
8001AAFC sb    v0,6(a0)
```

This supersedes the old raw `03CB` “Surround flag” lead. The menu selection is
a three-way byte in decoded state, not a proven two-way flag at that raw offset.

## 3. Message window color

**Verified — Disassembly / execution. Unverified — In-game rendering.**
Decoded **`30,34,38,3C`**, four words `00BBGGRR`, are **UL, UR, LL, LR**.
Group 10 supplies those corner labels; `M+C8` is only the temporary corner
selection, initialized to zero, not a separately saved color preset.
The constructor loop `8007E108..8007E12C` copies S+30..3F to M+D8..E7.

```text
8007FCD0 lh    v0,64(s1)       ; selected corner in color dialog
8007FCD8 sll   v0,v0,2
8007FCDC addu  v0,v0,s4        ; s4=parent M
8007FCE0 lw    v1,D8(v0)
8007FCE8 andi  v0,v1,FF
8007FCEC sh    v0,66(s1)       ; R
8007FCF0 srl   v0,v1,8
8007FCF4 andi  v0,v0,FF
8007FCF8 srl   v1,v1,10
8007FCFC andi  v1,v1,FF
8007FD00 sh    v0,68(s1)       ; G
8007FD08 sh    v1,6A(s1)       ; B
...
800801C4 sll   v1,v1,8
800801C8 or    a0,a0,v1
800801CC sll   v0,v0,10
800801D0 or    a0,a0,v0
800801D4 lh    v0,64(s1)
800801D8 lw    a1,8(s1)        ; parent M
800801DC sll   v0,v0,2
800801E0 addu  v0,v0,a1
800801E4 sw    a0,D8(v0)
...
8007E480 lw    v0,D8(a0)       ; destructor loop, a0 initially M
8007E484 addiu a0,a0,4
8007E488 addiu a1,a1,1
8007E48C sw    v0,30(v1)       ; v1 initially S
8007E490 slti  v0,a1,4
8007E494 bnez  v0,8007E480
8007E498 addiu v1,v1,4
```

Color adjustment `80080238` reads the component row and adds ±1, masking `FF`
before its stores at `800802B0/C8/DC`. The actual renderer independently loads
S+30/34/38/3C into GPU color words at `8006F424..8006F470`. Its first word gets
the polygon command in the high byte. Color-dialog packing zeros that byte;
it is not a fourth editable alpha channel.

## 4. Targeting mode

**Verified — Disassembly / execution. Unverified — In-game combat.**
Decoded **`49`: 2=Auto, 0=Semi-Auto, 1=Manual**.
Group 11 strings are Auto/Semi-Auto/Manual in that on-screen order.
`8007F150..8007F158` binds M+CA to three choices, but it is converted on entry
and exit; copying the screen index directly into the save would be wrong.

```text
8007E338 lbu   a0,49(v1)       ; v1=S
8007E33C jal   8007F5D0        ; saved 0,1,2 -> UI 1,2,0
8007E34C sh    v0,CA(s3)
8007ED58 lh    a1,CA(s0)
8007ED5C jal   8007EE00
8007ED60 addiu a3,zero,3
8007ED68 sh    v0,CA(s0)
8007E41C lhu   a0,CA(s0)
8007E424 jal   8007F5FC        ; UI 0,1,2 -> saved 2,0,1
8007E428 andi  a0,a0,7FFF
8007E430 lw    v1,5270(v1)
8007E438 sb    v0,49(v1)
```

The conversion leaves are included in `evidence.asm` and were actually executed
for all three cases. Group 18's help text independently discusses automatic,
semi-automatic, and manual enemy selection. Full combat AI was not executed.

## 5. Camera work

**Verified — Disassembly / execution. Unverified — In-game camera motion.**
Decoded **`4A`: 0=Normal, 1=Leader-Centered**. Group 12 at `35B/362` supplies
these labels; `8007F1C0..8007F1C8` binds M+CC to two choices. Group 19 describes
normal combat camera movement versus concentration on the controlled character.

```text
8007E350 lbu   v0,4A(v1)       ; v1=S
8007E358 sh    v0,CC(s3)
8007ED70 lh    a1,CC(s0)
8007ED74 jal   8007EE00
8007ED78 addiu a3,zero,2
8007ED80 sh    v0,CC(s0)
8007E440 lw    v1,5270(v1)
8007E444 lhu   v0,CC(s0)
8007E44C sb    v0,4A(v1)
```

## 6. Combat motion mode

**Verified — Disassembly / execution (field and two choices).
Unverified — In-game movement/camera behavior and final icon rendering.**
Decoded **`4B`, u8 `0/1`**. Group 13 contains icon-bearing labels rather than
plain English button names: raw first choice is
`8C 80 04 0B 8C 80 0D 00`; second is `Only ` followed by `8C 80 0D 00`.
`400C` is the shared renderer's icon control (`800D9374..800D9378`), which
consumes the following byte and subtracts one at `800D94BC`.
Thus **0 = icon 3 + icon 12; 1 = Only icon 12**. The associated group-20
help text describes Square-button movement mode versus directional-key movement
mode, with Square used to pan in the latter. These support interpreting the
labels as button-plus-direction versus direction-only; the final icon artwork
was not independently rendered in this pass, so the literal token mapping is
preserved here as the exact evidence.

```text
8007E35C lbu   v0,4B(v1)       ; v1=S
8007E364 sh    v0,CE(s3)
8007ED84 lh    a1,CE(s0)
8007ED88 jal   8007EE00
8007ED8C addiu a3,zero,2
8007ED94 sh    v0,CE(s0)
8007E454 lw    v1,5270(v1)
8007E458 lhu   v0,CE(s0)
8007E460 sb    v0,4B(v1)
```

Drawing selects group 13 at `8007F1F8/FC` and binds M+CE at `8007F214..21C`.
This field is a combat movement-control option; no animation-speed encoding is
claimed from the English word “motion.”

## 7. Key customization

**Verified — Disassembly / execution. Unverified — New in-game remapping test.**
Eight **u16** masks at decoded `00..0F`, not just the historical four fields.
Group 15 labels the rows; the getter/setter switches both bound action index
to `0..7`. The following defaults were used as synthetic execution inputs and
also match the first 16 bytes of both extracted resume states.

| Action index | Decoded | Label | Observed default mask |
|---:|---|---|---|
| 0 | `00` | ENTER | `0040` (Cross) |
| 1 | `02` | CANCEL | `0020` (Circle) |
| 2 | `04` | MENU | `0010` (Triangle) |
| 3 | `06` | Movement | `0080` (Square) |
| 4 | `08` | Killer Move 1 | `0004` |
| 5 | `0A` | Killer Move 2 | `0008` |
| 6 | `0C` | Character Quick Change | `0001` |
| 7 | `0E` | Manual/Auto Switch | `0002` |

`8007E898` handles remapping input after shared input processing. It requires
the key-customization page/column and a nonzero low byte at `M+28`; selected
action is `M+C0`. It saves the old mask, clears the selected action, searches
all eight for the requested mask, assigns the old mask to its previous owner,
then sets the selected action. This is a **swap**, not duplicate assignment.

```text
8007E900 lh    a0,C0(s1)
8007E904 jal   80033AE0        ; getter: old assignment
8007E908 move  s0,zero
8007E90C move  a1,zero
8007E910 lh    a0,C0(s1)
8007E914 jal   80033BC8        ; clear selected action
8007E918 move  s2,v0
8007E91C jal   80033AE0
8007E920 move  a0,s0
8007E924 lw    v1,28(s1)       ; requested button mask
8007E928 andi  v0,v0,FFFF
8007E92C bne   v0,v1,8007E93C
8007E930 move  a0,s0
8007E934 jal   80033BC8
8007E938 andi  a1,s2,FFFF      ; give old button to previous owner
8007E93C addiu s0,s0,1
8007E940 slti  v0,s0,8
8007E944 bnez  v0,8007E91C
8007E948 nop
8007E94C lh    a0,C0(s1)
8007E950 lhu   a1,28(s1)
8007E954 jal   80033BC8
8007E958 nop
```

The resident getter begins `80033AE0 sltiu v0,a0,8`, with `lhu` at
`80033B14/2C/44/5C/74/8C/A4/BC` reading S+0/2/4/6/8/A/C/E.
The setter begins `80033BC8 sltiu v0,a0,8`, with matching `sh` stores at
`80033BF8`, `80033C08/18/28/38/48/58/68`. These instructions were executed
for all 64 selected-action/requested-button combinations, including no-op swaps.
The full controller polling/physical-button translation was not emulated.

## 8. Vibration

**Verified — Disassembly / execution. Unverified — Physical motor behavior.**
Decoded **`46`: 0=OFF, 1=ON**. Group 14 names Vibration and group 16 at
`41F/423` contains OFF/ON. Drawing binds M+D2, count 2, at `8007F524..52C`.

```text
8007E368 lbu   v0,46(v1)       ; v1=S
8007E37C sh    v0,D2(s3)       ; constructor call's delay slot
8007EDB8 lh    a1,D2(s0)
8007EDBC jal   8007EE00
8007EDC0 addiu a3,zero,2
8007EDC8 sh    v0,D2(s0)
8007E468 lw    v1,5270(v1)
8007E46C lhu   v0,D2(s0)
8007E474 sb    v0,46(v1)
8007E4A8 lbu   a2,46(v0)       ; v0=S
8007E4B0 lw    a0,5268(a0)     ; controller context; a1=0
8007E4B4 jal   80013F84
8007E4B8 sltu  a2,zero,a2
80013F84 addu  a0,a0,a1
80013F88 jr    ra
80013F8C sb    a2,8(a0)
```

The execution checks verify the controller-context enable byte as well as S+46.
Adjacent S+47/+48 writes in this overlay belong to calibration processing;
they must not be folded into the vibration flag.

## Verification scope and remaining work

Passing checks: **59** real text-pointer lookups; **80** scalar input callback
trials (every legal value, both directions, highlight bit clear/set); **24**
constructor-import/commit/staging/serializer-copy/codec round trips; **64**
button swaps plus getter checks; **72** color-component/corner trials.

The bounded interpreter runs real instructions with branch delay slots and
immediate loads. It hooks UI redraw, upstream input collection, sound feedback,
resource-E lookup, and libc copies explicitly. Scalar commit executes the EXE's
sound/controller setters, then stops before base-object destruction. The color
tests isolate adjustment and packing blocks; scalar round trips verify the
later four-word commit. None of this is a full game boot, GPU render, audio
comparison, motor test, or complete save/load lifecycle run.

All requested **field locations and menu value mappings** are resolved at this
code-evidence level. Remaining checks are live save/reload confirmation and
observable effects, especially the icon-bearing combat motion choices. An
Options-open state would allow checking the current displayed values against M
and S/F directly; it is a concrete optional next validation step, not a blocker
on finding code. No claim is made to have exhausted every unmapped byte in
chunks 1 and 5; the direct Options writer made that unnecessary.

The old raw-options table's `0380` RNG guess is invalid (`0380` is compressed
length), and raw `0382/384/386/388` are not general button offsets. The old
message/audio diff failures do not demonstrate a separate config record.
Decoded offsets and the serializer path above supersede those leads.
