# Star Ocean 2 (PS1): Master Item Architecture & Database Reference

**Date**: 2026-09-28  
**Status**: ✅ **VERIFIED (Binary Extraction & Disassembly-Verified)**  
**Scope**: Complete PS1 US Disc 1 and Disc 2 Item & Equipment Engine (Disc Archive Entry 2, 48-byte records, 823 active items, 1,023 slot capacity).  
**Artifact**: [artifacts/so2-items/items_database.json](file:///C:/CodeTesting/SaveConverter/artifacts/so2-items/items_database.json) (1.09 MB, 39,694 lines)  
**Detailed Catalog**: [docs/SO2-ITEM-DATABASE.md](file:///C:/CodeTesting/SaveConverter/docs/SO2-ITEM-DATABASE.md)  
**Equip Restrictions**: [docs/SO2-ITEM-RESTRICTIONS.md](file:///C:/CodeTesting/SaveConverter/docs/SO2-ITEM-RESTRICTIONS.md)  

---

## 1. Executive Summary & Binary Locations

In *Star Ocean: The Second Story* (PS1), every weapon, armor piece, accessory, food item, crafting mineral, and story key item is defined within a single, contiguous fixed-width struct array indexed by 1-based Item ID.

| Binary Location | Property / Dimension | Value | Notes |
|---|---|---|---|
| **Disc 1 / Disc 2** | Archive Entry ID | `2` | Identical binary payload across both discs |
| **Disc LBA** | Sector Position | LBA 375 | Compressed size: 10,240 bytes (5 sectors) |
| **Compression** | Algorithm | SLZ2 (`53 4C 5A 02`) | Standard tri-Ace LZSS + Huffman variant |
| **Decompressed Payload** | Raw Byte Size | `49,104` bytes (`0xBFD0`) | $1,023 \times 48$ bytes |
| **Record Geometry** | Stride | `48` bytes (`0x30`) | Fixed-width struct per item |
| **Item ID Range** | Valid Indices | `1`..`823` (`0x001`..`0x337`) | Index 0 = Empty/None; 824..1023 = Zero-padded capacity |
| **CodeBreaker Mapping** | Action Replay / CB | `0x5000 + Item_ID` | e.g. Magic Canvas = `5001`, Farwell = `516A` (`0x16A` = 362) |
| **Live RAM Pointer** | Inventory Offset | `[80075278] + 0x820` | Points directly to decompressed 48-byte master array |
| **Accessor MIPS Routine** | Universal Getter | `0x8003C538` | `($a0 = inv_ptr, $a1 = item_id, $a2 = field_offset)` |

---

## 2. Master 48-Byte Record Struct Layout

Resident MIPS function `8003C538` calculates byte offsets using:
$$\text{Record Address} = \text{Base} + (\text{Item\_ID} - 1) \times 48$$

```mips
8003c538: bnez     $a1, 0x8003c548
8003c53c: addiu    $a1, $a1, -1          ; index = item_id - 1
8003c548: sll      $v0, $a1, 1           ; v0 = index * 2
8003c54c: addu     $v0, $v0, $a1         ; v0 = index * 3
8003c550: lw       $v1, 0x820($a0)       ; v1 = live master table base pointer
8003c554: sll      $v0, $v0, 4           ; v0 = index * 3 * 16 = index * 48 (0x30)
```

### Struct Memory Map (`sizeof = 0x30`)

| Offset | Width | Type | Field Name | Description |
|---|---|---|---|---|
| `+0x00` | 4 bytes | `uint32_t` | **Buy Price** | Base purchase price in Fol. Sell price is `(Buy Price * Sell_Rate) / 100`. |
| `+0x04` | 2 bytes | `uint16_t` | **Equip Mask** | 12-bit character eligibility mask: `1 << char_id`. |
| `+0x06` | 2 bytes | `int16_t` | **Secondary Stat** | Secondary parameter or internal weapon tier ID. |
| `+0x08` | 2 bytes | `int16_t` | **ATK** | Attack power bonus (applied directly to character base ATK). |
| `+0x0A` | 2 bytes | `int16_t` | **Reserved** | Always `0x0000`. |
| `+0x0C` | 2 bytes | `int16_t` | **HIT / CRT** | Hit rate or critical rate modifier. |
| `+0x0E` | 2 bytes | `int16_t` | **AVD** | Evade / avoidance stat modifier (e.g. Star Guard gives +121 AVD). |
| `+0x10` | 2 bytes | `int16_t` | **DEF** | Defense bonus (armor, shields, helmets, boots, accessories). |
| `+0x12` | 2 bytes | `int16_t` | **MAG / LUC** | Magic intelligence or luck modifier. |
| `+0x14` | 2 bytes | `int16_t` | **STR / AGL** | Strength or movement agility modifier (e.g. Bunny Shoes gives +80 AGL). |
| `+0x16` | 2 bytes | `int16_t` | **GUTS / STM** | Guts or stamina parameter modifier. |
| `+0x18` | 1 byte | `uint8_t` | **Behavior Flags** | Combat animation and behavioral flags. |
| `+0x19` | 1 byte | `uint8_t` | **Recovery / Slot** | Consumables: recovery % (e.g. 22 for Blackberry). Equipment: slot code. |
| `+0x1A` | 1 byte | `uint8_t` | **Proc Trigger Rate** | Special weapon/gear trigger probability percentage. |
| `+0x1B` | 1 byte | `uint8_t` | **Weapon Element** | Trail effect / elemental property (`0x0A`=Fire, `0x1E`=Water, `0x0D`=Wind, etc.). |
| `+0x1C..+0x25` | 10 bytes | `uint8_t[10]` | **Elemental Resists** | 10 elemental multipliers: 0=Neutral, 1=Weak, 2=Half, 3=Immune, 4=Absorb. |
| `+0x26` | 2 bytes | `uint16_t` | **Status Mask** | Status immunity / infliction bitmask. |
| `+0x28` | 1 byte | `uint8_t` | **Sub-Type / Effect** | Item model ID, cooking recipe ID, or consumable dispatch routine ID. |
| `+0x29` | 1 byte | `uint8_t` | **Usage Context** | 0=Passive/Key item, 1=Battle only, 2=Camp/Menu only, 3=Field & Battle. |
| `+0x2A` | 1 byte | `uint8_t` | **Major Category** | 0=Consumable/Item, 1=Weapon, 8=Armor, 9=Shield, 10=Helm, 11=Boots, 12=Accessory. |
| `+0x2B` | 1 byte | `uint8_t` | **Resale Tier** | Rarity and shop tier classification. |
| `+0x2C` | 1 byte | `uint8_t` | **Proc Effect ID** | Combat special proc (e.g. `0x28` for Eternal Sphere star projectile spray). |
| `+0x2D` | 1 byte | `uint8_t` | **Sell Rate %** | Resale multiplier percentage (e.g. 25%, 50%, 100%). |
| `+0x2E..+0x2F`| 2 bytes | `uint16_t` | **Padding** | Always `0x0000` to align struct to 48 bytes. |

---

## 3. Character Equip Mask Bit Assignments (`+0x04`)

Character eligibility is determined by bitwise-AND with `(1 << char_id)`:

| Char ID | Character Name | Bitmask Value | Canonical Groups |
|---|---|---|---|
| `0` | Claude C. Kenni | `0x0001` | Male, Fighter |
| `1` | Rena Lanford | `0x0002` | Female, Magician |
| `2` | Celine Jules | `0x0004` | Female, Magician |
| `3` | Bowman Jeane | `0x0008` | Male, Fighter |
| `4` | Dias Flac | `0x0010` | Male, Fighter |
| `5` | Precis F. Neumann | `0x0020` | Female, Fighter |
| `6` | Ashton Anchors | `0x0040` | Male, Fighter |
| `7` | Leon D. Geeste | `0x0080` | Male, Magician |
| `8` | Opera Vectra | `0x0100` | Female, Fighter |
| `9` | Ernest Ravine | `0x0200` | Male, Fighter |
| `10` | Noel Chandler | `0x0400` | Male, Fighter (Armor) / Magician (Spells) |
| `11` | Chisato Madison | `0x0800` | Female, Fighter |

---

## 4. Master Item Category Breakdown

The 823 active items are distributed across 10 distinct combat and gameplay categories:

```
Category 1: Weapons (177)
Category 8: Body Armor (35)
Category 9: Shields (19)
Category 10: Helmets (25)
Category 11: Boots / Greaves (27)
Category 12: Accessories & Minerals (131)
Category 0 / Usable 3: Medicine, Herbs & Potions (37)
Category 0 / Usable 1: Battle Only Usable (56)
Category 0 / Usable 2: Food, Cooking & Artwork (225)
Category 0 / Usable 0: Crafting Materials & Story Items (91)
Total Active Items: 823
Allocation Capacity: 1,023 (200 empty slots: 824..1023)
```

### Item Breakdown Table

| Major Category | Category ID (`+0x2A`) | Usage Context (`+0x29`) | Count | Key Examples |
|---|---|---|---|---|
| **Weapons** | `0x01` | `0` | **177** | Eternal Sphere (`0x168`), Sacred Tear (`0x165`), Farwell (`0x16A`), Melufa (`0x190`) |
| **Body Armor** | `0x08` | `0` | **35** | Seraphic Garb (`0x18B`), Battle Suit (`0x18C`), Bloody Armor (`0x187`), Reflect Plate (`0x188`) |
| **Shields** | `0x09` | `0` | **19** | Star Guard (`0x1A1`), Algol (`0x1A3`), Shield of the Rune (`0x19F`), Pallas Athena (`0x1A4`) |
| **Helmets** | `0x0A` | `0` | **25** | Dueling Helmet (`0x1B8`), Sylvan Helmet (`0x1BA`), Isis Tiara (`0x1B6`), Mithril Helm (`0x1B5`) |
| **Boots / Greaves** | `0x0B` | `0` | **27** | Bunny Shoes (`0x1D2`), Valkyrie Boots (`0x1D3`), Santa's Boots (`0x1D1`), Sylvan Boots (`0x1CF`) |
| **Accessories** | `0x0C` | `0` | **131** | Ring of Might (`0x1EB`), Berserk Ring (`0x1ED`), Tri-Emblem (`0x205`), Archangel's Feather (`0x217`) |
| **Medicine / Herbs** | `0x00` | `3` | **37** | Blackberry (`0x0A0`), Blueberry (`0x09F`), Resurrection Bottle (`0x0AF`), Cure Poison (`0x0A2`) |
| **Battle Usable** | `0x00` | `1` | **56** | Hexagram Card (`0x01C`), Extension Card (`0x018`), Mind Bomb (`0x074`), Megabomb (`0x076`) |
| **Food & Artwork** | `0x00` | `2` | **225** | Spring (`0x002`), The Scream (`0x003`), Gourmet Steak (`0x0F0`), Shortcake (`0x10B`) |
| **Materials & Story** | `0x00` | `0` | **91** | Magic Canvas (`0x001`), Mithril (`0x044`), Orichalcum (`0x049`), Ancient Book (`0x060`) |
| **Total** | - | - | **823** | Complete Disc 1 & Disc 2 Coverage |

---

## 5. Toolchain Integration

- **Exporter**: [`tools/export_item_database_json.py`](file:///C:/CodeTesting/SaveConverter/tools/export_item_database_json.py)
- **Database Builder**: [`tools/build_item_database.py`](file:///C:/CodeTesting/SaveConverter/tools/build_item_database.py)
- **JSON Target**: [`artifacts/so2-items/items_database.json`](file:///C:/CodeTesting/SaveConverter/artifacts/so2-items/items_database.json)
- **Documentation**: [`docs/SO2-ITEM-DATABASE.md`](file:///C:/CodeTesting/SaveConverter/docs/SO2-ITEM-DATABASE.md)
