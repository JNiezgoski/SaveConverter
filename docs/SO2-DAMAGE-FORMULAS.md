# Star Ocean: The Second Story (PS1) - Combat Damage Pipeline & Formulas

**Authoritative Technical Reference & MIPS Disassembly Analysis**  
*Document Version: 1.0.0 | Date: 2026-09-28*

---

## 1. Executive Summary

This document specifies the combat damage calculation algorithms used in *Star Ocean: The Second Story* (PlayStation 1, US Disc 1 & Disc 2).

All combat calculation routines reside in **Disc Archive 2129** (decompressed size `381,148` bytes / `0x5D0DC`), loaded into PlayStation Main RAM at base address **`0x8002F810`** (decompressed and executed via encounter overlay loader in Archive 2576 at `800105D0/800105D4`: `lui a2, 0x8003; addiu a2, a2, -0x7F0` = `0x8002F810`).

The damage engine is characterized by five core mechanics:
1. **Subtractive Base Damage**: Base physical combat damage is governed by $(\text{ATK} - \text{DEF})$.
2. **Fixed-Point Percentage Scaling**: All multipliers (elemental affinities, killer move scaling factors, spell multipliers, critical strike bonuses) scale using integer division by 100 via compiler reciprocal multiplication (`0x51eb851f` followed by `sra 5`).
3. **Multi-Channel Damage Dispatch**: Damage output is evaluated across discrete functional channels (physical strikes, killer moves, symbology spells, recoil reflection, status damage, item effects, shield stun).
4. **Central Modifier Dispatcher**: Action descriptors pass dedicated signed 16-bit modifiers (`+0x184..+0x192`) through a unified dispatch controller at **`0x80081934..0x80081A64`** (Archive 2129 offset `0x52124..0x52254`).
5. **Hard Ceiling Clamp**: Damage across all offensive channels is capped at **9,999** (`0x270F`); the shield stun gauge is capped at **999** (`0x3E7`); the status ailment infliction probability gauge is capped at **255** (`0x00FF`).

---

## 2. Damage Modifier Application & 9,999 Clamp

Primary physical scaling routine entry at **`0x800823D4..0x8008243C`** (Archive 2129 offset `0x52BC4..0x52C2C`):

```text
0x800823D4:  bgez  a1, 0x800823F0     ; If modifier a1 >= 0, branch to percentage scaling
0x800823D8:  move  a2, a0             ; Delay slot: a2 = CombatRecord pointer
0x800823DC:  lw    v0, 0x18(a2)      ; v0 = current base damage at record +0x18
0x800823E0:  nop                      ; Load delay
0x800823E4:  subu  v0, v0, a1        ; Flat modifier adjustment: v0 = v0 - a1
0x800823E8:  j     0x80082424        ; Branch directly to 9,999 clamp (skips percentage mult)
0x800823EC:  sw    v0, 0x18(a2)      ; Delay slot: store adjusted damage
0x800823F0:  lw    a0, 0x18(a2)      ; a0 = base net damage
0x800823F4:  nop                      ; Load delay
0x800823F8:  mult  a0, a1            ; net damage * percentage modifier (a1)
0x800823FC:  mflo  v1                ; v1 = product
0x80082400:  lui   v0, 0x51eb        ; High word of 1/100 reciprocal (0x51eb851f)
0x80082404:  ori   v0, v0, 0x851f    ; Reciprocal constant: 1374389535 (2^37 / 100)
0x80082408:  mult  v1, v0            ; product * reciprocal
0x8008240C:  sra   v1, v1, 31        ; Sign adjustment
0x80082410:  mfhi  a3                ; High 32 bits of reciprocal product
0x80082414:  sra   v0, a3, 5         ; Arithmetic shift right 5 (completes division by 100)
0x80082418:  subu  v0, v0, v1        ; Quotient correction: v0 = (damage * modifier) / 100
0x8008241C:  addu  a0, a0, v0        ; a0 = damage + (damage * modifier / 100)
0x80082420:  sw    a0, 0x18(a2)      ; Store scaled damage
0x80082424:  lw    v0, 0x18(a2)      ; Clamp entry point (from line 0x800823E8)
0x80082428:  nop                      ; Load delay
0x8008242C:  slti  v0, v0, 0x2710    ; Test if damage < 10000 (0x2710)
0x80082430:  bnez  v0, 0x8008243C    ; If valid, return
0x80082434:  addiu v0, zero, 0x270f  ; Delay slot / clamp: set to 9,999 (0x270F)
0x80082438:  sw    v0, 0x18(a2)      ; Store clamped damage
0x8008243C:  jr    ra                ; Return
```

### Physical Damage Mitigation Routine

At **`0x80082444..0x80082488`** (Archive 2129 offset `0x52C34..0x52C78`), percentage damage reduction (shields, defensive buffs) is applied, clamped to a minimum of 1 damage:
$$\text{Damage} = \max\left(1, \text{Damage} - \left\lfloor \frac{\text{Damage} \times \text{ReductionPercent}}{100} \right\rfloor \right)$$

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

The 8 elemental damage channels evaluated sequentially across loop `0x80081A84..0x80082320` are:
1. **Fire** (`s6 = 0`)
2. **Water** (`s6 = 1`)
3. **Wind** (`s6 = 2`)
4. **Earth** (`s6 = 3`)
5. **Thunder** (`s6 = 4`)
6. **Star** (`s6 = 5`)
7. **Light** (`s6 = 6`)
8. **Dark** (`s6 = 7`)

---

## 4. Multi-Channel Combat Damage Dispatch

The central dispatch pipeline at **`0x80081934..0x80081A64`** reads the modifier halfwords from the action descriptor block (`0x184..0x192($v0)`) and invokes the corresponding channel calculation routine:

| Channel Offset | Modifier Reg | Routine PC | File Offset | Action Channel | Mathematical Formula | Bounds Clamp |
| :---: | :---: | :---: | :---: | :--- | :--- | :---: |
| `+0x18` | `+0x184` | `0x800823D4` | `0x52BC4` | **Primary Physical Attack** | $\text{Base} + \lfloor \frac{\text{Base} \times M}{100} \rfloor$ (if $M \ge 0$)<br>$\text{Base} - M$ (if $M < 0$) | $[1, 9999]$ |
| `+0x18` | `+0x184` | `0x80082444` | `0x52C34` | **Physical Mitigation** | $\max(1, \text{Dmg} - \lfloor \frac{\text{Dmg} \times \text{Red}}{100} \rfloor)$ | Min 1 |
| `+0x22` | `+0x186` | `0x8008248C` | `0x52C7C` | **Shield / Stun Gauge Threshold** | $\text{Stun} + \lfloor \frac{\text{Stun} \times M}{100} \rfloor$ | $[0, 999]$ |
| `+0x22` | `+0x186` | `0x80082504` | `0x52CF4` | **Stun Mitigation / Recovery** | $\max(0, \text{Stun} - \lfloor \frac{\text{Stun} \times \text{Red}}{100} \rfloor)$ | Min 0 |
| `+0x2C` | `+0x188` | `0x80082554` | `0x52D44` | **Killer Move / Special Art** | $\text{Base} + \lfloor \frac{\text{Base} \times M}{100} \rfloor$ | $[0, 9999]$ |
| `+0x32` | `+0x18A` | `0x800825BC` | `0x52DAC` | **Symbology / Heraldry Spell** | $\text{Base} + \lfloor \frac{\text{Base} \times M}{100} \rfloor$ | $[0, 9999]$ |
| `+0x3E` | `+0x18C` | `0x80082630` | `0x52E20` | **Recoil / Counter Reflection** | $\text{Dmg} + \lfloor \frac{\text{Dmg} \times M}{100} \rfloor$ | $[0, 9999]$ |
| `+0x44` | — | `0x800826A0` | `0x52E90` | **Status / Persistent Damage** | $\text{Base} + \lfloor \frac{\text{Base} \times M}{100} \rfloor$ | $[0, 9999]$ |
| `+0x38` | `+0x18E` | `0x80082710` | `0x52F00` | **Item / Summon Art Effect** | $\text{Base} + \lfloor \frac{\text{Base} \times M}{100} \rfloor$ | $[0, 9999]$ |
| `+0x4A` | `+0x192` | `0x80081A00` | `0x521F0` | **Status Affliction Rate** | $\text{Prob} + \lfloor \frac{\text{Prob} \times M}{100} \rfloor$ | $[0, 255]$ |

---

## 5. Detailed Channel Math Specifications

### 5.1 Killer Moves (`+0x2C`, `0x80082554`)
The killer move channel loads the base skill damage from record offset `0x2C($a0)` and scales it by the killer move modifier passed in `$a1`:
$$\text{Damage}_{\text{KM}} = \text{Base} + \left\lfloor \frac{\text{Base} \times M_{\text{KM}}}{100} \right\rfloor$$
- Upper bound: If $\text{Damage} \ge 10,000$ (`0x2710`), clamped to **9,999** (`0x270F`) at `0x8008259C`.
- Lower bound: If $\text{Damage} < 0$, clamped to **0** at `0x800825B4`.

### 5.2 Symbology / Heraldry Spells (`+0x32`, `0x800825BC`)
Symbology spell damage is stored as a 16-bit halfword at `0x32($a0)` and scaled by the spell power modifier in `$a1`:
$$\text{Damage}_{\text{spell}} = \text{Base} + \left\lfloor \frac{\text{Base} \times M_{\text{spell}}}{100} \right\rfloor$$
- Upper bound: Clamped to **9,999** at `0x8008260C`.
- Lower bound: Clamped to **0** at `0x80082624`.

### 5.3 Counter / Recoil Reflection (`+0x3E` / `+0x40`, `0x80082630`)
When a counter or reflection effect triggers, the incident damage in `$a0` is multiplied by the reflection percentage in `$a1`:
$$\text{Damage}_{\text{recoil}} = \text{Damage} + \left\lfloor \frac{\text{Damage} \times M_{\text{reflect}}}{100} \right\rfloor$$
- Reflected damage value is stored to `0x3E($a2)` and `0x40($a2)`.
- Upper bound: Clamped to **9,999** at `0x8008267C`.
- Lower bound: Clamped to **0** at `0x80082694`.

### 5.4 Item & Summon Art Effects (`+0x38`, `0x80082710`)
Offensive items (e.g. attack items) and summon effects load potency from `0x38($a0)` and scale by `$a1`:
$$\text{Damage}_{\text{item}} = \text{Base} + \left\lfloor \frac{\text{Base} \times M_{\text{item}}}{100} \right\rfloor$$
- Upper bound: Clamped to **9,999** at `0x8008275C`.
- Lower bound: Clamped to **0** at `0x80082774`.

### 5.5 Status Ailment Affliction Rate (`+0x4A`, `0x80081A00`)
Status infliction probability is calculated as an 8-bit percentage gauge at `0x4A($s3)`:
$$\text{Chance}_{\text{status}} = \text{BaseChance} + \left\lfloor \frac{\text{BaseChance} \times M_{\text{status}}}{100} \right\rfloor$$
- Upper bound: If $\text{Chance} \ge 256$ (`0x100`), clamped to **255** (`0x00FF` / 100% max probability) at `0x80081A48`.
- Lower bound: If $\text{Chance} < 0$, clamped to **0** at `0x80081A60`.

---

## 6. Critical Hits & GUTS Dynamic Interaction

1. **Critical Hits**:
   - Critical hits bypass target DEF calculation and apply a flat $+50$ to the modifier:
     $$\text{Damage}_{\text{crit}} = \text{ATK} \times 1.5$$
2. **GUTS Stun Meter (`+0x22` in Combat Record)**:
   - When taking a hit, target stun gauge increases dynamically up to ceiling 999 (`0x3E7` at `0x800824F0`).
   - If stun gauge exceeds threshold, combatant enters Stun status, disabling movement and evasion until recovery.
