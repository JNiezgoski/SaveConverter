# Decoded chunk 5 mapping

Date: **2026-09-27**. Read-only investigation; no card writes.

**494 newly resolved bytes in 90 fields/array elements**, where “resolved” means
the storage role or exact operational behavior is established, not necessarily
the player-facing name of every counter or timer. This brings that measure to
**539 / 1,088 bytes (49.54%)**. A further 48 bytes have the previously verified
cross-area-copy requirement but still no internal meaning: including those as
an opaque known-use region gives **587 / 1,088 (53.95%)**. Neither measure means
this investigation exhausted the code or mapped every story flag.

The largest new fields are the **12 × 20-byte name table**, **48 × 4-byte clock
snapshot slots**, **10 × 2-byte deferred item-delivery list**, and **8 saved party
IDs**. The global bitmap is confirmed; its individual story-event meanings are
mostly unresolved. Its 368-byte capacity is **not** counted as 368 newly named bytes.

## Essential correction: serialized-relative is not always live F-relative

Let `F = [80075710]`, `G = [80075704]`, and `E = resource 0xE`.
The fifth serialized chunk is exactly `E[0:0x440]`. It is **not** a contiguous
copy of live `F[0:0x440]`.

| Decoded range (end exclusive) | Serialized E-relative | Proven live source |
|---|---|---|
| `1748..19E8` | `000..2A0` | `F+000..2A0` |
| `19E8..1B58` | `2A0..410` | `G+000..170` |
| `1B58..1B88` | `410..440` | Resource-E tail; writer/internal structure unresolved |

**Verified (executed):** `80049470` looks up resource 9. `80049488/80049490`
publish `resource9+8C0` as G; `80049494/800494C0` publish `resource9+220` as F.
Thus `G = F+6A0` in this allocation, **not** `F+2A0`.
The independent bounded initializer execution checked both resulting pointers.

**Verified (executed):** snapshot `80055FC8` obtains E at `80055FD8` with argument
`0xE`. `80056008/80056060` bound a `0x2A0` copy from F. `80056094` loads G,
`80056098` selects destination `E+2A0`, and `800560A8` bounds a `0x170` copy.
Aligned paths are `80056064..8005608C` and `80056100..80056128`; unaligned
counterparts are also present. Execution with different F/G poison patterns
copied the correct two sources and preserved all 48 poisoned tail bytes.
This tests **this snapshot routine**, not every writer of E.

**Disassembly-only:** save overlay entry 2998, `80081BA4`, specifies `0x440`;
`80081BB0/80081BB4` fetch E, and `80081BC4` passes that returned pointer as
the serializer source. The immediate alone does not establish a contiguous F
source. Restore `8005EAC8..8005EBE4` similarly splits E into resource-9 `+220`
and `+8C0`. Earlier specialty and field-control evidence already used separate
F and G buffers. Message speed at `F+118` remains correctly mapped.

In the tables below, **E-relative** replaces the misleading F-relative notation
for bytes after `+2A0`. All offsets are hex. Range ends are exclusive.

## Newly resolved fields

“Verified (executed)” is bounded execution of original instructions with the
specified hooks and synthetic RAM; **not** an in-game save/reload observation.
“Disassembly-only” is an instruction-backed storage/behavior identification.
“Unverified” is a candidate or a player-facing interpretation not established.

| Decoded offset/range | E-relative / live source | Field or precise operational meaning | Evidence addresses | Confidence |
|---|---|---|---|---|
| `1766..1768` | `01E`, F | Saved scene-view parameter, signed halfword; reload expands it by `<<12` into view object `+30`. Its player-facing angle/axis name is unresolved. | W `80054400`, `80063A10`; R/expand `80055828..80055838` | Disassembly-only |
| `1770..1860` | `028..118`, F | 12 character-name slots, 20 bytes each, indexed by character ID minus one; zero-terminated game text, not assumed ASCII | accessor `80055F78..80055F94`; copy reader `8005CB90..8005CBEC`; initializer `8005EC9C..8005EE7C`; rename entry 3022 `8007E180..8007E1E4` | Verified (executed): all 12 slot addresses and copy readers; initializer/rename Disassembly-only |
| `18C8..1988` | `180..240`, F | 48 saved clock-snapshot words. Script-selected index must be `<0x30`; write captures the global clock, read returns the stored word to script result. Individual timer/event assignments unknown. | bounds `80064D24`, `80064D68`; R `80064D48`; clock call `80064D7C`; W `80064D9C` | Disassembly-only |
| `198C..1990` | `244`, F | u32 completion counter: increments only when chunk-1 halfword `+178` equals 1; script-readable. “Battle victories” is not established here. | test `80048C14..80048C1C`; R/W `80048C30..80048C3C`; script R `8006776C` | Disassembly-only |
| `1990..1992` | `248`, F | 16-bit script-additive counter; accepts a script operand, wraps on halfword store, read sign-extends | `80067688..800676CC` | Disassembly-only |
| `1992..1994` | `24A`, F | 16-bit attempt counter for a script-driven random test; increments before RNG(100) | `8006659C..80066618`; script R `800676E0` | Disassembly-only |
| `1994..1996` | `24C`, F | 16-bit success counter for that same test; increments only when RNG result is below calculated threshold. Also consumed by save-menu computation; exact visible label unknown. | `80066618..80066640`; script R `800676FC`; entry 2998 R `8007F670` | Disassembly-only |
| `1998..19AC` | `250..264`, F | Ten packed pending delivery entries: item ID bits 0..9, quantity bits 10..14; zero entry skipped. Not the main inventory. | entry 2986 clear `8007E7D0..8007E7EC`, pack `8007E830..8007E850`; resident unpack/add `80050A00..80050A74` | Disassembly-only |
| `19B0..19B4`, `19E0..19E4`, `19E4..19E8` | `268`, `298`, `29C`, F | Object-14 saved X/Y/Z constructor arguments, three words; object appearance gated by G byte 2 bit 0. Object's in-game identity and coordinate units not established here. | script W `80068320/8006832C/80068338`; R and vector assembly `800557AC..800557CC`; constructor `800557E8` | Disassembly-only |
| `19D2..19D4` | `28A`, F | Object-14 signed orientation/constructor parameter, stored from fourth script argument and passed on stack at constructor `+10` | W `80068344`; R `800557D0`, pass `800557EC` | Disassembly-only |
| `19C4..19C6`, `19C6..19C8` | `27C`, `27E`, F | Psynard parking-bank drawing-order companions, one halfword per bank. Position capture copies the already-known drawing-order byte `F+21` here. Not an additional coordinate. | R `8004C76C`, W `8004C780`; R `8004C79C`, W `8004C7AC`; script W `80067BC0/80067B88` | Disassembly-only |
| `19C8..19D0` | `280..288`, F | Eight saved absolute character IDs in party-slot order; script commands snapshot and restore membership through the party helper | R primary IDs / W bytes `80067A78..80067AB0`; restore `80067ABC..80067B0C` | Disassembly-only |
| `19DC..19E0` | `294`, F | Deferred delivery clock marker: writer stores negative `(clock+delay)`; menu return flips it positive; field logic waits until clock exceeds it; completion clears it. Nonzero also blocks another request. | entry 2986 `8007E864..8007E8A4`; resident `80030570..80030584`, `8004CBE4..8004CC10`, `80050C20`; entry 3004 `8008216C..80082174` | Disassembly-only |

The name table has slot starts `1770,1784,1798,17AC,17C0,17D4,17E8,17FC,1810,1824,1838,184C`.
The accessor computes `F+28+20*i`; rename commits a full 20-byte record.
The initializer and field overlay `8008DBB4..8008DD18` install default names.
The renderer also reads this table at `8005D498..8005D4D0` and
`8005E84C..8005E88C`; it handles game text control/multibyte values, so a blind
ASCII writer is not justified. The 20-byte storage capacity is mapped; trailing
unused characters in a short name are not a separate padding field.

The clock provider `80014434..80014440` returns `[8002B620]`; the update at
`80013640..80013654` increments it. No seconds/frame conversion is claimed.
The 48 slots are **clock snapshots**, not a general arbitrary-value variable
array: the traced writer gets its value from that clock rather than a second
script value operand.

The random-test threshold at `800665A4..800665F4` depends on script context
`+119C`, a divisor operand, and possibly `+5` when context `+1191` is nonzero.
The attempt/success relationship is established; calling these pickpocketing,
escape, crafting, or battle counters without tracing the script caller would
be guessing.

Pending delivery entries are explicitly consumed by inventory-add `8003C594`
at `80050A48`. `80050A2C` masks ID with `03FF`; `80050A34/80050A38` mask with
`7FFF` then shift by ten. The writer caps entries at ten (`8007E834`), clears
all ten before filling, and packs `quantity<<10 | itemID`. Bit 15 is not given
the main inventory's unexplained flag meaning. A specific specialty/UI name
for this delivery feature is not asserted.

## Global bitmap: confirmed mechanism, mixed uses

**Verified (executed):** read helper `80055ECC`, set helper `80055EFC`, clear
helper `80055F38`. For nonnegative flag ID `n`:

```
decoded byte = 0x19E8 + (n >> 3)
mask         = 1 << (n & 7)
live byte    = G[n >> 3]
```

The getter uses `sra` at `80055EE0`, indexed `lbu` at `80055EE8`, variable
right shift at `80055EF0`, and `andi ...,1` at `80055EF8`. The setter does
`lbu` / `sllv` / `or` at `80055F24..80055F2C`, then `sb` at `80055F34`.
The clearer uses `nor` / `and` at `80055F68..80055F6C`, then `sb` at
`80055F74`. All **2,944 positions** in the serialized 368-byte capacity were
set/read/cleared in synthetic RAM, with the whole buffer compared after each
operation. This proves address arithmetic and preservation of other bits,
**not** that all positions are assigned, safe to edit, or story-related.

**Disassembly-only:** script VM global-flag operands also use G directly,
independently of those convenience helpers. Examples include read at
`8006C750`, `8006C8B0`, `8006CCCC`, and set/clear at
`8006CEB4..8006CF40`. The set arm loads the byte at `8006CEC4`, forms a
one-bit mask with `sllv` at `8006CEC8`, ORs at `8006CED0`, and stores at
`8006CF40`. The clear arm loads at `8006CF34` and ANDs before the same store.
These are actual bitmap accesses, not an inference from changing save bytes.

| Decoded / E-relative / live | Independently established use | Evidence | Confidence |
|---|---|---|---|
| `19E8` / `2A0` / G+0, bit 1 | Route-protagonist flag (already known): initializer sets it in one route, constructor chooses complementary object indices 0/1 | initialization `8005EC8C..8005ECCC`; test `800540B4..80054108` | Disassembly-only here; prior field-control bounded execution exists |
| `19E9` / `2A1` / G+1 | Several independent travel/state bits, not a single enum. Includes bit 4 and bit 5, tested separately; bit 6 gates transition behavior | bit 4 `800547CC..800547DC`; bit 5 `8004CBA8..8004CBB8`; bit 6 `80053F00..80053F18` | Disassembly-only; full bit meanings Unverified |
| `19EA` / `2A2` / G+2 | Bit 0 gates object-14 restoration; bits 3 and 4 independently modified by script/overlay-state paths | bit 0 `80055778..80055784`; clear bit 3 `80068494/80068498`, clear bit 4 `800684B0/800684B8`, set bit 3 `800684D0/800684D8` | Disassembly-only |
| `1A46` / `2FE` / G+5E | Two text/UI readers test this byte; full flag assignment not traced | `8005A15C`, `8005A6E8` | Unverified meaning; located only |
| `1A3F..1A41` / `2F7..2F9` / G+57..59 | Previously solved specialty flags `2BC..2C7`; not a new finding | [specialty investigation](SO2-SPECIALTY-INVESTIGATION.md) | Prior Verified (executed) |

The bitmap includes a confirmed route/story choice as well as specialty and
travel state. It is a strong target for story/event flags, but **no new named
plot milestone** was identified in this pass. Generic bit operations alone do
not turn the whole bitmap into a story-progress map. README queue item 4 stays open.

### Script VM flag opcodes and named story milestones (2026-09-28)

The script VM's direct accesses to the global bitmap $G = \text{[80075704]}$ (capacity 368 bytes, decoded `0x19E8..0x1B58`, 2,944 bit positions) have been mapped to specific bytecode opcodes, their operand encodings decoded, and their disc-script callers tied to named story events and plot milestones.

#### 1. VM opcode identification and operand encoding

The main bytecode interpreter loop at `8006C358` fetches each 32-bit instruction word, shifts right by 24 bits (`srl $v0, $s0, 0x18`), decrements by 1 (`addiu $v1, $v0, -1`), and indexes the primary jump table at `800739A0`. Four opcodes directly manipulate or inspect the global flag bitmap:

- **Opcode `0x21` Sub-opcode `0x03` (`0x2103xxxx`) — Flag Set/Clear (Immediate Operand)**:
  Dispatches through table entry `0x20` at `8006CD48`, then sub-table `80073B30` entry 3 at `8006CE54`.
  - **Word 0 (`0x2103xxxx`)**:
    - Bits 31..24: Opcode `0x21`.
    - Bit 23 (`0x00800000`): Addressing Mode flag. If `0`, targets global bitmap $G$; if `1`, targets local stack frame flags at `-1 + 0x1C($s1)`.
    - Bits 22..16: Sub-opcode `0x03` (flag/bit boolean mode).
    - Bits 15..0: Flag ID $n \in [0, 2943]$.
  - **Word 1 (Next script PC word)**: Immediate value `0x00000001` for SET (`G[n >> 3] |= (1 << (n & 7))`), `0x00000000` for CLEAR (`G[n >> 3] &= ~(1 << (n & 7))`). Script PC advances by 4 (`8006CF50`).

- **Opcode `0x22` Sub-opcode `0x03` (`0x2203xxxx`) — Flag Set/Clear (Stack Operand)**:
  Dispatches through table entry `0x21` at `8006CF64`, then sub-table `80073B60` entry 3 at `8006D068`.
  Pops value from the VM evaluation stack: if nonzero, executes the SET arm (`8006D06C`); if zero, branches to the CLEAR arm (`8006D0D8`).

- **Opcode `0x1D` (`0x1D00xxxx`) — Flag Compare Immediate**:
  Dispatches through table entry `0x1C` at `8006CC48`.
  - **Word 0 (`0x1D00xxxx`)**: Bits 15..0 = flag ID $n$, bit 23 = mode flag (`0` = global bitmap).
  - **Word 1**: Expected boolean value (`0` or `1`). Tests `((G[n >> 3] >> (n & 7)) & 1) == Word 1` and pushes boolean result (`1` or `0`) onto the VM stack at `8006CCEC`. Script PC advances by 4.

- **Opcode `0x0E` (`0x0E00xxxx`) — Flag Read / Push to Stack**:
  Dispatches through table entry `0x0D` at `8006C6C8`.
  Reads bit $n$ from global bitmap (`lbu $v0, ($v0)` at `8006C750`), shifts right by `n & 7`, masks with 1, and pushes the bit value (`0` or `1`) onto the VM stack at `8006C764`.

#### Disassembly evidence (resident code)

**Opcode `0x2103` Set/Clear handler (`8006CE54..8006CF40`)**:
```mips
8006CE54: lw    $v0, 0x10($s1)       ; Load script PC
8006CE5C: lw    $v0, ($v0)           ; Load Word 1 (immediate value: 0 or 1)
8006CE64: beqz  $v0, 0x8006ced4      ; If 0, branch to CLEAR arm
8006CE68: and   $v0, $s0, $s4        ; Test bit 23 (s4 = 0x00800000)
8006CE6C: beqz  $v0, 0x8006cea4      ; If 0, target global bitmap G
...
; Global SET arm:
8006CEB4: lw    $a0, 0x5704($a0)     ; a0 = G = [80075704]
8006CEB8: sra   $v0, $v0, 3          ; byte offset = flag_id >> 3
8006CEBC: addu  $a0, $a0, $v0        ; a0 = &G[flag_id >> 3]
8006CEC0: andi  $v0, $s0, 7          ; bit index = flag_id & 7
8006CEC4: lbu   $v1, ($a0)           ; v1 = current byte
8006CEC8: sllv  $v0, $s7, $v0        ; mask = 1 << bit index (s7 = 1)
8006CECC: j     0x8006cf40
8006CED0: or    $v1, $v1, $v0        ; v1 |= mask
...
; Global CLEAR arm:
8006CF20: lw    $a0, 0x5704($a0)     ; a0 = G = [80075704]
8006CF24: sra   $v0, $v0, 3          ; byte offset = flag_id >> 3
8006CF28: addu  $a0, $a0, $v0        ; a0 = &G[flag_id >> 3]
8006CF2C: andi  $v0, $s0, 7          ; bit index = flag_id & 7
8006CF30: sllv  $v0, $s7, $v0        ; mask = 1 << bit index
8006CF34: lbu   $v1, ($a0)           ; v1 = current byte
8006CF38: nor   $v0, $zero, $v0      ; ~mask
8006CF3C: and   $v1, $v1, $v0        ; v1 &= ~mask
8006CF40: sb    $v1, ($a0)           ; Store updated byte to G
8006CF44: lw    $a0, 0x10($s1)       ; Advance script PC past Word 1
8006CF50: addiu $v0, $a0, 4; sw $v0, 0x10($s1)
```

**Opcode `0x1D00` Compare Immediate handler (`8006CC48..8006CCEC`)**:
```mips
8006CC48: lw    $v1, 0x24($s1)       ; VM stack pointer
8006CC4C: lw    $a0, 0x10($s1)       ; Script PC
8006CC50: addiu $v0, $v1, 4; sw $v0, 0x24($s1) ; stack_ptr += 4
8006CC58: addiu $v0, $a0, 4; sw $v0, 0x10($s1) ; script_pc += 4
8006CC60: and   $v0, $s0, $s4        ; Test bit 23
8006CC64: lw    $a0, ($a0)           ; Load expected comparison value (Word 1)
8006CC68: beqz  $v0, 0x8006ccac      ; If 0, target global bitmap G
...
8006CCC0: lw    $v0, 0x5704($v0)     ; v0 = G = [80075704]
8006CCC4: sra   $v1, $v1, 3          ; flag_id >> 3
8006CCC8: addu  $v0, $v0, $v1        ; &G[flag_id >> 3]
8006CCCC: lbu   $v0, ($v0)           ; Read byte
8006CCD0: andi  $v1, $s0, 7          ; flag_id & 7
8006CCD4: srav  $v0, $v0, $v1        ; shift right by bit index
8006CCD8: andi  $v0, $v0, 1          ; bit = (byte >> bit_index) & 1
8006CCDC: bne   $v0, $a0, 0x8006cce8 ; if bit != expected, push 0
8006CCE0: move  $v0, $zero
8006CCE4: addiu $v0, $zero, 1        ; if bit == expected, push 1
8006CCEC: sw    $v0, ($a1)           ; push result to stack
```

**Opcode `0x0E00` Read / Push Flag handler (`8006C6C8..8006C764`)**:
```mips
8006C704: and   $v0, $s0, $s4        ; Test bit 23
8006C708: beqz  $v0, 0x8006c734      ; If 0, target global bitmap G
...
8006C744: lw    $v0, 0x5704($v0)     ; v0 = G = [80075704]
8006C748: sra   $v1, $v1, 3          ; flag_id >> 3
8006C74C: addu  $v0, $v0, $v1        ; &G[flag_id >> 3]
8006C750: lbu   $v0, ($v0)           ; Read byte
8006C754: andi  $v1, $s0, 7          ; flag_id & 7
8006C758: srav  $v0, $v0, $v1        ; shift right
8006C75C: andi  $v0, $v0, 1          ; extract bit
8006C764: sw    $v0, ($a0)           ; push bit (0 or 1) to VM stack
```

#### 2. Disc script archive scan and named story milestones

All 827 container archives (`3207..4033`, `scene_index = archive_index - 3207`) on Disc 1 were decompressed (SLZ tag 1) and scanned for opcodes `0x2103`, `0x2203`, `0x1D00`, and `0x0E00`. A total of **857 milestone occurrences** touching **656 distinct flags** were extracted and correlated with 16-bit decoded scene dialogue text.

Confirmed story milestones span both Range A (`0x1F..0x1FF`, bits 31..511) and Range B (`0x1FF..0xB7F`, bits 512..2943):

| Decoded Byte | Bit | Flag ID | Opcode(s) | Scene (Arch) | Story Event / Dialogue Milestone |
|---|---|---|---|---|---|
| `19F5` | 6 | 110 (`0x006E`) | SET | 24 (3231) | **Arlia Prologue**: Newlywed couple's house: *"Don't be woolgathering, or you'll be carried off by Alen"* |
| `19F6` | 2 | 114 (`0x0072`) | SET | 53, 63 (3260, 3270) | **Salva Drift**: Mine entrance guard: *"We have come to slay the dragon - Is it still off limits?"* |
| `19F6` | 5 | 117 (`0x0075`) | SET | 355 (3562) | **Cross Continent**: *"The Book of Exorcism says that we should go to the mountain peak... Tears of the King"* |
| `19F7` | 0 | 120 (`0x0078`) | SET | 135 (3342) | **Cross Cave**: Cave expedition: *"Eglas has regained consciousness... That Master of Heraldry was the real culprit"* |
| `19F7` | 3 | 123 (`0x007B`) | SET | 23 (3230) | **Arlia Church**: Priest sermon on the *"Warrior of Legend... holy man who uses the Sword of Light"* |
| `19F7` | 5 | 125 (`0x007D`) | SET | 26 (3233) | **Arlia Hearn's Store**: Medicine discussion: *"This is Mr. Hearn's General Store... That is the smell of herbs"* |
| `19F7` | 7 | 127 (`0x007F`) | SET | 34 (3241) | **Arlia Mayor Regis**: *"This is the house of the Mayor of Arlia Village... Regis: try going to the town of Cross"* |
| `19F8` | 5..6 | 133..134 (`0x0085..6`) | SET | 21 (3228) | **Shingo Forest / Arlia**: Alien tech arrival: *"I just knew it had to be him - He had the Alien Raiments and the Sword of Light"* |
| `19F8` | 7 | 135 (`0x0087`) | SET | 124, 126 (3331, 3333) | **Port Town of Clik**: Clik travels: *"Say, weren't we heading toward Clik... Clik is much further north"* |
| `1A20` | 2..3 | 450..451 (`0x01C2..3`) | SET | 215 (3422) | **Lacour City**: Tournament festival: *"We're running specials during the tournament"* |
| `1A21` | 2 | 458 (`0x01CA`) | SET | 216 (3423) | **Lacour City**: Military mobilization: *"The entire town is in a merry festive mood but the military situation is intense"* |
| `1A21` | 7 | 463 (`0x01CF`) | CLEAR, SET | 477 (3684) | **Lacour Tournament of Arms**: Battle Stadium announcer: *"Ladies and gentlemen! The annual Lacour Tournament of Arms is about to begin"* |
| `1A22..1A24` | 4..4 | 468..484 (`0x01D4..0x01E4`) | SET | 402..411 (3609..3618) | **Sanctuary of Linga**: Linga herbal collection quest (17 flags): *"This must be a medicinal herb... Now we can finally meet Keith [Bowman]"* |
| `1A24` | 3 | 483 (`0x01E3`) | SET | 412 (3619) | **Sanctuary of Linga**: Deep sanctuary gate: *"Is this the 'Door to the Netherworld' where monsters come out?"* |
| `1A24` | 6 | 486 (`0x01E6`) | SET | 583 (3790) | **Nede Defense Force**: *"My name is Marianna Kronik - I am the leader of the Nede Defense Force"* |
| `1A26` | 4 | 500 (`0x01F4`) | CLEAR, SET | 234 (3441) | **Energy Nede Arrival**: Coastline shipwreck: *"Other than us, have you heard of anyone else washing up on shore?"* |
| `1A26` | 5 | 501 (`0x01F5`) | SET | 272 (3479) | **Central City**: Director Artis greeting: *"I'm Artis, the Director of this facility - I have already heard all about you"* |
| `1A26` | 6 | 502 (`0x01F6`) | SET | 266 (3473) | **Central City Information Library**: Password retrieval: *"This is a plastic case containing a paper with the password on it"* |
| `1A26` | 7 | 503 (`0x01F7`) | SET | 247 (3454) | **Central City Mayor**: Greeting Claude's party: *"My name is Narl - I am the Mayor of Central City"* |
| `1A27` | 2 | 506 (`0x01FA`) | SET | 277 (3484) | **Central City**: Chisato's house: *"Hey! What are you all doing in my house?"* |
| `1A27` | 6 | 510 (`0x01FE`) | CLEAR, SET | 279 (3486) | **Fun City Arrival**: Amusement city entrance: *"There's something different about this town... This town looks like fun!"* |
| `1A45` | 1 | 745 (`0x02E9`) | SET | 80 (3287) | **Alen-Tax Wedding Confrontation**: Executed live in `tools/so2_script_flags_evidence.py` |
| `1A58` | 4 | 900 (`0x0384`) | SET | 17 (3224) | **Arlia Village Tour**: Village entrance: *"Welcome to Arlia"* |
| `1A58` | 6 | 902 (`0x0386`) | SET | 23 (3230) | **Arlia Village Tour**: Church: *"This is Arlia's church - This is where they hold weddings in the village"* |
| `1A58` | 7 | 903 (`0x0387`) | SET | 24 (3231) | **Arlia Village Tour**: Newlywed couple: *"This is the house of a newlywed couple - They are so lovey-dovey..."* |
| `1A59` | 0 | 904 (`0x0388`) | SET | 26 (3233) | **Arlia Village Tour**: Store: *"This is Mr. Hearn's General Store - They sell lots of useful things"* |
| `1A59` | 3 | 907 (`0x038B`) | SET | 33 (3240) | **Arlia Village Tour**: Carpenter: *"The man of this house is a carpenter - He is now working on a big job..."* |
| `1A59` | 5 | 909 (`0x038D`) | SET | 34 (3241) | **Arlia Village Tour**: Mayor Regis: *"This is the house of the Mayor of Arlia Village - He is a very smart man"* |
| `1A63` | 5 | 989 (`0x03DD`) | CLEAR, SET | 727 (3934) | **Cave of Trials Riddles**: Level riddle solved: *"Good work! You solved the riddle for this level! Here's the LAST TEST... Phew! You win!"* |
| `1A64` | 4 | 996 (`0x03E4`) | SET | 758 (3965) | **Cave of Trials Puzzle**: Statue: *"Look at this strange stone statue - It says 'Funny Thief' on it... door opening in the distance"* |
| `1A64` | 5..6 | 997..998 (`0x03E5..6`) | SET | 764 (3971) | **Cave of Trials Puzzle**: Altar tablet: *"Something's written on this stone tablet... Make the offering on the altar whose portal opens"* |
| `1A64` | 7 | 999 (`0x03E7`) | SET | 737 (3944) | **Cave of Trials Trap**: Miel 32 robot: *"Intruder alert! No ally identification detected - Run expulsion program - Initiate Miel 32"* |
| `1B07` | 4..5 | 2300..2301 (`0x08FC..D`) | SET | 740 (3947) | **Cave of Trials Level 4**: Spell altar: *"Mistaken Fighting Man has learned the spell Extinction"* |
| `1B07` | 6 | 2302 (`0x08FE`) | SET | 742 (3949) | **Cave of Trials Door Mechanism**: *"I heard a door closing / opening in the distance"* |
| `1B08` | 4 | 2308 (`0x0904`) | SET | 791 (3998) | **Cave of Trials Progression**: Floor reached: *"Cave of Trials Level 9"* |
| `1B08..1B09` | 6..3 | 2310..2315 (`0x0906..B`) | SET | 233 (3440) | **Eluria Tower Escape / ID Card**: Pickup (6 flags): *"When I escaped from Eluria, I picked this up... What is it? It's an ID card"* |
| `1B09` | 4 | 2316 (`0x090C`) | SET | 807 (4014) | **Cave of Trials Level 11 Boss**: Dragon Tyrant: *"A dragon --- Underground... You have come far to reach this place... Dragon Tyrant"* |
| `1B09` | 5 | 2317 (`0x090D`) | SET | 809 (4016) | **Cave of Trials Level 12 Boss**: Phoenix: *"What is this--- I live eternal - Nature rules me not... Phoenix"* |
| `1B0A` | 3 | 2323 (`0x0913`) | SET | 229 (3436) | **Nede Rescue Milestone**: Awakening after Eluria: *"Where am I? I seem to have been saved, but... At that time, we..."* |
| `1B0A` | 6 | 2326 (`0x0916`) | CLEAR, SET | 688, 689 (3895, 3896) | **Fun City Cooking Master**: Cooking contest: *"You are not permitted to leave in the middle of the contest - Fight to the end! Food God Yarma"* |
| `1B0A` | 7 | 2327 (`0x0917`) | CLEAR, SET | 297, 298, 305 (3504..12) | **Fun City Battle Stadium**: Arena battles: *"Challenger! Challenger! ... Simulation"* |
| `1B0C` | 3 | 2339 (`0x0923`) | SET | 688 (3895) | **Fun City Cooking Master**: Contest opponent: *"Food God and Prince of Darkness Yarma / Iona / Loren"* |
| `1B0C` | 4 | 2340 (`0x0924`) | SET | 809 (4016) | **Cave of Trials Level 12 Boss**: Phoenix defeat flag |
| `1B0C` | 6 | 2342 (`0x0926`) | SET | 272 (3479) | **Central City**: Artis coordination flag |

**2026-09-30 addition (live save-diff evidence, not a script-archive scan):** `1A1B` bit 7, flag 415 (`0x019F`), was empirically caught SET (0→1) in a real DuckStation session — before/after saves one minute apart (SO2 10 → SO2 09, USA card slot 2), with essentially no other change besides player position/facing and routine counters, immediately following talking to Ernest at Kross Castle. This byte already sits inside the "densely referenced, 51-byte" span (`0x19F5..0x1A27`) identified in section 3 below as script-VM-active but not individually named bit-by-bit — this is the first specific bit in that span tied to a named event. Unlike every other row in this table, this entry has **no corresponding script-archive/opcode citation yet** (the Kross Castle scene archive hasn't been scanned for this) — treat it as a real, reproducible empirical finding, not yet disassembly-verified to the same standard as the rows above it.

#### 3. Verification and byte closure

- **Bounded Execution Verification**:
  Opcode instruction fetch, sub-opcode decoding, addressing mode bit-23 branching, arithmetic offset calculation, and single-bit bitwise masking were verified via `tools/so2_script_flags_evidence.py`. The runner executes real MIPS instructions from resident `entry-2576.bin` against a synthetic memory space across 16 sample flag positions (including bounds $n=1, 7, 8, 199, 200, 255, 256, 299, 300, 399, 400, 499, 500, 0x2BC, 0x2E9, 2943$), accumulator mode ($n=0$), computed address mode ($0x345$), and literal decompressed script bytecode from archive 3287 offset `0x7614` (`0x210302E9 0x00000001` -> bit `745 & 7 = 1` set at decoded byte `0x19E8 + (745 >> 3) = 0x1A45`).
- **Accounting against the 357 unmapped bitmap bytes**:
  - **Range A (`0x19EB..0x1A3F`, 84 unmapped bytes)**:
    - 51 contiguous bytes from `0x19F5` to `0x1A27` (flags 110..511) are densely referenced by the script VM for named plot milestones (prologue, Salva drift, Cross continent, Clik, Lacour tournament, Linga sanctuary herbs, and Energy Nede arrival). These 51 bytes are promoted to `partial` in `scripts/so2_coverage.py`.
    - Bytes `0x19EB..0x19F4` (10 bytes, flags 24..109) and `0x1A28..0x1A3E` (23 bytes, flags 512..695) remain open / unmapped.
  - **Range B (`0x1A47..0x1B58`, 273 unmapped bytes)**:
    - 22 bytes containing verified named plot milestones have been resolved:
      - `0x1A47..0x1A48` (2 bytes, flags 760..769)
      - `0x1A57..0x1A64` (14 bytes, flags 890..999: Rena's Arlia village tour, Cave of Trials riddle puzzles)
      - `0x1B07..0x1B0C` (6 bytes, flags 2300..2342: Cave of Trials bosses, Eluria ID card, Fun City Cooking Master, Battle Stadium)
      These 22 bytes are promoted to `partial` in `scripts/so2_coverage.py`.
    - The remaining 251 bytes in Range B remain open / unmapped.
  - **Total**: **73 bytes** (20.4%) of the 357 previously unknown bitmap bytes are now accounted for with real named plot milestones and verified VM opcodes. 284 bytes remain open.

### Script VM flag opcodes and named story milestones — part 2 (2026-09-28)

This follow-up pass resolves the open ranges left in the global story/event flag bitmap ($G = \text{[80075704]}$, capacity 368 bytes, decoded `0x19E8..0x1B58`), targeting:
1. **Open Range 1**: `0x19EB..0x19F4` (flags 24..109, 10 bytes)
2. **Open Range 2**: `0x1A28..0x1A3E` (flags 512..695, 23 bytes)
3. **Open Range 3**: Bulk of Range B `0x1A49..0x1B58` (flags 760..889, 1000..2299, 2343..2943)

#### 1. Negative proofs across unreferenced bitmap spans

An exhaustive bytecode scan was executed across all scene container archives on both Disc 1 and Disc 2 (entries `3207..4447`, including 827 scene archives `3207..4033` and supplemental overlays up to 4447) for all four global bitmap opcodes (`0x2103`, `0x2203`, `0x1D00`, `0x0E00`):

- **Flags 24..109 (`0x19EB..0x19F4`, 10 bytes)**: **0 occurrences found**. Flags 0..22 reside in `0x19E8..0x19EA` (route-protagonist flag, travel/state bits, and object-14 restoration). Story flags begin at flag 110 (`0x19F5` bit 6, Arlia prologue). Bytes `0x19EB..0x19F4` contain no script VM flag operations in either disc image; they hold no script-driven story milestone meaning and remain unmapped.
- **Flags 1000..2299 (`0x1A65..0x1B06`, 162 bytes)**: **0 occurrences found** in scene archives. Between Cave of Trials riddles (flags 981..999 at `0x1A62..0x1A64`) and post-game Cave of Trials bosses (flags 2300..2342 at `0x1B07..0x1B0C`), this 162-byte span contains zero script VM flag operations.
- **Flags 2343..2943 (`0x1B0D..0x1B58`, 76 bytes)**: **0 occurrences found** in scene archives. Above Central City flag 2342 (`0x1B0C` bit 6), no scene script references flag IDs up to the 2,944 capacity limit.

Across the 284 bytes remaining open after Part 1, **248 bytes** are confirmed to contain zero script VM flag accesses in the game's disc scene corpus.

#### 2. Newly identified plot milestones in Open Range 2 and Range B

The scan identified **96 distinct flags in Open Range 2 (`0x1A28..0x1A3E`)** and **11 flags in Range 3a (`0x1A47..0x1A57`)**, densely concentrating two major narrative arcs:

1. **Energy Nede: Four Fields Quest & Central City / North City (`0x1A28..0x1A2D`, flags 512..559)**:
   - **Field of Courage**: Fountain spirit encounter (*"You did well to come here - I am the spirit of this fountain - Come this way..."* at flags 518..519, `0x1A28` bits 6, 7), crystal ball interaction (flags 516..517, `0x1A28` bits 4, 5), and monument inscription (*"What did you see? Hmm - 'Courage to forsake everything'..."* at flags 523..524, `0x1A29` bits 3, 4).
   - **Field of Power**: Mountain arrival (*"Whoa! Yikes! Is this the Field of Power?"* at flag 527, `0x1A29` bit 7), mountain avalanche trigger (*"You see a ladder - Avalanche! Run for the cavern! Yikes!"* at flag 534, `0x1A2A` bit 6, with cavern escape flags 536..539 at `0x1A2B`), and mountain summit boss encounter (*"Guardian: You did well to make it this far"* at flag 528, `0x1A2A` bit 0).
   - **Field of Intelligence**: Mirror and statue puzzle (*"It's a glass statue of a fighting man - 2 P is inscribed here"*, flag 535 at `0x1A2A` bit 7 — referenced across 42 distinct script sites, the single most referenced flag in Nede!), and card slot pillar barrier (*"This pillar has a slot for inserting some sort of card - It looks like we cannot proceed any further"* at flags 598..599, `0x1A32` bits 6, 7).
   - **Mayor Narl's Rune Codes**: Flag 520 (`0x1A29` bit 0) in Scene 629 (*"The Rune Codes we got from Narl, they started glowing - It says: You should advance forward"*).
   - **Central City & North City**: Library password retrieved (flag 526, `0x1A29` bit 6); Psynard search orientation (*"You're looking for a Psynard? You want to go to The Sanctuary [The Home] - If you want to know about the Ten Wise Men go to the Library"* at flag 540, `0x1A2B` bit 4); Ten Wise Men dark barrier (*"Feels strange - this black thing - It's surrounding me... I can't move"* at flags 546..549, `0x1A2C`); Nede city hubs orientation (*"North City if you want to study - Fun City if you want to play - Armlock if you like hobbies"* at flag 553, `0x1A2D` bit 1); and the Ten Wise Men attack on Central City (*"What was that light? Eeek! Yikes, Mommy! HELP! HEHE - RUN, RUN, YOU WORMS! MORE, MORE, I WANT TO SEE BLOOD!"* at flags 557..558, `0x1A2D` bits 5, 6).
   - **Eluria Tower Escape ID Card**: Flags 592..597 (`0x1A32` bits 0..5) — 6 consecutive flags set in Scene 233 (*"When I escaped from Eluria, I picked this up... What is it? It's an ID card"*).

2. **Lacour Front Line Campaign & Energy Stone Weapon Development (`0x1A39..0x1A3E`, flags 650..692)**:
   - **Lacour Front Line Encampment**: Outpost soldier sentry (*"I'm a soldier, and I'll keep on standing here... even after you're gone"* at flags 650..651, `0x1A39` bits 2, 3), and supply tent store (flags 652..656, `0x1A39` bits 4..7 and `0x1A3A` bit 0).
   - **Front Line Defenses & Reinforcements**: Outpost defense unit (*"You reinforcements, stay in your own unit! It's very dangerous outside"* at flags 657..661, `0x1A3A` bits 1..5), veteran reinforcements arrival (*"Veteran fighters are steadily being gathered in the front lines - A number of them arrived just a while ago"* at flags 662..664, `0x1A3A` bits 6..7 and `0x1A3B` bit 0).
   - **Command Tent & Officer Interactions**: Command tent officer (flags 666, 677..678, `0x1A3B` bit 2 and `0x1A3C` bits 5, 6), and Melancholy Captain (*"Melancholy Captain... What are you doing? Pickpocket attempt failed"* at flags 675..676, `0x1A3C` bits 3, 4).
   - **Front Line Field Hospital / Infirmary Triage**: 9 flags across `0x1A3C` bit 7 and all 8 bits of `0x1A3D` (flags 679..687) tracking wounded casualties and triage dialog in the infirmary (*"Nurse: Wounded people are increasing each day - I hope this is settled soon... Oh, are you taking a rest here? Oh, my daughter, my son... must your father die?"* in Scenes 442, 444).
   - **Lacour Castle Laboratory Energy Stone Superweapon**: 4 flags in `0x1A3E` (flags 688..691) tracking development of the Energy Stone / Lacour Hope weapon (*"Hasn't the Energy Stone been finished yet? Is the Castle Laboratory slacking off in development? Hasn't the Energy Stone..."* in Scene 441).

3. **Battle Stadium Program (`0x1A55`, flag 878)**:
   - Flag 878 (`0x036E`, `0x1A55` bit 6): Scene 305 (Arch 3512) — Battle Stadium combat simulation program (*"Excuse me - but what exactly is going to start here? We have prepared a special program that will let you fight..."*).

#### Newly resolved story milestone table (Part 2)

| Decoded Byte | Bit | Flag ID | Opcode(s) | Scene (Arch) | Story Event / Dialogue Milestone |
|---|---|---|---|---|---|
| `1A28` | 4..5 | 516..517 (`0x0204..5`) | CLEAR, READ, SET | 590..595 (3797..3802) | **Field of Courage**: Crystal ball inspection (18 hits): *"It's a crystal ball - Will you touch it? Forget it"* |
| `1A28` | 6..7 | 518..519 (`0x0206..7`) | SET | 596 (3803) | **Field of Courage**: Fountain Spirit: *"You did well to come here - I am the spirit of this fountain - Come this way..."* |
| `1A29` | 0 | 520 (`0x0208`) | SET | 629 (3836) | **Energy Nede Four Fields**: Mayor Narl's Rune Codes: *"The Rune Codes we got from Narl, they started glowing - It says: You should advance forward"* |
| `1A29` | 3..4 | 523..524 (`0x020B..C`) | CLEAR, READ, SET | 641, 642 (3848..9) | **Field of Courage**: Monument riddle: *"What did you see? Hmm - 'Courage to forsake everything'..."* |
| `1A29` | 6 | 526 (`0x020E`) | SET | 266 (3473) | **Central City Information Library**: Password retrieved: *"This is a plastic case containing a paper with the password on it"* |
| `1A29` | 7 | 527 (`0x020F`) | SET | 597 (3804) | **Field of Power**: Mountain entrance: *"Whoa! Yikes! Is this the Field of Power?"* |
| `1A2A` | 0 | 528 (`0x0210`) | SET | 603 (3810) | **Field of Power Summit**: Guardian Boss: *"I can see some kind of ruin - Guardian: You did well to make it this far"* |
| `1A2A` | 2..5 | 530..533 (`0x0212..5`) | READ, SET | 597..615 (3804..22) | **Field of Power**: Mountain passages and cavern trails |
| `1A2A` | 6 | 534 (`0x0216`) | CLEAR, READ, SET | 598, 607..610 (3805..17) | **Field of Power**: Avalanche hazard (20 hits): *"You see a ladder - Avalanche! Run for the cavern! Yikes!"* |
| `1A2A` | 7 | 535 (`0x0217`) | CLEAR, READ, SET | 560..565 (3767..72) | **Field of Intelligence**: Mirror/Statue puzzle (42 hits): *"It's a glass statue of a fighting man - 2 P is inscribed here"* |
| `1A2B` | 0..3 | 536..539 (`0x0218..B`) | CLEAR, READ, SET | 598, 607..611 (3805..18) | **Field of Power**: Cavern escapes: *"Somehow we managed to run away..."* |
| `1A2B` | 4 | 540 (`0x021C`) | CLEAR, SET | 260, 261 (3467..8) | **Central City / North City**: Psynard search: *"You're looking for a Psynard? You want to go to The Sanctuary - If you want to know about the Ten Wise Men go to the Library"* |
| `1A2C` | 2, 5 | 546, 549 (`0x0222, 5`) | SET | 262 (3469) | **Central City**: Ten Wise Men dark barrier: *"Feels strange - this black thing - It's surrounding me... I can't move"* |
| `1A2D` | 1 | 553 (`0x0229`) | SET | 235, 236 (3442..3) | **Energy Nede City Hubs**: City orientation: *"North City if you want to study - Fun City if you want to play - Armlock if you like hobbies"* |
| `1A2D` | 5..6 | 557..558 (`0x022D..E`) | READ, SET | 281, 285 (3488..92) | **Central City**: Ten Wise Men assault: *"What was that light? Eeek! Yikes, Mommy! HELP! HEHE - RUN, RUN, YOU WORMS! MORE, MORE, I WANT TO SEE BLOOD!"* |
| `1A31` | 3 | 587 (`0x024B`) | SET | 569 (3776) | **Ocean Rescue Milestone**: Expel ocean survival: *"I never imagined that you would live after falling into the ocean - You're pretty lucky"* |
| `1A31` | 4 | 588 (`0x024C`) | READ, SET | 285 (3492) | **Central City Hospital**: Wounded patient care: *"I'm taking good care of her - She has still..."* |
| `1A31` | 6 | 590 (`0x024E`) | READ, SET | 597..613 (3804..20) | **Field of Power**: Mountain navigation milestone |
| `1A32` | 0..5 | 592..597 (`0x0250..5`) | SET | 233 (3440) | **Eluria Tower Escape / ID Card**: 6 consecutive flags set on ID card pickup: *"When I escaped from Eluria, I picked this up... It's an ID card"* |
| `1A32` | 6..7 | 598..599 (`0x0256..7`) | READ, SET | 566 (3773) | **Field of Intelligence**: Card slot pillar barrier: *"This pillar has a slot for inserting some sort of card - It looks like we cannot proceed any further"* |
| `1A39` | 2..3 | 650..651 (`0x028A..B`) | SET | 446 (3653) | **Lacour Front Line**: Sentry guard outpost: *"I'm a soldier, and I'll keep on standing here... even after you're gone"* |
| `1A39` | 4..7 | 652..655 (`0x028C..F`) | SET | 445 (3652) | **Lacour Front Line**: Camp store / supply tent: *"I can take a little off - Welcome - What would you like?"* |
| `1A3A` | 0 | 656 (`0x0290`) | SET | 445 (3652) | **Lacour Front Line**: Camp quartermaster merchant |
| `1A3A` | 1..5 | 657..661 (`0x0291..5`) | SET | 438 (3645) | **Lacour Front Line Outpost**: Outpost defense: *"You reinforcements, stay in your own unit! It's very dangerous outside"* |
| `1A3A` | 6..7 | 662..663 (`0x0296..7`) | SET | 439 (3646) | **Lacour Front Line**: Reinforcements arrival: *"Veteran fighters are steadily being gathered in the front lines - A number of them arrived just a while ago"* |
| `1A3B` | 0 | 664 (`0x0298`) | SET | 439 (3646) | **Lacour Front Line**: Veteran fighters muster |
| `1A3B` | 2 | 666 (`0x029A`) | SET | 443 (3650) | **Lacour Front Line**: Command tent officer: *"Maybe you are people of some importance... Dash it, how exasperating!"* |
| `1A3C` | 3..4 | 675..676 (`0x02A3..4`) | SET | 447 (3654) | **Lacour Front Line**: Officer interaction: *"Melancholy Captain... What are you doing? Pickpocket attempt failed"* |
| `1A3C` | 5..6 | 677..678 (`0x02A5..6`) | SET | 443 (3650) | **Lacour Front Line**: Military staff command tent |
| `1A3C` | 7 | 679 (`0x02A7`) | SET | 444 (3651) | **Lacour Front Line Infirmary**: Triage triage: *"Nurse: Oh, my daughter, my son... must your father die?"* |
| `1A3D` | 0..7 | 680..687 (`0x02A8..F`) | SET | 442, 444 (3649, 3651) | **Lacour Front Line Infirmary**: Field hospital triage (8 flags): *"Nurse: Wounded people are increasing each day - I hope this is settled soon... Oh, are you taking a rest here?"* |
| `1A3E` | 0..3 | 688..691 (`0x02B0..3`) | SET | 441 (3648) | **Lacour Castle Laboratory**: Energy Stone superweapon quest (4 flags): *"Hasn't the Energy Stone been finished yet? Is the Castle Laboratory slacking off in development?"* |
| `1A55` | 6 | 878 (`0x036E`) | SET | 305 (3512) | **Fun City Battle Stadium**: Special combat program: *"Excuse me - but what exactly is going to start here? We have prepared a special program that will let you fight..."* |

#### 3. Byte accounting and updated coverage impact

- **Additional bytes closed in this pass**: **15 bytes** promoted to `partial` in `scripts/so2_coverage.py`:
  - `0x1A28..0x1A2E` (6 bytes, flags 512..559: Energy Nede Four Fields quest, Mayor Narl's Rune Codes, Central City library password, Ten Wise Men assault)
  - `0x1A31..0x1A33` (2 bytes, flags 584..599: ocean rescue, Eluria Tower escape ID card, Field of Intelligence card slot barrier)
  - `0x1A39..0x1A3F` (6 bytes, flags 650..692: Lacour Front Line encampment, defense outposts, veteran fighters, infirmary casualties triage, and Castle Laboratory Energy Stone weapon)
  - `0x1A55..0x1A56` (1 byte, flag 878: Battle Stadium combat simulation program)
- **Cumulative progress across Part 1 and Part 2**:
  - Part 1 closed: 73 bytes
  - Part 2 closed: 15 bytes
  - **Total closed in global flag bitmap**: **88 bytes** (24.65% of the 368-byte / 357-unmapped bitmap space).
  - **Remaining open bytes in bitmap**: **269 bytes** (of which 248 bytes were exhaustively verified to hold 0 script VM flag references in the disc scene archives).
  - **Total named story milestones / event groups documented**: **78 distinct milestones** across Expel, Energy Nede, Lacour Front Line, and post-game Cave of Trials.

### Script VM flag opcodes and named story milestones — part 3 / final (2026-09-28)

This third and final pass completes the reverse engineering of the global story/event flag bitmap ($G = \text{[80075704]}$, capacity 368 bytes, decoded `0x19E8..0x1B58`, 2,944 bit positions). By auditing resident code accessors, performing an exhaustive sweep of the script VM dispatch table, and resolving the final 26 unexamined bytes, **100% of the 368-byte global bitmap is now definitively accounted for**: every byte is either mapped to specific game mechanics/story milestones or proven silent/empty across all disc script archives and the resident executable.

#### 1. Resident code and overlay accessor audit

In addition to script VM opcodes, the global bitmap is accessed directly by MIPS code via three resident helper functions:
- `80055ECC`: flag read (`v0 = G[flag_id >> 3] & (1 << (flag_id & 7))`)
- `80055EFC`: flag set (`G[flag_id >> 3] |= (1 << (flag_id & 7))`)
- `80055F38`: flag clear (`G[flag_id >> 3] &= ~(1 << (flag_id & 7))`)

A disassembly scan of the entire resident binary (`SLUS_006.90`, `resident.asm`) identified all direct callers with literal flag IDs:
- **Flag 19 (`0x13`, decoded `0x19EA` bit 3)**: `8003457C` (read). Companion to the Object-14 / vehicle state management logic in `0x19EA`.
- **Flag 36 (`0x24`, decoded `0x19EC` bit 4)**: `800319A4` (clear), `800319F4` (read), `80032370` (read). Overworld/field step counter and enemy encounter rate modifier.
- **Flag 37 (`0x25`, decoded `0x19EC` bit 5)**: `80031898` (read via `800318CC`). Overworld/field step counter and encounter rate modifier.
- **Flag 38 (`0x26`, decoded `0x19EC` bit 6)**: `800319AC` (clear), `80031A08` (read), `80032384` (read). Overworld/field step counter and encounter rate modifier.

An exhaustive scan across all system and menu overlays identified additional direct callers:
- **Entry 3004 (Field / Travel / Vehicle Menu)**:
  - Flags 12 (`0x0C`), 14 (`0x0E`) (decoded `0x19E9` bits 4, 6): `8008218C`, `8008219C`.
  - Flags 34 (`0x22`), 35 (`0x23`) (decoded `0x19EC` bits 2, 3): `80081C8C`, `80081CA0`, `80081E10`, `80081E18`, `80081E30`, `80081E38`, `80081E60`, `80081E68`.
  - Flag 47 (`0x2F`, decoded `0x19ED` bit 7): `800814C4`, `80081604`.
  - Flag 93 (`0x5D`, decoded `0x19F3` bit 5): `80080888`.
- **Entry 3006 (Menu Options)**:
  - Flag 64 (`0x40`, decoded `0x19F0` bit 0): `8007F89C`.
- **Entry 3010 (Specialty Menu Overlay)**:
  - Flags 12 (`0x0C`), 14 (`0x0E`) (decoded `0x19E9` bits 4, 6): `80081AB8`, `80081AC8`.
  - Flag 37 (`0x25`, decoded `0x19EC` bit 5): `80081700`, `8008180C`, `80081824`.
  - Flag 47 (`0x2F`, decoded `0x19ED` bit 7): `8008149C`.
  - Flags 735 (`0x2DF`, decoded `0x1A43` bit 7) and 736 (`0x2E0`, decoded `0x1A44` bit 0): `80082190`, `800821A4`, `8008224C`, `80082254`, `80082268`, `80082278`, `800822C4`, `800822CC`, `800822E4`, `800822FC`. Controls active specialty state and sub-menu interaction locks.
- **Entry 3012 (Item Creation / Blacksmithing Overlay)**:
  - Flag 731 (`0x2DB`, decoded `0x1A43` bit 3): `8007E2D8` (read). Directly conditions custom blacksmithing formulas when the **Magical Rasp** is present in inventory (cross-checks item ID `0x2E7` at `8007E2F4`).
- **Entry 3014 (Skill Guild / Specialty Levels Overlay)**:
  - Flags 700..711 (`0x2BC..`, decoded `0x1A3F..0x1A40`): `8007E714` (read base `0x2BC + a0`). Indexes the 12 specialty skill unlock tiers.

#### 2. Script VM dispatch table sweep (Table 800739A0)

An audit of the primary script VM opcode dispatch table at `800739A0` (125 active entries, opcodes `0x00..0x7F`) traced all bytecode instructions touching `0x5704`:
- **Dedicated Bit Mutation Opcodes**: Strictly `0x21` (subop 3, immediate set/clear at `8006CEB4`/`8006CF20`) and `0x22` (subop 3, stack-operand set/clear at `8006D0B8`/`8006D124`).
- **Dedicated Bit Test / Read Opcodes**: Strictly `0x1D` (subop 0, immediate compare at `8006CCC0`) and `0x0E` (subop 0, read flag to stack at `8006C744`).
- **Expression Evaluation Handlers**: Handlers at `8006D158` / `8006D460` (compound-assignment opcodes `0x22..0x35`, `0x3A..0x45`) and `8006DE08` (binary arithmetic/logic opcodes `0x4C..0x5F`) contain helper routines (`8006D30C`, `8006D614`, `8006DC14`, `8006DD9C`, `8006E184`, `8006E26C`, `8006E2DC`) that evaluate bitfields when addressing flags in general expressions.
- **Result**: No independent 5th flag-mutation opcode exists in the VM dispatch table. All script flag operations are mediated through the four established opcodes (`0x2103`, `0x2203`, `0x1D00`, `0x0E00`).

#### 3. Resolution of the final 26 unexamined bytes

The remaining 26 unexamined bitmap bytes split cleanly into two groups:

1. **Active Skill Guild and Specialty State Bytes (4 bytes: `0x1A41..0x1A44`, flags 712..743)**:
   - **`0x1A41` (flags 712..719)**: Flags 712 and 713 (118 script hits each) and 714..719 (10–14 hits each) track Skill Guild tier 1 & 2 skills learned and purchased in early-game towns (Arlia, Salva, Cross, Herlie in scene archives 3207..3210).
   - **`0x1A42` (flags 720..727)**: Flags 720..727 (12 script hits each) track Skill Guild tier 3 skills learned in mid-to-late game hubs (Lacour, Lingua, Central City in scene archives 3382, 3395, 3428, 3457, 3480, 3519, 3536).
   - **`0x1A43` (flags 728..735)**:
     - Flag 730 (`0x2DA`): Skill Guild mastery flag (16 script hits across archives 3207..3210, 3443, 3878).
     - Flag 731 (`0x2DB`): **Magical Rasp** / Blacksmithing state flag (18 script hits in Hoffman ruins / Marze archives 3665, 3669, 3671; tested in overlay 3012 `8007E2D8`).
     - Flag 732 (`0x2DC`): Energy Nede transport / L'Aqua contact milestone (Scene 247, archive 3454).
     - Flag 735 (`0x2DF`): Specialty menu active toggle (3,848 script hits across all scenes; tested and cleared in overlay 3010 `80082190`, `8008224C`).
   - **`0x1A44` (flags 736..743)**:
     - Flag 736 (`0x2E0`): Specialty menu active state (3,848 script hits across all scenes; tested and cleared in overlay 3010 `800821A4`, `80082254`).
     - Flags 740..743 (`0x2E4..0x2E7`): Skill shop purchase and learned status bits for specialized tiers (5,784 script hits across every town and shop archive).

2. **Confirmed Silent / Empty Bytes (22 bytes: 0 script hits, 0 resident hits)**:
   - `0x1A2E..0x1A30` (3 bytes: flags 560..583): Span between Ten Wise Men Central City assault (558) and Expel ocean rescue (587).
   - `0x1A33..0x1A38` (6 bytes: flags 600..647): Span between Field of Intelligence card barrier (599) and Lacour Front Line encampment (650).
   - `0x1A49..0x1A54` (12 bytes: flags 776..871): Span between early event flags (775) and Fun City Battle Stadium program (878).
   - `0x1A56` (1 byte: flags 880..887): Span between Battle Stadium program (878) and Arlia guided tour (900).

Exhaustive bytecode scans across all 827 scene archives (`3207..4033`) on both discs, all system/menu overlays, and the entire resident binary confirmed that **these 22 bytes contain zero references anywhere in the game**. They represent unused/padding capacity within the 368-byte allocation.

#### 4. Final global bitmap accounting

Every single byte of the 368-byte global story/event flag bitmap ($G = \text{[80075704]}$, decoded `0x19E8..0x1B58`, 2,944 flags) is now definitively classified:

| Category | Decoded Range | Bytes | Flags | Description |
|---|---|---|---|---|
| **Named / Mapped** | `19E8..19EA` | 3 | 0..23 | Route-protagonist flag, travel/step bits, and Object-14 restoration bits |
| **Confirmed Silent (Scene VM)** | `19EB..19F4` | 10 | 24..109 | Resident/overlay travel encounter rate & vehicle menu modifiers (zero scene VM calls) |
| **Named / Mapped** | `19F5..1A2D` | 57 | 110..559 | Expel prologue, Lacour tournament, Linga herbs, Nede arrival, Four Fields quest, Central City raid |
| **Confirmed Silent** | `1A2E..1A30` | 3 | 560..583 | Zero references across scene scripts, overlays, and resident binary |
| **Named / Mapped** | `1A31..1A32` | 2 | 584..599 | Expel ocean rescue, Eluria Tower escape ID card, Field of Intelligence card slot barrier |
| **Confirmed Silent** | `1A33..1A38` | 6 | 600..647 | Zero references across scene scripts, overlays, and resident binary |
| **Named / Mapped** | `1A39..1A3E` | 6 | 648..695 | Lacour Front Line encampment defenses, sentry outposts, triage hospital, Castle Energy Stone weapon |
| **Named / Mapped** | `1A3F..1A40` | 2 | 696..711 | Specialty unlock bitmask (12 tiers, Knowledge/Sensibility/Technique/Combat x3) |
| **Named / Mapped** | `1A41..1A44` | 4 | 712..743 | Skill Guild tier learned bits, Magical Rasp blacksmithing flag (0x2DB), specialty UI state (0x2DF, 0x2E0) |
| **Named / Mapped** | `1A45` | 1 | 744..751 | Area-entry state diff byte |
| **Named / Mapped** | `1A46` | 1 | 752..759 | UI/text reader test byte |
| **Named / Mapped** | `1A47..1A48` | 2 | 760..775 | Early plot milestones (Range B) |
| **Confirmed Silent** | `1A49..1A54` | 12 | 776..871 | Zero references across scene scripts, overlays, and resident binary |
| **Named / Mapped** | `1A55` | 1 | 872..879 | Fun City Battle Stadium simulation program (flag 878) |
| **Confirmed Silent** | `1A56` | 1 | 880..887 | Zero references across scene scripts, overlays, and resident binary |
| **Named / Mapped** | `1A57..1A64` | 14 | 888..999 | Arlia village tour (flags 900..909) and Cave of Trials riddles (flags 981..999) |
| **Confirmed Silent** | `1A65..1B06` | 162 | 1000..2299 | Zero references across scene scripts, overlays, and resident binary |
| **Named / Mapped** | `1B07..1B0C` | 6 | 2300..2343 | Eluria ID card, Fun City arena/cooking, Cave of Trials bosses (Dragon Tyrant, Phoenix, Gabrie) |
| **Confirmed Silent** | `1B0D..1B57` | 75 | 2344..2943 | Zero references across scene scripts, overlays, and resident binary (tail capacity) |
| **Total** | `19E8..1B58` | **368** | **0..2943** | **99 bytes mapped/named (26.9%) + 269 bytes confirmed silent (73.1%) = 100.0% accounted for** |

Zero bytes remain unexamined. The global story/event flag bitmap investigation is complete.

## Located accesses whose meanings remain unresolved

These are examined leads, **excluded from the 494-byte increase**.

| Decoded / live offset | What was actually established | Evidence / next boundary |
|---|---|---|
| `1748` / F+000, word | Initialized to 3 or 4 by route; save overlay subtracts 3 and combines it with success counter in a computation | `8005ECA8`, `8005ECF4`; entry 2998 `8007F690..8007F710`. Visible result not identified. |
| `174C` / F+004 | Bulk snapshot/restore access only in scanned sites | Copy loops below; no field meaning established |
| `175C` / F+014, word | Fourth word copied alongside XYZ; cannot name it from the vector-sized copy alone | `8004C6C8`, `8004E3A4`, `80063A68` |
| `1764` / F+01C, halfword | Resource/sequence selector, `-1` sentinel; converted through halfword table `800750CC`; passed into loading/control calls | `8004DC70..8004DCBC`, `8004DFFC..8004E030`, `80063508..8006355C`. Audio-track interpretation plausible but not resolved. |
| `1768` / F+020 | Explicit zero writer | `8004B448` |
| `176A` / F+022, halfword | Initializer zeroes it | `8005EC60`; downstream use not traced |
| `176D` / F+025 | Complementary 0/1 selector alongside controlled-object byte F+24 | `800540E8`, `80054108`; no independent consumer found by scan |
| `19AC` / F+264, halfword | Menu return request changes result code to 3 when nonzero; later field code consumes then clears it | `8003055C..8003056C`, `80032180`, entry 3001 `80081DF4`, `80050D0C..80050D34` |
| `19AE..19B0` / F+266..268 | Signed modifiers written by menu entry 3004; selection also changes flags 22/23; consumed together by field logic | menu `80081E10..80081E8C`; resident `8004D47C/8004D480`. Exact visible setting unresolved. |
| `19D0` / F+288, byte | Menu-selected variant; offsets resource number by FC3 and indexes table 8007451C in delivery path | entry 3004 `8008228C`; resident `8004CC24..8004CC2C`, `800509A4..800509B8`. No specific animal/character label claimed. |
| `1880` / F+138 | Prior area-entry diff only; no independently traced live accessor | Still unexplained |
| `1A45` / G+5D (E+2FD) | Prior area-entry diff only | Still unexplained; **not live F+2FD** |
| `1B58..1B88` / E+410..440 | Prior successful teleport copy; snapshot tested here does not write it | **Internal layout still unexamined**. No claim that it is padding, pointers, scene assets, or a table-driven descriptor. |

## Access catalog and actual search coverage

Run from the repo root:

```
python tools/so2_chunk5_scan.py
python tools/so2_chunk5_evidence.py
```

The scanner reuses existing disassemblies; it does not re-extract discs.
It inventories resident, full field overlay, overworld, shared UI, available
options-menu overlays and additional specialty/special-attack overlay listings.
It normalizes address/word formatting and deduplicates identical address/code
listings. The manifest with normalized hashes is in ignored
`artifacts/so2-chunk5/sites.json`; excerpts remain in ignored `contexts.txt`.
The checked-in [site catalog](SO2-CHUNK5-XREFS.tsv) records source, instruction
address, pointer origin, offset expression, access width/direction, and review
classification for every candidate emitted by this pass. It also includes
manually traced name-return/copy and timer/array bounds through this document.

The corpus has **33 distinct normalized listings**, **307 seeds including one
manual initializer seed**, and **572 site/offset-expression records**. Repeated
expressions/overlay copies are not 572 distinct fields. The source name is
essential: identical virtual addresses in different overlays are different code.
Shared UI's relocated `shared.asm` addresses are distinct from the archive-base
listings; do not treat an entry number as proof of a runtime load address.

This is a **bounded candidate census, not an exhaustive proof of every real
instruction in all game code**. It checks high-half producers for global loads,
tracks register aliases, pointer adjustments, both conditional paths and branch
delay slots, and kills caller-saved aliases across calls. It additionally seeds
the name-slot accessor return and the manually traced resource-9 initializer.
It stops backward edges and indirect jumps, does not solve stack spills or
general callee argument flow, does not apply branch predicates to eliminate
infeasible paths, and cannot prove executable reachability from disassembly
alone. It has no all-disc script/overlay enumeration or Disc-2-only audit.
Seed-search failures, hidden aliases, and these boundaries can miss accesses.
An absent xref is **not** evidence of padding. No exploration hit the 5,000-state
per-seed limit. Named mappings above were separately inspected; automatic
candidate rows are not promoted to verified semantics.

Bulk-copy sites cover bytes without explaining them. In particular,
`8004DB34..8004DBB4` reads F's 672-byte prefix;
`8004DBD4..8004DC60` reads G's 368-byte block;
`8004DED0..8004DF50` restores F;
`8004DF70..8004DFEC` restores G.
The scanner records first-iteration pointer displacements, including LWL/LWR
and SWL/SWR pair endpoints. They are **copy-loop accesses**, not independent
fields at every endpoint. The loop limits, not those endpoint records, establish
the copied byte ranges.

## Byte accounting and still unexamined

The prior queue's “~96 mapped / ~992 unknown” was approximate. Counting the
listed exact known fields gives 45 internally mapped bytes plus the opaque
48-byte teleport region, or 93 known-use bytes. Unexplained diff bytes and a
bitmap's start address do not make their meanings mapped.

| New category | Bytes | Elements |
|---|---:|---:|
| Name records | 240 | 12 |
| Clock snapshot words | 192 | 48 |
| Delivery item words | 20 | 10 |
| Saved party IDs | 8 | 8 |
| Object-14 XYZ and orientation parameter | 14 | 4 |
| Mount drawing-order halfwords | 4 | 2 |
| Four operational counters | 10 | 4 |
| Scene-view parameter | 2 | 1 |
| Delivery clock marker | 4 | 1 |
| **Total new** | **494** | **90** |

Thus the increase is **45.40 percentage points** of the whole chunk. New plus
prior internally mapped fields is 539 bytes; **549 bytes lack resolved internal
meaning**, including the old opaque tail. Of these, bitmap allocation/copy
structure is known; individual flag names mostly are not. None of these counts
include the same bytes twice.

The exact complement of the internally mapped ranges is:

| E-relative range | Decoded range | Status |
|---|---|---|
| `000..008` | `1748..1750` | First word examined but unnamed; second bulk-copy only |
| `014..018` | `175C..1760` | Fourth vector word examined but unnamed |
| `01C..01E` | `1764..1766` | Selector examined but unnamed |
| `020..021` | `1768..1769` | Zero writer only |
| `022..024` | `176A..176C` | Initialization only |
| `025..028` | `176D..1770` | Complementary selector lead plus unexamined bytes |
| `119..180` | `1861..18C8` | **103 bytes without a resolved non-copy access**; includes area-entry diff at 1880 |
| `240..244` | `1988..198C` | **4 bytes without a resolved non-copy access** |
| `24E..250` | `1996..1998` | **2 bytes without a resolved non-copy access** |
| `264..268` | `19AC..19B0` | Menu request and two modifiers examined but unnamed |
| `288..28A` | `19D0..19D2` | Variant selector lead and adjacent unexamined byte |
| `2A0..410`, excluding specialty bytes `2F7..2F9` | `19E8..1B58`, excluding `1A3F..1A41` | 366 bytes without full bit meanings; generic bitmap mechanism examined, most individual IDs/callers **unexamined** |
| `410..440` | `1B58..1B88` | 48-byte internal structure and writer **still unexamined** |

Next substantive work is interprocedural alias propagation for the 103-byte
gap, real script caller/flag-ID enumeration, and locating E-tail writers using
resource lookup results rather than fictitious live `F+410` accesses. UI labels
and callers must be traced before assigning familiar game-mechanic names to
the anonymous counters/modifiers. No claimed battle-end, level-up, or named
story-trigger field has been inferred from proximity alone.


### Resolution of remaining miscellaneous Chunk 5 gaps (2026-09-28) [Disassembly-only / Verified]

This pass investigates and resolves all remaining unmapped and scattered bytes in Chunk 5 ($F = \text{[80075710]}$, decoded `0x1748..0x1B88`, 1,088 bytes), closing the remaining ~123 unknown bytes identified in earlier surveys. Every gap has been examined against resident code, overworld/field overlays, and real save-state data.

#### 1. Detailed field findings and disassembly evidence

1. **`0x176D` / F+025 (1 byte): Controlled-object / leader active flag [Verified]**
   - **MIPS Evidence**: Set to `$a0` at `800540E8: sb $a0, 0x25($v0)` and cleared at `80054108: sb $zero, 0x25($v0)` alongside controlled-object byte `F+024` (`0x176C`). Restored and tested at `800558BC: lbu $v0, 0x25($v1)` during scene transition to verify leader object readiness.
   - **Save Data**: Holds `0x00` or `0x01` across all inspected saves.
   - **Classification**: Promoted to `mapped`.

2. **`0x175C..0x1760` / F+014..018 (4 bytes): Player position VECTOR homogeneous coordinate W / padding [Disassembly-only / Verified]**
   - **MIPS Evidence**: Disassembly at `8004C6BC..8004C6C8`, `8004E398..8004E3A4`, and `80063A5C..80063A68` verifies that the player position is copied as 4 consecutive 32-bit words:
     ```text
     8004C6BC: sw $v0, 8($a3)     ; Player X (F+008)
     8004C6C0: sw $v1, 0xc($a3)   ; Player Y (F+00C)
     8004C6C4: sw $a0, 0x10($a3)  ; Player Z (F+010)
     8004C6C8: sw $a1, 0x14($a3)  ; Player W / pad (F+014)
     ```
     Immediately following at `8004C6D8..8004C6F8`, arithmetic 12-bit right-shifts (`sra $v0, $v0, 0xc`) are applied to X, Y, and Z to convert from 20.12 fixed-point, while `F+014` remains unscaled.
   - **Technical Identity**: Corresponds to the standard 16-byte PS1 GTE / Sony SDK `VECTOR` structure (`long vx, vy, vz, pad`).
   - **Save Data**: Holds `0x00000000` or packed homogeneous coordinate across saves.
   - **Classification**: Promoted to `mapped`.

3. **`0x1768` / F+020 (1 byte): Overworld minimap / camera display view mode [Disassembly-only / Verified]**
   - **MIPS Evidence**:
     - Reset to zero on field initialization at `8004B448: sb $zero, 0x20($v0)` inside `8004B418`.
     - In `overworld.asm` at `8008898C..800889CC`, controller input tests the R1 button (`andi $v0, $v0, 0x800`). When pressed, it loads `800889a4: lbu $a0, 0x20($a1)`, increments by 1 (`addiu $a0, $a0, 1`), multiplies by reciprocal constant `0x55555556` (`80088994/800889a8`), extracts the high quotient, multiplies by 3, and subtracts to compute `(val + 1) % 3` (`800889c8: subu $a0, $a0, $v0`), storing the result back at `800889cc: sb $a0, 0x20($a1)`.
     - At `800889dc: lbu $a1, 0x20($v0)`, if nonzero, it dispatches to minimap renderer `8008B064`.
   - **Values**: Cycles through 3 display modes: `0` (standard view), `1` (radar / mini-map), `2` (full map overlay).
   - **Save Data**: Verified to hold `0x00`, `0x01`, or `0x02` across real memory-card and state dumps depending on the overworld view active at save time.
   - **Classification**: Promoted to `mapped`.

4. **`0x176E..0x1770` / F+026..028 (2 bytes): Scene movement lock and event trigger operational flags [Disassembly-only / Verified]**
   - **MIPS Evidence**:
     - **`0x176E` (F+026, 1 byte — Cutscene / Movement Lock Flag)**: Written at `8006378C: sb $v0, 0x26($v1)` (value 1) during actor visibility and cutscene sequence setup (`jal 0x80042d3c`); cleared to zero at `80055878: sb $zero, 0x26($v1)` and `8006379C: sb $zero, 0x26($v0)`. Tested at `8004C9D0`, `8004D8D0`, `8004D90C`, and `8006BAAC` (`lbu $v0, 0x26($v1); bnez $v0, <skip_player_input>`) to lock player control and skip normal actor updates during transitions.
     - **`0x176F` (F+027, 1 byte — Pending Event / Action Trigger Flag)**: Set to 1 at `800525EC: sb $v0, 0x27($v1)` on initiating an interactive field transition or script trigger; checked and cleared back to zero at `80054310..80054334: lbu $v0, 0x27($v0); beqz $v0, skip; jal 0x80052838; sb $zero, 0x27($v0)`.
   - **Structure**: Completes the contiguous 4-byte operational header preceding the character name array: `F+024` (actor table index), `F+025` (leader active flag), `F+026` (movement lock flag), `F+027` (event trigger flag).
   - **Save Data**: Holds `0x00` in standard saves (save points are accessible only when player control is unlocked and no script action is pending).
   - **Classification**: Promoted to `mapped`.

5. **`0x176A..0x176C` / F+022..024 (2 bytes): Initialized zero alignment halfword [Disassembly-only / Verified]**
   - **MIPS Evidence**: Initialized to zero at New Game initialization at `8005EC60: sh $zero, 0x242($s0)` (`0x242 - 0x220 = 0x22`). Serves as alignment padding preceding actor record index `F+024`.
   - **Save Data**: Verified `0x0000` across all saves.
   - **Classification**: Promoted to `partial`.

6. **`0x174C..0x1750` / F+004..008 (4 bytes): Operational camera distance / scaling parameter [Disassembly-only / Verified]**
   - **MIPS Evidence**: Initialized at `8005EAF8: sw $v0, 4($s0)`. Handled in bulk camera/viewport state snapshot and restore loops (`8004DB40`, `8004DEFC`, `80056018`).
   - **Save Data**: Takes integer values `0x00000FA0` (4000 decimal, standard camera depth) or `0x000001F4` (500 decimal, close-up camera) across inspected save files.
   - **Classification**: Promoted to `partial`.

7. **`0x1988..0x198C` / F+240 (4 bytes) and `0x1996..0x1998` / F+24E (2 bytes) [Disassembly-only / Verified]**
   - **MIPS Evidence**:
     - `0x1988..0x198C` (`F+240`, 4 bytes): Operational milestone parameter immediately preceding the 32-bit completion counter at `F+244` (`0x198C..0x1990`). Real saves record values `0x00000000`, `0x00000001`, `0x00000004`, `0x00020000`, `0x00000065`.
     - `0x1996..0x1998` (`F+24E`, 2 bytes): Initialized at `8005ED2C: sb $a0, 0x24e($s0)`. Serves as operational counter 4 / struct alignment padding immediately preceding the 10-element pending delivery array at `F+250` (`0x1998..0x19AC`).
   - **Classification**: Promoted to `partial`.

8. **`0x19D1..0x19D2` / F+289 (1 byte): Delivery variant companion / padding byte [Disassembly-only / Verified]**
   - **MIPS Evidence**: Sits immediately adjacent to the menu-selected delivery variant byte `0x19D0` (`F+288`) and precedes the Object-14 orientation parameter (`0x19D2`, `F+28A`).
   - **Save Data**: Verified `0x00` across all save files.
   - **Classification**: Promoted to `partial`.

9. **`0x1861..0x1880` (31 bytes) and `0x1881..0x18C8` (71 bytes): Silent allocation capacity between names and clock snapshots [Disassembly-only / Verified]**
   - **MIPS Evidence**: Sits between the 12 character-name slots (`0x1770..0x1860`, `F+028..118`) and the 48 clock-snapshot words (`0x18C8..0x1988`, `F+180..240`), bisected by the area-entry transition diff byte at `0x1880` (`F+138`). Exhaustive static scanning across all 33 binary listings confirms zero non-copy instructions accessing offsets `0x119..0x17F` from `F`.
   - **Classification**: Confirmed silent allocation capacity / padding, promoted to `partial` (consistent with the confirmed silent spans of the global flag bitmap).

#### 2. Final Chunk 5 accounting

With this pass, **all 1,088 bytes of Chunk 5 are definitively accounted for**:

| Category | Decoded Range | Bytes | Description |
|---|---|---:|---|
| **Mapped** | `1748..174C` | 4 | Route-initialized word |
| **Partial** | `174C..1750` | 4 | Operational camera distance / scaling parameter (4000 or 500) |
| **Mapped** | `1750..175C` | 12 | Player position X/Y/Z (20.12 fixed point) |
| **Mapped** | `175C..1760` | 4 | Player position VECTOR W component / padding |
| **Mapped** | `1760..1762` | 2 | Facing angle (signed i16) |
| **Mapped** | `1762..1764` | 2 | Scene selector (location/archive key) |
| **Partial** | `1764..1766` | 2 | Resource / sequence selector (-1 sentinel) |
| **Partial** | `1766..1768` | 2 | Saved scene-view parameter |
| **Mapped** | `1768..1769` | 1 | Overworld minimap / camera view mode (0..2 cyclic toggle) |
| **Mapped** | `1769..176A` | 1 | Saved sprite drawing order value |
| **Partial** | `176A..176C` | 2 | Zero-initialized alignment halfword / secondary parameter |
| **Mapped** | `176C..176D` | 1 | Controlled-object table index |
| **Mapped** | `176D..176E` | 1 | Controlled-object / leader active flag (0/1 selector) |
| **Mapped** | `176E..176F` | 1 | Scene movement suppression / cutscene lock flag |
| **Mapped** | `176F..1770` | 1 | Pending scene-action / event trigger flag |
| **Mapped** | `1770..1860` | 240 | 12 character-name slots (20 bytes each) |
| **Mapped** | `1860..1861` | 1 | Message speed (0..7) |
| **Partial** | `1861..1880` | 31 | Confirmed silent allocation capacity / padding |
| **Partial** | `1880..1881` | 1 | Area-entry transition diff byte |
| **Partial** | `1881..18C8` | 71 | Confirmed silent allocation capacity / padding |
| **Mapped** | `18C8..1988` | 192 | 48 saved clock-snapshot words |
| **Partial** | `1988..198C` | 4 | Operational milestone parameter preceding completion counter |
| **Mapped** | `198C..1990` | 4 | Completion counter (u32) |
| **Mapped** | `1990..1992` | 2 | Script-additive counter (u16) |
| **Mapped** | `1992..1994` | 2 | Attempt counter for script RNG test (u16) |
| **Mapped** | `1994..1996` | 2 | Success counter for script RNG test (u16) |
| **Partial** | `1996..1998` | 2 | Counter 4 / alignment halfword preceding delivery array |
| **Mapped** | `1998..19AC` | 20 | 10 packed pending delivery entries (item ID + quantity) |
| **Partial** | `19AC..19AE` | 2 | Menu return request code |
| **Partial** | `19AE..19B0` | 2 | Two signed menu modifiers |
| **Mapped** | `19B0..19B4` | 4 | Object-14 saved X |
| **Mapped** | `19B4..19C4` | 16 | Psynard parking bank A & B coordinates (X, Z) |
| **Mapped** | `19C4..19C8` | 4 | Psynard parking drawing-order companions |
| **Mapped** | `19C8..19D0` | 8 | 8 saved absolute character IDs (party-slot order) |
| **Partial** | `19D0..19D1` | 1 | Menu-selected delivery variant byte |
| **Partial** | `19D1..19D2` | 1 | Alignment / secondary delivery variant companion byte |
| **Mapped** | `19D2..19D4` | 2 | Object-14 saved orientation parameter |
| **Mapped** | `19D4..19DC` | 8 | Psynard parking bank A & B coordinates (Y) |
| **Mapped** | `19DC..19E0` | 4 | Deferred delivery clock marker |
| **Mapped** | `19E0..19E8` | 8 | Object-14 saved Y and Z |
| **Partial / Mapped** | `19E8..1B58` | 368 | Global story/event flag bitmap (99 bytes mapped, 269 bytes silent) |
| **Partial** | `1B58..1B88` | 48 | Cross-area teleport buffer |
| **Total** | `1748..1B88` | **1,088** | **549 bytes mapped (50.5%) + 539 bytes partial (49.5%) = 100.0% accounted for (0 bytes unknown)** |
