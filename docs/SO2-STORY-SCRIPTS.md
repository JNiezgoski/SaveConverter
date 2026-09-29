# Star Ocean 2 (PS1): Dialogue & Story Script Engine Architecture

**Date**: 2026-09-28  
**Status**: ✅ **VERIFIED (Binary Extraction & Disassembly-Verified)**  
**Scope**: Complete PS1 US Disc 1 and Disc 2 Scene Script Bytecode Engine (Archives 3207..4154, ~948 scene containers).  
**Extractor Tool**: [`tools/so2_script_extractor.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_script_extractor.py)  
**Catalog**: [artifacts/so2-scripts/disc1_scenes_catalog.json](file:///C:/CodeTesting/SaveConverter/artifacts/so2-scripts/disc1_scenes_catalog.json)  

---

## 1. Scene Container Architecture

All town maps, dungeon levels, building interiors, and cutscene set-pieces are packaged into multi-part container archives in the range `3207..4154`.

### Container Header Structure

```c
struct SceneContainer {
    uint32_t num_parts;             // Number of sub-archives (typically 2 to 10)
    struct {
        uint32_t tag;               // Part type tag (1 = Script & Dialogue bytecode)
        uint32_t file_offset;       // Byte offset from start of archive to SLZ compressed payload
    } parts[num_parts];
};
```

When `tag == 1`, the decompressed SLZ payload contains the compiled map bytecode, trigger zones, NPC behaviors, and localized dialogue text.

---

## 2. Script Chunk Memory Layout

Each decompressed script chunk contains a header, a compiled bytecode instruction stream, a message offset table, and 16-bit encoded dialogue strings:

```
+-------------------------------------------------------------+
| Header (0x00..0x1B)                                         |
|   +0x00: word0 (uint32) - Bytecode stream length / Msg Base |
|   +0x04: uint32         - Scene Flags / Map Ident           |
|   +0x08: uint32         - Trigger Zone Count                |
|   +0x0C: num_msgs       - Number of Dialogue Messages       |
+-------------------------------------------------------------+
| Bytecode Instruction Stream (0x10 .. word0)                 |
|   Contiguous 32-bit instructions (Opcode, Sub/Mode, Imm16)  |
+-------------------------------------------------------------+
| Message Table Header (word0 .. word0 + 0x1B)                |
+-------------------------------------------------------------+
| Message Offset Array (word0 + 0x1C .. text_base)            |
|   uint16_t offsets relative to text_base (one per msg)      |
+-------------------------------------------------------------+
| Dialogue Text Strings (text_base .. end of chunk)           |
|   16-bit null-terminated string table                       |
+-------------------------------------------------------------+
```

---

## 3. 16-Bit Dialogue Text Encoding Scheme

Unlike the font-substitution cipher used in menu/system archives (e.g. Archive 3015), the scene script engine uses a 16-bit wide character table:

| Code Range | Character Representation | Description |
|---|---|---|
| `0x01B6`..`0x01CF` | `'A'`..`'Z'` | Standard Latin uppercase letters |
| `0x01D0`..`0x01E9` | `'a'`..`'z'` | Standard Latin lowercase letters |
| `0x01AA`..`0x01B3` | `'0'`..`'9'` | Numerical digits 0 through 9 |
| `0x02B6`..`0x02CF` | `'A'`..`'Z'` | Secondary/accented uppercase font glyphs |
| `0x02D0`..`0x02E9` | `'a'`..`'z'` | Secondary/accented lowercase font glyphs |
| `0x0185`, `0x0285` | `' '` | Whitespace space character |
| `0x0183`, `0x0283` | `'.'` | Period / full stop |
| `0x0184`, `0x0284` | `','` | Comma |
| `0x0186`, `0x0286` | `"'"` | Single quote / apostrophe |
| `0x0187`, `0x0287` | `'?'` | Question mark |
| `0x0188`, `0x0288` | `'!'` | Exclamation mark |
| `0x01B5` | `'-'` | Hyphen / dash |
| `0x0189`, `0x018A` | `'"'` | Double quote quotation mark |
| `0x018B`, `0x028B` | `':'` | Colon |
| `0x018C`, `0x028C` | `';'` | Semicolon |
| `0x80xx` / `0x00xx` | Formatting | Box positioning, pause wait, and speaker color codes |

---

## 4. Bytecode Instruction Set Architecture (ISA)

The tri-Ace script VM operates on 32-bit instructions structured as:
`[31..24: Opcode (8-bit)] [23: Mode Flag] [22..16: Sub-Opcode (7-bit)] [15..0: Immediate (16-bit)]`

```
 31         24 23 22          16 15                         0
+-------------+--+--------------+----------------------------+
|   Opcode    |M |  Sub-Opcode  |     16-bit Immediate       |
+-------------+--+--------------+----------------------------+
```

### Verified Instruction Opcodes

| Opcode | Mnemonic | Operands | Function / Operation |
|---|---|---|---|
| `0x00` | `NOP / PUSH0` | `imm` | No-op or push default zero onto operand stack. |
| `0x01` | `JUMP` | `target_pc` | Unconditional jump to relative word offset. |
| `0x0B` | `PUSH_REG` | `slot_id` | Push register or local variable slot value. |
| `0x0D` | `PUSH_LOCAL` | `var_id` | Push local scope variable onto stack. |
| `0x0E` | `READ_FLAG` | `flag_id` | Read global or scene story flag state (`0` or `1`). |
| `0x12` | `PUSH_IMM` | `val16` | Push signed 16-bit immediate value onto operand stack. |
| `0x13` | `PUSH_IND` | `var_id` | Push value from indirect variable pointer. |
| `0x14` | `PUSH_ADDR` | `addr16` | Push 32-bit heap address or bytecode label. |
| `0x15` | `JUMP_ABS` | `target_pc` | Absolute branch jump to target instruction. |
| `0x16` | `BRANCH_COND`| `target_pc` | Branch if top of stack is zero/nonzero (`BEQZ`/`BNEZ`). |
| `0x17` | `CALL` | `sub_id` | Call script subroutine and push return address. |
| `0x18` | `RET` | - | Return from script subroutine. |
| `0x1D` | `TEST_FLAG` | `flag_id` | Test if flag equals immediate condition word. |
| `0x21` | `SET_FLAG` | `flag_id, val`| Write value to story flag (`val=1`: set, `val=0`: clear). |
| `0x22` | `STORE_LOCAL`| `slot_id` | Pop stack and write into local storage slot. |
| `0x38` | `ADD` | - | Integer addition of top two stack operands. |
| `0x3B` | `SUB / CMP` | - | Integer subtraction or comparison check. |
| `0x41` | `CMP_EQ` | - | Test equality of operands (`$s0 == $s1`). |
| `0x7A` | `SHOW_DIALOG`| `msg_id` | Display message window with text index `msg_id`. |
| `0xFF` | `SYSCALL` | `sub_sys, imm`| Game engine syscall dispatcher. |

### Syscall Sub-Dispatch Codes (`0xFF`)

| Sub-Opcode | Syscall Name | Description |
|---|---|---|
| `0x10` | `Matrix_A_Adj` | Adjust Friendship Matrix A affinity points between character pair. |
| `0x11` | `Matrix_A_Get` | Query Friendship Matrix A value between two party members. |
| `0x12` | `Matrix_B_Adj` | Adjust Romance Matrix B affinity points between character pair. |
| `0x13` | `Matrix_B_Get` | Query Romance Matrix B value between two party members. |
| `0x76` | `Affinity_Rank` | Check ending qualification rank for party member pairing. |
| `0x25` | `Audio_BGM` | Trigger BGM track switch or cutscene sound cue. |
| `0x7F` | `Camera_Pan` | Control 2D/3D camera pivot and scroll coordinates. |

---

## 5. Scene Mapping Verification Sample

Extraction across Disc 1 maps all major narrative hubs and dungeons. Scene identity below was
confirmed by cross-referencing decoded map/NPC dialogue against known story locations; in-game text
itself is not reproduced, consistent with this project's sourcing convention.

| Archive ID | Scene ID | Map / Town Name | Message Count | Verification Note |
|---|---|---|---|---|
| `3224` | `Scene 017` | **Arlia (Village Center)** | 301 | Opening-village NPC greeting lines |
| `3225` | `Scene 018` | **Arlia (Rena's House)** | 357 | Rena's-house departure dialogue |
| `3226` | `Scene 019` | **Salva (Approach / Cave)** | 135 | Cross Cave directions dialogue |
| `3230` | `Scene 023` | **Arlia (Church)** | 155 | Church/wedding-venue description dialogue |
| `3231` | `Scene 024` | **Arlia (Newlywed House)** | 199 | Newlywed-couple flavor dialogue |
| `3285` | `Scene 078` | **Cross Castle (Throne Room)**| 182 | Sorcery Globe throne-room exposition |
| `3363` | `Scene 156` | **Linga (Academy Campus)** | 214 | Keith's ancient-language research dialogue |
| `3788` | `Scene 581` | **Disc 2 Ending Engine** | 128 | Ending matrix evaluation and character pair epilogue dispatch |

---

## 6. Project References

- **Script Extractor**: [`tools/so2_script_extractor.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_script_extractor.py)
- **Extracted Catalog**: [`artifacts/so2-scripts/disc1_scenes_catalog.json`](file:///C:/CodeTesting/SaveConverter/artifacts/so2-scripts/disc1_scenes_catalog.json)
- **Flag Correlation**: [`docs/SO2-STORYFLAGS-PART2.md`](file:///C:/CodeTesting/SaveConverter/docs/SO2-STORYFLAGS-PART2.md)
