"""Append 2026-09-28 verification section to docs/SO2-ITEM-RESTRICTIONS.md."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'docs/SO2-ITEM-RESTRICTIONS.md'

SECTION = '''
---

## 2026-09-28 Disassembly & Master Table Verification: Equip-Check Code & Restriction System

### 1. Executive Summary

This investigation locates and verifies the true in-game equipment restriction system in PS1 MIPS disassembly and reads the canonical master item data table from disc archives. 

- **Data Structure**: Every item's equipment eligibility is defined by a dedicated 16-bit little-endian bitmask (`u16`) located at byte offset `+0x04` of its 48-byte master record in Disc Archive Entry `2`.
- **Validation Engine**: In-game validation operates by bitwise AND (`equip_mask & (1 << char_id)`), implemented uniformly across resident auto-equip logic (`800310A0`), fast equipment cache queries (`8003bb2c`), and menu overlays (e.g. Overlay 3012 `80080144` / `80080dc4`).
- **Complete Verification**: All **414 equippable items** (177 weapons, 35 body armors, 19 shields, 25 helmets, 27 boots, 131 accessories) are now 100% verified against code.
- **Fan Data Assessment**: The fan wiki data was ~97% accurate, successfully capturing the broad character groups and oddities like Noel's asymmetric armor vs. accessory classification. However, code verification resolved both flagged uncertainties in the fan doc (confirming **Gusguine** as Claude-only and **Pain Cestus** as Rena-only) and identified **eight concrete contradictions/omissions** in the fan sources.

---

### 2. Disassembly Evidence: Real Equip-Check Code & Accessors

#### A. Universal Property Accessor (`8003C538`, `code-2576-lba-30736.bin`)
Every access to an item's master properties in heap RAM routes through resident function `8003C538`. It computes the item struct offset as `(item_id - 1) * 48` (`(item_id - 1) * 3 << 4`) from the base pointer stored at `[inventory_base + 0x820]`:

```mips
8003c538: bnez     $a1, 0x8003c548
8003c53c: addiu    $a1, $a1, -1          ; index = item_id - 1
8003c540: j        0x8003c58c
8003c544: move     $v0, $zero            ; return 0 for empty slot
8003c548: sll      $v0, $a1, 1           ; index * 2
8003c54c: addu     $v0, $v0, $a1         ; index * 3
8003c550: lw       $v1, 0x820($a0)       ; v1 = live master table pointer
8003c554: sll      $v0, $v0, 4           ; index * 3 * 16 = index * 48 (0x30 bytes)
8003c558: bnez     $a2, 0x8003c56c       ; if offset != 0, check field width
8003c55c: addu     $v1, $v1, $v0         ; v1 = item_record_ptr
8003c560: lw       $v0, ($v1)            ; offset 0: 32-bit Buy Price
8003c564: j        0x8003c58c
8003c568: nop      
8003c56c: addiu    $v0, $a2, -4          ; offset - 4
8003c570: sltiu    $v0, $v0, 0xf         ; if (unsigned)(offset - 4) < 15 (i.e. [4..18])
8003c574: bnez     $v0, 0x8003c588       ; branch to signed 16-bit halfword read
8003c578: addu     $v0, $v1, $a2
8003c57c: lbu      $v0, ($v0)            ; else: unsigned 8-bit byte read
8003c580: j        0x8003c58c
8003c584: nop      
8003c588: lh       $v0, ($v0)            ; return signed 16-bit halfword (stats / equip mask)
8003c58c: jr       $ra
8003c590: nop      
```

Resident function `80034100` wraps `8003C538`, passing the live inventory pointer from `[80075278]`.

#### B. Character Bitmask Generator (`8003381c`, `code-2576-lba-30736.bin`)
To test an item against a party member, the game resolves the party member's 1-based character ID (`1..12`) via `800337a4` and computes `1 << (char_id - 1)`:

```mips
8003381c: addiu    $sp, $sp, -0x18
80033820: sw       $ra, 0x10($sp)
80033824: jal      0x800337a4            ; returns 1-based character ID in $v0
80033828: nop      
8003382c: move     $a1, $v0
80033830: beqz     $a1, 0x8003385c       ; if char_id == 0, return 0
80033834: addiu    $a0, $zero, 1
80033838: slt      $v0, $a0, $a1
8003383c: beqz     $v0, 0x80033860       ; if char_id == 1 (Claude), return 1 (1 << 0)
80033840: addiu    $v1, $zero, 1
80033844: addiu    $v1, $v1, 1           ; loop v1 from 2 up to char_id
80033848: slt      $v0, $v1, $a1
8003384c: bnez     $v0, 0x80033844
80033850: sll      $a0, $a0, 1           ; a0 = a0 << 1 (computes 1 << (char_id - 1))
80033854: j        0x80033860
80033858: nop      
8003385c: move     $a0, $zero
80033860: lw       $ra, 0x10($sp)
80033864: move     $v0, $a0              ; returns single-bit character mask
80033868: jr       $ra
8003386c: addiu    $sp, $sp, 0x18
```

#### C. In-Game Equip-Validation Check (`800310A0`, `code-2576-lba-30736.bin`)
The real restriction check occurs when evaluating whether a character can equip an item:

```mips
800310a4: move     $a0, $s2              ; fast cache table pointer
800310a8: move     $a1, $s1              ; s1 = item_id
800310ac: jal      0x8003bb2c            ; selector 0: fetch item's 16-bit equip mask
800310b0: move     $a2, $zero            ; a2 = 0 (selector 0 = equip mask)
800310b4: and      $v0, $v0, $s4         ; BITWISE AND: equip_mask & (1 << char_id)
800310b8: beqz     $v0, 0x80031178       ; IF ZERO: CANNOT EQUIP! Branch to skip item!
800310bc: addiu    $s0, $zero, -1
```

#### D. Menu Overlay Equip Validation (Overlay 3012 `80080144` / `80080dc4`)
In menu overlays (such as Item Creation / Equipment evaluation Overlay 3012), the identical validation is executed directly via `80034100`:

```mips
; 80080144: Overlay 3012 Equip Validation
80080140: move     $a0, $s1              ; s1 = item_id
80080144: jal      0x80034100            ; property accessor
80080148: addiu    $a1, $zero, 4         ; offset 4 (16-bit equip mask)
8008014c: and      $v0, $v0, $s3         ; s3 = character bitmask (1 << char_id)
80080150: beqz     $v0, 0x80080204       ; IF ZERO: item is blocked / non-equippable!

; 80080dc4: Overlay 3012 Secondary Filter
80080dc0: move     $a0, $s1              ; s1 = item_id
80080dc4: jal      0x80034100            ; property accessor
80080dc8: addiu    $a1, $zero, 4         ; offset 4 (16-bit equip mask)
80080dcc: and      $v0, $v0, $s6         ; s6 = character bitmask
80080dd0: beqz     $v0, 0x80080dec       ; IF ZERO: item rejected
```

---

### 3. The Real Restriction Data Structure

Equip restrictions are not derived from complex runtime character class or level rules. Every item stores an independent 16-bit little-endian bitmask (`u16`) at byte offset `+0x04` of its 48-byte record in Disc Archive Entry 2:

| Bit | Value | Character | In-Game Role |
|---|---|---|---|
| **0** | `0x0001` | **Claude** | Longsword Fighter |
| **1** | `0x0002` | **Rena** | Knuckles / Mage |
| **2** | `0x0004` | **Celine** | Rod Mage |
| **3** | `0x0008` | **Bowman** | Knuckles Fighter |
| **4** | `0x0010` | **Dias** | Longsword Fighter |
| **5** | `0x0020` | **Precis** | Mechanical Hand Fighter |
| **6** | `0x0040` | **Ashton** | Dual-Sword Fighter |
| **7** | `0x0080` | **Leon** | Book Mage |
| **8** | `0x0100` | **Opera** | Kaleidoscope Launcher Fighter |
| **9** | `0x0200` | **Ernest** | Whip Fighter |
| **10** | `0x0400` | **Noel** | Knuckles / Mage |
| **11** | `0x0800` | **Chisato** | Stun Gun Fighter |

#### Canonical Archetypal Bitmasks in Star Ocean 2
- `0x0FFF` ($4095$): **Universal** (All 12 characters).
- `0x0F79` ($3961$): **Full Fighter Group** (Claude, Bowman, Dias, Precis, Ashton, Opera, Ernest, Noel, Chisato).
- `0x0F59` ($3929$): **Heavy Fighter Group** (Fighters excluding Precis: Claude, Bowman, Dias, Ashton, Opera, Ernest, Noel, Chisato).
- `0x0B79` ($2937$): **Standard Fighter Group** (Fighters excluding Noel: Claude, Bowman, Dias, Precis, Ashton, Opera, Ernest, Chisato).
- `0x06D9` ($1753$): **Male Characters** (Claude, Bowman, Dias, Ashton, Leon, Ernest, Noel).
- `0x0926` ($2342$): **Female Characters** (Rena, Celine, Precis, Opera, Chisato).
- `0x0086` ($134$): **Core Magicians** (Rena, Celine, Leon).
- `0x0486` ($1158$): **Extended Magicians** (Rena, Celine, Leon, Noel).
- `0x0904` ($2308$): **Female Casters / Gunners** (Celine, Opera, Chisato).
- `0x0051` ($81$): **Swordsmen Trio** (Claude, Dias, Ashton).
- `0x0011` ($17$): **Swordsmen Duo** (Claude, Dias).
- `0x0000` ($0$): **Nobody / Unusable** (Perforated Armor, dummy items).

#### Resolution of the Noel "Dual Classification" Mystery
The fan guide noted that Noel is treated as a Fighter for armor, but as a Magician for accessories. Code disassembly reveals why: **there is no unified character class system**. The item author simply tagged Noel's bit (`bit 10`, `0x0400`) in the `u16` bitmask of heavy armors (`0x0F79`/`0x0F59`) and in the bitmask of magic accessories (`0x0486`), while leaving bit 10 cleared on fighter accessories (`0x0B79`, e.g. Link Combo).

---

### 4. Direct Comparison with Fan Wiki Data

All 414 equippable items in the game were cross-referenced against the fan-sourced tables in this document.

#### A. Resolution of Flagged Uncertainties
| Item | Fan Doc Claim | Code Bitmask | Real Allowed Characters | Verdict |
|---|---|---|---|---|
| **Gusguine** (Sword) | Listed `C/D` with note "C-only per some sources" | `0x0001` | **Claude only** | ✅ **Confirmed**: Claude-only note is correct; Dias cannot equip. |
| **Pain Cestus** (Knuckles) | Listed `R only`, noted conflict with older FAQ listing Noel | `0x0002` | **Rena only** | ✅ **Confirmed**: Rena-only; Noel cannot equip. |
| **Star Guard** (Shield) | Flagged as excluding Re/Le/Ce/No | `0x0B79` | **Cl/Bo/Di/Pr/As/Op/Er/Ch** | ✅ **Confirmed**: Exact match with code and equip failure. |
| **Serpent's Tooth** (Knuckles) | Flagged Noel-exclusive | `0x0400` | **Noel only** | ✅ **Confirmed**: Noel-exclusive. |
| **Leather Helm** (Helmet) | Flagged as universal | `0x0FFF` | **All 12 characters** | ✅ **Confirmed**: Universal. |

#### B. Discovered Fan Wiki Contradictions & Corrections
| Item | Category | Fan Doc Claim | Code Bitmask | Real Allowed Characters | Concrete Correction |
|---|---|---|---|---|---|
| **Cat's Fangs** | Knuckles | Listed under `N` (Noel only) | `0x0402` | **Rena, Noel** | Rena CAN equip Cat's Fangs. |
| **Rune Full Moon** | Knuckles | Listed under `R only` | `0x000A` | **Rena, Bowman** | Bowman CAN equip Rune Full Moon. |
| **Weird Slayer** | Weapon | `Bo/Ch/No/Pr/Re` | `0x082A` | **Rena, Bowman, Precis, Chisato** | Noel CANNOT equip Weird Slayer. |
| **Steel Armor** | Body Armor | `Fighters` (implies Precis) | `0x0F59` | **Cl/Bo/Di/As/Op/Er/No/Ch** | Precis CANNOT equip Steel Armor. |
| **Barrier Armor** | Body Armor | `Fighters` (implies Precis) | `0x0F59` | **Cl/Bo/Di/As/Op/Er/No/Ch** | Precis CANNOT equip Barrier Armor. |
| **Bloody Armor** | Body Armor | `Fighters` (implies Precis) | `0x0F59` | **Cl/Bo/Di/As/Op/Er/No/Ch** | Precis CANNOT equip Bloody Armor. |
| **Duel Helm** | Helmet | `Fighters` | `0x0659` | **Cl/Bo/Di/As/Er/No** | Males except Leon. Precis, Opera, Chisato CANNOT equip; Noel CAN. |
| **The Armband of Kali** | Shield | `Ce/Ch/Pr/Re` | `0x0926` | **Re/Ce/Pr/Op/Ch** | Opera CAN equip The Armband of Kali (universal female shield). |
| **General's Ring** | Accessory | `Claude route only, Celine not in party` | `0x0FFF` | **All 12 characters** | Equip mask is universal; restriction is quest acquisition only. |

---

### 5. Final Verification Status

| Equipment Category | Total Game Items | Code Verified | Fan Data Match Rate |
|---|---|---|---|
| **Weapons** | 177 | 177 (100%) | 97.7% (4 corrections: Gusguine, Cat's Fangs, Rune Full Moon, Weird Slayer) |
| **Body Armor** | 35 | 35 (100%) | 91.4% (3 corrections: Steel Armor, Barrier Armor, Bloody Armor) |
| **Shields** | 19 | 19 (100%) | 94.7% (1 correction: The Armband of Kali) |
| **Helmets** | 25 | 25 (100%) | 96.0% (1 correction: Duel Helm) |
| **Boots & Greaves** | 27 | 27 (100%) | 100% (Exact match across all boots) |
| **Accessories** | 131 | 131 (100%) | 99.2% (1 clarification: General's Ring) |
| **Total Equippable** | **414** | **414 (100%)** | **97.6% overall match** |

For the complete item-by-item parameter catalog (stats, buy/sell prices, element affinities, proc IDs, and equip masks for all 823 active game items), see [docs/SO2-ITEM-DATABASE.md](SO2-ITEM-DATABASE.md).
'''

def main():
    text = TARGET.read_text(encoding='utf-8')
    if '## 2026-09-28 Disassembly & Master Table Verification' in text:
        print('Section already present, skipping.')
        return
    text = text.rstrip() + '\n' + SECTION.lstrip()
    TARGET.write_text(text, encoding='utf-8')
    print(f'Successfully appended verification section to {TARGET}.')

if __name__ == '__main__':
    main()
