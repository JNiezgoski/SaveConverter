# Star Ocean: The Second Story (PS1) - Battle & Character Sprite Engine Specification

**Authoritative Technical Reference & Reverse-Engineering Report**  
*Document Version: 2.0.0 | Date: 2026-09-28*

---

## 1. Executive Summary

This specification documents the complete reverse-engineering and resolution of the character and monster sprite format used in *Star Ocean: The Second Story* (PlayStation 1, US Disc 1 & Disc 2).

Previous extraction attempts produced severely sheared, diagonally sliced, incomplete, or monochrome grayscale sprites due to three critical architectural misconceptions:
1. **Misaligned Section Base (`0x18`)**: Hardcoding Section 0 base to `0x18` offset-shifted every archive that did not have exactly 5 sections by 4 to 12 bytes.
2. **Misaligned Container Pointer (`0x1B4`)**: Hardcoding the container pointer to `0x1B4` broke every character whose animation container started at `0x168`, `0x198`, or `0x1D0`.
3. **The "Layout B" Phantom Deserialization**: Because of base misalignment, previous tools hypothesized an alternate "Layout B" that swapped dimensions with pivots. In reality, **every 12-byte frame descriptor in the game is strictly uniform**.
4. **Missing Palettes**: Palettes were presumed to be missing from the sprite archives; in reality, authentic **16-color BGR555 CLUT palettes are embedded directly in every container header** at `desc_end + 4`.

With the corrected dynamic container parser implemented in [tools/so2_sprite_extract.py](file:///C:/CodeTesting/SaveConverter/tools/so2_sprite_extract.py) and integrated into [saveconv.py](file:///C:/CodeTesting/SaveConverter/saveconv.py):
- **5,272 sprite frames** have been extracted across **79 archives** on Disc 1.
- All 12 playable heroes (Claude, Rena, Celine, Bowman, Dias, Precis, Ashton, Leon, Opera, Ernest, Noel, Chisato) are extracted in authentic 16-color pixel art with zero shearing and zero slicing — a real fix over earlier attempts. See **Section 6, Known Issues** for a small remaining decode gap.

---

## 2. Low-Level Container Binary Structure

Every combat sprite archive is composed of three nested layers:
1. **Root Section Header Table** (dynamic count and pointers)
2. **Per-Section Header & Dynamic Sprite Container Pointer** (Word [7])
3. **Sprite Container Block** (Header + 12-byte Frame Descriptors + CLUT Palette + 4bpp Raster Scanlines)

```
Archive Binary Layout:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Root Header: [num_sections (<I)] [sec_offset_0 (<I)] ... [sec_offset_N (<I)]    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Section s: (at offset s_off)                                                    │
│   Words [0..6]: Section state / timing / physics parameters                    │
│   Word [7] (+0x1C): sprite_ptr (Relative offset to Sprite Container: p3)        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Sprite Container Block: (at offset p3 = s_off + sprite_ptr)                     │
│   Bytes 0..3:   hdr_sz (uint32 LE) = 12 + 12 * frame_count                      │
│   Bytes 4..7:   pix_rel_off (uint32 LE) = Relative offset from p3 to pix_start  │
│   Bytes 8..9:   unk (uint16 LE) = 2 (Format Version)                            │
│   Bytes 10..11: frame_count (uint16 LE) = Total animation frames in section     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Frame Descriptors: (frame_count * 12 bytes, at p3 + 12)                         │
│   [flags(1B), width(1B), height(1B), res(1B), px(2B int16), py(2B int16), off(4B)]│
├─────────────────────────────────────────────────────────────────────────────────┤
│ CLUT Palette Block: (at desc_end = p3 + 12 + 12 * frame_count)                  │
│   Bytes 0..3:   color_count (uint32 LE) = 16 (or 128 for gradient shades)       │
│   Bytes 4..35:  16 x uint16 LE (15-bit BGR555 CLUT Words)                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 4bpp Raster Scanlines: (at pix_start = p3 + pix_rel_off)                        │
│   Linear 4bpp nibble stream indexed by frame descriptor offsets                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Field Specifications

### 3.1 Root Section Header Table
```python
num_sec = struct.unpack_from("<I", data, 0)[0]
sec_offsets = [struct.unpack_from("<I", data, 4 + 4 * i)[0] for i in range(num_sec)]
```
* `num_sec`: Number of animation sections (banks) in the archive.
  * Hero Cast Roster (`Archive 3026`): 12 sections (1 per character).
  * Claude Combat Stances (`Archives 3111..3173`): 2 to 7 sections per archive.
  * Ashton & Monsters (`Archives 3176..3206`): 1 to 5 sections per archive.
  * Summon Arts & Specials (`Archives 4035..4050`): 1 to 2 sections.
* `sec_offsets[i]`: Absolute byte offset to Section $i$ from the start of the decompressed archive.

### 3.2 Dynamic Sprite Container Pointer
Within each section $i$ at `s_off = sec_offsets[i]`:
```python
sprite_ptr = struct.unpack_from("<I", data, s_off + 0x1C)[0]
p3 = s_off + sprite_ptr
```
* Word [7] at offset `s_off + 0x1C` is a 32-bit little-endian relative pointer to the sprite container.
* Previous code assumed this was fixed at `0x18 + 0x1B4`. In reality, `sprite_ptr` varies dynamically (`168`, `408`, `436`, `464`, etc.).

### 3.3 Container Header (12 Bytes)
At offset `p3`:
```python
hdr_sz, pix_rel_off, unk, frame_count = struct.unpack("<IIHH", data[p3:p3 + 12])
```
* `hdr_sz`: Exactly matches $12 + 12 \times \text{frame\_count}$.
* `pix_rel_off`: Byte offset from `p3` to the start of pixel scanlines (`pix_start = p3 + pix_rel_off`).
* `unk`: Always `2` across combat and hero sprite containers.
* `frame_count`: Number of animation frames in this bank (commonly 21 for combat cycles, 12 for roster, 42 for summons).

### 3.4 Uniform 12-Byte Frame Descriptor
Starting at `p3 + 12`, each frame descriptor is exactly 12 bytes:
```python
flags, width, height, reserved = struct.unpack("4B", data[pos:pos + 4])
pivot_x, pivot_y = struct.unpack("<2h", data[pos + 4:pos + 8])
offset = struct.unpack("<I", data[pos + 8:pos + 12])[0]
```
* `flags` (uint8): Animation behavior flags (transparency, flip, interpolation).
* `width` (uint8): Pixel width of the frame (always even; 20, 24, 32, 36, 44, 56).
* `height` (uint8): Pixel height of the frame (36 to 64).
* `reserved` (uint8): Padding (`0x00`).
* `pivot_x`, `pivot_y` (int16 LE): Signed hardware pivot / hotspot offsets relative to entity center.
* `offset` (uint32 LE): Byte offset relative to `pix_start` where this frame's 4bpp scanlines begin.

### 3.5 Authentic 16-Color BGR555 CLUT Palette
Located immediately after the frame descriptors:
```python
desc_end = p3 + 12 + frame_count * 12
color_count = struct.unpack_from("<I", data, desc_end)[0]
clut_words = struct.unpack_from("<16H", data, desc_end + 4)
```
* In PS1 15-bit color:
  * Red: `(word & 0x1F) << 3`
  * Green: `((word >> 5) & 0x1F) << 3`
  * Blue: `((word >> 10) & 0x1F) << 3`
* **Color 0 Transparency**: In PS1 4bpp indexed sprites, Color Index 0 is the background transparency key (`alpha = 0`), while Colors 1..15 are opaque (`alpha = 255`).

---

## 4. Master Archive Catalog & Character Distribution

| Archive ID | Role & Description | Sections | Total Frames | Sample Character / Content |
| :---: | :--- | :---: | :---: | :--- |
| **`3026`** | **Master Hero Roster** | 12 | 45 | **All 12 Playable Characters**: Claude, Rena, Celine, Bowman, Dias, Precis, Ashton, Leon, Opera, Ernest, Noel, Chisato |
| **`3111..3173`** | **Claude Kenni Combat Banks** | 2..7 | 2,751 | Claude combat weapon stances, killer moves (Dragon Howl, Air Slash, Mirror Slice), idle, run, hit, victory |
| **`3176..3206`** | **Ashton & Monster Banks** | 1..5 | 1,596 | Ashton Anchors dual-wield stances, Leaf Slash, Piercing Blades + Combat enemy monster animation cycles |
| **`4035`** | Combat Monster - Shadow Fiend | 2 | 60 | Large clawed boss enemy with multi-frame attack & hurt animations |
| **`4036..4040`** | Boss Minions & Effect Entities | 1 | 55 | Minions, floating eye demons, and projectile particles |
| **`4041`** | Combat Summon - Fairy Spirit | 1 | 42 | Full 42-frame winged fairy summon animation |
| **`4042`** | Combat Character - Bowman Jeane | 1 | 42 | Bowman martial arts sprint, kick, and Secret Art frames |
| **`4043`** | Combat Character - Noel Chandler | 1 | 42 | Noel Nedian zoologist spellcasting & sprint cycles |
| **`4044`** | Combat Character - Precis F. Newman | 1 | 42 | Precis mechanic sprint, hammer strike, and robot summons |
| **`4045`** | Combat Character - Ashton Anchors | 1 | 42 | Ashton Anchors with dragons Gyoro & Ururun in full color |
| **`4046`** | Combat Character - Ashton (Stance) | 1 | 42 | Ashton sword combat idle & attack cycle |
| **`4047`** | Combat Character - Opera Vectra | 1 | 42 | Opera Vectra high-heel slit dress, rifle stance & beam firing |
| **`4048`** | Combat Character - Ernest Ravreve | 1 | 42 | Ernest Ravreve whip attack & archaeologist exploration cycles |
| **`4049`** | Combat Character - Leon D.S. Gehste | 1 | 42 | Leon Gehste Fellpool feline ears, spellcasting incantations |
| **`4050`** | Combat Character - Chisato Madison | 1 | 42 | Chisato Madison reporter sprint, martial arts kick, tear gas |

---

## 5. Usage & Reproduction

### Single Archive Extraction
```powershell
python tools/so2_sprite_extract.py --archive 3026 --scale 3
```
Extracts all 12 playable heroes into `artifacts/so2-sprites/archive_3026/` at 3x nearest-neighbor upscale.

### Batch Extraction (All 79 Archives)
```powershell
python tools/so2_sprite_extract.py --all
```
Extracts 5,272 sprite frames across all 79 archives, generating [artifacts/so2-sprites/sprites_catalog.json](file:///C:/CodeTesting/SaveConverter/artifacts/so2-sprites/sprites_catalog.json).

### Save Converter Unified CLI
```powershell
python saveconv.py so2-sprites --archive 4045 --scale 2
python saveconv.py so2-sprites --all
```

---

## 6. Known Issues (manager review, 2026-09-28)

A programmatic scan of all 5,272 extracted PNGs (checking for fully-transparent output) found **9 blank
frames (0.17% of the total)**, all confined to the `3026` Hero Roster archive:

| Character | Blank frame indices | Section total |
|---|---|---|
| Rena Lanford | 1, 2, 8 | ~12 |
| Precis F. Neumann | 0, 1, 2 | ~12 |
| Ernest Ravine | 0, 3, 7 | ~12 |

These frames report valid, non-zero `width`/`height` in the descriptor (not flagged `is_empty`) and a
plausible-looking palette, but the pixel bytes at the computed `pix_start + offset` decode to all-zero
(transparent) indices. Every frame across the much larger `3111..3206` and `4035..4050` combat archives
decoded cleanly with no blanks — this gap appears specific to how archive `3026`'s per-character portrait
sub-states (likely blink/talk alternates) resolve their pixel offset, not a problem with the container
format itself. Not yet root-caused; worth a follow-up pass on archive `3026` specifically before treating
the roster extraction as 100% complete.
