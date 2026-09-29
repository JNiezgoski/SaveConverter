# Star Ocean: The Second Story (PS1) - Master Enemy & Monster Database

**Technical Reference & Bestiary Specification**  
*Total Documented Species: 184 | Struct Width: 92 Bytes | Source: Disc 1 & Disc 2*

---

## 1. Executive Summary & Binary Struct Architecture

In *Star Ocean: The Second Story*, all enemy combatant entities, dungeon monsters, and boss encounters
are defined using a **fixed 92-byte binary struct** embedded directly within combat encounter archives
(`Archives 1405..1968`). Each encounter archive begins with a header pointing to an embedded SLZ sub-archive
containing combat billboard sprites and animation sequences (`Word[0] = slz_offset`).

### 92-Byte (`0x5C`) Binary Memory Layout

| Offset | Width | Type | Field Name | Description |
| :--- | :---: | :--- | :--- | :--- |
| `+0x00..+0x0F` | 16 B | `char[16]` | **Entity Name** | Null-terminated ASCII enemy identifier string. |
| `+0x10..+0x13` | 4 B | `uint32_t` LE | **HP** | Maximum hit points (10 to 10,000,000). |
| `+0x14..+0x17` | 4 B | `uint32_t` LE | **MP** | Maximum magic points. |
| `+0x18..+0x1B` | 4 B | `uint32_t` LE | **EXP** | Base experience points awarded on defeat. |
| `+0x1C..+0x1F` | 4 B | `uint32_t` LE | **FOL** | Base money bounty awarded on defeat. |
| `+0x20..+0x25` | 6 B | `int16_t[3]` LE | **Bounding Box** | 3D collision dimensions (Width, Height, Depth). |
| `+0x26..+0x27` | 2 B | `int16_t` LE | **AGL / Speed** | Combat movement rate and approach agility. |
| `+0x28..+0x2B` | 4 B | `int16_t[2]` LE | **Model / Texture Link** | 3D mesh index and shadow descriptor offset. |
| `+0x2C..+0x2D` | 2 B | `uint16_t` LE | **ATK** | Base physical attack power. |
| `+0x2E..+0x2F` | 2 B | `uint16_t` LE | **INT** | Magic attack and spell defense scaling. |
| `+0x30..+0x31` | 2 B | `uint16_t` LE | **Drop Item ID** | Primary item ID (maps to `items_database.json`). |
| `+0x32..+0x33` | 2 B | `uint16_t` LE | **Drop Rate** | Probability percentage for primary drop (0..100%). |
| `+0x34..+0x35` | 2 B | `uint16_t` LE | **Level** | Monster level (used in combat damage scaling). |
| `+0x36..+0x37` | 2 B | `uint16_t` LE | **DEF** | Base physical defense threshold. |
| `+0x38..+0x39` | 2 B | `uint16_t` LE | **GUTS / STM** | Stamina / stun resistance recovery meter. |
| `+0x3A..+0x41` | 8 B | `uint8_t[8]` | **Elemental Affinities** | Resistance levels for Fire, Water, Wind, Earth, Thunder, Star, Light, Dark. |
| `+0x42..+0x45` | 4 B | `uint32_t` LE | **Status Mask** | Status ailment immunity flags (Petrify, Paralyze, Silence, Poison). |
| `+0x46..+0x5B` | 22 B | `uint8_t[22]` | **Mesh & Sprite Link** | 3D billboard scale, pivot offsets, and animation descriptor links. |

---

## 2. Complete Bestiary Catalog

Below is the complete database of all 184 unique enemy species, ordered from highest to lowest HP.

| Enemy Name | Level | HP | MP | EXP | FOL | ATK | DEF | INT | GUTS | Item Drop (Rate) | Archive |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Iselia-queen** | 500 | 3,300,000 | 20,000 | 4,000,000 | 50,000 | 5800 | 1000 | 1500 | 220 | Item #10000 (24%) | Arc 1966 (D1) |
| **Indalecio** | 240 | 1,500,000 | 16,000 | 4,900,000 | 60,000 | 3400 | 900 | 1500 | 180 | Item #5000 (160%) | Arc 1945 (D1) |
| **G-Celesta** | 255 | 1,000,000 | 20,000 | 2,200,000 | 80,000 | 5000 | 880 | 1500 | 150 | Item #14000 (24%) | Arc 1920 (D1) |
| **Weirdbeast** | 99 | 811,200 | 0 | 165,252 | 52,000 | 2600 | 820 | 10000 | 50 | None | Arc 1912 (D1) |
| **Wisesorcerer** | 300 | 700,000 | 30,000 | 1,000,000 | 300,000 | 5500 | 900 | 1500 | 180 | Item #16000 (64%) | Arc 1965 (D1) |
| **M-eater** | 170 | 600,000 | 400 | 242,000 | 60,000 | 8500 | 900 | 850 | 100 | None | Arc 1914 (D1) |
| **Rock-demon** | 250 | 550,000 | 500 | 950,000 | 50,000 | 8500 | 900 | 1550 | 600 | None | Arc 1869 (D1) |
| **Hell-servant** | 280 | 450,000 | 600 | 600,000 | 100,000 | 4000 | 920 | 1550 | 160 | Prine Tuna Steak (120%) | Arc 1766 (D1) |
| **E-beast** | 180 | 450,000 | 100 | 300,000 | 42,000 | 3000 | 850 | 400 | 80 | None | Arc 1915 (D1) |
| **Geo-guardian** | 200 | 400,000 | 100 | 300,000 | 100,000 | 4500 | 900 | 1100 | 600 | None | Arc 1917 (D1) |
| **Phoenix** | 220 | 350,000 | 6,300 | 1,000,000 | 500,000 | 3250 | 830 | 50 | 60 | Item #10000 (120%) | Arc 1919 (D1) |
| **Owlbear** | 200 | 300,000 | 100 | 800,000 | 100,000 | 4000 | 900 | 1600 | 600 | None | Arc 1862 (D1) |
| **Cyril** | 140 | 300,000 | 5,900 | 460,000 | 80,000 | 2300 | 460 | 600 | 300 | Thunder Punch (Hand) (200%) | Arc 1405 (D1) |
| **Miel32** | 140 | 190,000 | 150 | 400,000 | 50,000 | 3500 | 560 | 300 | 80 | None | Arc 1911 (D1) |
| **Vesper** | 120 | 180,000 | 300 | 125,000 | 45,000 | 1650 | 440 | 400 | 150 | Core Plate (Armor) (20%) | Arc 1942 (D1) |
| **Decus** | 120 | 180,000 | 300 | 125,000 | 45,000 | 1650 | 440 | 400 | 150 | Core Plate (Armor) (20%) | Arc 1942 (D1) |
| **Berle** | 77 | 170,000 | 100 | 99,000 | 58,000 | 1800 | 420 | 550 | 300 | None | Arc 1940 (D1) |
| **Weirdknight** | 110 | 160,000 | 500 | 350,000 | 20,000 | 2500 | 460 | 50 | 100 | Item #1500 (16%) | Arc 1908 (D1) |
| **D-feather** | 110 | 160,000 | 500 | 350,000 | 20,000 | 2500 | 460 | 50 | 100 | Item #1500 (16%) | Arc 1908 (D1) |
| **Shigeo** | 75 | 160,000 | 100 | 83,000 | 54,000 | 1600 | 420 | 550 | 50 | None | Arc 1938 (D1) |
| **Bark** | 80 | 150,000 | 400 | 59,800 | 55,000 | 4000 | 250 | 650 | 300 | None | Arc 1936 (D1) |
| **Marsilio** | 70 | 150,000 | 100 | 72,000 | 50,000 | 1800 | 400 | 600 | 100 | None | Arc 1935 (D1) |
| **Guardian** | 70 | 130,000 | 0 | 150,000 | 64,000 | 1500 | 400 | 650 | 150 | None | Arc 1930 (D1) |
| **Weirdavia** | 96 | 100,000 | 300 | 160,000 | 30,000 | 1420 | 550 | 350 | 120 | None | Arc 1591 (D1) |
| **Nicolus** | 77 | 85,200 | 180 | 25,000 | 36,000 | 1300 | 290 | 50 | 0 | None | Arc 1941 (D1) |
| **Jibril** | 77 | 85,200 | 180 | 25,000 | 36,000 | 1300 | 290 | 50 | 0 | None | Arc 1941 (D1) |
| **Orbiterbeast** | 165 | 84,000 | 0 | 120,000 | 6,000 | 2660 | 650 | 160 | 50 | None | Arc 1760 (D1) |
| **Gelatinblock** | 70 | 80,000 | 0 | 65,000 | 6,000 | 1600 | 420 | 900 | 0 | None | Arc 1968 (D1) |
| **Dreamshade** | 15 | 66,500 | 0 | 120,000 | 2,000 | 2420 | 740 | 45 | 10 | None | Arc 1861 (D1) |
| **Mindflayer** | 15 | 66,500 | 0 | 120,000 | 2,000 | 2420 | 740 | 45 | 10 | None | Arc 1860 (D1) |
| **Weird-mage** | 200 | 60,000 | 3,500 | 180,000 | 10 | 3100 | 890 | 850 | 100 | None | Arc 1864 (D1) |
| **Hellmaster** | 200 | 60,000 | 3,500 | 180,000 | 10 | 3100 | 890 | 850 | 100 | None | Arc 1864 (D1) |
| **Huntinggel** | 120 | 60,000 | 0 | 25,000 | 20,000 | 2300 | 480 | 10 | 100 | None | Arc 1909 (D1) |
| **Bloodgerell** | 120 | 60,000 | 0 | 25,000 | 20,000 | 2300 | 480 | 10 | 100 | None | Arc 1752 (D1) |
| **Breakwing** | 75 | 60,000 | 0 | 40,000 | 34,000 | 1100 | 320 | 0 | 100 | None | Arc 1933 (D1) |
| **Lover** | 75 | 60,000 | 0 | 40,000 | 34,000 | 1100 | 320 | 0 | 100 | None | Arc 1933 (D1) |
| **Miel128** | 190 | 59,000 | 0 | 70,000 | 6,000 | 3400 | 800 | 45 | 50 | None | Arc 1764 (D1) |
| **Snowman** | 86 | 58,700 | 0 | 5,200 | 32,800 | 1720 | 450 | 50 | 150 | None | Arc 1948 (D1) |
| **Soulmaster** | 250 | 50,000 | 1,900 | 200,000 | 10 | 4000 | 750 | 2 | 100 | Heart Breaker (Sword) (128%) | Arc 1868 (D1) |
| **Liveflayer** | 195 | 48,500 | 0 | 67,000 | 4,000 | 3200 | 770 | 85 | 0 | None | Arc 1853 (D1) |
| **Clubgunner** | 190 | 48,500 | 250 | 67,000 | 4,834 | 2900 | 800 | 85 | 50 | None | Arc 1765 (D1) |
| **Ruprecht** | 68 | 45,500 | 150 | 19,000 | 22,000 | 900 | 10 | 700 | 0 | None | Arc 1941 (D1) |
| **Synard** | 70 | 43,000 | 200 | 80,000 | 20,000 | 800 | 300 | 100 | 0 | None | Arc 1926 (D1) |
| **F-thiefL99** | 160 | 40,000 | 0 | 200,000 | 20,000 | 2600 | 690 | 10 | 50 | None | Arc 1757 (D1) |
| **Lastavenger** | 160 | 40,000 | 0 | 200,000 | 20,000 | 2600 | 690 | 10 | 50 | None | Arc 1828 (D1) |
| **Robinfake** | 160 | 40,000 | 0 | 200,000 | 20,000 | 2600 | 690 | 10 | 50 | None | Arc 1822 (D1) |
| **Evilwater** | 63 | 40,000 | 0 | 6,600 | 50 | 1500 | 424 | 5 | 50 | None | Arc 1572 (D1) |
| **Arcmene** | 55 | 40,000 | 0 | 39,000 | 26,000 | 1080 | 299 | 80 | 20 | None | Arc 1927 (D1) |
| **Ghastricgel** | 200 | 39,000 | 100 | 105,000 | 4,260 | 3112 | 850 | 150 | 50 | None | Arc 1858 (D1) |
| **Meduslizzard** | 78 | 38,000 | 0 | 74,000 | 4,600 | 1450 | 430 | 460 | 50 | None | Arc 1593 (D1) |
| **Punkponk** | 130 | 37,000 | 0 | 31,000 | 4,000 | 2150 | 400 | 10 | 500 | None | Arc 1753 (D1) |
| **Harfainx** | 40 | 36,700 | 100 | 20,000 | 5,000 | 600 | 200 | 50 | 20 | None | Arc 1615 (D1) |
| **Robinmaster** | 180 | 36,200 | 0 | 60,200 | 3,200 | 2815 | 720 | 50 | 150 | None | Arc 1847 (D1) |
| **Brigandogre** | 180 | 36,200 | 0 | 60,200 | 3,200 | 2815 | 720 | 50 | 150 | None | Arc 1847 (D1) |
| **Killergigant** | 170 | 35,000 | 0 | 52,000 | 4,200 | 2820 | 700 | 50 | 150 | None | Arc 1838 (D1) |
| **FunnyThief** | 130 | 35,000 | 0 | 60,000 | 30,000 | 2305 | 500 | 5 | 140 | None | Arc 1913 (D1) |
| **Foriger** | 130 | 35,000 | 0 | 60,000 | 30,000 | 2305 | 500 | 5 | 140 | None | Arc 1879 (D1) |
| **MetalFunny** | 130 | 35,000 | 0 | 60,000 | 30,000 | 2305 | 500 | 5 | 140 | None | Arc 1816 (D1) |
| **Weirddevil** | 130 | 35,000 | 0 | 60,000 | 30,000 | 2305 | 500 | 5 | 140 | None | Arc 1836 (D1) |
| **Reflectguard** | 80 | 35,000 | 400 | 13,000 | 2,200 | 1300 | 400 | 20 | 20 | Thunder Punch (Hand) (128%) | Arc 1562 (D1) |
| **Rikiha** | 80 | 35,000 | 400 | 13,000 | 2,200 | 1300 | 400 | 20 | 20 | Thunder Punch (Hand) (128%) | Arc 1568 (D1) |
| **Masterwizard** | 80 | 35,000 | 400 | 13,000 | 2,200 | 1300 | 400 | 20 | 20 | Thunder Punch (Hand) (128%) | Arc 1562 (D1) |
| **Atlus** | 146 | 30,000 | 0 | 35,200 | 2,955 | 2220 | 500 | 50 | 150 | None | Arc 1804 (D1) |
| **Livingarmor** | 101 | 30,000 | 0 | 15,000 | 1,200 | 1900 | 390 | 45 | 140 | None | Arc 1776 (D1) |
| **Gloomwing** | 101 | 30,000 | 0 | 15,000 | 1,200 | 1900 | 390 | 45 | 140 | None | Arc 1770 (D1) |
| **Wizard** | 75 | 30,000 | 100 | 7,600 | 2,020 | 1100 | 400 | 100 | 50 | Item #1000 (24%) | Arc 1706 (D1) |
| **Magichand** | 16 | 30,000 | 100 | 200 | 50 | 120 | 380 | 700 | 50 | None | Arc 1929 (D1) |
| **Guardbox** | 16 | 30,000 | 100 | 200 | 50 | 120 | 380 | 700 | 50 | None | Arc 1929 (D1) |
| **Magicbox** | 16 | 30,000 | 100 | 200 | 50 | 120 | 380 | 700 | 50 | None | Arc 1929 (D1) |
| **Workbox** | 16 | 30,000 | 100 | 200 | 50 | 120 | 380 | 700 | 50 | None | Arc 1929 (D1) |
| **Cokatricking** | 180 | 29,800 | 0 | 60,000 | 5,000 | 2800 | 730 | 85 | 24 | None | Arc 1763 (D1) |
| **Greatergoat** | 142 | 29,700 | 600 | 36,600 | 4,080 | 2620 | 550 | 10 | 50 | None | Arc 1755 (D1) |
| **Dragonaxe** | 142 | 29,700 | 600 | 36,600 | 4,080 | 2620 | 550 | 10 | 50 | None | Arc 1876 (D1) |
| **Giant** | 116 | 29,000 | 0 | 20,000 | 3,200 | 2200 | 450 | 60 | 0 | None | Arc 1751 (D1) |
| **Starguarder** | 170 | 28,650 | 0 | 50,000 | 3,500 | 2700 | 10000 | 10 | 350 | None | Arc 1761 (D1) |
| **Weirdmalesk** | 180 | 28,000 | 100 | 62,500 | 5,000 | 2800 | 720 | 150 | 50 | None | Arc 1841 (D1) |
| **Ladyquimira** | 140 | 27,500 | 200 | 36,000 | 4,000 | 2500 | 540 | 40 | 40 | None | Arc 1754 (D1) |
| **Ericodus** | 75 | 25,500 | 50 | 9,000 | 50 | 1000 | 450 | 5 | 250 | None | Arc 1578 (D1) |
| **Takicodos** | 75 | 25,500 | 50 | 9,000 | 50 | 1000 | 450 | 5 | 250 | None | Arc 1576 (D1) |
| **NiquialM** | 75 | 25,500 | 50 | 9,000 | 50 | 1000 | 450 | 5 | 250 | None | Arc 1577 (D1) |
| **Kidnier** | 75 | 25,500 | 50 | 9,000 | 50 | 1000 | 450 | 5 | 250 | None | Arc 1589 (D1) |
| **Fenrilbeast** | 60 | 25,000 | 0 | 22,000 | 1,500 | 1000 | 320 | 60 | 30 | None | Arc 1546 (D1) |
| **Warlock** | 120 | 24,600 | 500 | 27,000 | 3,500 | 2000 | 440 | 50 | 50 | Item #20000 (24%) | Arc 1794 (D1) |
| **Weirdgoat** | 120 | 24,600 | 500 | 27,000 | 3,500 | 2000 | 440 | 50 | 50 | Item #20000 (24%) | Arc 1789 (D1) |
| **Weirdaxe** | 110 | 23,500 | 50 | 20,000 | 1,500 | 2100 | 420 | 55 | 20 | None | Arc 1777 (D1) |
| **Gloomsting** | 140 | 22,000 | 210 | 30,000 | 2,250 | 2405 | 520 | 45 | 10 | None | Arc 1803 (D1) |
| **Lesserdevil** | 118 | 21,200 | 0 | 27,000 | 2,450 | 1900 | 320 | 50 | 50 | None | Arc 1791 (D1) |
| **Shin** | 60 | 21,000 | 200 | 45,000 | 52,000 | 900 | 250 | 200 | 50 | None | Arc 1921 (D1) |
| **Stonestatue** | 60 | 21,000 | 200 | 45,000 | 52,000 | 900 | 250 | 200 | 50 | None | Arc 1924 (D1) |
| **Mountsnow** | 76 | 20,700 | 0 | 3,000 | 50 | 1400 | 350 | 50 | 150 | None | Arc 1947 (D1) |
| **Hellhound** | 60 | 20,000 | 200 | 4,600 | 2,000 | 900 | 180 | 20 | 30 | Thunder Punch (Hand) (128%) | Arc 1713 (D1) |
| **Otif** | 60 | 20,000 | 200 | 4,600 | 2,000 | 900 | 180 | 20 | 30 | Thunder Punch (Hand) (128%) | Arc 1714 (D1) |
| **Atulatul** | 60 | 20,000 | 0 | 4,800 | 50 | 780 | 320 | 30 | 150 | None | Arc 1556 (D1) |
| **Ghast** | 60 | 20,000 | 0 | 4,800 | 50 | 780 | 320 | 30 | 150 | None | Arc 1556 (D1) |
| **Yety** | 60 | 20,000 | 0 | 6,500 | 18,000 | 120 | 80 | 100 | 50 | None | Arc 1931 (D1) |
| **XINE** | 35 | 20,000 | 300 | 8,300 | 3,200 | 320 | 100 | 0 | 160 | None | Arc 1604 (D1) |
| **Saberbunny** | 73 | 18,600 | 0 | 4,000 | 5,000 | 935 | 300 | 50 | 30 | None | Arc 1946 (D1) |
| **Meigus** | 160 | 18,200 | 0 | 30,000 | 1,024 | 2620 | 620 | 50 | 40 | None | Arc 1823 (D1) |
| **Cavesting** | 110 | 18,000 | 100 | 23,000 | 1,850 | 2100 | 360 | 45 | 40 | None | Arc 1781 (D1) |
| **Miel64** | 80 | 18,000 | 0 | 9,900 | 2,000 | 1520 | 360 | 50 | 20 | None | Arc 1585 (D1) |
| **Controlkey** | 70 | 14,000 | 0 | 6,200 | 2,000 | 1200 | 80 | 50 | 10 | None | Arc 1561 (D1) |
| **Goathead** | 50 | 13,000 | 0 | 13,000 | 4,000 | 580 | 240 | 25 | 10 | None | Arc 1525 (D1) |
| **Coldlizard** | 50 | 13,000 | 0 | 13,000 | 4,000 | 580 | 240 | 25 | 10 | None | Arc 1518 (D1) |
| **Periton** | 51 | 12,500 | 0 | 2,800 | 50 | 745 | 120 | 30 | 20 | None | Arc 1535 (D1) |
| **Darkcrusader** | 57 | 10,000 | 0 | 4,500 | 1,000 | 920 | 200 | 20 | 10 | None | Arc 1548 (D1) |
| **Succubus** | 57 | 10,000 | 0 | 4,500 | 1,000 | 920 | 200 | 20 | 10 | None | Arc 1671 (D1) |
| **Ricki** | 55 | 10,000 | 0 | 3,500 | 850 | 820 | 160 | 30 | 50 | None | Arc 1537 (D1) |
| **Visseyer** | 40 | 10,000 | 100 | 4,200 | 7,000 | 500 | 80 | 100 | 10 | None | Arc 1614 (D1) |
| **Nightmare** | 30 | 9,000 | 100 | 4,000 | 2,200 | 500 | 200 | 20 | 100 | Portrait I (16%) | Arc 1602 (D1) |
| **Bang** | 48 | 8,300 | 0 | 2,300 | 654 | 850 | 40 | 0 | 20 | None | Arc 1534 (D1) |
| **Ghost** | 48 | 8,200 | 100 | 5,200 | 8,500 | 420 | 150 | 0 | 50 | None | Arc 1616 (D1) |
| **Insaneload** | 60 | 8,000 | 0 | 4,950 | 1,200 | 960 | 300 | 20 | 10 | None | Arc 1552 (D1) |
| **Rikilo** | 58 | 8,000 | 0 | 3,650 | 800 | 880 | 170 | 20 | 0 | None | Arc 1550 (D1) |
| **Controller** | 55 | 8,000 | 0 | 3,100 | 550 | 880 | 320 | 5 | 10 | None | Arc 1536 (D1) |
| **Timekeeper** | 45 | 6,700 | 0 | 3,000 | 1,000 | 650 | 120 | 50 | 14 | None | Arc 1521 (D1) |
| **Darthwidow** | 45 | 6,700 | 0 | 3,000 | 1,000 | 650 | 120 | 50 | 14 | None | Arc 1528 (D1) |
| **Eldermagius** | 45 | 6,700 | 0 | 3,000 | 1,000 | 650 | 120 | 50 | 14 | None | Arc 1522 (D1) |
| **PADmaster** | 49 | 6,500 | 0 | 2,100 | 50 | 605 | 280 | 5 | 10 | None | Arc 1956 (D1) |
| **Burst** | 55 | 6,000 | 0 | 4,800 | 600 | 120 | 120 | 0 | 40 | None | Arc 1569 (D1) |
| **Lessassassin** | 40 | 6,000 | 0 | 700 | 10,000 | 340 | 120 | 10 | 10 | None | Arc 1603 (D1) |
| **Zand** | 40 | 6,000 | 100 | 2,000 | 10,000 | 240 | 120 | 0 | 10 | None | Arc 1670 (D1) |
| **Riverside** | 76 | 5,200 | 100 | 12,000 | 50 | 1280 | 80 | 0 | 50 | None | Arc 1579 (D1) |
| **Salamander** | 40 | 5,000 | 0 | 6,000 | 2,000 | 461 | 240 | 60 | 10 | None | Arc 1502 (D1) |
| **Doomaxe** | 40 | 5,000 | 0 | 6,000 | 2,000 | 461 | 240 | 60 | 10 | None | Arc 1505 (D1) |
| **Giantbow** | 40 | 5,000 | 0 | 6,000 | 2,000 | 461 | 240 | 60 | 10 | None | Arc 1513 (D1) |
| **Flarelizard** | 30 | 5,000 | 0 | 4,000 | 8,000 | 410 | 160 | 25 | 100 | None | Arc 1601 (D1) |
| **Ogre** | 30 | 4,200 | 0 | 1,000 | 850 | 350 | 120 | 10 | 15 | None | Arc 1608 (D1) |
| **Raystinger** | 50 | 4,000 | 0 | 2,600 | 660 | 720 | 80 | 20 | 40 | None | Arc 1531 (D1) |
| **Dias** | 35 | 4,000 | 0 | 20,000 | 60,000 | 460 | 200 | 300 | 200 | None | Arc 1609 (D1) |
| **Blackslime** | 37 | 3,600 | 0 | 1,100 | 350 | 400 | 90 | 40 | 10 | None | Arc 1508 (D1) |
| **Gelatinfloat** | 55 | 3,000 | 0 | 4,000 | 900 | 800 | 120 | 0 | 50 | None | Arc 1967 (D1) |
| **Defender** | 45 | 3,000 | 50 | 1,900 | 450 | 630 | 150 | 50 | 10 | None | Arc 1529 (D1) |
| **Rolesher** | 32 | 3,000 | 0 | 250 | 150 | 400 | 150 | 5 | 40 | None | Arc 1951 (D1) |
| **Varmillion** | 18 | 3,000 | 0 | 1,000 | 1,000 | 160 | 120 | 10 | 0 | None | Arc 1599 (D1) |
| **Troll** | 27 | 2,700 | 0 | 800 | 50 | 350 | 80 | 0 | 50 | None | Arc 1607 (D1) |
| **Killerrabi** | 33 | 2,300 | 0 | 850 | 350 | 390 | 100 | 5 | 20 | None | Arc 1501 (D1) |
| **Ooze** | 33 | 2,300 | 0 | 850 | 350 | 390 | 100 | 5 | 20 | None | Arc 1497 (D1) |
| **Gladiator** | 20 | 2,000 | 0 | 500 | 10 | 310 | 100 | 2 | 50 | None | Arc 1606 (D1) |
| **Ghark** | 16 | 2,000 | 0 | 10 | 300 | 10 | 0 | 10 | 1 | None | Arc 1595 (D1) |
| **Azamgil** | 15 | 2,000 | 0 | 200 | 550 | 50 | 0 | 0 | 10 | None | Arc 1611 (D1) |
| **Archer** | 23 | 1,600 | 0 | 420 | 134 | 286 | 60 | 20 | 10 | None | Arc 1471 (D1) |
| **Slimepool** | 23 | 1,600 | 0 | 420 | 134 | 286 | 60 | 20 | 10 | None | Arc 1465 (D1) |
| **Petrogerell** | 23 | 1,600 | 0 | 420 | 134 | 286 | 60 | 20 | 10 | None | Arc 1472 (D1) |
| **Gargoyle** | 18 | 1,500 | 0 | 500 | 850 | 105 | 120 | 0 | 20 | None | Arc 1928 (D1) |
| **Shielder** | 20 | 1,400 | 0 | 410 | 800 | 350 | 70 | 10 | 100 | None | Arc 1600 (D1) |
| **NiquiaHG** | 13 | 1,300 | 50 | 1,000 | 50 | 110 | 250 | 5 | 50 | None | Arc 1540 (D1) |
| **Flyingray** | 30 | 1,200 | 0 | 1,000 | 250 | 270 | 40 | 5 | 0 | None | Arc 1487 (D1) |
| **Cockatrice** | 30 | 1,200 | 0 | 1,000 | 250 | 270 | 40 | 5 | 0 | None | Arc 1484 (D1) |
| **Shadowflower** | 30 | 1,200 | 0 | 151 | 220 | 320 | 150 | 10 | 10 | None | Arc 1952 (D1) |
| **Wolfhead** | 33 | 1,100 | 0 | 940 | 288 | 355 | 100 | 20 | 20 | None | Arc 1495 (D1) |
| **Blackhound** | 33 | 1,100 | 0 | 940 | 288 | 355 | 100 | 20 | 20 | None | Arc 1494 (D1) |
| **Shynesslady** | 32 | 1,000 | 30 | 900 | 280 | 330 | 80 | 15 | 90 | None | Arc 1488 (D1) |
| **Pilesherry** | 30 | 1,000 | 0 | 800 | 150 | 325 | 120 | 10 | 40 | None | Arc 1478 (D1) |
| **Shout** | 30 | 1,000 | 0 | 800 | 150 | 325 | 120 | 10 | 40 | None | Arc 1479 (D1) |
| **Sandworm** | 20 | 1,000 | 0 | 50 | 210 | 360 | 50 | 5 | 30 | None | Arc 1953 (D1) |
| **Gerel** | 20 | 880 | 0 | 520 | 337 | 260 | 80 | 10 | 10 | None | Arc 1457 (D1) |
| **Scewer** | 20 | 880 | 0 | 520 | 337 | 260 | 80 | 10 | 10 | None | Arc 1455 (D1) |
| **Koboldking** | 28 | 850 | 0 | 580 | 130 | 310 | 100 | 2 | 50 | None | Arc 1483 (D1) |
| **Sargwen** | 28 | 850 | 0 | 580 | 130 | 310 | 100 | 2 | 50 | None | Arc 1482 (D1) |
| **Hood** | 25 | 850 | 0 | 280 | 147 | 280 | 100 | 5 | 6 | None | Arc 1460 (D1) |
| **Beastmaster** | 19 | 840 | 30 | 300 | 130 | 180 | 70 | 0 | 50 | None | Arc 1447 (D1) |
| **Werewolf** | 19 | 840 | 30 | 300 | 130 | 180 | 70 | 0 | 50 | None | Arc 1447 (D1) |
| **Mandrake** | 35 | 800 | 0 | 880 | 280 | 360 | 150 | 10 | 40 | None | Arc 1492 (D1) |
| **Magius** | 15 | 800 | 0 | 300 | 260 | 167 | 100 | 10 | 20 | None | Arc 1698 (D1) |
| **Carlaeagle** | 15 | 800 | 0 | 300 | 260 | 167 | 100 | 10 | 20 | None | Arc 1440 (D1) |
| **Sandglass** | 20 | 780 | 0 | 400 | 260 | 250 | 170 | 0 | 20 | None | Arc 1452 (D1) |
| **Guarder** | 35 | 600 | 0 | 1,000 | 320 | 372 | 60 | 20 | 20 | None | Arc 1511 (D1) |
| **Robberaxe** | 14 | 600 | 0 | 130 | 90 | 170 | 50 | 5 | 20 | None | Arc 1637 (D1) |
| **Bugbear** | 14 | 600 | 0 | 130 | 90 | 170 | 50 | 5 | 20 | None | Arc 1435 (D1) |
| **Bloodworm** | 12 | 600 | 0 | 125 | 100 | 150 | 40 | 10 | 60 | None | Arc 1437 (D1) |
| **Stingray** | 15 | 588 | 0 | 150 | 250 | 166 | 60 | 2 | 10 | None | Arc 1439 (D1) |
| **Bandit** | 15 | 500 | 0 | 300 | 360 | 150 | 70 | 10 | 10 | None | Arc 1597 (D1) |
| **Gelatincube** | 17 | 460 | 0 | 160 | 130 | 250 | 80 | 40 | 20 | None | Arc 1450 (D1) |
| **Alen-Tax** | 18 | 400 | 0 | 150 | 500 | 40 | 0 | 0 | 0 | None | Arc 1596 (D1) |
| **Hounddog** | 28 | 200 | 0 | 295 | 155 | 260 | 80 | 0 | 20 | None | Arc 1467 (D1) |
| **Armedknight** | 9 | 200 | 0 | 45 | 40 | 95 | 60 | 6 | 32 | None | Arc 1429 (D1) |
| **Alraune** | 9 | 200 | 0 | 45 | 40 | 95 | 60 | 6 | 32 | None | Arc 1428 (D1) |
| **Slime** | 9 | 200 | 0 | 45 | 40 | 95 | 60 | 6 | 32 | None | Arc 1427 (D1) |
| **Landworm** | 6 | 200 | 0 | 35 | 40 | 95 | 10 | 8 | 0 | None | Arc 1424 (D1) |
| **Vopalbunny** | 4 | 120 | 0 | 16 | 25 | 69 | 10 | 0 | 22 | None | Arc 1419 (D1) |
| **Lizardaxe** | 5 | 65 | 0 | 15 | 30 | 58 | 5 | 1 | 0 | None | Arc 1416 (D1) |
| **Kobold** | 5 | 65 | 0 | 15 | 30 | 58 | 5 | 1 | 0 | None | Arc 1415 (D1) |
| **Kitty** | 5 | 60 | 0 | 4,000 | 1,200 | 450 | 228 | 0 | 150 | None | Arc 1512 (D1) |
| **Deathsaucer** | 1 | 10 | 10 | 4 | 3 | 105 | 10000 | 5 | 40 | None | Arc 1957 (D1) |
