# SO2 raw-header story-flags candidate: bounded code check

Investigation date: 2026-09-26. US PS1, SCUS-94421 / BASCUS-94421.

## Finding

**The bytes are read and written by save/load code, through a fixed-range
copy. Their interpretation as story/event flags remains inconclusive.**
The save writer at `0x80080FC0` copies 256 bytes from live state into raw
save offsets `0x280..0x37F`, including all of `0x2B4..0x2E3`. The load
routine at `0x80081990` copies that range back. Thus there is a concrete
write trigger: constructing a save, via the copy call at `0x800817E4`.
This is not evidence of a story-script opcode changing an individual flag.

No individual header-relative field access in the requested 48-byte range
was established by this check. In particular, this is **not** a finding
that no code touches the range, nor proof that every byte in the copied
range has gameplay meaning. Bulk serialization can also preserve unused
bytes. Downgrade the old "strongest untouched lead" to **checked,
inconclusive as story flags; save/load copying confirmed**.

## Sources and address conventions

Used the established extraction and pointer conventions in
[the Fol investigation](SO2-FOL-INVESTIGATION.md) and
[the checksum investigation](SO2-CHECKSUM-INVESTIGATION.md).
Here `B` is the start of the entire save block (the user's `header_base`),
not the signature/checksum header at `B+0x200`.
`S = [0x80075270]` is the dynamically allocated live-state pointer.

| Source | Disc location | RAM/load address | Relevant evidence |
|---|---|---|---|
| `artifacts/so2-fol/disc-code/code-2998-lba-36213.bin` | SO2.BIN entry 2998, LBA 36213 | `0x8007E000` | Save/load overlay; copy call sites |
| `artifacts/so2-fol/disc-code/code-2576-lba-30736.bin` | SO2.BIN entry 2576, LBA 30736 | `0x8002F810` | Resident fixed-offset candidate scan |
| `SCUS_944.21;1` | LBA 24; payload starts LBA 25 | `0x80010000` | Resident byte-copy helper `0x80023ED0` |

Archive entries are compressed on disc: RAM address minus load address is
an offset into the **extracted entry**, not a byte offset into its disc sectors.
For example, `0x800817E4` is entry-2998 offset `0x37E4`, and `0x80081A34`
is offset `0x3A34`. The executable helper is payload offset `0x13ED0`
(EXE file offset `0x146D0`).

Entry 2998 SHA256:
`f56ace2f46ff6c3d886e5f372a1e8f41db9da1d3667e65c4afb9189ddc3d9186`.
Entry 2576 SHA256:
`6dec3950348b57068a85759f472ea7d5c92241d28b00ff4ea139ddd8dc1587cf`.
The executable payload (`0x1F800` bytes) SHA256 is
`9bd6d6c52056c2a8c91633ab44900ae687a67ba51bf29ed4d8f8c87e83f96a4b`.
Its helper bytes were checked against the existing `artifacts/so2-fol/ram.bin`
and match at `0x80023ED0..0x80023F03`. The disc was read only; no new
archive extraction or tool was needed. The suggested party/inventory
`disc-code` directories do not exist in this workspace; their existing
evidence tools also use the Fol extraction.

## Fixed-range write and read evidence

Selected instructions from entry 2998; gaps are intentional. MIPS call
and branch delay slots execute before control transfers.

```text
80080FD0 move  s5,a1             ; save writer argument: B
80081110 move  s3,s5             ; s3 = B
800816D0 addiu s2,s3,0x200       ; s2 = B+0x200 (aligned copy path)
80081728 move  s3,s2             ; s3 = B+0x200
80081798 addiu s3,s3,0x80        ; s3 = B+0x280
8008179C move  a0,s3             ; copy destination
800817BC addiu a2,zero,0x100     ; copy length
800817D8 lui   a1,0x8007
800817DC lw    a1,0x5270(a1)     ; S
800817E0 addiu s3,s3,0x100       ; next serialization position B+0x380
800817E4 jal   0x80023ED0
800817E8 addiu a1,a1,0x1A0       ; delay slot: source S+0x1A0
```

The unaligned preceding copy path establishes the same `s2=B+0x200`
at `0x800816A0`. Therefore, for `0 <= i < 0x100`, the call writes
`B[0x280+i] = S[0x1A0+i]`. In the requested range:

```text
raw B+0x2B4..B+0x2E3  <->  live S+0x1D4..S+0x203
```

This is a live-memory offset, **not** an offset in the decompressed save
stream. In the existing Disc-1 RAM artifact, `S=0x8009A9C0`, so the live
range is `0x8009AB94..0x8009ABC3`; its address changes with allocation.

The reverse copy follows successful body-checksum validation:

```text
800819F4 lw    s2,0x7BC(a1)      ; B, save input buffer
80081A08 addiu s1,s2,0x280
80081A1C bne   s0,v0,0x80081A50  ; reject checksum mismatch
80081A20 addiu v0,zero,-2
80081A24 move  a1,s1             ; source B+0x280
80081A28 lui   a0,0x8007
80081A2C lw    a0,0x5270(a0)     ; S
80081A30 addiu a2,zero,0x100
80081A34 jal   0x80023ED0
80081A38 addiu a0,a0,0x1A0       ; delay slot: destination S+0x1A0
```

The resident helper supplies the actual load/store instructions:

```text
80023ED0 beqz  a0,0x80023EFC
80023ED4 move  v0,zero
80023ED8 blez  a2,0x80023EF8
80023EDC move  v1,a0
80023EE0 lbu   v0,0(a1)
80023EE4 addiu a1,a1,1
80023EE8 addiu a2,a2,-1
80023EEC sb    v0,0(a0)
80023EF0 bgtz  a2,0x80023EE0
80023EF4 addiu a0,a0,1
80023EF8 move  v0,v1
80023EFC jr    ra
80023F00 nop
```

On save-copy iterations `0x34..0x63` (zero-based), its `sb` writes precisely
the requested 48 bytes. On load, its `lbu` reads them. The caller is an
overlay, while the copy helper is resident executable code; this distinction
matters when interpreting "resident reference." There is no literal
`0x2B4` displacement in this path: pointer setup plus loop coverage proves
the access.

## Scope and limits

Scanned aligned MIPS load/store and address-add immediate candidates in
the five existing extracted entries (2576, 2982, 2985, 2986, 2998), for
raw offsets `0x2B4..0x2E3` and the corresponding live offsets
`0x1D4..0x203`; inspected save/load pointer setup and relevant live-state
pointer contexts. Equal numeric displacements alone are not evidence of
save-header access. This is a bounded static check, not exhaustive alias
analysis or a claim to have ruled out indexed accesses in all overlays.

The raw candidate lies before the compressed stream at `0x382`; no codec
is involved. The old button-config citation at raw `0x382` is inconsistent
with the established compression result and was not used as an address
anchor. The preview writer remains a valid control: `s2=B+0x200`, then
`0x80081770` starts its offset at `0x34`, and `0x80081780/84` passes
`B+0x234` to the preview helper.

No before/after gameplay test, bit-to-event mapping, or mapping of another
save region was attempted. A future investigation could trace indexed
writers to this live-state range; that is left open here. Only this note
and the story/event-flags open item were changed. Nothing under
`C:/CodeTesting/StarOcean2/SaveGames` was modified.
