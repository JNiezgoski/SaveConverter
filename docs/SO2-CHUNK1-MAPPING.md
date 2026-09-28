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
