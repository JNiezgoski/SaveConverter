# SO2 special attack/magic list: assignment UI found, nine-entry claim unresolved

Investigation date: 2026-09-27. US PS1 Disc 1, SCUS-94421 / BASCUS-94421.

## Finding

**The reported nine-entry `8009B994..8009B9A4` cheat list remains unmapped.**
This pass did find and execute an ability-assignment menu in archive entry
**3004**, including its candidate builder, assignment reader and commit store.
Its persistent assignment storage is **four one-byte ability IDs**, at decoded
**`0x56C..0x56F + slot*0xD0`**, in the secondary character record. The ordinary
display reads the first two; an additional mode displays all four. It is not
a nine-halfword assignment list or a bitmask of the 46 proficiency skills.

The menu also accesses 32 ability-availability bytes and an indexed halfword
array in that same record. Neither the halfwords' complete meaning nor their
correspondence to the historical cheat addresses was established. In particular,
**do not label nine of those halfwords as button assignments**. This is a
positive map of the actual assignment storage, but a **checked-and-inconclusive
result for the specific nine-entry claim**. No new editor or candidate card was
created.

## Sources and scope

Reused the addressing, compression and extraction methods from the
[Fol investigation](SO2-FOL-INVESTIGATION.md),
[checksum investigation](SO2-CHECKSUM-INVESTIGATION.md),
[party investigation](SO2-PARTY-MEMBER-INVESTIGATION.md), and
[specialty investigation](SO2-SPECIALTY-INVESTIGATION.md).

The requested `artifacts/so2-party/disc-code/` and
`artifacts/so2-inventory/disc-code/` directories do not exist in this workspace.
The resident/shared UI/menu-summary extracts under `so2-fol` were checked first.
Further existing menu extracts were found under `so2-specialty/disc-code/`;
scanning their selected-secondary-pointer and assignment-byte references led
to entry 3004. **No new disc or resume extraction was performed.**

| Existing extract | LBA | Load | Size |
|---|---:|---|---|
| `artifacts/so2-fol/disc-code/code-2576-lba-30736.bin` | 30736 | `8002F810` | `4C7FC` |
| `artifacts/so2-specialty/disc-code/code-3004-lba-36241.bin` | 36241 | `8007E000` | `6204` |
| `artifacts/so2-fol/disc-code/code-2998-lba-36213.bin` | 36213 | `8007E000` | `4D28` |

SHA256, in that order:

```text
6dec3950348b57068a85759f472ea7d5c92241d28b00ff4ea139ddd8dc1587cf
0960a153c9556a57f9d49d37a8943837199c88598b217a108b88ff8a8af937bb
f56ace2f46ff6c3d886e5f372a1e8f41db9da1d3667e65c4afb9189ddc3d9186
```

Addresses below are loaded instruction addresses, **overlay-specific** where
applicable. For example, entry-3004 `80080288` is extracted-file offset `2288`;
entry 2998 at that same RAM address contains unrelated code. The resident menu
resource dispatcher selects `0xBBC = 3004` at `80034EC8/CC`; `80034F80/84`
passes that resource ID to `80011B98`, and `80034FF4/F8` passes it and the
destination to loader `80038EEC`. Entry 3004's internal UI pointers target its
`80083xxx..80084xxx` data, consistent with the `8007E000` load.

Byte-bearing focused listings: [evidence.asm](../artifacts/so2-special-attack/evidence.asm).
Hashes, per-slot outputs and checks: [verification.json](../artifacts/so2-special-attack/verification.json).
Reproducer: [tools/so2_special_attack_evidence.py](../tools/so2_special_attack_evidence.py).

### Historical source limitation

Read-only inspection found no `8009B994`, `8009B9A4`, or “Special Attack/Magic
Max” entry in `C:/CodeTesting/StarOcean2/gameshark_codes.txt`. The actual local
lead is **`C:/CodeTesting/StarOcean2/skill_order.txt`, lines 2 and 8–10**. It
attributes the addresses to Almar's Guides' “First Position” page and explicitly
calls the attack-button interpretation **“likely”**. That is a prior hypothesis,
not a verified description of the field. This pass did not retrieve the web
page or independently verify its cheat values.

SHA256:

```text
gameshark_codes.txt 452b729f8b5aee05dd67e49f126802c8c352d6271568b06fc33ca1ab57e0e98a
skill_order.txt     9b4903472b5d18a057d9179626bb40c4a7525d05de86c59602439162d3b8bbab
```

## Live pointer and save correspondence

Let `Q=[80075280]`, `P=[80074080]`, and `s` be the selected party slot (0..7).
Resident selector `800331C8` computes **`P=Q+s*0xD0`** and the parallel primary
pointer with stride `0x60`. The relevant instructions are:

```text
800331C8 sll   v0,a0,1
800331CC addu  v0,v0,a0       ; 3*s
800331D4 sll   v0,v0,2       ; 12*s
800331E0 addu  v0,v0,a0      ; 13*s
800331F4 lw    v1,5280(v1)   ; Q
800331F8 sll   v0,v0,4       ; D0*s
80033204 addu  v1,v1,v0
8003320C sw    v1,4080(at)   ; P
```

Entry 2998 copies `0x680 = 8*0xD0` bytes between `Q` and decoded buffer
`+0x4A0` (`80081B20..80081B2C`). Its helper `80081C38` selects the direction;
the load branch moves `a3` (live pointer) into the destination at `80081C48`
and decoded pointer `a2` into the source in the delay slot at `80081C50`.
Thus secondary-relative `+CC` corresponds to decoded `4A0+CC = 56C`, not to
the primary unresolved ranges and not to a new allocation.

Existing RAM snapshots illustrate why historical absolute addresses cannot
be translated without their original allocation state:

| Dump under `artifacts/so2-fol/` | `Q` | Slot-0 assignment addresses | Bytes |
|---|---|---|---|
| `ram.bin` | `8009B8A8` | `8009B974..8009B977` | `00 00 00 00` |
| `SCUS-94422_resume.ram` | `8009BBB8` | `8009BC84..8009BC87` | `07 0B 00 00` |

These are slot-0 observations, not assertions that slot 0 was the selected
menu character when the snapshots were made. For any selected slot the code
uses `P+CC..CF`. Neither snapshot establishes the allocation or slot numbering
used by the cheat author. No numeric subtraction from the cheat addresses was
used to assign a decoded field.

## Assignment menu: candidate IDs and byte writes

All addresses in this section belong to entry 3004. The candidate builder
`800800B8..80080168` clears its temporary list, inserts choice zero, then walks
**32**, not nine, secondary bytes:

```text
800800D0 addiu a1,zero,1     ; list count includes zero / clear assignment
800800D4 move  t2,zero      ; ability index
800800DC lw    t4,4080(t4)  ; selected secondary P
800800E4 sw    zero,5C(s1)  ; choice 0
800800E8 slti  v0,t2,20     ; 32 candidate positions
800800EC beqz  v0,8008016C
800800F0 addu  v0,t4,t2     ; delay slot
800800F4 lb    v0,3C(v0)    ; availability byte P+3C+index
800800FC beqz  v0,80080164  ; unavailable
80080100 addiu t1,t2,1      ; one-based ability ID, delay slot
...
80080110 slti  v0,a2,2      ; two groups
80080118 addiu v1,a0,CC
8008011C addiu a3,a0,CE     ; two bytes per group
80080120 lbu   v0,0(v1)
80080128 bne   t1,v0,80080134
80080130 move  t0,zero      ; exclude an already-assigned ID
...
80080158 sw    t1,5C(t3)    ; append eligible ID to temporary UI word list
80080160 addiu a1,a1,1
80080168 addiu t2,t2,1
```

The temporary list uses **words** at UI context `+5C`, but the persistent
assignment uses **bytes**. `800801F4/F8` stores the chosen group and column at
context `+54/+58`. The selection callback reads the cursor at context `+34`:

```text
80080254 lw    v0,54(s0)    ; group
8008025C lw    v1,4080(v1)  ; P
80080260 lw    a2,58(s0)    ; column
80080264 sll   v0,v0,1
80080268 addu  v0,v0,v1
8008026C lh    v1,34(s0)    ; candidate-list cursor
80080270 addiu v0,v0,CC
80080274 sll   v1,v1,2
80080278 addu  v1,v1,s0
8008027C lw    v1,5C(v1)    ; chosen ID
80080280 addu  v0,v0,a2
80080284 jal   800E0984     ; UI notification; delay slot commits first
80080288 sb    v1,0(v0)     ; P+CC+2*group+column
```

The corresponding reader `8007EE50..8007EE64` loads the same selected pointer,
forms `P+2*group+column`, and uses **`lbu a1,CC(v0)`**. Zero is the explicit
clear choice; IDs 1..32 index the character's availability array. They are
character-local ability indices, not the 46 general proficiency skill IDs.
The full sign semantics of the availability bytes are not mapped here; the
candidate loop only requires nonzero, even though it uses signed `lb`.

Ordinary rendering loads `+CC` at `8007FAF8` and `+CD` at `8007FB58`.
The branch at `8007FA9C`, gated by secondary `+3B`, instead displays
`CC,CE` and `CD,CF` (`8007FBB0/FBC8/FC28/FC40`). The setup likewise supplies
a count of two at `8007F954`; the alternate path configures additional controls.
The trace supports two ordinary selections plus two additional-mode selections.
Exact controller-button labels and that mode's complete enabling rules were
not established here, so no unconditional “four usable buttons” claim is made.

| Secondary-relative | Decoded slot-0 | Established use |
|---|---|---|
| `+3C..5B` | `4DC..4FB` | 32 per-ability bytes tested for candidate availability |
| `+8C..CB` | `52C..56B` | 32 indexed halfwords read by ability detail UI; semantics incomplete |
| `+CC..CF` | `56C..56F` | Four unsigned-byte assignment IDs; zero clears |

For other slots add `slot*D0` to decoded addresses. The halfword relationship
comes from the detail reader: `8007EFE8 sll a1,s1,1`, `8007EFF0 lw
v1,4080(v1)`, `8007F000 addu v1,v1,a1`, and **`8007F008 lh a2,8A(v1)`**.
Here `s1` is a nonzero one-based ability ID; ID 1 therefore reads `P+8C`.
This establishes the address and signed-halfword read, not a safe maximum,
usage-count encoding, or nine-entry boundary. It is a focused future lead
for the “Max” cheat description, not a field assignment based on that name.

## Executed verification

Run from the workspace:

```powershell
python tools/so2_special_attack_evidence.py
```

The harness pins resident/menu/serializer code hashes and uses the existing
`Machine` interpreter. It executes extracted MIPS instructions, including
branch delay slots, rather than a Python replacement of the candidate builder
or assignment store. Loads are immediate as in earlier bounded investigations;
this is not cycle-accurate PS1 emulation.

Inputs are the **retained decoded captures** in `artifacts/so2-specialty/`, not
an assumption about what today's card boxes contain:

```text
S01.decoded 18536c1d4a294eabcf34cbd05856aa004606b17cab018cba153a24f534283340
S02.decoded 2af887cf9adf8ab852d868cea1ac5b07e4a11946167d1c25e42b4389050b6192
S15.decoded 8f457cf6feac4fd96fe8fb2cef99b8e1698f23f43921db3b0ebf86d020c2ce40
```

For each capture, the actual serializer direction helper loads primary and
secondary arrays into deliberately separate allocations (`80100000` and
`80110000`), using only the existing host `memcpy` substitution. The actual
resident selector is then run for every slot. Results:

- **24 complete candidate-loop executions** exactly matched nonzero availability
  bytes with assigned IDs excluded, plus the explicit zero choice.
- **96 assignment reads** matched all four original bytes in all 24 records.
- **768 indexed halfword reads** matched the saved halfwords for IDs 1..32.
- **96 isolated commit executions** wrote the chosen candidate to exactly
  `P+CC+2*group+column`. Whole emulated-memory comparison and the store log
  allowed only that one-byte store and the callback's stack prologue stores.
  All other primary/secondary bytes, including the halfword array, were preserved.

Example outputs (IDs and choices decimal):

| Capture / slot | Character ID | Read assignment bytes | Candidate list |
|---|---:|---|---|
| S01 / 0 | 1 | `7,11,0,0` | `0,1,2,4,5,6,8,9,10` |
| S01 / 1 | 9 | `1,4,0,0` | `0,2,3,5,6,7,8,9` |
| S02 / 1 | 7 | `8,3,0,0` | `0,1,2,4,5,6,7,9,10` |
| S15 / 1 | 1 | `0,0,0,0` | `0,1` |

For example, S01 slot 0's first isolated commit writes candidate 1 to decoded
`56C`, replacing 7; the other three assignment bytes remain `11,0,0`.
Every group/column trial restores the original record before execution.
Empty and spellcaster records were also exercised as structural tests; this
does **not** assert that the normal UI exposes this callback for every class,
or that forcing an assignment into an empty slot is valid gameplay.

Candidate execution stops at `8008016C` before UI layout calls; assignment
reading stops before `8007EF74`; commit execution stops upon entering
`800E0984`, **after** the store in its call delay slot. The later
`80038DFC` refresh and UI-close path are outside the test. No graphics/input
simulation, full menu execution, codec round-trip, or emulator-load result is
claimed. No source save, memory card, or file under `StarOcean2/SaveGames`
was modified; all generated evidence is inside this workspace.

## What remains open

No original cheat-author RAM snapshot or instruction-backed correspondence
links `8009B994..8009B9A4` to these allocations. The assignment UI found here
provides concrete contrary evidence to the old *interpretation* of a universal
nine-slot shortcut list, but cannot prove what those historical addresses meant.
The primary `+04..0F` and `+5A..5F` ranges remain unresolved; this pass neither
assigns the nine entries to them nor proves they lack other battle data.
Follow-up, if desired, should establish the original cheat context or trace
the `+8C` halfword writers. No unrelated character-region mapping is attempted.
