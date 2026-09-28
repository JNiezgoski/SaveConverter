# Star Ocean 2: Master Item Database & Struct Specification

**Date**: 2026-09-28  
**Status**: ✅ **VERIFIED (Executed & Disassembly-Verified)**  
**Scope**: Complete PS1 US Disc 1 and Disc 2 Master Item Data Table (Archive Entry 2, 48-byte records, 1,023 item capacity, 823 active items).  

---

## 1. Master Item Table Architecture

In *Star Ocean: The Second Story*, all item definitions—including weapons, armor, accessories, consumables, food, crafting materials, and key items—are stored in a single, contiguous fixed-width struct array indexed by Item ID.

### Storage & Location
- **Disc Archive Location**: Disc Archive Entry `2` on both Disc 1 (LBA 375, compressed 10,240 bytes) and Disc 2 (exact binary match).
- **Compression Format**: SLZ2 (`53 4C 5A 02`).
- **Decompressed Payload Size**: `49,104` bytes (`0xBFD0`).
- **Record Geometry**: Exactly 1,023 records of `48` bytes (`0x30`) each ($1023 \times 48 = 49,104$ bytes).
- **Item ID Indexing**: 1-based index where record for `item_id` starts at byte offset `(item_id - 1) * 48`. `item_id = 0` denotes "None/Empty". Active item IDs range from `0x001` (1) through `0x337` (823). Records `824` through `1023` are zero-padded allocation capacity.
- **CodeBreaker Code Mapping**: `CodeBreaker Code = 0x5000 + Item_ID`.

### Live RAM Resolution & Accessors
During gameplay, the entire master item table is decompressed into heap RAM. The heap pointer to the start of this table is stored at offset `+0x820` of the inventory chunk (see [docs/SO2-INVENTORY-ADD-INVESTIGATION.md](SO2-INVENTORY-ADD-INVESTIGATION.md)):
- `[80075278] + 0x820`: Holds the 32-bit RAM address of the decompressed 48-byte item table (e.g. `0x80129F38` in live dumps).

Resident getter function `8003C538` (`code-2576-lba-30736.bin`) provides the canonical universal property access:
```mips
; 8003C538: Universal Item Property Getter
; Inputs: $a0 = live inventory base pointer, $a1 = item_id (1-based), $a2 = byte offset within struct
; Output: $v0 = requested field value
8003c538: bnez     $a1, 0x8003c548
8003c53c: addiu    $a1, $a1, -1          ; index = item_id - 1
8003c540: j        0x8003c58c
8003c544: move     $v0, $zero            ; if item_id == 0, return 0
8003c548: sll      $v0, $a1, 1           ; v0 = index * 2
8003c54c: addu     $v0, $v0, $a1         ; v0 = index * 3
8003c550: lw       $v1, 0x820($a0)       ; v1 = live master table base pointer
8003c554: sll      $v0, $v0, 4           ; v0 = index * 3 * 16 = index * 48 (0x30)
8003c558: bnez     $a2, 0x8003c56c       ; if offset != 0, branch to field decoder
8003c55c: addu     $v1, $v1, $v0         ; v1 = item_record_ptr = base + index * 48
8003c560: lw       $v0, ($v1)            ; offset 0: return 32-bit word (Buy Price)
8003c564: j        0x8003c58c
8003c568: nop      
8003c56c: addiu    $v0, $a2, -4          ; check if offset in [4..18]
8003c570: sltiu    $v0, $v0, 0xf         ; (unsigned)(offset - 4) < 15
8003c574: bnez     $v0, 0x8003c588       ; if in range [4..18], read signed 16-bit halfword
8003c578: addu     $v0, $v1, $a2         ; v0 = item_record_ptr + offset
8003c57c: lbu      $v0, ($v0)            ; else: return unsigned 8-bit byte
8003c580: j        0x8003c58c
8003c584: nop      
8003c588: lh       $v0, ($v0)            ; return signed 16-bit halfword (stats / equip mask)
8003c58c: jr       $ra
8003c590: nop      
```

Resident function `80034100` wraps `8003C538`, taking `($a0 = item_id, $a1 = offset)` and fetching the live inventory pointer from `80075278`.

---

## 2. Fast Equipment Cache (Embedded SLZ2 Table)

In addition to the master 48-byte table in heap memory, the resident executable (`code-2576-lba-30736.bin`) contains an embedded compressed SLZ2 table at file offset `0x80072134` (uncompressed size: 11,536 bytes = 824 records $\times$ 14 bytes).

On menu initialization (`8003b320`), this table is decompressed and expanded into an allocated 16-byte-per-item cache ($824 \times 16 = 0\text{x}3380$ bytes):
- Offset `+0x00` (`u16`): Equip restriction bitmask (from master `+0x04`)
- Offset `+0x02` (`s16`): Attack ATK (from master `+0x08`)
- Offset `+0x04` (`s16`): Defense DEF (from master `+0x10`)
- Offset `+0x06` (`s16`): Stat 3 / CRT / HIT (from master `+0x0C`)
- Offset `+0x08` (`s16`): Stat 4 / AVD (from master `+0x0E`)
- Offset `+0x0A` (`s16`): Stat 5 / MAG / LUC (from master `+0x12`)
- Offset `+0x0C` (`u16`): Sub-type / Recipe ID (from master `+0x28`)
- Offset `+0x0E` (`u16`): Category byte (from master `+0x2A`)

Resident function `8003bb2c` uses this 16-byte fast cache when allocated, or falls back to calling `80034100` against the 48-byte master table.

---

## 3. Master 48-Byte Item Record Specification

| Offset | Width | Type | Field Name | Description |
|---|---|---|---|---|
| `+0x00` | 4 bytes | `u32` | **Buy Price** | Base purchase price in Fol. Sell price is computed using `+0x2D` percentage. |
| `+0x04` | 2 bytes | `u16` | **Equip Mask** | Character equip restriction bitmask: `1 << char_id`. `0x0FFF` = universal, `0x0000` = none. |
| `+0x06` | 2 bytes | `s16` | **Secondary Stat** | Secondary equipment parameter or flat bonus. |
| `+0x08` | 2 bytes | `s16` | **ATK** | Attack power bonus (weapons and offensive accessories). |
| `+0x0A` | 2 bytes | `s16` | **Reserved** | Unused padding field (always `0x0000`). |
| `+0x0C` | 2 bytes | `s16` | **HIT / CRT** | Hit rate, dexterity bonus, or critical hit rate modifier. |
| `+0x0E` | 2 bytes | `s16` | **AVD** | Evade / avoid rate modifier (e.g. Star Guard gives +121 AVD). |
| `+0x10` | 2 bytes | `s16` | **DEF** | Defense bonus (armor, shields, helmets, boots, accessories). |
| `+0x12` | 2 bytes | `s16` | **MAG / LUC** | Magic power, intelligence, or luck stat modifier. |
| `+0x14` | 2 bytes | `s16` | **STR / AGL** | Strength or agility/movement modifier (e.g. Bunny Shoes gives +80 AGL). |
| `+0x16` | 2 bytes | `s16` | **GUTS / STM** | Guts or stamina modifier / special elemental parameter. |
| `+0x18` | 1 byte | `u8` | **Flags / Special** | Combat animation/behavioral flag. |
| `+0x19` | 1 byte | `u8` | **Recovery Value / Slot** | For consumables: HP/MP recovery percentage (e.g. 22 for Blackberry/Blueberry). For gear: slot indicator. |
| `+0x1A` | 1 byte | `u8` | **Proc Trigger Rate** | Chance or trigger threshold for special weapon/gear effects. |
| `+0x1B` | 1 byte | `u8` | **Weapon Element** | Combat elemental property / weapon trail effect (`0x0A`=Fire, `0x1E`=Water, `0x0D`=Wind, `0x05`=Earth, `0x18`=Dark). |
| `+0x1C..+0x25` | 10 bytes | `u8[10]` | **Elemental Resistances** | 10 elemental affinity multipliers: `0`=Neutral, `1`=Weak, `2`=Half (Resist), `3`=Immune (Nullify), `4`=Absorb. |
| `+0x26..+0x27` | 2 bytes | `u16` | **Status Ailment Mask** | Status protection or infliction bitmask (Poison, Paralysis, Stone, Silence, etc.). |
| `+0x28` | 1 byte | `u8` | **Sub-type / Effect ID** | Item model/sprite ID, cooking recipe family, or consumable effect dispatch ID. |
| `+0x29` | 1 byte | `u8` | **Usage Context** | `0`=Passive/Material/Key item, `1`=Battle only, `2`=Camp/Menu only (Food/Art), `3`=Field & Battle (Medicine). |
| `+0x2A` | 1 byte | `u8` | **Major Category** | `0`=General/Consumable, `1`=Weapon, `8`=Body Armor, `9`=Shield, `10`=Helmet, `11`=Boots, `12`=Accessory. |
| `+0x2B` | 1 byte | `u8` | **Resale Tier** | Shop resale modifier or item rarity rank. |
| `+0x2C` | 1 byte | `u8` | **Proc Effect ID** | Special combat proc effect (e.g. `0x28` for Eternal Sphere star projectile spray). |
| `+0x2D` | 1 byte | `u8` | **Sell Rate %** | Base sale price percentage relative to Buy Price (`25` = 25%, `50` = 50%, `100` = 100%). |
| `+0x2E..+0x2F` | 2 bytes | `u16` | **Alignment Padding** | Always `0x0000` to maintain 48-byte structure boundary. |

---

## 4. Equip Restriction Bitmask Scheme (`+0x04`)

The 16-bit integer at offset `+0x04` directly encodes character eligibility as an independent bitmask (`1 << char_id`), evaluated via bitwise-AND (`equip_mask & (1 << char_id)`):

| Bit | Character | Value | Bit | Character | Value |
|---|---|---|---|---|---|
| **0** | Claude | `0x0001` | **6** | Ashton | `0x0040` |
| **1** | Rena | `0x0002` | **7** | Leon | `0x0080` |
| **2** | Celine | `0x0004` | **8** | Opera | `0x0100` |
| **3** | Bowman | `0x0008` | **9** | Ernest | `0x0200` |
| **4** | Dias | `0x0010` | **10** | Noel | `0x0400` |
| **5** | Precis | `0x0020` | **11** | Chisato | `0x0800` |

Canonical composite masks in the data:
- `0x0FFF` ($4095$): Universal (All 12 characters)
- `0x0F79` ($3961$): Full Fighter Group (Claude, Bowman, Dias, Precis, Ashton, Opera, Ernest, Noel, Chisato)
- `0x0F59` ($3929$): Heavy Fighter Group (Precis excluded)
- `0x0B79` ($2937$): Standard Fighter Group (Noel excluded)
- `0x06D9` ($1753$): Male Characters (Claude, Bowman, Dias, Ashton, Leon, Ernest, Noel)
- `0x0926` ($2342$): Female Characters (Rena, Celine, Precis, Opera, Chisato)
- `0x0086` ($134$): Core Magician Group (Rena, Celine, Leon)
- `0x0486` ($1158$): Extended Magician Group (Rena, Celine, Leon, Noel)
- `0x0904` ($2308$): Female Casters / Gunners (Celine, Opera, Chisato)
- `0x0051` ($81$): Swordsmen Trio (Claude, Dias, Ashton)
- `0x0011` ($17$): Classic Swordsmen (Claude, Dias)

---

## 5. Weapons Catalog (Category 1, 177 items)

| ID | Code | Name | ATK | Extra Stats | Price | Equip Mask | Element / Special |
|---|---|---|---|---|---|---|---|
| `0x133` | `5133` | Sharpness (Sword) | 500 | CRT/HIT+50 | 20000 | `Di` (`0x0010`) | Elem 0x21 (Proc 0x0A) |
| `0x156` | `5156` | Sacred Tear (Sword) | 1250 | CRT/HIT+50, DEF+20 | 0 | `Cl` (`0x0001`) | Water |
| `0x157` | `5157` | Fallen Hope (Armor) | 1000 | CRT/HIT+50, DEF+50, MAG+300 | 0 | `Re` (`0x0002`) | Elem 0x14 |
| `0x165` | `5165` | Levantine Sword (Sword) | 3000 | CRT/HIT+50, STR/AGL+50 | 0 | `Cl/Di/As` (`0x0051`) | Elem 0x23 (Proc 0x32) |
| `0x16A` | `516A` | Hoy Sword Farwell (Sword)  [in game: Holy Sword Farwell] | 1900 | CRT/HIT+70, DEF+70, AVD+70, MAG+70 | 4000000 | `Cl/Di/As` (`0x0051`) | Elem 0x0F |
| `0x16F` | `516F` | Million Staff (Staff) | 800 | CRT/HIT+80, MAG+800, STR/AGL+30, GUTS+286 | 8000000 | `Ce/Le/No` (`0x0484`) | Elem 0x28 |
| `0x188` | `5188` | Weird Slayer (Knuckles) | 1000 | CRT/HIT+40, STR/AGL+10 | 0 | `Re/Bo/Pr/Ch` (`0x082A`) | - (Proc 0x0A) |
| `0x18C` | `518C` | Funny Slayer (weapon) | 1 | - | 300 | `All` (`0x0FFF`) | Elem 0x28 |
| `0x1E5` | `51E5` | Dull Sword (Sword) | 2 | - | 5 | `Cl/Di` (`0x0011`) | Elem 0x01 |
| `0x1E6` | `51E6` | Worn-out Sword (Sword) | 3 | - | 200 | `Cl/Di` (`0x0011`) | - |
| `0x1E7` | `51E7` | Golden Fangs (Sword) | 10 | - | 10000 | `Cl` (`0x0001`) | - |
| `0x1E8` | `51E8` | Silver Fangs (Sword) | 12 | - | 8000 | `Cl` (`0x0001`) | - |
| `0x1E9` | `51E9` | Broad Sword (Sword) | 60 | - | 400 | `Cl` (`0x0001`) | - |
| `0x1EA` | `51EA` | Long Sword (Sword) | 30 | - | 200 | `Cl/Di` (`0x0011`) | - |
| `0x1EB` | `51EB` | Sinclair Sabre (Sword) | 100 | - | 860 | `Cl` (`0x0001`) | - |
| `0x1EC` | `51EC` | Flame Blade (Sword) | 160 | CRT/HIT+20 | 4800 | `Cl/Di` (`0x0011`) | Fire |
| `0x1ED` | `51ED` | Walloon Sword (Sword) | 240 | - | 3900 | `Cl/Di` (`0x0011`) | - |
| `0x1EE` | `51EE` | Gusguine (Sword) | 250 | - | 4500 | `Cl` (`0x0001`) | - |
| `0x1EF` | `51EF` | Long Edge (Sword) | 285 | - | 12300 | `Cl` (`0x0001`) | Earth |
| `0x1F0` | `51F0` | Sharp Edge (Sword) | 222 | CRT/HIT+60 | 5000 | `Cl/Di` (`0x0011`) | Fire |
| `0x1F1` | `51F1` | Veil Piercer (Sword) | 480 | - | 8000 | `Cl` (`0x0001`) | - |
| `0x1F2` | `51F2` | Grand Stinger (Sword) | 620 | CRT/HIT+120 | 50000 | `Cl/Di` (`0x0011`) | Fire |
| `0x1F3` | `51F3` | Ignite Sword (Sword) | 720 | - | 17000 | `Cl/Di` (`0x0011`) | - |
| `0x1F4` | `51F4` | Heart Breaker (Sword) | 550 | CRT/HIT+20 | 50000 | `Cl` (`0x0001`) | Fire |
| `0x1F5` | `51F5` | Marvel Sword (Sword) | 1100 | CRT/HIT+100, DEF+10, AVD+10, STR/AGL+10 | 350000 | `Cl/Di` (`0x0011`) | Elem 0x0F |
| `0x1F6` | `51F6` | Minus Sword (Sword) | 599 | CRT/HIT+80 | 40000 | `Cl/Di` (`0x0011`) | Fire |
| `0x1F7` | `51F7` | Sawed (Sword) | 990 | CRT/HIT+80 | 200000 | `Cl` (`0x0001`) | Elem 0x14 (Proc 0x3C) |
| `0x1F8` | `51F8` | Force Sword (Sword) | 908 | - | 50000 | `Cl` (`0x0001`) | - |
| `0x1F9` | `51F9` | Windsley Sword (Sword) | 1400 | - | 600000 | `Cl` (`0x0001`) | - |
| `0x1FA` | `51FA` | Silvance (Sword) | 1210 | CRT/HIT+99, DEF+20, AVD+20 | 180000 | `Cl/Di` (`0x0011`) | Water |
| `0x1FB` | `51FB` | Eternal Sphere (Sword) | 1600 | CRT/HIT+70 | 1000000 | `Cl` (`0x0001`) | Light (Proc 0x28) |
| `0x1FC` | `51FC` | Aura Blade (Sword) | 1200 | CRT/HIT+80 | 260000 | `Cl` (`0x0001`) | Elem 0x20 |
| `0x1FD` | `51FD` | All-Purpose Knife (Sword) | 160 | - | 12000 | `All` (`0x0FFF`) | Fire |
| `0x1FE` | `51FE` | Bastard Sword (Sword) | 150 | CRT/HIT+10 | 1000 | `Di` (`0x0010`) | Fire |
| `0x1FF` | `51FF` | Baselard (Sword) | 180 | - | 900 | `Di` (`0x0010`) | - |
| `0x200` | `5200` | Oriental Blade (Sword) | 448 | - | 5000 | `Di` (`0x0010`) | - |
| `0x201` | `5201` | Murasome Sword (Sword) | 552 | CRT/HIT+20 | 20000 | `Di` (`0x0010`) | Elem 0x16 (Proc 0x0A) |
| `0x202` | `5202` | Soul Slayer (Sword) | 982 | CRT/HIT+10 | 50000 | `Di` (`0x0010`) | Elem 0x0C |
| `0x203` | `5203` | Whirlwind (Sword) | 780 | CRT/HIT+50 | 40000 | `Di` (`0x0010`) | Wind |
| `0x204` | `5204` | The Hope Of Breeze (Sword) | 770 | CRT/HIT+30 | 40000 | `Di` (`0x0010`) | Elem 0x14 |
| `0x205` | `5205` | Hard Cleaver (Sword) | 1100 | CRT/HIT+60 | 220000 | `Di` (`0x0010`) | Water |
| `0x206` | `5206` | Ruins' Fate (Sword) | 1000 | CRT/HIT+50 | 190000 | `Di` (`0x0010`) | - |
| `0x207` | `5207` | Pleiad Sword (Sword) | 1200 | CRT/HIT+60 | 280000 | `Di` (`0x0010`) | Water |
| `0x208` | `5208` | Crimson Diablos (Sword) | 1100 | CRT/HIT+80, STR/AGL+50 | 880000 | `Di` (`0x0010`) | Fire/Dark |
| `0x209` | `5209` | Cromlea Sword (Sword) | 1399 | - | 580000 | `Di` (`0x0010`) | - |
| `0x20A` | `520A` | Wobbly Sword (Sword) | 3 | - | 20 | `As` (`0x0040`) | Elem 0x01 |
| `0x20B` | `520B` | Twin Swords (Dual-Sword) | 40 | - | 320 | `As` (`0x0040`) | - |
| `0x20C` | `520C` | Guard Sword (Dual-Sword) | 160 | CRT/HIT+10, AVD+20 | 8000 | `As` (`0x0040`) | Elem 0x0B |
| `0x20D` | `520D` | Both Shaver (Dual-Sword) | 120 | AVD+20 | 850 | `As` (`0x0040`) | - |
| `0x20E` | `520E` | Smaller (Dual-Sword) | 180 | AVD+30 | 2000 | `As` (`0x0040`) | - |
| `0x20F` | `520F` | Twin-edge (Dual-Sword) | 340 | AVD+30 | 3000 | `As` (`0x0040`) | - |
| `0x210` | `5210` | Pair Nuts (Dual-Sword) | 380 | CRT/HIT+20, AVD+50 | 10000 | `As` (`0x0040`) | Elem 0x0C |
| `0x211` | `5211` | Shield Sword (Dual-Sword) | 490 | AVD+35 | 10000 | `As` (`0x0040`) | - |
| `0x212` | `5212` | Twin Picks (Dual-Sword) | 500 | CRT/HIT+50, AVD+50 | 20000 | `As` (`0x0040`) | Elem 0x14 |
| `0x213` | `5213` | Scyther (Dual-Sword) | 820 | - | 18000 | `As` (`0x0040`) | - |
| `0x214` | `5214` | Doubledemon Sword (Dual-Sword) | 700 | - | 580000 | `As` (`0x0040`) | - |
| `0x215` | `5215` | Double Masher (Dual-Sword) | 799 | CRT/HIT+40, DEF+8, AVD+60 | 82050 | `As` (`0x0040`) | Elem 0x0F |
| `0x216` | `5216` | Lotus Eater (Dual-Sword) | 1150 | CRT/HIT+50 | 188000 | `As` (`0x0040`) | - |
| `0x217` | `5217` | Gemini (Dual-Sword) | 1200 | CRT/HIT+80, DEF+10, AVD+60, GUTS+50 | 200000 | `As` (`0x0040`) | Elem 0x15 |
| `0x218` | `5218` | Holy Cross (Dual-Sword) | 1240 | CRT/HIT+60, DEF+20, AVD+70, GUTS+80 | 280000 | `As` (`0x0040`) | Elem 0x12 |
| `0x219` | `5219` | Melufa (Dual-Sword) | 1320 | CRT/HIT+80, DEF+25, AVD+75, GUTS+100 | 1200000 | `As` (`0x0040`) | Elem 0x28 |
| `0x21A` | `521A` | Worn Knuckles (Knuckles) | 1 | - | 10 | `Re/Bo/No` (`0x040A`) | - |
| `0x21B` | `521B` | Knuckles (Knuckles) | 30 | - | 110 | `Re/Bo/No` (`0x040A`) | - |
| `0x21C` | `521C` | Hard Knuckles (Knuckles) | 58 | MAG+10 | 300 | `Re/Bo/No` (`0x040A`) | - |
| `0x21D` | `521D` | Cestus (Knuckles) | 140 | MAG+20 | 1400 | `Re/Bo` (`0x000A`) | - |
| `0x21E` | `521E` | Fellper Nails (Knuckles) | 1200 | CRT/HIT+50, AVD+50, MAG+30 | 500000 | `Re` (`0x0002`) | - |
| `0x21F` | `521F` | Metal Fangs (Knuckles) | 400 | MAG+50 | 5000 | `Re/No` (`0x0402`) | - |
| `0x220` | `5220` | Magical Gloves (Knuckles) | 688 | CRT/HIT+50, MAG+60 | 35526 | `Re/Bo` (`0x000A`) | Elem 0x0C |
| `0x221` | `5221` | Braised Knuckles (Knuckles) | 599 | CRT/HIT+30, MAG+70 | 15000 | `Re/Bo` (`0x000A`) | Elem 0x06 |
| `0x222` | `5222` | Pain Cestus (Knuckles) | 580 | MAG+80 | 15000 | `Re` (`0x0002`) | - |
| `0x223` | `5223` | Dragon's Claws (Knuckles) | 450 | CRT/HIT+20, MAG+100 | 20850 | `Re/No` (`0x0402`) | Elem 0x1A |
| `0x224` | `5224` | Rune Full Moon (Knuckles) | 900 | MAG+150 | 50000 | `Re/Bo` (`0x000A`) | - |
| `0x225` | `5225` | Sorceress Knuckles (Knuckles) | 1000 | MAG+180 | 90000 | `Re/Bo` (`0x000A`) | - |
| `0x226` | `5226` | Kaiser Knuckles (Knuckles) | 1100 | CRT/HIT+60, MAG+200 | 186000 | `Re/Bo/No` (`0x040A`) | Elem 0x04 |
| `0x227` | `5227` | Empresia (Knuckles) | 1220 | CRT/HIT+70, MAG+300 | 300000 | `Re` (`0x0002`) | Water |
| `0x228` | `5228` | Bagh Nakh (Knuckles) | 165 | - | 1400 | `Bo` (`0x0008`) | - |
| `0x229` | `5229` | Giant Fists (Knuckles) | 470 | CRT/HIT+10, STR/AGL+80 | 8000 | `Bo` (`0x0008`) | Elem 0x1A |
| `0x22A` | `522A` | Hecatoncheire (Knuckles) | 630 | CRT/HIT+50 | 16200 | `Bo` (`0x0008`) | Elem 0x1B |
| `0x22B` | `522B` | Asura (Knuckles) | 750 | CRT/HIT+20 | 60000 | `Bo` (`0x0008`) | Elem 0x03 |
| `0x22C` | `522C` | Titan's Fists (Knuckles) | 1000 | CRT/HIT+30, STR/AGL+50, GUTS+512 | 70000 | `Bo` (`0x0008`) | Earth |
| `0x22D` | `522D` | Flare Burst (Knuckles) | 1300 | - | 386000 | `Bo` (`0x0008`) | - |
| `0x22E` | `522E` | Moon Fists (Knuckles) | 1200 | CRT/HIT+60, DEF+10, AVD+30 | 220000 | `Bo` (`0x0008`) | Elem 0x08 |
| `0x22F` | `522F` | Cat's Fangs (Knuckles) | 120 | - | 60000 | `Re/No` (`0x0402`) | - |
| `0x230` | `5230` | Eagle's Claws (Knuckles) | 760 | MAG+110 | 20000 | `No` (`0x0400`) | Fire |
| `0x231` | `5231` | Serpent's Tooth (Knuckles) | 900 | CRT/HIT+20, MAG+150 | 180000 | `No` (`0x0400`) | Elem 0x0C |
| `0x232` | `5232` | Death Fangs (Knuckles) | 1350 | CRT/HIT+50, AVD+20 | 250000 | `No` (`0x0400`) | Elem 0x0F (Proc 0x0A) |
| `0x233` | `5233` | Grizzly Claps (Knuckles) | 840 | CRT/HIT+60, MAG+200 | 140000 | `No` (`0x0400`) | - |
| `0x234` | `5234` | Tiger's Fangs (Knuckles) | 600 | CRT/HIT+30, AVD+30, MAG+100 | 80000 | `No` (`0x0400`) | Elem 0x14 |
| `0x235` | `5235` | Platinum Nails (Knuckles) | 850 | CRT/HIT+55, AVD+20, MAG+300 | 199000 | `No` (`0x0400`) | Elem 0x02 |
| `0x236` | `5236` | Bent Rod (Staff) | 5 | MAG+1 | 90 | `Ce` (`0x0004`) | - |
| `0x237` | `5237` | Silver Rod (Staff) | 350 | CRT/HIT+20, MAG+250 | 9800 | `Ce` (`0x0004`) | - |
| `0x238` | `5238` | Rod (Staff) | 10 | MAG+5 | 10 | `Ce` (`0x0004`) | - |
| `0x239` | `5239` | Ruby Wand (Staff) | 70 | MAG+20 | 600 | `Ce` (`0x0004`) | - |
| `0x23A` | `523A` | Tongue Twister (Staff) | 300 | MAG+25 | 25000 | `Ce` (`0x0004`) | - |
| `0x23B` | `523B` | Crest Rod (Staff) | 100 | MAG+25 | 1200 | `Ce` (`0x0004`) | - |
| `0x23C` | `523C` | Holy Rod (Staff) | 520 | MAG+240 | 50000 | `Ce` (`0x0004`) | - |
| `0x23D` | `523D` | Silvermoon (Staff) | 1000 | MAG+300 | 80000 | `Ce` (`0x0004`) | - |
| `0x23E` | `523E` | Prime Prayer (Staff) | 1000 | CRT/HIT+80, DEF+20, AVD+20, MAG+80 | 400000 | `Ce` (`0x0004`) | Earth |
| `0x23F` | `523F` | Magical Rod (Staff) | 150 | DEF+30 | 2000 | `Ce` (`0x0004`) | Fire |
| `0x240` | `5240` | Rod of Snakes (Staff) | 700 | CRT/HIT+60, DEF+10, MAG+50 | 250000 | `Ce` (`0x0004`) | Elem 0x06 |
| `0x241` | `5241` | Dragon's Tusk (Staff) | 990 | CRT/HIT+80, MAG+360 | 260000 | `Ce` (`0x0004`) | Elem 0x06 |
| `0x242` | `5242` | Ruby Rod (Staff) | 680 | MAG+300 | 80000 | `Ce` (`0x0004`) | - |
| `0x243` | `5243` | Clap Rod (Staff) | 280 | MAG+30 | 5000 | `Ce` (`0x0004`) | - |
| `0x245` | `5245` | Booster Box (Kaleidoscope) | 128 | - | 150 | `Op` (`0x0100`) | - |
| `0x246` | `5246` | Radio Box (Kaleidoscope) | 162 | - | 280 | `Op` (`0x0100`) | - |
| `0x247` | `5247` | Black Box (Kaleidoscope) | 200 | CRT/HIT+20, AVD+10 | 10000 | `Op` (`0x0100`) | Elem 0x14 |
| `0x248` | `5248` | Light Box (Kaleidoscope) | 490 | - | 600 | `Op` (`0x0100`) | - |
| `0x249` | `5249` | Seventh Ray (Kaleidoscope) | 280 | CRT/HIT+60 | 52500 | `Op` (`0x0100`) | Elem 0x23 |
| `0x24A` | `524A` | X Box (Kaleidoscope) | 500 | - | 12200 | `Op` (`0x0100`) | - |
| `0x24B` | `524B` | Magic Box (Kaleidoscope) | 650 | CRT/HIT+50, AVD+20 | 65000 | `Op` (`0x0100`) | Elem 0x14 |
| `0x24C` | `524C` | Alpha Box (Kaleidoscope) | 690 | CRT/HIT+50 | 139900 | `Op` (`0x0100`) | - |
| `0x24D` | `524D` | Burst Box (Kaleidoscope) | 780 | CRT/HIT+60, AVD+30 | 230000 | `Op` (`0x0100`) | Elem 0x14 |
| `0x24E` | `524E` | Psycho Box (Kaleidoscope) | 1050 | - | 199000 | `Op` (`0x0100`) | - |
| `0x24F` | `524F` | Beta Box (Kaleidoscope) | 690 | CRT/HIT+30, AVD+24 | 150000 | `Op` (`0x0100`) | Elem 0x14 |
| `0x250` | `5250` | Gamma Box (Kaleidoscope) | 750 | CRT/HIT+50, AVD+34 | 200000 | `Op` (`0x0100`) | Elem 0x14 |
| `0x251` | `5251` | Pulse Box (Kaleidoscope) | 1000 | CRT/HIT+60, AVD+40 | 295000 | `Op` (`0x0100`) | Elem 0x14 |
| `0x252` | `5252` | Magic Hand (Hand) | 125 | - | 200 | `Pr` (`0x0020`) | - |
| `0x253` | `5253` | Iron Punch (Hand) | 165 | - | 300 | `Pr` (`0x0020`) | - |
| `0x254` | `5254` | One-two Punch (Hand) | 280 | - | 800 | `Pr` (`0x0020`) | - |
| `0x255` | `5255` | Straight Punch (Hand) | 400 | - | 500 | `Pr` (`0x0020`) | - |
| `0x256` | `5256` | Fire Punch (Hand) | 699 | - | 21300 | `Pr` (`0x0020`) | - |
| `0x257` | `5257` | Ice Punch (Hand) | 380 | - | 21300 | `Pr` (`0x0020`) | - |
| `0x258` | `5258` | Thunder Punch (Hand) | 420 | CRT/HIT+50 | 18500 | `Pr` (`0x0020`) | Light |
| `0x259` | `5259` | Ultra Punch (Hand) | 650 | - | 2000 | `Pr` (`0x0020`) | - |
| `0x25A` | `525A` | Great Punch (Hand) | 850 | - | 14000 | `Pr` (`0x0020`) | - |
| `0x25B` | `525B` | Hyper Punch (Hand) | 1250 | - | 300000 | `Pr` (`0x0020`) | - |
| `0x25C` | `525C` | Burning Hand (Hand) | 600 | CRT/HIT+50 | 40000 | `Pr` (`0x0020`) | Elem 0x14 |
| `0x25D` | `525D` | Atomic Punch (Hand) | 1120 | CRT/HIT+55 | 170000 | `Pr` (`0x0020`) | - |
| `0x25E` | `525E` | Spark Hand (Hand) | 650 | CRT/HIT+30 | 50000 | `Pr` (`0x0020`) | Elem 0x14 |
| `0x25F` | `525F` | SD Punch (Hand) | 1150 | CRT/HIT+50 | 80000 | `Pr` (`0x0020`) | Elem 0x14 (Proc 0x32) |
| `0x260` | `5260` | UGA Punch (Hand) | 1300 | CRT/HIT+60 | 200000 | `Pr` (`0x0020`) | Light (Proc 0x3C) |
| `0x261` | `5261` | SDUGA Punch (Hand) | 1600 | - | 400000 | `Pr` (`0x0020`) | Water (Proc 0x41) |
| `0x262` | `5262` | Limp Whip (Whip) | 2 | - | 110 | `Er` (`0x0200`) | - |
| `0x263` | `5263` | Leather Whip (Whip) | 60 | - | 150 | `Er` (`0x0200`) | - |
| `0x264` | `5264` | Splinter (Whip) | 460 | - | 1300 | `Er` (`0x0200`) | - |
| `0x265` | `5265` | Hard Whip (Whip) | 550 | - | 3000 | `Er` (`0x0200`) | - |
| `0x266` | `5266` | Twin-tail (Whip) | 860 | - | 182500 | `Er` (`0x0200`) | - |
| `0x267` | `5267` | Rose Whip (Whip) | 600 | CRT/HIT+66 | 23000 | `Er` (`0x0200`) | Light |
| `0x268` | `5268` | Flare Whip (Whip) | 800 | CRT/HIT+80 | 50000 | `Er` (`0x0200`) | Light |
| `0x269` | `5269` | Light Whip (Whip) | 820 | - | 14000 | `Er` (`0x0200`) | - |
| `0x26A` | `526A` | Cat o'9 Tails (Whip) | 1280 | - | 292500 | `Er` (`0x0200`) | - |
| `0x26B` | `526B` | Freeze Whip (Whip) | 800 | CRT/HIT+80 | 50000 | `Er` (`0x0200`) | Light |
| `0x26C` | `526C` | Spark Whip (Whip) | 1080 | CRT/HIT+50 | 160000 | `Er` (`0x0200`) | - |
| `0x26D` | `526D` | Molecule Wire (Whip) | 799 | CRT/HIT+60, DEF+10, AVD+10 | 156000 | `Er` (`0x0200`) | Fire/Dark |
| `0x26E` | `526E` | Dark Whip (Whip) | 1100 | CRT/HIT+50 | 2800000 | `Er` (`0x0200`) | Water |
| `0x26F` | `526F` | Invisible Whip (Whip) | 950 | CRT/HIT+150 | 260000 | `Er` (`0x0200`) | Elem 0x1F (Proc 0x28) |
| `0x270` | `5270` | Thick Book (Book) | 180 | MAG+15 | 1100 | `Le` (`0x0080`) | - |
| `0x271` | `5271` | Reference Book (Book) | 280 | MAG+50 | 2300 | `Le` (`0x0080`) | - |
| `0x272` | `5272` | Brain Structure (Book) | 890 | CRT/HIT+50, MAG+80 | 120000 | `Le` (`0x0080`) | - |
| `0x273` | `5273` | Illustrated Book (Book) | 320 | MAG+22 | 3100 | `Le` (`0x0080`) | - |
| `0x274` | `5274` | Treatise (Book) | 50 | MAG+390, GUTS+50 | 200000 | `Le` (`0x0080`) | - |
| `0x275` | `5275` | Mental Revolution (Book) | 680 | MAG+60 | 60000 | `Le` (`0x0080`) | - |
| `0x276` | `5276` | Heraldry (Book) | 290 | MAG+100 | 7000 | `Le` (`0x0080`) | - |
| `0x277` | `5277` | Dictionary (Book) | 340 | MAG+50 | 20000 | `Le` (`0x0080`) | - |
| `0x278` | `5278` | All About ESP (Book) | 780 | MAG+70 | 100000 | `Le` (`0x0080`) | - |
| `0x279` | `5279` | Heraldry Book (Book) | 500 | CRT/HIT+50, MAG+100 | 120000 | `Le` (`0x0080`) | - |
| `0x27A` | `527A` | Holy Scriptures (Book) | 920 | CRT/HIT+50, MAG+199 | 150000 | `Le` (`0x0080`) | - |
| `0x27B` | `527B` | Book of Awakening (Book) | 50 | CRT/HIT+20, DEF+20, AVD+20, MAG+88, STR/AGL+20, GUTS+20 | 203000 | `Le` (`0x0080`) | - |
| `0x27C` | `527C` | Encyclopedia (Book) | 500 | MAG+100 | 50000 | `Le` (`0x0080`) | - |
| `0x27D` | `527D` | Ancient Wisdom (Book) | 800 | CRT/HIT+50, MAG+380, GUTS+20 | 250000 | `Le` (`0x0080`) | - |
| `0x27E` | `527E` | Book of Darkness (Book) | 700 | MAG+80 | 80000 | `Le` (`0x0080`) | - |
| `0x27F` | `527F` | Book of Chaos (Book) | 950 | CRT/HIT+80, MAG+400 | 190000 | `Le` (`0x0080`) | - |
| `0x280` | `5280` | 10 Volt Stun Gun (Gun) | 10 | GUTS+512 | 120 | `Ch` (`0x0800`) | Fire |
| `0x281` | `5281` | Stun Gun (Gun) | 200 | CRT/HIT+50, GUTS+512 | 5000 | `Ch` (`0x0800`) | Elem 0x32 |
| `0x282` | `5282` | Electric (Gun) | 280 | CRT/HIT+60, GUTS+512 | 6000 | `Ch` (`0x0800`) | Elem 0x32 |
| `0x283` | `5283` | Shock Gun (Gun) | 380 | CRT/HIT+40, GUTS+512 | 13000 | `Ch` (`0x0800`) | Elem 0x32 |
| `0x284` | `5284` | Voltage (Gun) | 460 | CRT/HIT+70, GUTS+512 | 12000 | `Ch` (`0x0800`) | Elem 0x32 |
| `0x285` | `5285` | Freeze (Gun) | 600 | CRT/HIT+40, GUTS+512 | 100000 | `Ch` (`0x0800`) | Elem 0x32 |
| `0x286` | `5286` | Electro Gun (Gun) | 410 | GUTS+512 | 15000 | `Ch` (`0x0800`) | - |
| `0x287` | `5287` | Flame Gun (Gun) | 550 | CRT/HIT+60, GUTS+512 | 100000 | `Ch` (`0x0800`) | Elem 0x32 |
| `0x288` | `5288` | Lightning Gun (Gun) | 650 | CRT/HIT+51, GUTS+512 | 158000 | `Ch` (`0x0800`) | - |
| `0x289` | `5289` | Cracker (Gun) | 660 | GUTS+512 | 100000 | `Ch` (`0x0800`) | Elem 0x32 |
| `0x28A` | `528A` | Aero Gun (Gun) | 800 | GUTS+512 | 276000 | `Ch` (`0x0800`) | - |
| `0x28B` | `528B` | Spark (???) | 750 | CRT/HIT+60, GUTS+512 | 60000 | `Ch` (`0x0800`) | Elem 0x50 |
| `0x28C` | `528C` | Flare Gun (Gun) | 920 | CRT/HIT+65, GUTS+512 | 220000 | `Ch` (`0x0800`) | Elem 0x5A |
| `0x28D` | `528D` | Electron (???) | 830 | CRT/HIT+66, GUTS+512 | 100000 | `Ch` (`0x0800`) | Elem 0x3C |
| `0x28E` | `528E` | Psychic Gun (Gun) | 980 | CRT/HIT+65, GUTS+512 | 220000 | `Ch` (`0x0800`) | Elem 0x46 |

---

## 6. Body Armor Catalog (Category 8, 35 items)

| ID | Code | Name | DEF | Extra Stats | Price | Equip Mask | Resistances / Notes |
|---|---|---|---|---|---|---|---|
| `0x146` | `5146` | Valkyrie's Garb (Armor) | 480 | - | 900000 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x16C` | `516C` | Seraphic Garb (Armor) | 400 | AVD+40, MAG+100, STR/AGL+50, GUTS+50 | 1800000 | `All` (`0x0FFF`) | Half Wind, Half Dark |
| `0x2A4` | `52A4` | Perforated Armor (Armor) | 1 | - | 50 | `None` (`0x0000`) | - |
| `0x2A5` | `52A5` | Leather Armor (Armor) | 6 | - | 300 | `All` (`0x0FFF`) | - |
| `0x2A6` | `52A6` | Flashy Armor (Armor) | 1 | - | 150 | `All` (`0x0FFF`) | - |
| `0x2A7` | `52A7` | Banded Mail (Armor) | 12 | - | 600 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2A8` | `52A8` | Odd Clothes (Armor) | 2 | - | 80 | `All` (`0x0FFF`) | - |
| `0x2A9` | `52A9` | Robe (Armor) | 3 | - | 10 | `Re/Ce/Le` (`0x0086`) | - |
| `0x2AA` | `52AA` | Ringed Mail (Armor) | 20 | - | 1200 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2AB` | `52AB` | Silk Robe (Armor) | 12 | - | 1800 | `Re/Ce/Le` (`0x0086`) | - |
| `0x2AC` | `52AC` | Brigandine (Armor) | 30 | - | 3500 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2AD` | `52AD` | Amber Robe (Armor) | 30 | - | 4000 | `Re/Ce/Le` (`0x0086`) | - |
| `0x2AE` | `52AE` | Evening Dress (Armor) | 30 | MAG+100 | 5000 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x2AF` | `52AF` | Plate Mail (Armor) | 90 | - | 13400 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2B0` | `52B0` | Silver Robe (Armor) | 70 | MAG+120 | 10000 | `Re/Ce/Le` (`0x0086`) | Half Thunder |
| `0x2B1` | `52B1` | Flying Hawk Robes (Armor) | 170 | MAG+150 | 80000 | `Re/Ce/Le` (`0x0086`) | Half Earth, Half Thunder, Half Special |
| `0x2B2` | `52B2` | Mirage Robe (Armor) | 230 | AVD+60, MAG+150, STR/AGL+50, GUTS+50 | 200000 | `Re/Ce/Le` (`0x0086`) | Null Thunder, Null Star, Null Light, Null Dark, Null Void |
| `0x2B3` | `52B3` | Mithril Coat (Armor) | 88 | MAG+80 | 15000 | `Re/Ce/Bo/Pr/Le/Op/Er/No/Ch` (`0x0FAE`) | Half Star, Half Dark |
| `0x2B4` | `52B4` | Holy Cloak (Armor) | 100 | MAG+100 | 30000 | `Re/Ce/Le` (`0x0086`) | - |
| `0x2B5` | `52B5` | Mithril Dress (Armor) | 20 | AVD+120, MAG+220 | 120000 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | Half Earth, Half Thunder, Half Star, Half Light, Half Dark |
| `0x2B6` | `52B6` | Star Cloak (Armor) | 220 | MAG+220 | 120000 | `Re/Ce/Le` (`0x0086`) | Absorb Star |
| `0x2B7` | `52B7` | Jeanne's Armor (Armor) | 180 | - | 100000 | `Pr/Op/Ch` (`0x0920`) | Half Light, Half Dark |
| `0x2B8` | `52B8` | Steel Armor (Armor) | 150 | - | 52000 | `Cl/Bo/Di/As/Op/Er/No/Ch` (`0x0F59`) | - |
| `0x2B9` | `52B9` | Battle Suit (Armor) | 500 | - | 20000000 | `All` (`0x0FFF`) | - |
| `0x2BA` | `52BA` | Wizard's Mail (Armor) | 200 | MAG+10 | 240000 | `Re/Ce/Le/No` (`0x0486`) | - |
| `0x2BB` | `52BB` | Ishtar's Robe (Armor) | 230 | AVD+30, MAG+230, STR/AGL+50 | 290000 | `Re/Ce/Le` (`0x0086`) | - |
| `0x2BC` | `52BC` | Core Plate (Armor) | 100 | - | 35000 | `Cl/Bo/Di/As/Op/Er/No/Ch` (`0x0F59`) | Half Thunder, Half Star |
| `0x2BD` | `52BD` | Mithril Mesh (Armor) | 200 | - | 250000 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2BE` | `52BE` | Barrier Armor (Armor) | 92 | AVD+5 | 24000 | `Cl/Bo/Di/As/Op/Er/No/Ch` (`0x0F59`) | Half Fire, Half Water, Half Wind |
| `0x2BF` | `52BF` | Sylvan Mail (Armor) | 240 | - | 200000 | `Pr/Op/Ch` (`0x0920`) | - |
| `0x2C0` | `52C0` | Valiant Mail (Armor) | 500 | - | 5000000 | `Cl/Bo/Di/As/Le/Er/No` (`0x06D9`) | - |
| `0x2C1` | `52C1` | Duel Suit (Armor) | 300 | - | 180000 | `Cl/Di/As` (`0x0051`) | - |
| `0x2C2` | `52C2` | Reflective Armor (Armor) | 290 | AVD+10, STR/AGL+20 | 220000 | `Cl/Bo/Di/Pr/As/Op/No/Ch` (`0x0D79`) | Half Fire, Half Earth, Half Thunder, Half Star, Half Light, Null Dark, Absorb Special |
| `0x2C3` | `52C3` | Chaos Mail (Armor) | 99 | AVD+9 | 1999 | `Cl/Bo/Di/As/Op/Er/No/Ch` (`0x0F59`) | Weak Thunder, Weak Star, Weak Dark |
| `0x2C4` | `52C4` | Bloody Armor (Armor) | 144 | AVD+44 | 1444 | `Cl/Bo/Di/As/Op/Er/No/Ch` (`0x0F59`) | Weak Water, Weak Wind, Weak Thunder, Weak Star, Weak Void, Weak Special |

---

## 7. Shields Catalog (Category 9, 19 items)

| ID | Code | Name | DEF | AVD | Price | Equip Mask | Resistances / Notes |
|---|---|---|---|---|---|---|---|
| `0x2C5` | `52C5` | Wooden Shield (Shield) | 2 | 50 | 120 | `Cl/Di/Pr/Er` (`0x0231`) | - |
| `0x2C6` | `52C6` | Round Shield (Shield) | 4 | 60 | 500 | `Cl/Di/Pr/Er` (`0x0231`) | - |
| `0x2C7` | `52C7` | Knight's Shield (Shield) | 10 | 60 | 1000 | `Cl/Di` (`0x0011`) | - |
| `0x2C8` | `52C8` | Odd Shield (Shield) | 5 | 10 | 400 | `Cl/Di/Pr` (`0x0031`) | - |
| `0x2C9` | `52C9` | Odd Gauntlets (Shield) | 0 | 10 | 50 | `Cl/Di/Pr` (`0x0031`) | - |
| `0x2CA` | `52CA` | Buckler (Shield) | 1 | 30 | 650 | `All` (`0x0FFF`) | - |
| `0x2CB` | `52CB` | Fine Shield (Shield) | 15 | 70 | 6800 | `Cl/Di` (`0x0011`) | - |
| `0x2CC` | `52CC` | Rune Buckler (Shield) | 5 | 60 | 9200 | `Re/Ce/Le/No` (`0x0486`) | - |
| `0x2CD` | `52CD` | Crestier Guard (Shield) | 20 | 80 | 36600 | `Cl/Di/Pr/Er` (`0x0231`) | Half Water |
| `0x2CE` | `52CE` | The Armband of Kali (Shield) | 30 | 30 | 198500 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | Half Special |
| `0x2CF` | `52CF` | Star Guard (Shield) | 33 | 121 | 262000 | `Cl/Bo/Di/Pr/As/Op/Er/Ch` (`0x0B79`) | - |
| `0x2D0` | `52D0` | Rare Gauntlets (Shield) | 20 | 30 | 105000 | `All` (`0x0FFF`) | - |
| `0x2D1` | `52D1` | Jeanne's Shield (Shield) | 30 | 80 | 200000 | `Pr/Ch` (`0x0820`) | Half Thunder, Half Star |
| `0x2D2` | `52D2` | Algol (Shield) | 40 | 80 | 180000 | `Pr/Ch` (`0x0820`) | - |
| `0x2D3` | `52D3` | Mithril Shield (Shield) | 31 | 60 | 199000 | `Cl/Di/Pr/Er` (`0x0231`) | Half Wind, Half Void, Half Special |
| `0x2D4` | `52D4` | Valiant Guard (Shield) | 120 | 120 | 4900000 | `Cl/Bo/Di/As/Le/Er/No` (`0x06D9`) | - |
| `0x2D5` | `52D5` | Valkyrie Guard (Shield) | 100 | 120 | 4990000 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x2D6` | `52D6` | Barrier Shield (Shield) | 24 | 40 | 19000 | `Cl/Di/Pr/Er` (`0x0231`) | Half Water, Half Thunder |
| `0x2D7` | `52D7` | Pallas Athena (Shield) | 20 | 80 | 260000 | `Cl/Di/Pr/Er` (`0x0231`) | Half Fire, Half Water, Half Wind, Half Earth, Half Thunder, Half Star, Half Light, Half Dark, Half Void |

---

## 8. Helmets & Headgear Catalog (Category 10, 25 items)

| ID | Code | Name | DEF | Extra Stats | Price | Equip Mask | Resistances / Notes |
|---|---|---|---|---|---|---|---|
| `0x041` | `5041` | Frog | 1 | - | 256 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x099` | `5099` | Golden Crown | 0 | - | 5000 | `All` (`0x0FFF`) | - |
| `0x0A0` | `50A0` | Crown | 0 | - | 1600 | `All` (`0x0FFF`) | - |
| `0x0A1` | `50A1` | Dream Crown | 0 | - | 100000 | `Re/Ce/Le/No` (`0x0486`) | Half Fire, Half Water, Half Wind, Half Thunder, Half Special |
| `0x0A2` | `50A2` | Moon Tiara | 0 | - | 100000 | `Re/Ce` (`0x0006`) | - |
| `0x0A5` | `50A5` | Beret | 0 | - | 40000 | `All` (`0x0FFF`) | - |
| `0x28F` | `528F` | Leather Helm (Helment) | 3 | - | 50 | `All` (`0x0FFF`) | - |
| `0x290` | `5290` | Odd Helment (Helment) | 6 | - | 120 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x291` | `5291` | Odd Hat (Helment) | 1 | - | 10 | `Re/Ce/Le` (`0x0086`) | - |
| `0x292` | `5292` | Banded Helm (Helment) | 6 | - | 120 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x293` | `5293` | Magical Hat (Helment) | 10 | - | 600 | `Re/Ce/Le` (`0x0086`) | - |
| `0x294` | `5294` | Fame Helm (Helment) | 12 | - | 500 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x295` | `5295` | Iron Helm (Helment) | 25 | - | 1200 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x296` | `5296` | Rune Cap (Helment) | 26 | - | 20000 | `Re/Ce/Le` (`0x0086`) | - |
| `0x297` | `5297` | Plate Helm (Helment) | 38 | - | 7000 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x298` | `5298` | Isis Tiara (Helment) | 50 | - | 50000 | `Re/Ce/Le` (`0x0086`) | - |
| `0x299` | `5299` | Steel Helm (Helment) | 50 | - | 16000 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x29A` | `529A` | Jeanne's Helm (Helment) | 56 | - | 8600 | `Pr/Op/Ch` (`0x0920`) | Half Water, Half Special |
| `0x29B` | `529B` | Wizard's Hat (Helment) | 29 | - | 65200 | `Re/Ce/Le/No` (`0x0486`) | - |
| `0x29C` | `529C` | Mithril Helm (Helment) | 65 | - | 83400 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x29D` | `529D` | Sylvan Helm (Helment) | 50 | - | 100000 | `Pr/Op/Ch` (`0x0920`) | - |
| `0x29E` | `529E` | Duel Helm (Helment) | 100 | - | 100000 | `Cl/Bo/Di/As/Er/No` (`0x0659`) | - |
| `0x29F` | `529F` | Hermit's Helm (Helment) | 35 | - | 20000 | `Re/Ce/Le` (`0x0086`) | Half Wind |
| `0x2A0` | `52A0` | Odin's Helm (Helment) | 50 | MAG+10 | 160000 | `Cl/Di/As` (`0x0051`) | Half Special |
| `0x2A1` | `52A1` | Bloody Helm (Helment) | 33 | MAG+33 | 333 | `Cl/Bo/Di/As/Op/Er/No/Ch` (`0x0F59`) | - |

---

## 9. Boots & Greaves Catalog (Category 11, 27 items)

| ID | Code | Name | DEF | AGL / Move | Price | Equip Mask | Notes |
|---|---|---|---|---|---|---|---|
| `0x042` | `5042` | Glass Slippers | 1 | - | 120 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x189` | `5189` | Bunny Shoe (Boot) | 10 | +80 | 200000 | `All` (`0x0FFF`) | - |
| `0x2D8` | `52D8` | Sandals (Boot) | 1 | - | 10 | `All` (`0x0FFF`) | - |
| `0x2D9` | `52D9` | Leather Greaves (Boot) | 5 | - | 50 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2DA` | `52DA` | Boots (Boot) | 3 | - | 40 | `All` (`0x0FFF`) | - |
| `0x2DB` | `52DB` | Secret Boots (Boot) | 3 | - | 80 | `All` (`0x0FFF`) | - |
| `0x2DC` | `52DC` | Suede Boots (Boot) | 5 | - | 200 | `All` (`0x0FFF`) | - |
| `0x2DD` | `52DD` | Iron Greaves (Boot) | 10 | - | 110 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2DE` | `52DE` | Original Boots (Boot) | 3 | - | 150 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x2DF` | `52DF` | Leather Boots (Boot) | 6 | - | 105 | `All` (`0x0FFF`) | - |
| `0x2E0` | `52E0` | Plate Greaves (Boot) | 18 | - | 800 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2E1` | `52E1` | High Heels (Boot) | 5 | - | 120 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x2E2` | `52E2` | High-laced Shoes (Boot) | 25 | - | 4100 | `Re/Ce/Le` (`0x0086`) | - |
| `0x2E3` | `52E3` | Silver Greaves (Boot) | 30 | - | 5200 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2E4` | `52E4` | Odd Shoes (Boot) | 1 | - | 50 | `All` (`0x0FFF`) | - |
| `0x2E5` | `52E5` | Pin Heels (Boot) | 3 | - | 300 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x2E7` | `52E7` | Mud Boots (Boot) | 0 | - | 0 | `All` (`0x0FFF`) | - |
| `0x2E8` | `52E8` | Valkyrie Boots (Boot) | 250 | - | 3000000 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x2E9` | `52E9` | Steel-toes Boots (Boot) | 8 | - | 3200 | `All` (`0x0FFF`) | AVD+20 |
| `0x2EA` | `52EA` | Rune Shoes (Boot) | 20 | - | 30000 | `Re/Ce/Le/No` (`0x0486`) | AVD+20 |
| `0x2EB` | `52EB` | Mithril Greaves (Boot) | 45 | - | 76000 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | - |
| `0x2EC` | `52EC` | Witch's Boots (Boot) | 34 | - | 40000 | `Re/Ce/Le` (`0x0086`) | AVD+10 |
| `0x2ED` | `52ED` | Valiant Boots (Boot) | 260 | - | 2200000 | `Cl/Bo/Di/As/Le/Er/No` (`0x06D9`) | - |
| `0x2EE` | `52EE` | Sylvan Boots (Boot) | 60 | - | 110000 | `Pr/Op/Ch` (`0x0920`) | - |
| `0x2EF` | `52EF` | Neo Greaves (Boot) | 20 | - | 18400 | `Cl/Bo/Di/Pr/As/Op/Er/No/Ch` (`0x0F79`) | AVD+5, GUTS+10 |
| `0x2F0` | `52F0` | Star Greaves (Boot) | 60 | - | 80000 | `Cl/Bo/Di/Pr/As/Op/Er/Ch` (`0x0B79`) | - |
| `0x2F1` | `52F1` | Neumann Boots (Boot) | 4 | +10 | 2980 | `Pr` (`0x0020`) | AVD+4 |

---

## 10. Accessories & Minerals Catalog (Category 12, 131 items)

| ID | Code | Name | ATK/DEF | Price | Equip Mask | Elemental Multipliers / Special Effects |
|---|---|---|---|---|---|---|
| `0x038` | `5038` | Moonlight | - | 5200 | `All` (`0x0FFF`) | - |
| `0x039` | `5039` | Silver Idol | AVD+1 | 3000 | `All` (`0x0FFF`) | - |
| `0x03A` | `503A` | Golden Idol | HIT/CRT+1 | 3500 | `All` (`0x0FFF`) | - |
| `0x03B` | `503B` | Pretty Idol | MAG+1 | 5000 | `All` (`0x0FFF`) | - |
| `0x03C` | `503C` | Weird Doll | - | 32 | `All` (`0x0FFF`) | - |
| `0x03D` | `503D` | Reverse Doll | - | 5650 | `All` (`0x0FFF`) | Half Fire, Half Water, Half Wind, Half Earth, Half Thunder, Half Star, Half Light, Half Dark, Half Void, Half Special, Proc `0x14` |
| `0x03E` | `503E` | Silver Pendant | AVD+10 | 1000 | `All` (`0x0FFF`) | Proc `0x05` |
| `0x03F` | `503F` | Sturm Ring | HIT/CRT+15, AVD+15, GUTS+5 | 2000 | `All` (`0x0FFF`) | - |
| `0x040` | `5040` | Green Bracelet | GUTS+5 | 600 | `All` (`0x0FFF`) | - |
| `0x043` | `5043` | Regeneration Ring | DEF+2 | 6500 | `All` (`0x0FFF`) | - |
| `0x044` | `5044` | Useless Decoration | - | 20 | `All` (`0x0FFF`) | - |
| `0x045` | `5045` | Luna Tablet | - | 3400 | `All` (`0x0FFF`) | - |
| `0x046` | `5046` | Poison Check | - | 5000 | `All` (`0x0FFF`) | - |
| `0x047` | `5047` | Paralysis Check | - | 6000 | `All` (`0x0FFF`) | - |
| `0x048` | `5048` | Stone Check | - | 7000 | `All` (`0x0FFF`) | - |
| `0x049` | `5049` | Purple Mist | GUTS+10 | 14000 | `All` (`0x0FFF`) | - |
| `0x04A` | `504A` | Magic Mist | - | 26000 | `All` (`0x0FFF`) | - |
| `0x04B` | `504B` | Necklace | AVD+1 | 1200 | `All` (`0x0FFF`) | - |
| `0x04C` | `504C` | Might Chain | STR/AGL+30 | 1200 | `All` (`0x0FFF`) | - |
| `0x04D` | `504D` | Surrender Pendant | - | 4000 | `All` (`0x0FFF`) | - |
| `0x04E` | `504E` | Leaf Pendant | GUTS+10 | 6000 | `Re/Ce/Le/No` (`0x0486`) | - |
| `0x04F` | `504F` | Ruby Pendant | - | 1000 | `All` (`0x0FFF`) | - |
| `0x050` | `5050` | Star Necklace | - | 16000 | `Re/Ce/Le/No` (`0x0486`) | - |
| `0x051` | `5051` | Fairy Tear | - | 10000 | `All` (`0x0FFF`) | Half Water, Weak Wind |
| `0x052` | `5052` | Pyre Tear | - | 10000 | `All` (`0x0FFF`) | Weak Water, Half Wind |
| `0x053` | `5053` | Silver Charm | MAG+3 | 20000 | `Re/Ce/Le/No` (`0x0486`) | - |
| `0x054` | `5054` | Blue Talisman | STR/AGL+12 | 6000 | `Cl/Bo/Di/Pr/As/Op/Er/Ch` (`0x0B79`) | Half Water |
| `0x055` | `5055` | Talisman | STR/AGL+8 | 3000 | `All` (`0x0FFF`) | - |
| `0x056` | `5056` | Luna Talisman | - | 6000 | `All` (`0x0FFF`) | Proc `0x14` |
| `0x057` | `5057` | Gold Ring | AVD+1 | 2000 | `All` (`0x0FFF`) | - |
| `0x058` | `5058` | Princess Ring | MAG+2 | 7000 | `Re/Ce/Le/No` (`0x0486`) | - |
| `0x059` | `5059` | Healing Ring | - | 4400 | `All` (`0x0FFF`) | - |
| `0x05A` | `505A` | Mental Ring | - | 8800 | `All` (`0x0FFF`) | - |
| `0x05B` | `505B` | Wisdom Ring | - | 5300 | `All` (`0x0FFF`) | - |
| `0x05C` | `505C` | Weighty Ring | DEF+2 | 10 | `All` (`0x0FFF`) | Weak Light, Weak Void, Weak Special, Proc `0x05` |
| `0x05D` | `505D` | Hard Ring | - | 800 | `All` (`0x0FFF`) | Weak Star, Proc `0x06` |
| `0x05E` | `505E` | Heavy Ring | - | 600 | `All` (`0x0FFF`) | Weak Wind, Weak Earth, Weak Thunder, Proc `0x0A` |
| `0x05F` | `505F` | Atlas Ring | - | 30000 | `All` (`0x0FFF`) | Weak Fire, Weak Water, Weak Wind, Weak Earth, Weak Thunder, Weak Star, Weak Light, Weak Dark, Weak Void, Weak Special |
| `0x060` | `5060` | Eclipse Ring | - | 3400 | `Cl/Bo/Di/Pr/As/Op/Er/Ch` (`0x0B79`) | - |
| `0x061` | `5061` | Insanity Ring | - | 1200 | `All` (`0x0FFF`) | - |
| `0x062` | `5062` | Infinity Ring | - | 20000 | `All` (`0x0FFF`) | Weak Fire, Weak Water, Weak Wind, Weak Earth, Weak Thunder, Weak Star, Weak Light, Weak Dark, Weak Void, Weak Special |
| `0x063` | `5063` | Battalia Ring | DEF+30 | 8500 | `All` (`0x0FFF`) | Weak Fire, Weak Wind, Weak Thunder, Weak Light, Weak Void |
| `0x064` | `5064` | Demonslayer Ring | - | 8200 | `All` (`0x0FFF`) | - |
| `0x065` | `5065` | Reflection Ring | MAG+6 | 2000 | `All` (`0x0FFF`) | - |
| `0x066` | `5066` | Protection Ring | DEF+6 | 2000 | `All` (`0x0FFF`) | - |
| `0x067` | `5067` | Ring Of Happiness | MAG+10, STR/AGL+10, GUTS+50 | 10000 | `Re` (`0x0002`) | - |
| `0x068` | `5068` | Ring of Sadness | - | 8200 | `All` (`0x0FFF`) | - |
| `0x069` | `5069` | Promised Ring | STR/AGL+20, GUTS+10 | 10000 | `All` (`0x0FFF`) | Proc `0x14` |
| `0x06A` | `506A` | Stardust Ring | - | 5000 | `All` (`0x0FFF`) | - |
| `0x06B` | `506B` | Peep Half | - | 18000 | `All` (`0x0FFF`) | Proc `0x05` |
| `0x06C` | `506C` | Peep Non | - | 24000 | `All` (`0x0FFF`) | Proc `0x0A` |
| `0x06D` | `506D` | Slayer's Ring | STR/AGL+30 | 28000 | `All` (`0x0FFF`) | Proc `0x0A` |
| `0x06E` | `506E` | Meteor Ring | STR/AGL+10 | 28000 | `All` (`0x0FFF`) | Proc `0x05` |
| `0x06F` | `506F` | Lunatic Ring | - | 3510 | `All` (`0x0FFF`) | - |
| `0x070` | `5070` | Berserk Ring | - | 3600 | `All` (`0x0FFF`) | - |
| `0x071` | `5071` | Shield Ring | - | 1000 | `All` (`0x0FFF`) | - |
| `0x072` | `5072` | Resistance Ring | - | 1000 | `All` (`0x0FFF`) | - |
| `0x073` | `5073` | Aqua Ring | - | 3000 | `All` (`0x0FFF`) | Half Water, Weak Wind |
| `0x074` | `5074` | Flare Ring | - | 3000 | `All` (`0x0FFF`) | Weak Water, Half Wind |
| `0x075` | `5075` | General's Ring | STR/AGL+20 | 3500 | `All` (`0x0FFF`) | - |
| `0x076` | `5076` | Prism Ring | - | 6200 | `All` (`0x0FFF`) | Proc `0x05` |
| `0x077` | `5077` | Holy Ring | - | 1500 | `All` (`0x0FFF`) | - |
| `0x078` | `5078` | Emerald Ring | STR/AGL+10 | 64800 | `All` (`0x0FFF`) | - |
| `0x079` | `5079` | Water Ring | MAG+10, STR/AGL+10 | 8000 | `Re/Ce/Le/No` (`0x0486`) | Half Water, Weak Wind, Proc `0x0A` |
| `0x07A` | `507A` | Fire Ring | MAG+10, STR/AGL+10 | 8000 | `Re/Ce/Le/No` (`0x0486`) | Weak Water, Half Wind, Proc `0x0A` |
| `0x07B` | `507B` | Thunder Ring | - | 8000 | `Re/Ce/Le/No` (`0x0486`) | Weak Water, Half Thunder, Proc `0x1E` |
| `0x07C` | `507C` | Fairy Ring | - | 78200 | `All` (`0x0FFF`) | - |
| `0x07D` | `507D` | Black Earring | - | 45000 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x07E` | `507E` | Golden Earring | - | 2500 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x07F` | `507F` | Ruby Earring | DEF+1 | 6000 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x080` | `5080` | Blood Earring | - | 2800 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x081` | `5081` | Shield Earring | - | 5000 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x082` | `5082` | Zephyr Earring | - | 5000 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x083` | `5083` | Flash Earring | - | 5000 | `Ce/Op/Ch` (`0x0904`) | Half Thunder |
| `0x084` | `5084` | Gaudy Earring | - | 98 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x085` | `5085` | Gale Earring | HIT/CRT+10, AVD+10 | 30000 | `Ce/Op/Ch` (`0x0904`) | Half Earth |
| `0x086` | `5086` | Hard Earring | - | 1200 | `Ce/Op/Ch` (`0x0904`) | - |
| `0x087` | `5087` | Emerald Earring | - | 6000 | `Ce` (`0x0004`) | Half Earth |
| `0x088` | `5088` | Star Earring | - | 3000 | `Ce` (`0x0004`) | Half Star |
| `0x089` | `5089` | Attack Earring | ATK+20 | 3000 | `Ce` (`0x0004`) | Proc `0x14` |
| `0x08A` | `508A` | First Earring | GUTS+20 | 5000 | `Re/Ce/Op/Ch` (`0x0906`) | Half Light |
| `0x08B` | `508B` | Lunatic Earring | - | 5000 | `Ce/Op/Ch` (`0x0904`) | Weak Light |
| `0x08C` | `508C` | Silver Cross | - | 3000 | `All` (`0x0FFF`) | Weak Wind, Half Light, Half Dark |
| `0x08D` | `508D` | Golden Cross | HIT/CRT+50 | 6000 | `All` (`0x0FFF`) | Half Wind, Weak Light |
| `0x08E` | `508E` | Magic Cross | - | 2000 | `All` (`0x0FFF`) | Half Star, Half Light, Half Dark |
| `0x08F` | `508F` | Silver Ring | DEF+2, STR/AGL+10, GUTS+10 | 2800 | `All` (`0x0FFF`) | Half Light, Half Dark, Half Void, Status Prot `0x0032` |
| `0x090` | `5090` | Right Cross | DEF+20, AVD+40, GUTS+20 | 10000 | `All` (`0x0FFF`) | Half Fire, Weak Water, Half Wind, Half Earth, Half Thunder, Weak Star, Weak Light, Weak Dark, Half Void, Weak Special, Proc `0x0A` |
| `0x091` | `5091` | Left Cross | HIT/CRT+40, MAG+20, STR/AGL+20 | 10000 | `All` (`0x0FFF`) | Weak Fire, Half Water, Weak Wind, Weak Earth, Weak Thunder, Half Star, Half Light, Half Dark, Weak Void, Half Special |
| `0x092` | `5092` | Silver Barrette | DEF+3 | 1300 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x093` | `5093` | Angle Hair | AVD+5 | 500 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x094` | `5094` | Golden Bracelet | DEF+10 | 2000 | `All` (`0x0FFF`) | - |
| `0x095` | `5095` | Anklet | DEF+3 | 400 | `All` (`0x0FFF`) | - |
| `0x096` | `5096` | Lot Bracelet | - | 10000 | `All` (`0x0FFF`) | - |
| `0x097` | `5097` | Recoil Bracelet | - | 1200 | `All` (`0x0FFF`) | - |
| `0x098` | `5098` | Dream Bracelet | - | 2000 | `All` (`0x0FFF`) | - |
| `0x09A` | `509A` | Shiny Earring | - | 1500 | `Ce/Op/Ch` (`0x0904`) | Half Dark |
| `0x09B` | `509B` | Moon Earring | - | 1500 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | Half Light |
| `0x09C` | `509C` | Mind Ring | - | 8000 | `All` (`0x0FFF`) | Weak Thunder |
| `0x09D` | `509D` | Feet Symbol | - | 3000 | `All` (`0x0FFF`) | - |
| `0x09E` | `509E` | Silver Earring | - | 30000 | `Re/Ce/Pr/Op/Ch` (`0x0926`) | - |
| `0x09F` | `509F` | Misty Symbol | - | 3000 | `All` (`0x0FFF`) | - |
| `0x13C` | `513C` | Israfil's Tear | ATK+60, DEF+30, HIT/CRT+30, AVD+30, MAG+80, GUTS+50 | 0 | `Re/Ce` (`0x0006`) | Absorb Special, Status Prot `0x00FF`, Proc `0x14` |
| `0x141` | `5141` | Tri-emplem | ATK+10, DEF+12, HIT/CRT+10, AVD+5, MAG+3 | 31419 | `All` (`0x0FFF`) | - |
| `0x15C` | `515C` | Link Combo | - | 0 | `Cl/Bo/Di/Pr/As/Op/Er/Ch` (`0x0B79`) | - |
| `0x181` | `5181` | Angle Armband (strong)  [in game: Angel Armband] | ATK+60, DEF+60, HIT/CRT+60, AVD+60, MAG+200, GUTS+572 | 15000000 | `All` (`0x0FFF`) | Half Fire, Half Water, Absorb Wind, Half Earth, Absorb Thunder, Absorb Star, Half Light, Half Dark, Half Void, Half Special, Status Prot `0x6464`, Proc `0x3C` |
| `0x1A3` | `51A3` | Iron | HIT/CRT+1 | 200 | `All` (`0x0FFF`) | - |
| `0x1A4` | `51A4` | Gold | AVD+1 | 300 | `All` (`0x0FFF`) | - |
| `0x1A5` | `51A5` | Silver | DEF+1 | 200 | `All` (`0x0FFF`) | - |
| `0x1A6` | `51A6` | Moonite | - | 1500 | `All` (`0x0FFF`) | Half Light |
| `0x1A7` | `51A7` | Orichalcum | - | 10000 | `All` (`0x0FFF`) | Half Void, Half Special |
| `0x1A8` | `51A8` | Meteorite | - | 5200 | `All` (`0x0FFF`) | Half Void |
| `0x1A9` | `51A9` | Mithril | - | 15000 | `All` (`0x0FFF`) | Half Dark |
| `0x1AA` | `51AA` | Damascus | - | 6400 | `All` (`0x0FFF`) | Half Void |
| `0x1AB` | `51AB` | Rune Metal | - | 7000 | `All` (`0x0FFF`) | Half Thunder |
| `0x1AD` | `51AD` | Green Beryl | - | 500 | `All` (`0x0FFF`) | Half Earth |
| `0x1AE` | `51AE` | Sapphire | - | 800 | `All` (`0x0FFF`) | Half Water |
| `0x1AF` | `51AF` | Ruby | - | 400 | `All` (`0x0FFF`) | Half Wind |
| `0x1B0` | `51B0` | Star Ruby | - | 10000 | `All` (`0x0FFF`) | Half Wind, Half Void |
| `0x1B1` | `51B1` | Crystal | - | 500 | `All` (`0x0FFF`) | Half Thunder |
| `0x1B2` | `51B2` | Sage's Stone | - | 50000 | `All` (`0x0FFF`) | Half Dark, Half Void, Half Special |
| `0x1B3` | `51B3` | Diamond | - | 9000 | `All` (`0x0FFF`) | Half Thunder |
| `0x1B4` | `51B4` | Rainbow Diamond | - | 14000 | `All` (`0x0FFF`) | Half Star, Half Dark |
| `0x1B5` | `51B5` | Bandit's Gloves | - | 40000 | `All` (`0x0FFF`) | - |
| `0x1BC` | `51BC` | Magician's Hand | - | 3000 | `All` (`0x0FFF`) | - |
| `0x2A2` | `52A2` | Salamander Helment (Helment) | DEF+12, AVD+10 | 6000 | `As` (`0x0040`) | - |
| `0x2A3` | `52A3` | Sacknoth's Helment (Helment) | DEF+40, AVD+15 | 12000 | `As` (`0x0040`) | - |
| `0x2E6` | `52E6` | Santa's Boots (Boot) | - | 10000000 | `All` (`0x0FFF`) | - |
| `0x2FB` | `52FB` | Tri-emblem | ATK+200, DEF+50, HIT/CRT+50, AVD+50, MAG+100, STR/AGL+50, GUTS+50 | 5000000 | `All` (`0x0FFF`) | Half Fire, Half Water, Half Wind, Half Earth, Half Thunder, Half Star, Half Light, Half Dark, Half Void, Half Special, Proc `0x14` |
| `0x303` | `5303` | Mischief | - | 1200 | `All` (`0x0FFF`) | Weak Fire |
| `0x304` | `5304` | Trickster | - | 2200 | `All` (`0x0FFF`) | Weak Water |
| `0x305` | `5305` | Fortune | - | 3200 | `All` (`0x0FFF`) | Weak Wind |

---

## 11. Medicine, Herbs & Potions Catalog (Category 0, Usable 3, 37 items)

| ID | Code | Name | Recovery Value | Effect ID | Price | Sell Rate | Function / Usage |
|---|---|---|---|---|---|---|---|
| `0x022` | `5022` | Angle's Statue | 30% | `0x02` | 160 | 25% | Field & Battle Usable |
| `0x024` | `5024` | Goddess Statue | 30% | `0x04` | 300 | 25% | Field & Battle Usable |
| `0x0DC` | `50DC` | Mandrake | - | `0x25` | 150 | 25% | Field & Battle Usable |
| `0x0DD` | `50DD` | Rose Hips | 2% | `0x01` | 230 | 25% | Field & Battle Usable |
| `0x0DE` | `50DE` | Artemis Leaf | 10% | `0x5D` | 720 | 25% | Field & Battle Usable |
| `0x0DF` | `50DF` | Wolfsbane | - | `0x27` | 360 | 25% | Field & Battle Usable |
| `0x0E0` | `50E0` | Lavender | 3% | `0x01` | 490 | 25% | Field & Battle Usable |
| `0x0E1` | `50E1` | Aceras | 2% | `0x01` | 660 | 25% | Field & Battle Usable |
| `0x0E4` | `50E4` | Energy Tonic | - | `0x2A` | 1000 | 25% | Field & Battle Usable |
| `0x0E6` | `50E6` | Smelling Salts | - | `0x2C` | 200 | 25% | Field & Battle Usable |
| `0x0EA` | `50EA` | Herbal Oil | - | `0x30` | 300 | 25% | Field & Battle Usable |
| `0x0EF` | `50EF` | Fairy's Cologne | - | `0x35` | 450 | 25% | Field & Battle Usable |
| `0x0F0` | `50F0` | Merlin Drink | 100% | `0x03` | 500 | 25% | Field & Battle Usable |
| `0x0F3` | `50F3` | Ressurrection Mist | 100% | `0x06` | 6000 | 25% | Field & Battle Usable |
| `0x0F4` | `50F4` | Risky Liquid | - | `0x39` | 80 | 25% | Field & Battle Usable |
| `0x0F6` | `50F6` | Danger Pot | - | `0x3B` | 220 | 25% | Field & Battle Usable |
| `0x0F7` | `50F7` | Nightmare Pot | - | `0x3C` | 190 | 25% | Field & Battle Usable |
| `0x0FB` | `50FB` | Sour Syrup | 30% | `0x03` | 300 | 25% | Field & Battle Usable |
| `0x0FC` | `50FC` | Sweet Syrup | 30% | `0x01` | 300 | 25% | Field & Battle Usable |
| `0x0FD` | `50FD` | Maple Syrup | 20% | `0x01` | 200 | 25% | Field & Battle Usable |
| `0x0FE` | `50FE` | Fruit Syrup | 45% | `0x05` | 600 | 25% | Field & Battle Usable |
| `0x0FF` | `50FF` | Fresh Syrup | 100% | `0x01` | 800 | 25% | Field & Battle Usable |
| `0x100` | `5100` | Hot Syrup | - | `0x40` | 300 | 25% | Field & Battle Usable |
| `0x101` | `5101` | Mixed Syrup | 30% | `0x05` | 500 | 25% | Field & Battle Usable |
| `0x102` | `5102` | Cure Poison | - | `0x41` | 140 | 25% | Field & Battle Usable |
| `0x103` | `5103` | Cure Paralysis | - | `0x42` | 180 | 25% | Field & Battle Usable |
| `0x104` | `5104` | Wonder Drug | 10% | `0x43` | 800 | 25% | Field & Battle Usable |
| `0x108` | `5108` | Violence Pill | - | `0x47` | 140 | 25% | Field & Battle Usable |
| `0x10C` | `510C` | Succubus Cologne | - | `0x4B` | 500 | 25% | Field & Battle Usable |
| `0x113` | `5113` | Holy Mist | 60% | `0x02` | 3200 | 25% | Field & Battle Usable |
| `0x115` | `5115` | Resurrection Bottle | 60% | `0x06` | 3600 | 25% | Field & Battle Usable |
| `0x116` | `5116` | Spring Water | - | `0x52` | 120 | 25% | Field & Battle Usable |
| `0x1D7` | `51D7` | Odd Medicine | - | `0x47` | 200 | 25% | Field & Battle Usable |
| `0x2F3` | `52F3` | Aquaberry | 10% | `0x5D` | 105 | 25% | Field & Battle Usable |
| `0x2F4` | `52F4` | Blackberry | 22% | `0x03` | 200 | 25% | Field & Battle Usable |
| `0x2F5` | `52F5` | Blueberry | 22% | `0x01` | 60 | 25% | Field & Battle Usable |
| `0x302` | `5302` | Cure Stone | - | `0x62` | 450 | 25% | Field & Battle Usable |

---

## 12. Battle Usable Items Catalog (Category 0, Usable 1, 56 items)

| ID | Code | Name | Effect Parameter | Effect ID | Price | Sell Rate | Function / Usage |
|---|---|---|---|---|---|---|---|
| `0x003` | `5003` | 'The Scream' | - | `0x0B` | 500 | 25% | Battle Only |
| `0x004` | `5004` | 'Judgment Day' | - | `0x0C` | 400 | 25% | Battle Only |
| `0x005` | `5005` | 'The Last Supper' | - | `0x0D` | 650 | 25% | Battle Only |
| `0x013` | `5013` | Victorial Card | - | `0x0E` | 120 | 25% | Battle Only |
| `0x014` | `5014` | Mortalial Card | - | `0x0F` | 120 | 25% | Battle Only |
| `0x015` | `5015` | Revival Card | - | `0x10` | 200 | 25% | Battle Only |
| `0x016` | `5016` | Fol Up Card | - | `0x11` | 500 | 25% | Battle Only |
| `0x017` | `5017` | Dicovery Card | - | `0x12` | 500 | 25% | Battle Only |
| `0x018` | `5018` | Extension Card | - | `0x13` | 600 | 25% | Battle Only |
| `0x019` | `5019` | Fairies Card | - | `0x14` | 200 | 25% | Battle Only |
| `0x01B` | `501B` | Silence Card | - | `0x16` | 300 | 25% | Battle Only |
| `0x01C` | `501C` | Hexagram Card | - | `0x17` | 350 | 25% | Battle Only |
| `0x01D` | `501D` | Magic Rock | - | `0x18` | 110 | 25% | Battle Only |
| `0x01F` | `501F` | Tri-ball | - | `0x19` | 300 | 25% | Battle Only |
| `0x020` | `5020` | Hyperball | - | `0x1A` | 200 | 25% | Battle Only |
| `0x021` | `5021` | Super Ball | - | `0x1B` | 200 | 25% | Battle Only |
| `0x023` | `5023` | Fairy's Statue | - | `0x1C` | 400 | 25% | Battle Only |
| `0x025` | `5025` | Dummy Doll | - | `0x1D` | 300 | 25% | Battle Only |
| `0x026` | `5026` | Idol | - | `0x1E` | 800 | 25% | Battle Only |
| `0x027` | `5027` | Skanda | - | `0x1F` | 420 | 25% | Battle Only |
| `0x02A` | `502A` | Mirror of Wisdom | - | `0x22` | 1200 | 25% | Battle Only |
| `0x036` | `5036` | Spectacles | - | `0x61` | 8 | 25% | Battle Only |
| `0x037` | `5037` | Magical Drops | - | `0x5F` | 8500 | 25% | Battle Only |
| `0x0E2` | `50E2` | Skanda Compress | - | `0x28` | 200 | 25% | Battle Only |
| `0x0E3` | `50E3` | Attack Vial | - | `0x29` | 230 | 25% | Battle Only |
| `0x0E5` | `50E5` | Kamikaze Tonic | - | `0x2B` | 1000 | 25% | Battle Only |
| `0x0E7` | `50E7` | Shock Oil | - | `0x2D` | 200 | 25% | Battle Only |
| `0x0E8` | `50E8` | Smoke Oil | - | `0x2E` | 180 | 25% | Battle Only |
| `0x0EB` | `50EB` | Bubble Lotion | - | `0x31` | 500 | 25% | Battle Only |
| `0x0EC` | `50EC` | Paralysis Oil | - | `0x32` | 500 | 25% | Battle Only |
| `0x0ED` | `50ED` | Bitter Lotion | - | `0x33` | 500 | 25% | Battle Only |
| `0x0EE` | `50EE` | Fairy Glass | - | `0x34` | 10000 | 25% | Battle Only |
| `0x0F1` | `50F1` | Medical Rinse | - | `0x37` | 120 | 25% | Battle Only |
| `0x0F2` | `50F2` | Melting Lotion | - | `0x38` | 120 | 25% | Battle Only |
| `0x0F5` | `50F5` | Lilith Tonic | - | `0x3A` | 150 | 25% | Battle Only |
| `0x0FA` | `50FA` | Mental Pot | - | `0x3F` | 300 | 25% | Battle Only |
| `0x105` | `5105` | Natural High | - | `0x44` | 550 | 25% | Battle Only |
| `0x106` | `5106` | Crush Pill | - | `0x45` | 140 | 25% | Battle Only |
| `0x107` | `5107` | Care Tablet | - | `0x46` | 400 | 25% | Battle Only |
| `0x109` | `5109` | Marionette Pill | - | `0x48` | 140 | 25% | Battle Only |
| `0x10A` | `510A` | Skanda Ointment | - | `0x49` | 500 | 25% | Battle Only |
| `0x10B` | `510B` | Stink Gel | - | `0x4A` | 300 | 25% | Battle Only |
| `0x10E` | `510E` | Pixie Cologne | - | `0x4D` | 1000 | 25% | Battle Only |
| `0x10F` | `510F` | Smoke Mist | - | `0x4E` | 300 | 25% | Battle Only |
| `0x110` | `5110` | Paralysis Mist | - | `0x4F` | 300 | 25% | Battle Only |
| `0x111` | `5111` | Fairy Mist | - | `0x50` | 13000 | 25% | Battle Only |
| `0x114` | `5114` | Madness Mist | - | `0x51` | 500 | 25% | Battle Only |
| `0x1BE` | `51BE` | Killer Poison | - | `0x53` | 300 | 40% | Battle Only |
| `0x1BF` | `51BF` | Peep-peep Bomb | - | `0x54` | 500 | 80% | Battle Only |
| `0x1C0` | `51C0` | Mind Bomb | - | `0x55` | 400 | 80% | Battle Only |
| `0x1C1` | `51C1` | Flare Bomb | - | `0x56` | 450 | 40% | Battle Only |
| `0x1C2` | `51C2` | Tetra-bomb | - | `0x57` | 600 | 80% | Battle Only |
| `0x1C3` | `51C3` | Assault Bomb | - | `0x58` | 1000 | 80% | Battle Only |
| `0x1C4` | `51C4` | Protection Bomb | - | `0x59` | 2000 | 80% | Battle Only |
| `0x1C5` | `51C5` | Half-dead Bomb | - | `0x5A` | 2500 | 80% | Battle Only |
| `0x1C7` | `51C7` | Nuclear Bomb | - | `0x5C` | 4000 | 80% | Battle Only |

---

## 13. Food, Cooking & Artwork Catalog (Category 0, Usable 2, 225 items)

| ID | Code | Name | Price | Effect ID | Sub-Type | Sell Rate | Notes |
|---|---|---|---|---|---|---|---|
| `0x002` | `5002` | 'Spring' | 300 | `0x0A` | `0x00` | 25% | Camp/Menu Usable |
| `0x006` | `5006` | Portrait A | 1000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x007` | `5007` | Portrait B | 2000 | `0x00` | `0x00` | 80% | Camp/Menu Usable |
| `0x008` | `5008` | Portrait C | 3000 | `0x00` | `0x00` | 60% | Camp/Menu Usable |
| `0x009` | `5009` | Portrait G | 1600 | `0x00` | `0x00` | 50% | Camp/Menu Usable |
| `0x00A` | `500A` | Portrait I | 3000 | `0x00` | `0x00` | 80% | Camp/Menu Usable |
| `0x00B` | `500B` | Portrait D | 800 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x00C` | `500C` | Portrait F | 2000 | `0x00` | `0x00` | 80% | Camp/Menu Usable |
| `0x00D` | `500D` | Portrait J | 1500 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x00E` | `500E` | Portrait H | 1500 | `0x00` | `0x00` | 50% | Camp/Menu Usable |
| `0x00F` | `500F` | Portrait E | 3000 | `0x00` | `0x00` | 60% | Camp/Menu Usable |
| `0x010` | `5010` | Portrait L | 2000 | `0x00` | `0x00` | 60% | Camp/Menu Usable |
| `0x011` | `5011` | Portrait K | 1600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x01A` | `501A` | Fountain Card | 1000 | `0x15` | `0x00` | 25% | Camp/Menu Usable |
| `0x028` | `5028` | Treasure Chest | 3000 | `0x20` | `0x00` | 25% | Camp/Menu Usable |
| `0x029` | `5029` | Jack-in-the-box | 2100 | `0x21` | `0x00` | 25% | Camp/Menu Usable |
| `0x0A6` | `50A6` | Pose Collection | 600 | `0x23` | `0x00` | 25% | Camp/Menu Usable |
| `0x0A7` | `50A7` | Today's Dish | 600 | `0x24` | `0x00` | 25% | Camp/Menu Usable |
| `0x0A8` | `50A8` | Musical Theory | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0A9` | `50A9` | Operation Manual | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0AA` | `50AA` | Engineering | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0AB` | `50AB` | Choose Ingredients | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0AC` | `50AC` | Cook From The Heart | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0AD` | `50AD` | Mystical Beings | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0AE` | `50AE` | Heart Barriers | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0AF` | `50AF` | Nature's Life Force | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B0` | `50B0` | The Land's Secret | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B1` | `50B1` | Pocket Encyclopedia | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B2` | `50B2` | Gold/Silversmith | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B3` | `50B3` | Pieces for Learners | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B4` | `50B4` | No Need for Words | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B5` | `50B5` | Grammar | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B6` | `50B6` | The Hermes Theory | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B7` | `50B7` | Forest Friends | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B8` | `50B8` | All About Herbs | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0B9` | `50B9` | On Revenge | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0BA` | `50BA` | On Training | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0BB` | `50BB` | Before Tea's Ready | 600 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0C4` | `50C4` | Planet of the Winds | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0C5` | `50C5` | I Can Only See You | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0C6` | `50C6` | The World is Mine | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0C7` | `50C7` | Advanced Heraldry | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0C8` | `50C8` | The Bloody Road | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0C9` | `50C9` | New Civilization | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0CA` | `50CA` | Cat House Murder | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0CB` | `50CB` | Mr. 'No' | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0CC` | `50CC` | Buy it... Ok? | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0CD` | `50CD` | Living with Animals | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0CE` | `50CE` | But One Truth | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0CF` | `50CF` | Countdown | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D0` | `50D0` | Ocean of Stars | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D1` | `50D1` | Falling in Love | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D2` | `50D2` | Lady in Red | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D3` | `50D3` | Special Heraldry | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D4` | `50D4` | To Live | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D5` | `50D5` | Historic Greats | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D6` | `50D6` | Wax Doll Murders | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D7` | `50D7` | Never Turn Back | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D8` | `50D8` | A Maiden's Secret | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0D9` | `50D9` | Principles of Nature | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0DA` | `50DA` | Killer's Book | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0DB` | `50DB` | Lost Sanctuary | 5000 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x0E9` | `50E9` | Twin's Tonic | 100000 | `0x2F` | `0x00` | 25% | Camp/Menu Usable |
| `0x0F8` | `50F8` | Flash Pot | 300 | `0x3D` | `0x00` | 25% | Camp/Menu Usable |
| `0x10D` | `510D` | Aphrodisiac | 100000 | `0x4C` | `0x00` | 25% | Camp/Menu Usable |
| `0x11D` | `511D` | Sashimi | 2800 | `0x01` | `0x46` | 40% | Camp/Menu Usable |
| `0x11F` | `511F` | Sole & Wine Sauce | 1900 | `0x01` | `0x3C` | 50% | Camp/Menu Usable |
| `0x122` | `5122` | Shark Potstickers | 3000 | `0x01` | `0x46` | 50% | Camp/Menu Usable |
| `0x123` | `5123` | Shark Fin Soup | 600 | `0x03` | `0x28` | 50% | Camp/Menu Usable |
| `0x124` | `5124` | Bird's Nest Soup | 5000 | `0x03` | `0x46` | 50% | Camp/Menu Usable |
| `0x125` | `5125` | Broth | 300 | `0x03` | `0x1E` | 50% | Camp/Menu Usable |
| `0x126` | `5126` | Mushroom Soup | 2200 | `0x03` | `0x42` | 50% | Camp/Menu Usable |
| `0x127` | `5127` | Steamed Aspic | 2100 | `0x02` | `0x32` | 50% | Camp/Menu Usable |
| `0x129` | `5129` | Orangeade | 110 | `0x03` | `0x0A` | 40% | Camp/Menu Usable |
| `0x12A` | `512A` | Pear Compote | 5000 | `0x43` | `0x28` | 50% | Camp/Menu Usable |
| `0x12B` | `512B` | Stawberry Mochi | 2250 | `0x01` | `0x37` | 40% | Camp/Menu Usable |
| `0x12E` | `512E` | Muscat Grape Jelly | 4200 | `0x41` | `0x32` | 50% | Camp/Menu Usable |
| `0x12F` | `512F` | Konyaku Jelly | 3300 | `0x01` | `0x28` | 50% | Camp/Menu Usable |
| `0x132` | `5132` | Coconut Milk | 2000 | `0x43` | `0x37` | 50% | Camp/Menu Usable |
| `0x134` | `5134` | Fruit Sandwich | 1800 | `0x04` | `0x32` | 40% | Camp/Menu Usable |
| `0x135` | `5135` | Sole & Fruit Sauce | 600 | `0x01` | `0x16` | 50% | Camp/Menu Usable |
| `0x136` | `5136` | Sweet Rice Cakes | 2000 | `0x01` | `0x50` | 50% | Camp/Menu Usable |
| `0x137` | `5137` | Fried Rice | 300 | `0x01` | `0x1A` | 40% | Camp/Menu Usable |
| `0x138` | `5138` | Meat Fried Rice | 2000 | `0x02` | `0x3C` | 50% | Camp/Menu Usable |
| `0x139` | `5139` | Sake Lees Pickles | 2000 | `0x42` | `0x46` | 50% | Camp/Menu Usable |
| `0x13B` | `513B` | French Toast | 1800 | `0x03` | `0x37` | 40% | Camp/Menu Usable |
| `0x13E` | `513E` | Shrimp Shu-mai | 2000 | `0x03` | `0x3C` | 50% | Camp/Menu Usable |
| `0x13F` | `513F` | Hamburger | 200 | `0x01` | `0x13` | 40% | Camp/Menu Usable |
| `0x140` | `5140` | Sirlion Steak | 2000 | `0x02` | `0x50` | 50% | Camp/Menu Usable |
| `0x142` | `5142` | Peking Duck | 2000 | `0x02` | `0x46` | 50% | Camp/Menu Usable |
| `0x143` | `5143` | Creamed Stew | 2000 | `0x03` | `0x46` | 50% | Camp/Menu Usable |
| `0x145` | `5145` | Fish Squash Salad | 2000 | `0x43` | `0x44` | 50% | Camp/Menu Usable |
| `0x147` | `5147` | Daikon Radish | 1300 | `0x01` | `0x0A` | 40% | Camp/Menu Usable |
| `0x148` | `5148` | Happo-sai | 6500 | `0x01` | `0x14` | 50% | Camp/Menu Usable |
| `0x149` | `5149` | Fried Vegetables | 4000 | `0x02` | `0x32` | 50% | Camp/Menu Usable |
| `0x14C` | `514C` | Yogurt Salad | 2000 | `0x41` | `0x50` | 50% | Camp/Menu Usable |
| `0x14E` | `514E` | Tea Cloth Sushi | 5000 | `0x03` | `0x46` | 50% | Camp/Menu Usable |
| `0x14F` | `514F` | Plain Omlet | 2420 | `0x01` | `0x42` | 50% | Camp/Menu Usable |
| `0x151` | `5151` | Toro Tuna | 2000 | `0x02` | `0x14` | 40% | Camp/Menu Usable |
| `0x153` | `5153` | Seaweed Miso Soup | 190 | `0x04` | `0x14` | 50% | Camp/Menu Usable |
| `0x154` | `5154` | Shu-mai | 280 | `0x02` | `0x0A` | 40% | Camp/Menu Usable |
| `0x155` | `5155` | Amoeba Soup | 370 | `0x03` | `0x44` | 50% | Camp/Menu Usable |
| `0x158` | `5158` | Shrimp au Gratin | 500 | `0x01` | `0x1A` | 50% | Camp/Menu Usable |
| `0x159` | `5159` | Big Tuna | 3000 | `0x01` | `0x2D` | 50% | Camp/Menu Usable |
| `0x15A` | `515A` | Salmon Omlet | 500 | `0x01` | `0x1D` | 50% | Camp/Menu Usable |
| `0x15B` | `515B` | Shrimp Pilaf | 400 | `0x01` | `0x1E` | 50% | Camp/Menu Usable |
| `0x15D` | `515D` | Root Beer | 300 | `0x03` | `0x23` | 40% | Camp/Menu Usable |
| `0x15E` | `515E` | 'Ishidaya' Tea | 15000 | `0x04` | `0x3C` | 50% | Camp/Menu Usable |
| `0x15F` | `515F` | Yukiyucho Tea | 12000 | `0x03` | `0x37` | 50% | Camp/Menu Usable |
| `0x160` | `5160` | Hassaku Tea | 2800 | `0x03` | `0x28` | 50% | Camp/Menu Usable |
| `0x161` | `5161` | Yaegaki Tea | 10000 | `0x03` | `0x32` | 50% | Camp/Menu Usable |
| `0x162` | `5162` | 'Usunigori' Tea | 4000 | `0x03` | `0x2D` | 50% | Camp/Menu Usable |
| `0x163` | `5163` | Sambai Tea | 50 | `0x03` | `0x03` | 50% | Camp/Menu Usable |
| `0x164` | `5164` | Sweet Dumpling | 140 | `0x01` | `0x0C` | 40% | Camp/Menu Usable |
| `0x166` | `5166` | Daikon Miso Soup | 300 | `0x03` | `0x0A` | 40% | Camp/Menu Usable |
| `0x167` | `5167` | Gruel | 400 | `0x01` | `0x0A` | 50% | Camp/Menu Usable |
| `0x168` | `5168` | Rice Cakes | 110 | `0x01` | `0x13` | 50% | Camp/Menu Usable |
| `0x169` | `5169` | Pancakes | 340 | `0x01` | `0x17` | 40% | Camp/Menu Usable |
| `0x16B` | `516B` | Soda-Pop | 230 | `0x04` | `0x1E` | 50% | Camp/Menu Usable |
| `0x16D` | `516D` | Shrimp Doria | 550 | `0x01` | `0x15` | 50% | Camp/Menu Usable |
| `0x16E` | `516E` | Rice Omlet | 400 | `0x01` | `0x14` | 50% | Camp/Menu Usable |
| `0x170` | `5170` | Berry Juice | 200 | `0x03` | `0x05` | 40% | Camp/Menu Usable |
| `0x171` | `5171` | Seltzer | 100 | `0x05` | `0x5A` | 30% | Camp/Menu Usable |
| `0x172` | `5172` | Orange Sherbet | 16 | `0x01` | `0x0A` | 40% | Camp/Menu Usable |
| `0x173` | `5173` | Banana Crepes | 90 | `0x01` | `0x12` | 40% | Camp/Menu Usable |
| `0x174` | `5174` | Apple Cider | 5000 | `0x03` | `0x28` | 50% | Camp/Menu Usable |
| `0x175` | `5175` | Pickled Plum | 1000 | `0x01` | `0x02` | 50% | Camp/Menu Usable |
| `0x176` | `5176` | Strawberry Mousse | 120 | `0x01` | `0x0E` | 50% | Camp/Menu Usable |
| `0x177` | `5177` | Apple Crepes | 200 | `0x01` | `0x0F` | 40% | Camp/Menu Usable |
| `0x178` | `5178` | Peach Ice Cream | 150 | `0x01` | `0x0A` | 50% | Camp/Menu Usable |
| `0x179` | `5179` | Aged Berry Juice | 10000 | `0x43` | `0x3C` | 50% | Camp/Menu Usable |
| `0x17A` | `517A` | Orange Au Gratin | 170 | `0x01` | `0x15` | 50% | Camp/Menu Usable |
| `0x17B` | `517B` | Bitter Juice | 7 | `0x03` | `0x01` | 50% | Camp/Menu Usable |
| `0x17C` | `517C` | Meat Dumpling | 360 | `0x01` | `0x16` | 40% | Camp/Menu Usable |
| `0x17D` | `517D` | Potstickers | 280 | `0x01` | `0x13` | 40% | Camp/Menu Usable |
| `0x17E` | `517E` | Beef Croquettes | 420 | `0x01` | `0x1E` | 40% | Camp/Menu Usable |
| `0x17F` | `517F` | Chicken Skewers | 500 | `0x01` | `0x05` | 40% | Camp/Menu Usable |
| `0x180` | `5180` | Jambalaya | 480 | `0x01` | `0x2E` | 50% | Camp/Menu Usable |
| `0x182` | `5182` | Chicken Doria | 520 | `0x01` | `0x30` | 40% | Camp/Menu Usable |
| `0x183` | `5183` | Steak | 600 | `0x01` | `0x32` | 40% | Camp/Menu Usable |
| `0x184` | `5184` | Baby Rabbit Risotto | 600 | `0x01` | `0x23` | 50% | Camp/Menu Usable |
| `0x185` | `5185` | Ground Lamb Steak | 500 | `0x01` | `0x28` | 50% | Camp/Menu Usable |
| `0x186` | `5186` | Gelatin Steak | 350 | `0x03` | `0x3C` | 50% | Camp/Menu Usable |
| `0x187` | `5187` | Bad Tasting Stew | 3 | `0x03` | `0x01` | 25% | Camp/Menu Usable |
| `0x18A` | `518A` | Squash Croquettes | 400 | `0x01` | `0x16` | 50% | Camp/Menu Usable |
| `0x18B` | `518B` | Corn Potage | 300 | `0x03` | `0x14` | 50% | Camp/Menu Usable |
| `0x18D` | `518D` | Spring Roll | 300 | `0x01` | `0x14` | 50% | Camp/Menu Usable |
| `0x18E` | `518E` | Carrot Juice | 220 | `0x03` | `0x0D` | 50% | Camp/Menu Usable |
| `0x18F` | `518F` | Cabbage Roll | 280 | `0x01` | `0x1A` | 50% | Camp/Menu Usable |
| `0x190` | `5190` | Squash Spring Rolls | 300 | `0x01` | `0x1C` | 50% | Camp/Menu Usable |
| `0x191` | `5191` | Vegetable Juice | 200 | `0x03` | `0x1A` | 50% | Camp/Menu Usable |
| `0x192` | `5192` | Green Potage | 300 | `0x03` | `0x19` | 50% | Camp/Menu Usable |
| `0x193` | `5193` | Wilted Salad | 10 | `0x01` | `0x02` | 50% | Camp/Menu Usable |
| `0x194` | `5194` | Fried Eggs | 200 | `0x01` | `0x12` | 50% | Camp/Menu Usable |
| `0x195` | `5195` | Slime Jelly | 110 | `0x03` | `0x3C` | 50% | Camp/Menu Usable |
| `0x196` | `5196` | Fruit Smoothie | 120 | `0x03` | `0x08` | 50% | Camp/Menu Usable |
| `0x197` | `5197` | Yogurt | 200 | `0x01` | `0x05` | 50% | Camp/Menu Usable |
| `0x198` | `5198` | Egg Sandwich | 250 | `0x01` | `0x13` | 40% | Camp/Menu Usable |
| `0x199` | `5199` | Chocolate Crepes | 115 | `0x01` | `0x16` | 40% | Camp/Menu Usable |
| `0x19A` | `519A` | Bacon & Eggs | 190 | `0x01` | `0x14` | 50% | Camp/Menu Usable |
| `0x19B` | `519B` | Vanilla Ice Cream | 30 | `0x01` | `0x0A` | 40% | Camp/Menu Usable |
| `0x19C` | `519C` | Shortcake | 180 | `0x01` | `0x10` | 50% | Camp/Menu Usable |
| `0x19D` | `519D` | Custard Pudding | 103 | `0x01` | `0x0F` | 50% | Camp/Menu Usable |
| `0x19E` | `519E` | Macaroni Au Gratin | 150 | `0x01` | `0x0A` | 50% | Camp/Menu Usable |
| `0x19F` | `519F` | Spicy Cake | 10 | `0x01` | `0x01` | 50% | Camp/Menu Usable |
| `0x1A0` | `51A0` | Raw Milk | 1 | `0x03` | `0x01` | 50% | Camp/Menu Usable |
| `0x1A1` | `51A1` | Fruit Nectar | 100000 | `0x05` | `0x64` | 100% | Camp/Menu Usable |
| `0x1B9` | `51B9` | Music Box | 2150 | `0x00` | `0x00` | 100% | Camp/Menu Usable |
| `0x1D0` | `51D0` | Holoprojector | 0 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1D1` | `51D1` | Plasma Zap-stick | 0 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1D2` | `51D2` | Mech Launcher | 0 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1D3` | `51D3` | White System | 0 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1D4` | `51D4` | Black System | 0 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1D5` | `51D5` | Green System | 0 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1D8` | `51D8` | Lady Fingers | 80 | `0x05` | `0x08` | 100% | Camp/Menu Usable |
| `0x1DB` | `51DB` | Fill-up | 800 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1DF` | `51DF` | Second Ledger | 1200 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1E1` | `51E1` | Forged Medals | 1200 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1E2` | `51E2` | Lien | 1200 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1E3` | `51E3` | Contract | 1200 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x1E4` | `51E4` | Life Insurance | 1200 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x2F2` | `52F2` | Cinderella Glass | 1200 | `0x00` | `0x00` | 25% | Camp/Menu Usable |
| `0x2F6` | `52F6` | Strawberry Jam | 50 | `0x01` | `0x0A` | 25% | Camp/Menu Usable |
| `0x2F7` | `52F7` | Raspberry Jam | 60 | `0x01` | `0x0B` | 25% | Camp/Menu Usable |
| `0x2F8` | `52F8` | Apple Jam | 70 | `0x01` | `0x0C` | 25% | Camp/Menu Usable |
| `0x2F9` | `52F9` | Aloe Jam | 80 | `0x5E` | `0x00` | 25% | Camp/Menu Usable |
| `0x2FC` | `52FC` | Rice Croquettes | 120 | `0x01` | `0x0C` | 25% | Camp/Menu Usable |
| `0x2FD` | `52FD` | Soy Milk | 80 | `0x03` | `0x0A` | 25% | Camp/Menu Usable |
| `0x2FE` | `52FE` | Smelly Rice Cakes | 10 | `0x01` | `0x01` | 25% | Camp/Menu Usable |
| `0x2FF` | `52FF` | Quick Pickles | 20 | `0x01` | `0x05` | 25% | Camp/Menu Usable |
| `0x300` | `5300` | Rice-bran Pickles | 30 | `0x01` | `0x06` | 25% | Camp/Menu Usable |
| `0x301` | `5301` | Carrot Ice Cream | 40 | `0x01` | `0x0C` | 25% | Camp/Menu Usable |
| `0x306` | `5306` | Rotten Sashimi | 1 | `0x27` | `0x00` | 25% | Camp/Menu Usable |
| `0x307` | `5307` | Go-home Frog | 300001 | `0x60` | `0x00` | 25% | Camp/Menu Usable |
| `0x317` | `5317` | Milky Potage | 2000 | `0x03` | `0x50` | 100% | Camp/Menu Usable |
| `0x318` | `5318` | Special Stir-fry | 4000 | `0x04` | `0x46` | 100% | Camp/Menu Usable |
| `0x319` | `5319` | Magical Salad | 5200 | `0x03` | `0x64` | 100% | Camp/Menu Usable |
| `0x31A` | `531A` | Golden Stew | 12000 | `0x04` | `0x5A` | 100% | Camp/Menu Usable |
| `0x31B` | `531B` | Fine Saute | 9700 | `0x01` | `0x46` | 100% | Camp/Menu Usable |
| `0x31C` | `531C` | Exciting Tenderloin | 6500 | `0x02` | `0x46` | 100% | Camp/Menu Usable |
| `0x31D` | `531D` | Prime Sirloin | 24000 | `0x02` | `0x50` | 100% | Camp/Menu Usable |
| `0x31E` | `531E` | Inviting Filet | 20000 | `0x01` | `0x64` | 100% | Camp/Menu Usable |
| `0x31F` | `531F` | Tuna Skewers | 20000 | `0x04` | `0x46` | 100% | Camp/Menu Usable |
| `0x320` | `5320` | Prine Tuna Steak | 18000 | `0x01` | `0x50` | 100% | Camp/Menu Usable |
| `0x321` | `5321` | Fish of Happiness | 12000 | `0x01` | `0x46` | 100% | Camp/Menu Usable |
| `0x322` | `5322` | Special Tuna | 30000 | `0x05` | `0x46` | 100% | Camp/Menu Usable |
| `0x323` | `5323` | Ichigoni | 5000 | `0x03` | `0x5A` | 100% | Camp/Menu Usable |
| `0x324` | `5324` | Ichigoni Supreme | 15000 | `0x04` | `0x5A` | 100% | Camp/Menu Usable |
| `0x325` | `5325` | Prince's Zoni Stew | 7700 | `0x05` | `0x3C` | 100% | Camp/Menu Usable |
| `0x326` | `5326` | Sea Urchin on Rice | 26000 | `0x05` | `0x64` | 100% | Camp/Menu Usable |
| `0x327` | `5327` | Deluxe Doria | 8000 | `0x01` | `0x58` | 100% | Camp/Menu Usable |
| `0x328` | `5328` | Miracle Fried Rice | 7200 | `0x01` | `0x4B` | 100% | Camp/Menu Usable |
| `0x329` | `5329` | Risotto Ecstasy | 20000 | `0x05` | `0x50` | 100% | Camp/Menu Usable |
| `0x32A` | `532A` | Heavenly Doria | 30000 | `0x05` | `0x64` | 100% | Camp/Menu Usable |
| `0x32B` | `532B` | Au Gratin Climax | 10000 | `0x01` | `0x44` | 100% | Camp/Menu Usable |
| `0x32C` | `532C` | Cheese Pizza | 4000 | `0x01` | `0x44` | 100% | Camp/Menu Usable |
| `0x32D` | `532D` | Assorted Cheeses | 8000 | `0x01` | `0x46` | 100% | Camp/Menu Usable |
| `0x32E` | `532E` | Gorgonzola | 19000 | `0x01` | `0x4E` | 100% | Camp/Menu Usable |
| `0x32F` | `532F` | Gateau Marjolaine | 5000 | `0x01` | `0x64` | 100% | Camp/Menu Usable |
| `0x330` | `5330` | 1-up Pudding | 30000 | `0x06` | `0x64` | 100% | Camp/Menu Usable |
| `0x331` | `5331` | Beautiful Ice Cream | 28000 | `0x05` | `0x50` | 100% | Camp/Menu Usable |
| `0x332` | `5332` | Ginger Ale | 80000 | `0x05` | `0x64` | 100% | Camp/Menu Usable |
| `0x333` | `5333` | Genie's Veggie Soup | 40000 | `0x04` | `0x5A` | 100% | Camp/Menu Usable |
| `0x334` | `5334` | Genie's Steak | 50000 | `0x02` | `0x5A` | 100% | Camp/Menu Usable |
| `0x335` | `5335` | Energy Drink | 30000 | `0x43` | `0x64` | 100% | Camp/Menu Usable |

---

## 14. Crafting Materials, Ingredients & Story Items Catalog (Category 0, Usable 0, 91 items)

| ID | Code | Name | Price | Sub-Type ID | Sell Rate | Item Classification |
|---|---|---|---|---|---|---|
| `0x001` | `5001` | Magic Canvas | 1000 | `0x00` | 25% | Material / Key Item |
| `0x012` | `5012` | Scribbles | 3 | `0x00` | 25% | Material / Key Item |
| `0x01E` | `501E` | Weird Lump | 5 | `0x00` | 25% | Material / Key Item |
| `0x02B` | `502B` | Magical Clay | 600 | `0x00` | 25% | Material / Key Item |
| `0x02C` | `502C` | Feather Pen | 20 | `0x00` | 25% | Material / Key Item |
| `0x02D` | `502D` | Piano | 30000 | `0x00` | 5% | Material / Key Item |
| `0x02E` | `502E` | Cembalo | 8000 | `0x00` | 5% | Material / Key Item |
| `0x02F` | `502F` | Illusive Shamisen | 550000 | `0x00` | 100% | Material / Key Item |
| `0x030` | `5030` | Silver Trumpet | 30000000 | `0x00` | 100% | Material / Key Item |
| `0x031` | `5031` | Harmonica | 500 | `0x00` | 15% | Material / Key Item |
| `0x032` | `5032` | Lyre | 5000 | `0x00` | 20% | Material / Key Item |
| `0x033` | `5033` | Violin | 21000 | `0x00` | 10% | Material / Key Item |
| `0x034` | `5034` | Organ | 12000 | `0x00` | 10% | Material / Key Item |
| `0x035` | `5035` | Conductor's Baton | 85 | `0x00` | 25% | Material / Key Item |
| `0x0A3` | `50A3` | Crumpled Paper | 1 | `0x00` | 100% | Material / Key Item |
| `0x0A4` | `50A4` | Fountain Pen | 460 | `0x00` | 25% | Material / Key Item |
| `0x0BC` | `50BC` | Fanzine ? | 200 | `0x00` | 25% | Material / Key Item |
| `0x0BD` | `50BD` | Fanzine ... | 573 | `0x00` | 25% | Material / Key Item |
| `0x0BE` | `50BE` | Fanzine | 800 | `0x00` | 25% | Material / Key Item |
| `0x0BF` | `50BF` | Fanzine (music note) | 3000 | `0x00` | 25% | Material / Key Item |
| `0x0C0` | `50C0` | Fanzine ! | 10000 | `0x00` | 25% | Material / Key Item |
| `0x0C1` | `50C1` | Fanzine (heart) | 50000 | `0x00` | 25% | Material / Key Item |
| `0x0C2` | `50C2` | Fanzine (male symbol) | 10000 | `0x00` | 25% | Material / Key Item |
| `0x0C3` | `50C3` | Fanzine (female symbol) | 10000 | `0x00` | 25% | Material / Key Item |
| `0x0F9` | `50F9` | Mint Pot | 0 | `0x00` | 25% | Material / Key Item |
| `0x112` | `5112` | Blanking Mist | 3000 | `0x00` | 25% | Material / Key Item |
| `0x117` | `5117` | Seafood | 500 | `0x00` | 25% | Material / Key Item |
| `0x118` | `5118` | Fruit | 80 | `0x00` | 25% | Material / Key Item |
| `0x119` | `5119` | Grain | 145 | `0x00` | 25% | Material / Key Item |
| `0x11A` | `511A` | Meat | 300 | `0x00` | 25% | Material / Key Item |
| `0x11B` | `511B` | Vegetables | 30 | `0x00` | 25% | Material / Key Item |
| `0x11C` | `511C` | Egg/Dairy Products | 10 | `0x00` | 25% | Material / Key Item |
| `0x11E` | `511E` | ?MACHINE | 0 | `0x00` | 50% | Material / Key Item |
| `0x120` | `5120` | ?MACHINE | 0 | `0x00` | 25% | Material / Key Item |
| `0x121` | `5121` | Cracked Gem | 0 | `0x00` | 25% | Material / Key Item |
| `0x128` | `5128` | ?MACHINE | 0 | `0x00` | 25% | Material / Key Item |
| `0x12C` | `512C` | ?MACHINE | 0 | `0x00` | 25% | Material / Key Item |
| `0x12D` | `512D` | ?MACHINE | 0 | `0x00` | 25% | Material / Key Item |
| `0x130` | `5130` | ?MACHINE | 0 | `0x00` | 25% | Material / Key Item |
| `0x131` | `5131` | ?MACHINE | 0 | `0x00` | 25% | Material / Key Item |
| `0x13A` | `513A` | ?JEWELRY | 0 | `0x00` | 25% | Material / Key Item |
| `0x13D` | `513D` | Red Lotus Gem | 0 | `0x00` | 25% | Material / Key Item |
| `0x144` | `5144` | Lezard Flask | 120000 | `0x00` | 25% | Material / Key Item |
| `0x14A` | `514A` | Missing Number | 0 | `0x00` | 25% | Material / Key Item |
| `0x14B` | `514B` | Missing Number | 0 | `0x00` | 25% | Material / Key Item |
| `0x14D` | `514D` | Missing Number | 0 | `0x00` | 25% | Material / Key Item |
| `0x150` | `5150` | Missing Number | 0 | `0x00` | 25% | Material / Key Item |
| `0x152` | `5152` | Missing Number | 0 | `0x00` | 25% | Material / Key Item |
| `0x1A2` | `51A2` | Pet Food | 10 | `0x01` | 25% | Material / Key Item |
| `0x1AC` | `51AC` | Rock | 10 | `0x00` | 25% | Material / Key Item |
| `0x1B6` | `51B6` | Blurry Photo | 20 | `0x00` | 25% | Material / Key Item |
| `0x1B7` | `51B7` | Magical Camera | 9800 | `0x00` | 25% | Material / Key Item |
| `0x1B8` | `51B8` | Magic Film | 900 | `0x00` | 25% | Material / Key Item |
| `0x1BA` | `51BA` | Element Analyzer | 12000 | `0x00` | 100% | Material / Key Item |
| `0x1BB` | `51BB` | Graphic Software | 6500 | `0x00` | 100% | Material / Key Item |
| `0x1BD` | `51BD` | Rirca | 5800 | `0x00` | 100% | Material / Key Item |
| `0x1C6` | `51C6` | Soul Trap | 0 | `0x00` | 80% | Material / Key Item |
| `0x1C8` | `51C8` | Material Kit | 1200 | `0x00` | 80% | Material / Key Item |
| `0x1C9` | `51C9` | Musical Software | 8000 | `0x00` | 50% | Material / Key Item |
| `0x1CA` | `51CA` | Erlenmeyer Flask | 12200 | `0x00` | 100% | Material / Key Item |
| `0x1CB` | `51CB` | Magical Rasp | 350000 | `0x00` | 25% | Material / Key Item |
| `0x1CC` | `51CC` | Soldering Iron | 1800 | `0x00` | 100% | Material / Key Item |
| `0x1CD` | `51CD` | Survival Kit | 6000 | `0x00` | 100% | Material / Key Item |
| `0x1CE` | `51CE` | Text Software | 4000 | `0x00` | 100% | Material / Key Item |
| `0x1CF` | `51CF` | Antiseptic Gloves | 5000 | `0x00` | 100% | Material / Key Item |
| `0x1D6` | `51D6` | Smith's Hammer | 250 | `0x00` | 25% | Material / Key Item |
| `0x1D9` | `51D9` | Vallum Paper | 150 | `0x00` | 25% | Material / Key Item |
| `0x1DA` | `51DA` | Bounced Check | 1000 | `0x00` | 25% | Material / Key Item |
| `0x1DC` | `51DC` | Forged Bills | 5000 | `0x00` | 100% | Material / Key Item |
| `0x1DD` | `51DD` | Forged Checks | 20000 | `0x00` | 100% | Material / Key Item |
| `0x1DE` | `51DE` | Forged Documents | 50000 | `0x00` | 100% | Material / Key Item |
| `0x1E0` | `51E0` | Stock Certificates | 10000 | `0x00` | 100% | Material / Key Item |
| `0x244` | `5244` | Scrap Iron | 5 | `0x00` | 100% | Material / Key Item |
| `0x2FA` | `52FA` | Missing Number | 0 | `0x00` | 25% | Material / Key Item |
| `0x308` | `5308` | ?HERB | 0 | `0x00` | 0% | Material / Key Item |
| `0x309` | `5309` | ?HERB | 0 | `0x00` | 0% | Material / Key Item |
| `0x30A` | `530A` | ?HERB | 0 | `0x00` | 0% | Material / Key Item |
| `0x30B` | `530B` | ?HERB | 0 | `0x00` | 0% | Material / Key Item |
| `0x30C` | `530C` | ?HERB | 0 | `0x00` | 0% | Material / Key Item |
| `0x30D` | `530D` | ?HERB | 0 | `0x00` | 0% | Material / Key Item |
| `0x30E` | `530E` | Purity Leaf | 1500 | `0x00` | 50% | Material / Key Item |
| `0x30F` | `530F` | Juicy Beef | 3000 | `0x00` | 50% | Material / Key Item |
| `0x310` | `5310` | Prime Tuna | 4000 | `0x00` | 50% | Material / Key Item |
| `0x311` | `5311` | Ganze Sea Urchin | 3200 | `0x00` | 50% | Material / Key Item |
| `0x312` | `5312` | Magical Rice | 900 | `0x00` | 50% | Material / Key Item |
| `0x313` | `5313` | Creamy Cheese | 300 | `0x00` | 50% | Material / Key Item |
| `0x314` | `5314` | Sweet Fruit | 250 | `0x00` | 50% | Material / Key Item |
| `0x315` | `5315` | Slippery Slime | 10 | `0x00` | 10% | Material / Key Item |
| `0x316` | `5316` | Jiggly Slime | 10 | `0x00` | 10% | Material / Key Item |
| `0x336` | `5336` | Yarma Cooking Set | 1000 | `0x00` | 100% | Material / Key Item |
| `0x337` | `5337` | ? (japanese characters) | 100 | `0x00` | 0% | Material / Key Item |

---

## 15. Verification Summary

| Category | Category ID | Usable Type | Active Items | In-Game Verified Status |
|---|---|---|---|---|
| Weapons | `0x01` | `0` | 177 | ✅ 100% verified (Atk, Price, Equip Mask) |
| Body Armor | `0x08` | `0` | 35 | ✅ 100% verified (Def, Price, Equip Mask) |
| Shields | `0x09` | `0` | 19 | ✅ 100% verified (Def, Avd, Price, Equip Mask) |
| Helmets | `0x0A` | `0` | 25 | ✅ 100% verified (Def, Price, Equip Mask) |
| Boots / Greaves | `0x0B` | `0` | 27 | ✅ 100% verified (Def, Agl, Price, Equip Mask) |
| Accessories & Minerals | `0x0C` | `0` | 131 | ✅ 100% verified (Stats, Price, Equip Mask) |
| Medicine, Herbs & Potions | `0x00` | `3` | 37 | ✅ 100% verified (Recovery %, Price, Effect ID) |
| Battle Usable Items | `0x00` | `1` | 56 | ✅ 100% verified (Price, Effect ID) |
| Food, Cooking & Artwork | `0x00` | `2` | 225 | ✅ 100% verified (Price, Sub-ID) |
| Crafting Materials & Story | `0x00` | `0` | 91 | ✅ 100% verified (Price, Material ID) |
| **Total Active Items** | - | - | **823** | ✅ **100% Complete Game Coverage** |
| Allocation Capacity | - | - | 1,023 | 200 unused zero-padding slots (IDs 824..1023) |
