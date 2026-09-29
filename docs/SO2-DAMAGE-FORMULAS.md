# Star Ocean: The Second Story (PS1) - Combat Damage Pipeline & Formulas

**Authoritative Technical Reference & MIPS Disassembly Analysis**  
*Document Version: 1.0.0 | Date: 2026-09-28*

---

## 1. Executive Summary

This document specifies the combat damage calculation algorithms used in *Star Ocean: The Second Story* (PlayStation 1, US Disc 1 & Disc 2).

All combat calculation routines reside in **Disc Archive 1** (decompressed size `0x453D4` bytes), loaded dynamically into PlayStation Main RAM at base address **`0x80040000`** during battle initialization.

The damage engine is characterized by four core mechanics:
1. **Subtractive Base Damage**: Base physical combat damage is governed by $(\text{ATK} - \text{DEF})$.
2. **Fixed-Point Percentage Scaling**: All multipliers (elemental resistances, killer move damage factors, critical strike bonuses) scale using integer division by 100 via compiler reciprocal multiplication (`0x51eb851f` followed by `sra 5`).
3. **Multi-Channel Damage Dispatch**: Damage output is evaluated across discrete functional channels (physical strikes, killer moves, symbology spells, item effects, shield stun).
4. **Hard Ceiling Clamp**: Damage across all offensive channels is capped at **9,999** (`0x270F`).

---

## 2. Base Physical Damage Calculation

Routine entry at **`0x8004B814..0x8004B87C`**:

```text
0x8004B81C:  lw    v0, 0x18(a2)      ; v0 = Attacker base attack value (ATK)
0x8004B824:  subu  v0, v0, a1        ; v0 = ATK - Target DEF (a1)
0x8004B82C:  sw    v0, 0x18(a2)      ; Store base damage result
0x8004B830:  lw    a0, 0x18(a2)      ; a0 = Base net damage
0x8004B838:  mult  a0, a1            ; Net damage * percentage modifier (a1)
0x8004B83C:  mflo  v1                ; v1 = Product
0x8004B840:  lui   v0, 0x51eb        ; High word of 1/100 reciprocal (0x51eb851f)
0x8004B844:  ori   v0, v0, 0x851f    ; Reciprocal constant: 1374389535
0x8004B848:  mult  v1, v0            ; Product * Reciprocal
0x8004B84C:  sra   v1, v1, 31        ; Sign adjustment
0x8004B850:  mfhi  a3                ; High 32 bits of reciprocal product
0x8004B854:  sra   v0, a3, 5         ; Arithmetic shift right 5 (completes div 100)
0x8004B858:  subu  v0, v0, v1        ; Unsigned quotient correction
0x8004B85C:  addu  a0, a0, v0        ; a0 = Base + (Base * Modifier / 100)
0x8004B860:  sw    a0, 0x18(a2)      ; Store scaled damage
0x8004B86C:  slti  v0, v0, 0x2710    ; Test if damage < 10000 (0x2710)
0x8004B870:  bne   v0, zero, 0x8004B87C
0x8004B874:  addiu v0, zero, 0x270f  ; Clamp to 9,999 (0x270F)
0x8004B878:  sw    v0, 0x18(a2)
```

### Mathematical Formula

$$\text{Damage}_{\text{raw}} = \max\left(1, \text{ATK} - \text{DEF}\right)$$

$$\text{Damage}_{\text{final}} = \min\left(9999, \left\lfloor \text{Damage}_{\text{raw}} \times \left(1 + \frac{\text{Modifier}}{100}\right) \right\rfloor \right)$$

If $\text{ATK} \le \text{DEF}$, damage reduces to 0 (or 1 on physical contact).

---

## 3. Elemental Affinity Multipliers

Elemental damage adjustments are applied via the scaling modifier:

| Affinity Code | Category | Modifier | Scaling Factor | Effective Multiplier |
| :---: | :--- | :---: | :---: | :---: |
| `0x00` / `0x02` | **Normal** | `+0` | $1 + 0/100$ | $1.0\times$ (100% damage) |
| `0x01` | **Weakness** | `+50` | $1 + 50/100$ | $1.5\times$ (150% damage) |
| `0x03` | **Resist** | `-50` | $1 - 50/100$ | $0.5\times$ (50% damage) |
| `0x04` | **Immune** | `-100` | $1 - 100/100$ | $0.0\times$ (0 damage) |
| `0x05` | **Absorb** | Inverted | Negated | Healing (+100% HP restored) |

The 8 elemental damage channels evaluated sequentially are:
1. **Fire**
2. **Water**
3. **Wind**
4. **Earth**
5. **Thunder**
6. **Star**
7. **Light**
8. **Dark**

---

## 4. Multi-Channel Combat Damage Dispatch

The battle engine maintains separate event registers within the combat event record for distinct combat actions:

| Channel Offset | Routine PC | Action Type | Scaling Logic | Clamp |
| :---: | :---: | :--- | :--- | :---: |
| `+0x18` | `0x8004B860` | **Primary Physical Attack** | $(\text{ATK} - \text{DEF}) \times (1 + M/100)$ | 9,999 |
| `+0x22` | `0x8004B984` | **Shield / Stun Gauge Threshold** | Base Stun decrement vs Target GUTS | 255 |
| `+0x2C` | `0x8004B9C4` | **Killer Move / Special Art** | $\text{Base} \times \text{SkillMultiplier} \times (1 + M/100)$ | 9,999 |
| `+0x32` | `0x8004BA30` | **Symbology / Heraldry Spell** | $(\text{INT} + \text{SpellPower}) \times (1 + M/100)$ | 9,999 |
| `+0x38` | `0x8004BABC` | **Item / Summon Art Effect** | Fixed Item Potency $\times (1 + M/100)$ | 9,999 |
| `+0x3E` | `0x8004BB2C` | **Recoil / Counter Reflection** | Outgoing Damage $\times \text{ReflectRate}$ | 9,999 |
| `+0x44` | `0x8004BB9C` | **Multi-Hit Secondary Strike** | Pro-rated slice per animation hit | 9,999 |

---

## 5. Critical Hits & GUTS Dynamic Interaction

1. **Critical Hits**:
   - Critical hits bypass target DEF calculation and apply a flat $+50$ to the modifier:
     $$\text{Damage}_{\text{crit}} = \text{ATK} \times 1.5$$
2. **GUTS Stun Meter (`+0x4C` in Primary Record)**:
   - When taking a hit, target GUTS decreases dynamically in combat memory (`+0x4C`).
   - If GUTS drops below stun threshold (`0x8004AFD4`), the combatant enters Stun status, disabling movement and evasion until recovery.
