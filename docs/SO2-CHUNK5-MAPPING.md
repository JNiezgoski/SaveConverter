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
