"""Star Ocean: The Second Story (PS1) - 2D Field Scene NPC Sprite Extractor.

Extracts 2D field NPC sprites, dungeon creatures, and interactable entity frames
from scene container archives (Archives 3207..4154) across Disc 1 and Disc 2.

In scene containers (tag == 2), NPC sprite banks are packaged as dynamic multi-section
containers containing a mode-dependent 12/16-byte header, 12-byte frame descriptors,
16-color BGR555 CLUT palettes,
and 4bpp indexed pixel streams.

Outputs extracted PNG frames to artifacts/so2-sprites/scene_<id>/.
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

DEFAULT_DISC1 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")
DEFAULT_DISC2 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
OUT_BASE = _ROOT / "artifacts" / "so2-sprites"


def extract_scene_npc_sprites(
    disc_path: Path,
    archive_id: int,
    scale: int = 1,
    out_dir: Optional[Path] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """Extract all 2D NPC sprite sections from tag == 2 of a scene container archive."""
    if out_dir is None:
        out_dir = OUT_BASE / f"scene_{archive_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))
        if archive_id not in tbl:
            raise ValueError(f"Archive {archive_id} not found in disc archive table.")

        lba, sz = tbl[archive_id]
        raw = read_sectors(f, lba, sz)

    if len(raw) < 12:
        return {"error": "Archive too small", "sections": []}

    num_parts = struct.unpack_from("<I", raw, 0)[0]
    if num_parts > 30:
        return {"error": f"Invalid scene container parts count: {num_parts}", "sections": []}

    tag2_offset = None
    for p in range(num_parts):
        tag, off = struct.unpack_from("<2I", raw, 4 + 8 * p)
        if tag == 2:
            tag2_offset = off
            break

    if tag2_offset is None or tag2_offset >= len(raw):
        if verbose:
            print(f"Archive {archive_id}: No tag == 2 (NPC Sprite Bank) found.")
        return {"archive_id": archive_id, "has_tag2": False, "sections": []}

    dec = slz(raw[tag2_offset:])
    if len(dec) < 8:
        return {"archive_id": archive_id, "has_tag2": True, "error": "Dec payload too small", "sections": []}

    num_sec = struct.unpack_from("<I", dec, 0)[0]
    if num_sec == 0 or num_sec > 100:
        return {"archive_id": archive_id, "has_tag2": True, "error": f"Invalid section count: {num_sec}", "sections": []}

    sec_offsets = [struct.unpack_from("<I", dec, 4 + 4 * i)[0] for i in range(num_sec)]

    results: Dict[str, Any] = {
        "archive_id": archive_id,
        "num_sections": num_sec,
        "extracted_frames": 0,
        "sections": []
    }

    total_frames = 0
    for s_idx, soff in enumerate(sec_offsets):
        if soff + 0x20 > len(dec):
            continue

        rec_count, selector = struct.unpack_from("<2I", dec, soff)
        a_off = struct.unpack_from("<I", dec, soff + 0x18)[0]
        sptr = struct.unpack_from("<I", dec, soff + 0x1C)[0]
        mode = dec[soff + a_off + 2] if soff + a_off + 3 <= len(dec) else 1
        hdr_len = 12 if mode == 1 else 16
        p3 = soff + sptr
        if p3 + hdr_len > len(dec):
            continue

        hsz, preloff, unk, fc = struct.unpack("<IIHH", dec[p3 : p3 + 12])
        if fc == 0 or fc > 256:
            continue

        pix_start = p3 + preloff
        desc_end = p3 + hdr_len + fc * 12
        if desc_end + 36 > len(dec):
            continue

        pal_len = preloff - hsz
        is_8bpp = (pal_len >= 512)
        if desc_end + 4 > len(dec):
            continue
        color_count = struct.unpack_from("<I", dec, desc_end)[0]
        num_colors = 256 if is_8bpp else color_count

        # Extract CLUT palette words
        if desc_end + 4 + num_colors * 2 > len(dec):
            continue
        all_pal_words = struct.unpack_from(f"<{num_colors}H", dec, desc_end + 4)
        num_rows = max(1, color_count // 16)

        sec_info = {
            "section_index": s_idx,
            "selector_id": selector,
            "mode": mode,
            "bpp": 8 if is_8bpp else 4,
            "color_count": color_count,
            "palette_rows": num_rows if not is_8bpp else 1,
            "frame_count": fc,
            "extracted_count": 0,
            "frames": []
        }

        for f_idx in range(fc):
            pos = p3 + hdr_len + f_idx * 12
            if pos + 12 > len(dec):
                break

            flags, w, h, res = struct.unpack("4B", dec[pos : pos + 4])
            px, py = struct.unpack("<2h", dec[pos + 4 : pos + 8])
            off = struct.unpack("<I", dec[pos + 8 : pos + 12])[0]

            if w == 0 or h == 0 or w > 256 or h > 256:
                continue

            bpr = w if is_8bpp else (w // 2)
            f_start = pix_start + off
            f_end = f_start + bpr * h
            if f_end > len(dec):
                continue

            f_bytes = dec[f_start:f_end]
            if not f_bytes or all(b == 0 for b in f_bytes):
                continue

            if is_8bpp:
                exp = f_bytes
                pal_words = all_pal_words[:256]
                pal_row = 0
            else:
                exp = bytearray(w * h)
                for i, b in enumerate(f_bytes):
                    exp[i * 2] = b & 0x0F
                    exp[i * 2 + 1] = (b >> 4) & 0x0F
                # desc[0] (flags) is the 16-color palette row selector (verified at 0x80042068/0x8004215C)
                pal_row = flags if flags < num_rows else 0
                pal_words = all_pal_words[pal_row * 16 : (pal_row + 1) * 16]

            palette_rgb = []
            for pw in pal_words:
                r = (pw & 0x1F) << 3
                g = ((pw >> 5) & 0x1F) << 3
                b = ((pw >> 10) & 0x1F) << 3
                palette_rgb.extend([r, g, b])
            while len(palette_rgb) < 768:
                palette_rgb.extend([0, 0, 0])

            img = Image.frombytes("P", (w, h), bytes(exp))
            img.putpalette(palette_rgb)
            rgba = img.convert("RGBA")

            # Transparency for color index 0 (transparent background)
            rgba_bytes = bytearray(rgba.tobytes())
            for idx in range(0, len(rgba_bytes), 4):
                if exp[idx // 4] == 0:
                    rgba_bytes[idx + 3] = 0
            rgba = Image.frombytes("RGBA", (w, h), bytes(rgba_bytes))

            if scale > 1:
                rgba = rgba.resize((w * scale, h * scale), Image.NEAREST)

            frame_fname = f"sec{s_idx:02d}_f{f_idx:02d}.png"
            frame_path = out_dir / frame_fname
            rgba.save(frame_path, "PNG")

            sec_info["frames"].append({
                "frame_index": f_idx,
                "palette_row": pal_row,
                "width": w,
                "height": h,
                "pivot_x": px,
                "pivot_y": py,
                "filename": frame_fname
            })
            sec_info["extracted_count"] += 1
            total_frames += 1

        if sec_info["extracted_count"] > 0:
            results["sections"].append(sec_info)

    results["extracted_frames"] = total_frames
    if verbose:
        print(f"Archive {archive_id}: Extracted {total_frames} frames across {len(results['sections'])} sections to {out_dir}")
    return results


def extract_all_scene_npcs(
    disc_path: Path,
    scale: int = 2,
    out_base: Optional[Path] = None,
    archive_range: Tuple[int, int] = (3207, 4155)
) -> Dict[str, Any]:
    """Batch-extract tag==2 NPC sprite banks across every scene archive in range."""
    if out_base is None:
        out_base = OUT_BASE
    out_base.mkdir(parents=True, exist_ok=True)

    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))

    catalog: Dict[str, Any] = {
        "archive_range": list(archive_range),
        "total_archives_scanned": 0,
        "total_archives_with_npc_sprites": 0,
        "total_frames_extracted": 0,
        "archives": {}
    }

    lo, hi = archive_range
    for arc_id in range(lo, hi):
        if arc_id not in tbl:
            continue
        catalog["total_archives_scanned"] += 1
        try:
            res = extract_scene_npc_sprites(
                disc_path, arc_id, scale=scale,
                out_dir=out_base / f"scene_{arc_id}", verbose=False
            )
        except Exception as e:
            print(f"  [-] Archive {arc_id}: skipped ({e})")
            continue

        if res.get("extracted_frames", 0) > 0:
            catalog["archives"][str(arc_id)] = {
                "num_sections": res["num_sections"],
                "extracted_frames": res["extracted_frames"],
                "section_count_with_sprites": len(res["sections"]),
            }
            catalog["total_archives_with_npc_sprites"] += 1
            catalog["total_frames_extracted"] += res["extracted_frames"]
            print(f"  [+] Archive {arc_id}: {res['extracted_frames']} frames across {len(res['sections'])} sections")

    cat_path = out_base / "scene_npc_catalog.json"
    cat_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"\nScanned {catalog['total_archives_scanned']} archives, "
          f"{catalog['total_archives_with_npc_sprites']} had NPC sprite banks, "
          f"{catalog['total_frames_extracted']} total frames extracted.")
    print(f"Catalog saved to {cat_path}")
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract 2D Scene NPC Sprites from Star Ocean 2")
    parser.add_argument("--archive", "-a", type=int, default=None, help="Scene Archive ID (single-archive mode)")
    parser.add_argument("--all", action="store_true", help="Batch extract across all scene archives (3207-4154)")
    parser.add_argument("--disc", "-d", type=int, choices=[1, 2], default=1, help="Disc number (1 or 2, default: 1)")
    parser.add_argument("--scale", "-s", type=int, default=2, help="Nearest-neighbor upscale factor (default: 2)")
    parser.add_argument("--out", "-o", type=Path, default=None, help="Output directory")
    args = parser.parse_args()

    disc_path = DEFAULT_DISC1 if args.disc == 1 else DEFAULT_DISC2
    if args.all or args.archive is None:
        extract_all_scene_npcs(disc_path, scale=args.scale, out_base=args.out)
    else:
        extract_scene_npc_sprites(disc_path, args.archive, scale=args.scale, out_dir=args.out)


if __name__ == "__main__":
    main()
