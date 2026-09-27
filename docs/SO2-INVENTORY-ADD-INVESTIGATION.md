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
python so2_inventory.py artifacts/so2-inventory/source-live-card-20260926.mcd --save S15 --id 364 --count 20 --out artifacts/so2-inventory/seraphic-garb-20-another-copy.mcd

# Regenerate evidence and verify the existing candidate. Requires capstone.
python tools/so2_inventory_evidence.py --source artifacts/so2-inventory/source-live-card-20260926.mcd --candidate artifacts/so2-inventory/seraphic-garb-20-S15-candidate.mcd
python -m unittest discover -s tests -v
```

All writes were confined to `C:/CodeTesting/SaveConverter`. Nothing under
`C:/CodeTesting/StarOcean2/SaveGames` was modified.
