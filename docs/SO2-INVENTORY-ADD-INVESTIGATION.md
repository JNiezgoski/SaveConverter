# SO2 inventory: fixed slots, first-vacant allocation, runtime integrity cache

Investigation date: 2026-09-26. US PS1 SCUS-94421 / BASCUS-94421.

## Result

**The general add routine is resident `0x8003C594`. Inventory is a fixed
1,024-slot u16 array at decoded `[0xB20,0x1320)`, reached in RAM through
`[0x80075278]`. A new item replaces the first count-zero slot. Nothing is
inserted into the decoded buffer and no following field moves.**

There is no distinct-item count, end marker, or sorted-insertion requirement
in this routine. It scans all 1,024 slots, including entries beyond holes.
The serializer copies the entire fixed array without sorting or compaction.
Compression makes the on-card representation variable in length; the decoded
inventory and complete decoded state remain fixed in size.

The routine also updates a 16-ID recent-item list and a runtime integrity
byte for the changed slot. Crucially, the serializer **zeros all 1,024 integrity
bytes before copying the inventory chunk to the save**, and rebuilds them
after the copy in either direction. An edited card does not need a persisted
per-slot integrity checksum: load computes it from the edited item words.

Candidate [seraphic-garb-20-S15-candidate.mcd](../artifacts/so2-inventory/seraphic-garb-20-S15-candidate.mcd)
adds **Seraphic Garb (364), zero to 20**, to the matching live S15 snapshot.
The actual extracted add instructions match an independent implementation.
The actual complete serializer, including its codec, reproduces the candidate
payload exactly, and its load direction restores the state with valid caches.
**Not loaded in-game.** This establishes the mechanism with instruction-level
evidence, not a completed emulator test.

## Sources and reuse

Read in order and reused: [Fol](SO2-FOL-INVESTIGATION.md),
[checksum](SO2-CHECKSUM-INVESTIGATION.md), and
[party membership](SO2-PARTY-MEMBER-INVESTIGATION.md). The established
`so2_fol.state/encode`, corrected signer, archive extraction, RAM conventions,
and bounded MIPS harness were reused. No new disc extraction or RAM dump was
necessary. The harness gained only MIPS `nor` and explicit executable ranges
so the existing save overlay could run alongside resident code.

| Archive entry | Disc LBA | Load address | Size | Use |
|---|---:|---:|---:|---|
| 2576 | 30736 | `8002F810` | `4C7FC` | Add/remove, lookup, recent list, integrity generator/validator |
| 2986 | 36126 | `8007E000` | `3E2C` | Shop's purchase and sale call sites; inspected first |
| 2998 | 36213 | `8007E000` | `4D28` | Complete serializer and established codec |

These are existing `artifacts/so2-fol/disc-code` extracts from SO2.BIN,
ISO LBA 300. Shared UI entry 2985 was not needed after the shop led directly
to the resident routine. Overlay addresses refer to their respective entry.

Byte-bearing disassembly: [evidence.asm](../artifacts/so2-inventory/evidence.asm).
Full code/RAM hashes and anchors: [sources.json](../artifacts/so2-inventory/sources.json).
Reproducer: [tools/so2_inventory_evidence.py](../tools/so2_inventory_evidence.py).

| Existing RAM dump | Inventory pointer `[75278]` | Valid integrity bytes | Add/remove code matches resident extract |
|---|---|---:|---|
| `artifacts/so2-fol/ram.bin` | `8009AC70` | 1024/1024 | Yes, `[8003C594,8003C9D0)` |
| `artifacts/so2-fol/SCUS-94422_resume.ram` | `8009ACD0` | 1024/1024 | Yes, same range |

These are prior-session dumps, not tonight's current RAM. The candidate's
input is tonight's card snapshot, described below.

## Exact chunk and field boundaries

| Inventory-relative range | Absolute decoded range | Meaning |
|---|---|---|
| `[000,800)` | `[B20,1320)` | 1024 fixed u16 item slots |
| `[800,820)` | `[1320,1340)` | 16 recent item IDs, u16 each |
| `[820,824)` | `[1340,1344)` | Runtime item-property-table pointer (`8003C550`); preserved by editor |
| `[824,C24)` | `[1344,1744)` | 1024 runtime integrity bytes; zero in canonical saved payload |
| `C24` | `1744` | Nonzero tells recent-list updater to clear/reset history first |
| `[C25,C28)` | `[1745,1748)` | Not interpreted; preserved exactly |

The pointer at chunk+820 is used by `8003C538` to access 0x30-byte item
property records. This investigation does not redefine its initialization
or portability; it preserves the source bytes like the game serializer.

Serializer evidence:

```text
80081AF0 addiu s2,s4,0B20     ; fourth chunk's decoded address
80081B38 lw    s3,5278(s3)    ; inventory allocation
80081B3C slti  v0,v1,0400
80081B48 sb    zero,0824(v0)  ; v0=s3+index, clear cache
80081B54 addiu s1,zero,0C28
80081B60 move  a2,s2          ; decoded buffer + B20
80081B6C lw    a3,5278(a3)    ; live inventory base
80081B74 jal   80081C38       ; direction-selecting fixed-size copy
80081B78 sw    s1,10(sp)      ; length C28, delay slot
80081B7C slti  v0,s0,0400
80081B88 move  a1,s0          ; slot index
80081B8C jal   8003C8A0       ; regenerate runtime integrity
80081B90 ori   a2,zero,FFFF   ; request random nibble
80081B98 sb    v0,0824(v1)    ; v1=inventory+slot
```

`80081C38..80081C60` selects copy direction using the load flag. Consequently,
save copies zeros in the cache range; load overwrites/restores the chunk and
then regenerates cache bytes. The cache is never a missing saved insertion
counter. Full serializer execution independently confirms these directions.

The fifth `0x440` chunk at decoded `[1748,1B88)` is resolved differently:
`80081BA8..80081BB4` calls `80012108([80075258], 0xE)`. The RAM-resident helper
scans 16 resource tags at table+44+4*i, returning table+4+4*i's pointer on a
match. Both existing dumps have table `80095A30`, resource E at index 4:

| Dump | Fifth chunk pointer |
|---|---|
| `ram.bin` | `80114374` |
| `SCUS-94422_resume.ram` | `8018EA44` |

Thus this chunk is not another assumed adjacent direct global pointer. Its
contents are outside the inventory edit and remain unchanged.

## General-purpose callers and entry representation

Shop purchases call the resident routine directly:

```text
8007E8D8 move  a2,s0          ; purchased quantity
8007E8E4 lw    a0,5278(a0)    ; inventory base
8007E8E8 lh    a1,2(v1)      ; item ID
8007E8EC jal   8003C594
8007E8F0 addiu a3,zero,1      ; bit-15 flag
```

Resident script handler `800669BC..800669D8` reads an argument with
`80068DB8` then calls the same routine with quantity 1 and flag 1.
Wrapper `8003368C..800336AC` does likewise. This is general-purpose inventory
code, not a Seraphic Garb special case. Shop selling resolves an item index
through `8003C820`, then calls removal `8003C798` at `8007E748`.

The full word layout is:

```python
item_id = word & 0x3ff
count = (word >> 10) & 0x1f
flag = word >> 15
word = item_id | (count << 10) | (flag << 15)
```

**Count is five bits, not six.** The inspected shop/script/equipment-return
callers pass flag 1; the routine supports 0 too. The user-visible meaning of
bit 15 is not established here. It is excluded from the runtime integrity
calculation. The editor defaults to flag 1 to match those callers; `--marked 0`
is available. For 364 x20 the words are respectively `D16C` and `516C`.
The simpler original encoding remains valid when this separate flag is zero.

## Actual add algorithm: first vacancy, no shifting

Arguments to `8003C594`: a0=inventory allocation, a1=item ID, a2=quantity
increment, a3=bit-15 flag. The return value is 1 for success, 0 for failure.

1. Scan indices 0..1023. Remember the first slot with count zero. For occupied
   slots, compare their low ten ID bits; stop if the requested ID is found.
2. If absent, use that first vacancy or fail when none exists. Store the word
   at `base+2*slot`. No adjacent word moves.
3. If present, validate its integrity byte through `8003C928`. A valid slot
   receives old count + increment, unless the total exceeds 20 (failure, no
   change). Both new and existing paths write the supplied bit-15 flag.
4. Recalculate the changed slot's integrity byte and call recent-list updater
   `8003C70C` with the item ID.

```text
8003C5D0 slti  v0,s0,0400    ; fixed capacity, not an owned-count field
8003C5DC lhu   v1,0(a0)
8003C5E4 srl   v0,v1,0A
8003C5E8 andi  v0,v0,001F    ; count, excluding bit 15
8003C600 move  s1,s0         ; remember first vacancy
8003C604 andi  v0,v1,03FF    ; occupied-slot ID
8003C608 beq   v0,s3,8003C61C
...
8003C630 sll   a3,s1,1       ; NEW slot address = base + 2*vacancy
8003C634 addu  a3,a3,s2
8003C638 sll   v0,s4,0A      ; quantity
8003C63C or    v0,s3,v0      ; ID
8003C640 sll   v1,s5,0F      ; separate flag
8003C644 or    v0,v0,v1
8003C648 jal   8003C8A0
8003C64C sh    v0,0(a3)      ; delay slot: overwrite exactly one word
```

The raw new-slot branch does not independently clamp quantity: callers are
expected to supply valid counts. The tool checks 1..20 before execution and
rejects existing totals over 20. It also rejects duplicate/invalid occupied
entries and noncanonical saved caches. Item IDs must fit the nonzero 10-bit
domain; this is not a claim that every possible ID has a valid item-table row.
Use established game item IDs.

An existing slot with an invalid integrity byte takes `8003C6D8..8003C6E0`:
clear that slot and return 1. This unusual path matters for direct RAM writes,
but does not explain a correctly decoded card edit: load rebuilds the cache.

`8003C70C` clears its 16-word history if byte C24 is nonzero, clears that byte,
then promotes the item ID to position 0. If already present, it shifts only
the preceding IDs right; if absent, it shifts positions 0..14 and drops the
last. **This small auxiliary list shifts; the 1,024 inventory slots do not.**
No other persistent counter/flag is written along this routine's normal path.

## Integrity bytes and removal explain the misleading clues

`8003C8A0(base, slot, nonce)` uses a random nibble when nonce=FFFF, otherwise
the supplied nibble. Let n be that nibble, w=slot word & 7FFF, and f be the XOR
of w's four nibbles:

```python
integrity_byte = (((~slot & 15) ^ n) << 4) | (f ^ n)
```

Validator `8003C928` recovers n from the stored high nibble XOR (~slot & 15),
recomputes the byte, and compares it. `8003C974` validates all 1,024 slots.
The formula matches all slots in both existing RAM dumps and 100 sampled
word/index/nonce cases executed through the actual generator and validator.

Removal `8003C798(base, slot_index, quantity)` subtracts from the five-bit count:

```text
8003C7C0 srl   v0,a1,0A
8003C7C4 andi  v0,v0,001F
8003C7C8 subu  v1,v0,a2
8003C7CC bltz  v1,8003C808   ; insufficient quantity: no write
8003C7D4 bnez  v1,8003C7E4
8003C7D8 andi  v0,a1,83FF    ; preserve ID and flag if count remains
8003C7DC j     8003C7F0
8003C7E0 sh    zero,0(a0)    ; exactly zero: clear this fixed slot
...
8003C7F8 jal   8003C8A0      ; update runtime integrity byte
```

No deletion/compaction occurs. `00 00 xx` in compressed data is the established
zero-run token: xx counts additional zeros, not tombstone metadata. A cleared
u16 slot may merge with adjacent zeros, explaining apparently variable-size
removal. Exact token boundaries depend on neighboring bytes.

The earlier SAVE-FORMAT inventory description mixed compressed positions with
decoded structure. Party size changes compression length, not the decoded
inventory offset. A naive encoded splice can change decoded length/alignment
or damage a zero-run token; a decoded insertion shifts every later field.
Both are structurally wrong. **The exact two historical failed files were not
identified/analyzed here**, so their particular corruption is not retroactively
attributed to a specific byte. There is no evidence for the earlier proposed
save-time inventory sorting/compaction mechanism in the traced serializer.

## Candidate, preservation, and independent verification

Read-only source:

```text
C:/CodeTesting/StarOcean2/SaveGames/Star Ocean - The Second Story (USA)_1.mcd
BASCUS-94421S02-S15 / physical block 10
workspace snapshot: artifacts/so2-inventory/source-live-card-20260926.mcd
source card SHA256
ec3e3c7bd94220ec5b3ba4db5d9860373fc25ff3d2c549ff08ad217873dd30a2
candidate card SHA256
1b37e4608a0b29a02fdc43d222d301852691b734819cda5d61fbcf59bb9b44e6
candidate block SHA256
5f7a3d3fce4b874bbb15bc3a84740cf3a88b9b42d56ea7635035f1a03fa109d0
```

This S15 matches the requested state: 119 occupied types, Seraphic Garb absent
from all 1,024 slots, equipped in secondary slots 1 and 2; Angel Armband is
slot 70, word `5181` (20). The first free slot is 119. The recent-item list
already starts with ID 364 in the source, so its update is a no-op here.
That history entry is not an owned inventory entry or proof of permanent
ownership history. All equipment and Angel Armband remain byte-identical.

| Property | Source | Candidate |
|---|---:|---:|
| Decoded inventory slot 119 at `C0E` | `0000` | `D16C` |
| Seraphic Garb owned count | 0 | 20 |
| Compressed count | 2437 (`985`) | 2439 (`987`) |
| C | 3335 (`D07`) | 3337 (`D09`) |
| A | 9699 (`25E3`) | 9765 (`2625`) |
| B | 169333 (`29575`) | 169652 (`296B4`) |

Only decoded offsets **C0E and C0F** change. The decoded length remains
`1B88`. 379 physical card bytes change because the compressed suffix moves.
All bytes outside block 10—including directory and other saves—are identical.
Inside that block, only checksums, C, compressed length, and the new compressed
stream may change; bytes beyond the new stream are preserved.
Full details: [candidate-report.json](../artifacts/so2-inventory/candidate-report.json).

[so2_inventory.py](../so2_inventory.py) reconstructs legal runtime cache
values, executes actual `8003C594` instructions, checks a strict write allowlist,
then zeros cache bytes exactly as save does. An independent Python prediction
must agree byte-for-byte across the complete C28 chunk. It re-encodes, updates
both lengths, signs, and verifies decoded and physical preservation. CLI
outputs are confined to new files under `artifacts/so2-inventory/`; existing
files are refused using exclusive creation. `--count` is an **increment**.

The evidence verifier separately executes actual encoder and decoder leaves,
then the **entire serializer `80081A70`** in both save and load directions.
Save output equals the candidate's length word plus compressed stream exactly.
Load restores all five chunks exactly apart from deliberately rebuilt valid
runtime cache bytes. The serializer's allocator/free/resource-E lookup are
explicit hooks; memcpy uses the existing libc hook. RNG supplies legal seeded
nibbles rather than reproducing the PS1 PRNG. The add routine itself has only
that RNG substitution; its inventory/history/checksum logic executes normally.
No gameplay, graphics, or emulator-load claim is implied. Branch delay slots
execute; loads are immediate under the established safely scheduled-code
assumption. Unknown instructions/external calls fail closed.

`python -m unittest discover -s tests -v`: **28 tests pass**, including ten new
inventory tests. Coverage includes sparse unsorted arrays, occupied entries
after holes, zero-count stale words, history promotion/reset, integrity
validation/tampering, removal/reuse, capacity and stack overflow, random sparse
states, input rejection, real-candidate preservation, and full serialization.
The prior save reader still emits its unrelated unclosed-file ResourceWarning.

## Reproduction

```powershell
# NEW output filename required. Source snapshot is already inside the workspace.
python scripts/so2_inventory.py artifacts/so2-inventory/source-live-card-20260926.mcd --save S15 --id 364 --count 20 --out artifacts/so2-inventory/seraphic-garb-20-another-copy.mcd

# Regenerate evidence and verify the existing candidate. Requires capstone.
python tools/so2_inventory_evidence.py --source artifacts/so2-inventory/source-live-card-20260926.mcd --candidate artifacts/so2-inventory/seraphic-garb-20-S15-candidate.mcd
python -m unittest discover -s tests -v
```

All writes were confined to `C:/CodeTesting/SaveConverter`. Nothing under
`C:/CodeTesting/StarOcean2/SaveGames` was modified.

## 2026-09-28 Follow-up Investigation: Meaning and Lifecycle of Inventory Bit 15

Investigation date: 2026-09-28. US PS1 SCUS-94421 / BASCUS-94421.

### Result

**Bit 15 is a transient "New Acquisition / Pending Auto-Equip Evaluation" flag.**

When an item is granted to the player, bit 15 is written as `1` by add routine `8003C594`. When a field item pickup or script event occurs, the engine's field update loop detects the new acquisition, invokes the equipment upgrade evaluator `80030FC8` (which tests `srl $v1, $v0, 0xF; beqz $v1` and **only** considers items with bit 15 = 1), optionally presents the field equip prompt, and then executes mass-clearing routine `80030F84` (`andi $v0, $v1, 0x7FFF; sh $v0`), resetting bit 15 to `0` across all 1,024 inventory slots.

This explains why:
1. **Every standalone item producer passes `a3 = 1`**: every newly acquired item starts as "unprocessed / new".
2. **The field restore opcode passes dynamic bit 15**: when restoring confiscated inventory (e.g. Lacour Tournament of Arms), it preserves each item's prior evaluated state.
3. **The runtime integrity calculation `8003C8A0` masks out bit 15 (`andi $s0, $v0, 0x7FFF`)**: bit 15 is dynamic state that gets bulk-cleared on the field; excluding it from the XOR checksum allows `80030F84` to clear bit 15 across all 1,024 slots with a single `sh` instruction without invalidating or recalculating slot integrity bytes.
4. **UI menus (camp item menu, shop sell, battle items) do not display or branch on bit 15**: all UI displays mask count with `(word >> 10) & 0x1F` and ID with `word & 0x3FF`. Bit 15 is not a "NEW" icon or sale-restriction flag.

---

### Comprehensive Caller Census for `8003C594`

An exhaustive binary scan for `jal 0x8003C594` (`65 f1 00 0c`) across all 167 binaries in `artifacts/`, the resident binary (`entry-2576.bin`, LBA 30736, RAM `8002F810`), and all archives on Disc 1 and Disc 2 TOC identified **15 real caller sites**:

#### Resident Binary Callers (11 sites in Entry 2576 / LBA 30736)

| Address | Function / Context | `$a3` Argument | Disassembly |
|---|---|:---:|---|
| `80033674` | General item add wrapper (`80033640`) | `1` | `addiu $a3, $zero, 1` |
| `800336A8` | Single-item add wrapper (`8003368C`) | `1` | `addiu $a3, $zero, 1` |
| `80050A48` | Post-battle spoils / enemy drop processor (`800509E8`) | `1` | `addiu $a3, $zero, 1` |
| `800669D4` | Script VM item grant opcode handler | `1` | `addiu $a3, $zero, 1` |
| `80069394` | Unequip weapon return to inventory | `1` | `addiu $a3, $zero, 1` |
| `800693BC` | Unequip armor return to inventory | `1` | `addiu $a3, $zero, 1` |
| `800693E4` | Unequip shield return to inventory | `1` | `addiu $a3, $zero, 1` |
| `8006940C` | Unequip helmet return to inventory | `1` | `addiu $a3, $zero, 1` |
| `80069434` | Unequip greaves return to inventory | `1` | `addiu $a3, $zero, 1` |
| `80069464` | Unequip accessory 1 return to inventory | `1` | `addiu $a3, $zero, 1` |
| `800695B0` | Unequip accessory 2 return to inventory | `1` | `addiu $a3, $zero, 1` |

All 11 resident callers unconditionally pass `addiu $a3, $zero, 1`.

#### Disc Overlay Callers (4 sites across Overlays 2986, 3012, 3101)

| Archive Entry | Overlay Base | Call Site | Context | `$a3` Argument | Disassembly |
|---|---:|---:|---|:---:|---|
| `2986` | `8007E000` | `8007E8EC` | Shop item purchase | `1` | `addiu $a3, $zero, 1` |
| `3012` | `8007E000` | `800802CC` | Customization output | `1` | `addiu $a3, $zero, 1` |
| `3012` | `8007E000` | `800808E4` | Synthesis output | `1` | `addiu $a3, $zero, 1` |
| `3101` (and duplicates `3112..3174`) | `8007E000` | `8008EB34` | Confiscated inventory restore (Script Opcode `0x10`) | **Dynamic (`word >> 15`)** | `srl $a3, $a3, 0xf` |

Entry 3100 is an uncompressed duplicate sector image of resident entry 2576. Entries `3112..3174` are identical sector placements of field overlay 3101 placed across the disc to reduce CD-ROM seek latency.

---

### The Dynamic Restore Site (`Entry 3101` `8008EB34`)

Script VM opcodes `0x0F`, `0x10`, and `0x33` manage party inventory confiscation and restoration during events (e.g. Lacour Tournament of Arms, prison sequences):

- **Opcode `0x0F` (`800678D8` $\to$ `8008EA0C`)**: Copies all `0xC28` bytes of live inventory `[0x80075278]` to temporary backup buffer `[0x80076228]`, zeros the live array, regenerates checksums, and sets backup flag `8007622c = 1`.
- **Opcode `0x10` (`800678E8` $\to$ `8008EAD8`)**: Restores inventory from `[0x80076228]` back into `[0x80075278]`:

```text
8008EAF4: slti    $v0, $s0, 0x400       ; scan all 1024 slots
8008EAF8: beqz    $v0, 0x8008eb44
8008EAFC: sll     $v0, $s0, 1
8008EB00: lui     $v1, 0x8007
8008EB04: lw      $v1, 0x6228($v1)      ; backup buffer pointer
8008EB0C: addu    $v0, $v0, $v1
8008EB10: lhu     $v0, ($v0)            ; load saved slot word
8008EB18: andi    $a1, $v0, 0x3ff       ; item_id = word & 0x3FF
8008EB1C: beqz    $a1, 0x8008eb3c       ; empty slot -> skip
8008EB20: andi    $a3, $v0, 0xffff      ; entire word
8008EB24: srl     $a2, $a3, 0xa         ; count = (word >> 10) & 0x1F
8008EB28: lui     $a0, 0x8007
8008EB2C: lw      $a0, 0x5278($a0)      ; live inventory pointer
8008EB30: andi    $a2, $a2, 0x1f
8008EB34: jal     0x8003c594            ; add_item(inv, id, count, flag)
8008EB38: srl     $a3, $a3, 0xf         ; flag = word >> 15 (DELAY SLOT)
8008EB3C: j       0x8008eaf4
8008EB40: addiu   $s0, $s0, 1
8008EB44: lui     $at, 0x8007
8008EB48: sb      $zero, 0x622c($at)    ; clear backup flag
```

Because `8008EB38` executes `srl $a3, $a3, 0xF`, it passes the slot's original bit 15. If the item was already processed prior to confiscation (bit 15 = 0), it restores with 0; if it was pending evaluation (bit 15 = 1), it restores with 1.

---

### Consumer Analysis: Field Auto-Equip and Batch Clearing

A complete instruction-by-instruction scan of resident code and all disc overlays for shift-15 (`srl/sll/sra ..., 15`) and masks (`0x7FFF`, `0x8000`, `0x83FF`) identified exactly how bit 15 is consumed and cleared:

#### 1. Field Acquisition Trigger (`80048BA4`, `800669E4`, `8004C9F4`)

When a treasure chest is opened in the field (`80048BA4`) or a script opcode gives an item (`800669E4`), the engine sets byte `[0x80076278] = 1`. In the resident field loop:

```text
8004C9F4: lbu     $v0, 0x6278($v0)      ; check acquisition flag
8004C9FC: beqz    $v0, 0x8004cb9c       ; no new items -> skip
8004CA04: jal     0x80030dec            ; setup evaluation buffer
8004CA40: jal     0x80030d5c            ; evaluate equipment upgrades
```

If an upgrade candidate is found (`$v0 != 0`), `8004CA58` triggers dialog prompt `0xFC2` ("Equip now?").

#### 2. Auto-Equip Candidate Filter (`80030FC8`)

Routine `80030FC8` iterates across all 1,024 inventory slots to find equipment upgrades:

```text
80031080: lhu     $v0, ($v1)            ; load inventory slot word
80031088: andi    $s1, $v0, 0x3ff       ; item_id = word & 0x3FF
8003108C: beqz    $s1, 0x80031178       ; empty slot -> skip
80031090: srl     $v1, $v0, 0xf         ; v1 = bit 15 (flag)
80031094: slti    $v0, $s1, 0x338       ; item_id < 824 (0x338) -> equipment only
80031098: beqz    $v0, 0x80031178       ; consumables/materials -> skip
800310A0: beqz    $v1, 0x80031178       ; IF BIT 15 == 0 -> SKIP!
800310A4: move    $a0, $s2
800310A8: move    $a1, $s1
800310AC: jal     0x8003bb2c            ; can character equip item?
```

`800310A0: beqz $v1, 0x80031178` actively skips any slot where bit 15 is 0. Only items marked with bit 15 = 1 are considered for auto-equip evaluation.

#### 3. Mass-Clearing of Bit 15 (`80030F84`)

Following evaluation across all 8 party members, `80030E6C` unconditionally calls `80030F84` at `80030F54`:

```text
80030F84: move    $a1, $zero            ; slot index 0..1023
80030F88: lui     $a0, 0x8007
80030F8C: lw      $a0, 0x5278($a0)      ; live inventory pointer
80030F90: slti    $v0, $a1, 0x400
80030F94: beqz    $v0, 0x80030fc0       ; done all 1024 slots -> return
80030F9C: lhu     $v1, ($a0)            ; load slot word
80030FA4: andi    $v0, $v1, 0x3ff       ; item_id
80030FA8: beqz    $v0, 0x80030fb4       ; empty -> next
80030FAC: andi    $v0, $v1, 0x7fff      ; CLEAR BIT 15 (word & 0x7FFF)
80030FB0: sh      $v0, ($a0)            ; WRITE BACK TO INVENTORY
80030FB4: addiu   $a0, $a0, 2
80030FB8: j       0x80030f90
80030FBC: addiu   $a1, $a1, 1
80030FC0: jr      $ra
```

This clears bit 15 to `0` across every occupied slot in inventory. Once cleared, those items are never re-evaluated by subsequent field pickup events.

#### 4. The Checksum Exclusion Rationale (`8003C8A0`)

Routine `8003C8A0` generates the per-slot runtime integrity byte:

```text
8003C8C8: andi    $s0, $v0, 0x7fff      ; w = slot_word & 0x7FFF
```

Bit 15 is explicitly stripped before computing XOR parity. Because bit 15 does not contribute to the integrity checksum, `80030F84` is able to mass-clear bit 15 across all 1,024 slots with a simple `sh` store loop without invalidating or recalculating runtime integrity bytes.

#### 5. Item Removal Preservation (`8003C798`)

When items are removed/consumed via `8003C798`:

```text
8003C7D8: andi    $v0, $a1, 0x83ff      ; preserve item_id (0..9) and bit 15
```

If remaining count > 0, the slot retains its existing bit-15 flag state.

---

### UI Menus and Save Files

- **UI Menus (Camp Menu 2985, Shop Sell 2986, Battle Items 3006)**: An audit of all inventory display loops confirms that UI code only inspects `word & 0x3FF` (item ID) and `(word >> 10) & 0x1F` (count). No UI screen reads bit 15 to display a "NEW" tag, alter text colors, or restrict selling.
- **Save File Persistence**: The save serializer (`80081AF0..80081C60`) writes all 1,024 words directly to memory card blocks. Any item added to inventory whose bit 15 has not yet been cleared by a field event retains bit 15 = 1 on the card. Save load regenerates integrity bytes via `8003C8A0`, which ignores bit 15. The format is fully bidirectional and safe regardless of whether bit 15 is 0 or 1.

