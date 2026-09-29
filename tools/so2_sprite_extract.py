"""Star Ocean: The Second Story (PS1) - Battle & Character Sprite Extractor.

Extracts authentic 4bpp (16-color BGR555) character and monster battle sprite
frames from tri-Ace graphic archives on Disc 1 & Disc 2.

Discovered Archive Categories:
- Archive 3026: Hero Roster (All 12 Playable Characters: Claude, Rena, Celine,
  Bowman, Dias, Precis, Ashton, Leon, Opera, Ernest, Noel, Chisato)
- Archives 3111..3173 (odd): Claude Kenni Combat Animation Banks & Weapon Stances
- Archives 3176..3206: Ashton Anchors Combat Animation Banks & Battle Monster Sets
- Archives 4035..4050: Combat Summon Arts, Special Skill Sprites & Boss Monsters
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tools.so2_disc_code import archive_table, read_sectors, slz

DEFAULT_DISC = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")

ROSTER_3026_NAMES = [
    "Claude_Kenni",
    "Rena_Lanford",
    "Celine_Jules",
    "Bowman_Jeane",
    "Dias_Flac",
    "Precis_F_Newman",
    "Ashton_Anchors",
    "Leon_DS_Gehste",
    "Opera_Vectra",
    "Ernest_Ravreve",
    "Noel_Chandler",
    "Chisato_Madison",
]

KNOWN_ARCHIVES = {
    3026: "Hero Roster (All 12 Playable Characters)",
    4035: "Combat Monster - Shadow Fiend",
    4036: "Combat Monster - Effect Sprite",
    4037: "Combat Monster - Boss Minion A",
    4038: "Combat Monster - Boss Minion B",
    4039: "Combat Monster - Floating Eye",
    4040: "Combat Monster - Lesser Demon",
    4041: "Combat Summon - Fairy Spirit",
    4042: "Combat Character - Bowman Jeane",
    4043: "Combat Character - Noel Chandler",
    4044: "Combat Character - Precis F. Newman",
    4045: "Combat Character - Ashton Anchors (with Gyoro & Ururun)",
    4046: "Combat Character - Ashton Anchors (Stance)",
    4047: "Combat Character - Opera Vectra",
    4048: "Combat Character - Ernest Ravreve",
    4049: "Combat Character - Leon D.S. Gehste",
    4050: "Combat Character - Chisato Madison",
}


def decode_bgr555_palette(data: bytes, offset: int, num_colors: int = 16) -> Tuple[List[int], List[Dict[str, int]]]:
    """Decode 16-bit BGR555 palette into PIL flat palette and RGBA dictionary."""
    clut_words = struct.unpack_from(f"<{num_colors}H", data, offset)
    pal_flat: List[int] = []
    pal_rgba: List[Dict[str, int]] = []
    for i, c in enumerate(clut_words):
        r = (c & 0x1F) << 3
        g = ((c >> 5) & 0x1F) << 3
        b = ((c >> 10) & 0x1F) << 3
        a = 0 if i == 0 else 255
        pal_flat.extend([r, g, b])
        pal_rgba.append({"r": r, "g": g, "b": b, "a": a, "raw_hex": f"0x{c:04X}"})
    # Pad to 256 RGB entries (768 bytes) for PIL 'P' mode
    pal_flat.extend([0] * (768 - len(pal_flat)))
    return pal_flat, pal_rgba


def extract_sprite_frames(
    archive_id: int,
    disc_path: Path = DEFAULT_DISC,
    output_dir: Path | None = None,
    scale: int = 2
) -> Dict[str, Any]:
    """Extract all authentic 4bpp sprite frames across all animation sections in an archive."""
    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))
        if archive_id not in tbl:
            raise ValueError(f"Archive {archive_id} not found in archive table.")
        raw = read_sectors(f, tbl[archive_id][0], tbl[archive_id][1])
        try:
            data = slz(raw) if raw[:3] == b"SLZ" else raw
        except Exception as e:
            raise ValueError(f"SLZ decompression failed for Archive {archive_id}: {e}")

    if len(data) < 32:
        raise ValueError(f"Archive {archive_id} is too small ({len(data)} bytes).")

    num_sec = struct.unpack_from("<I", data, 0)[0]
    if num_sec == 0 or num_sec > 64:
        raise ValueError(f"Archive {archive_id} has invalid section count: {num_sec}")

    sec_offsets = [struct.unpack_from("<I", data, 4 + 4 * i)[0] for i in range(num_sec)]

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    archive_info: Dict[str, Any] = {
        "archive_id": archive_id,
        "name": KNOWN_ARCHIVES.get(
            archive_id,
            f"Claude Combat Stance Bank {archive_id}" if 3111 <= archive_id <= 3173
            else f"Ashton/Monster Bank {archive_id}" if 3176 <= archive_id <= 3206
            else f"Sprite Archive {archive_id}"
        ),
        "total_sections": num_sec,
        "valid_sections": 0,
        "total_frames_extracted": 0,
        "sections": []
    }

    for s_idx, s_off in enumerate(sec_offsets):
        if s_off + 0x20 > len(data):
            continue

        sprite_ptr = struct.unpack_from("<I", data, s_off + 0x1C)[0]
        p3 = s_off + sprite_ptr
        if p3 + 12 > len(data):
            continue

        hdr_sz, pix_rel_off, unk, frame_count = struct.unpack("<IIHH", data[p3:p3 + 12])
        if frame_count == 0 or frame_count > 256:
            continue

        pix_start = p3 + pix_rel_off
        if pix_start > len(data):
            continue

        # Palette is stored at desc_end + 4
        desc_end = p3 + 12 + frame_count * 12
        if desc_end + 4 + 32 > len(data):
            continue

        pal_flat, pal_rgba = decode_bgr555_palette(data, desc_end + 4, 16)

        sec_name = ROSTER_3026_NAMES[s_idx] if archive_id == 3026 and s_idx < len(ROSTER_3026_NAMES) else f"section_{s_idx:02d}"
        sec_info: Dict[str, Any] = {
            "section_index": s_idx,
            "section_name": sec_name,
            "frame_count": frame_count,
            "palette": pal_rgba,
            "frames": []
        }

        frames_extracted_in_sec = 0
        for f_idx in range(frame_count):
            pos = p3 + 12 + f_idx * 12
            if pos + 12 > len(data):
                break

            flags, w, h, res = struct.unpack("4B", data[pos:pos + 4])
            px, py = struct.unpack("<2h", data[pos + 4:pos + 8])
            off = struct.unpack("<I", data[pos + 8:pos + 12])[0]

            frame_entry: Dict[str, Any] = {
                "frame_index": f_idx,
                "width": w,
                "height": h,
                "pivot_x": px,
                "pivot_y": py,
                "offset": off,
                "is_empty": (w == 0 or h == 0)
            }

            if w == 0 or h == 0 or w > 512 or h > 512:
                sec_info["frames"].append(frame_entry)
                continue

            bpr = w // 2
            f_start = pix_start + off
            f_end = f_start + bpr * h
            if f_end > len(data):
                frame_entry["error"] = "Pixel data out of bounds"
                sec_info["frames"].append(frame_entry)
                continue

            f_bytes = data[f_start:f_end]
            if not f_bytes or all(b == 0 for b in f_bytes):
                frame_entry["is_empty"] = True
                frame_entry["note"] = "All-zero blank placeholder frame"
                sec_info["frames"].append(frame_entry)
                continue

            expanded = bytearray(w * h)
            for i, b in enumerate(f_bytes):
                expanded[i * 2] = b & 0x0F
                expanded[i * 2 + 1] = (b >> 4) & 0x0F

            im = Image.frombytes("P", (w, h), bytes(expanded))
            im.putpalette(pal_flat)
            im.info["transparency"] = 0
            im_rgba = im.convert("RGBA")

            if scale > 1:
                im_rgba = im_rgba.resize((w * scale, h * scale), Image.NEAREST)

            if output_dir is not None:
                if archive_id == 3026:
                    fn = f"{s_idx:02d}_{sec_name}_f{f_idx:02d}.png"
                else:
                    fn = f"arc{archive_id:04d}_s{s_idx:02d}_f{f_idx:02d}.png"
                im_rgba.save(output_dir / fn)
                frame_entry["filename"] = fn

            sec_info["frames"].append(frame_entry)
            frames_extracted_in_sec += 1

        if frames_extracted_in_sec > 0:
            archive_info["valid_sections"] += 1
            archive_info["total_frames_extracted"] += frames_extracted_in_sec
            archive_info["sections"].append(sec_info)

    return archive_info


def extract_all_sprites(
    disc_path: Path = DEFAULT_DISC,
    output_base: Path | None = None,
    scale: int = 2
) -> Dict[str, Any]:
    """Scan and batch extract all verified combat sprite archives on Disc 1."""
    if output_base is None:
        output_base = _ROOT / "artifacts" / "so2-sprites"
    output_base.mkdir(parents=True, exist_ok=True)

    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))

    # All discovered archives:
    # 3026: Master Hero Roster
    # 3111..3173 (odd): Claude Stances & Special Arts
    # 3176..3206: Ashton Banks & Monsters
    # 4035..4050: Party Special Sprites, Summons, and Boss Entities
    target_archives = (
        [3026]
        + list(range(3111, 3174, 2))
        + list(range(3176, 3207))
        + list(range(4035, 4051))
    )

    catalog: Dict[str, Any] = {
        "disc": 1,
        "total_archives_queued": len(target_archives),
        "total_archives_extracted": 0,
        "total_frames_extracted": 0,
        "archives": {}
    }

    print(f"Batch extracting {len(target_archives)} verified combat and hero sprite archives...")
    for idx in target_archives:
        if idx not in tbl:
            continue
        try:
            arc_dir = output_base / f"archive_{idx:04d}"
            info = extract_sprite_frames(idx, disc_path, arc_dir, scale)
            if info["total_frames_extracted"] > 0:
                catalog["archives"][str(idx)] = info
                catalog["total_archives_extracted"] += 1
                catalog["total_frames_extracted"] += info["total_frames_extracted"]
                print(
                    f"  [+] Archive {idx:04d} ({info['name']}): "
                    f"{info['total_frames_extracted']:3d} frames across "
                    f"{info['valid_sections']} sections -> {arc_dir.name}/"
                )
        except Exception as e:
            print(f"  [-] Archive {idx:04d}: skipped ({e})")
            continue

    cat_json = output_base / "sprites_catalog.json"
    cat_json.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"\n=================================================================")
    print(f"Sprite Extraction Complete!")
    print(f"Extracted {catalog['total_frames_extracted']} frames across {catalog['total_archives_extracted']} archives.")
    print(f"Catalog saved to {cat_json}")
    print(f"=================================================================\n")
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract SO2 PS1 combat and character sprites.")
    parser.add_argument("--archive", type=int, default=None, help="Specific Archive ID to extract (e.g. 3026, 3111, 3178)")
    parser.add_argument("--all", action="store_true", help="Batch extract all valid combat sprite archives")
    parser.add_argument("--disc", type=Path, default=DEFAULT_DISC, help="Path to Disc 1 BIN")
    parser.add_argument("--out", type=Path, default=None, help="Output directory")
    parser.add_argument("--scale", type=int, default=2, help="Upscale multiplier (default: 2)")
    args = parser.parse_args()

    if args.all or args.archive is None:
        extract_all_sprites(args.disc, args.out, args.scale)
    else:
        out_dir = args.out
        if out_dir is None:
            out_dir = _ROOT / "artifacts" / "so2-sprites" / f"archive_{args.archive:04d}"

        print(f"Extracting sprites from Archive {args.archive}...")
        info = extract_sprite_frames(args.archive, args.disc, out_dir, args.scale)
        print(
            f"Extracted {info['total_frames_extracted']} frames across "
            f"{info['valid_sections']} sections to {out_dir}."
        )


if __name__ == "__main__":
    main()
