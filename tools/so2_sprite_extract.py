"""Star Ocean: The Second Story (PS1) - Battle Sprite Extractor.

Extracts 4bpp (16-color) character and monster battle sprite frames from
tri-Ace combat graphic archives (Archives 3111..3207) on Disc 1.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Tuple

from PIL import Image

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tools.so2_disc_code import archive_table, read_sectors, slz

DEFAULT_DISC = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")


def extract_sprite_frames(
    archive_id: int,
    disc_path: Path = DEFAULT_DISC,
    output_dir: Path | None = None,
    scale: int = 2
) -> List[Tuple[int, int, int, int, int]]:
    """Extract all 4bpp sprite frames from a battle archive."""
    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))
        if archive_id not in tbl:
            raise ValueError(f"Archive {archive_id} not found in archive table.")
        raw = read_sectors(f, tbl[archive_id][0], tbl[archive_id][1])
        data = slz(raw) if raw[:3] == b"SLZ" else raw

    base = 0x18
    p3 = base + 0x1B4
    if p3 + 12 > len(data):
        raise ValueError(f"Archive {archive_id} does not contain standard battle sprite container.")

    hdr_sz, pix_rel_off, unk, frame_count = struct.unpack("<IIHH", data[p3:p3 + 12])
    pix_start = p3 + pix_rel_off

    # Detect descriptor layout:
    # Variant A: [w (>H), h (<H), px (<H), py (<H), offset (<I)]
    # Variant B: [px (<H), py (<H), offset (<I), w (>H), h (<H)]
    layout_b = False
    if frame_count > 1 and p3 + 24 <= len(data):
        # Check if frame 1 offset is at pos+4 or pos+8
        off_at_4 = struct.unpack("<I", data[p3 + 24 + 4 : p3 + 24 + 8])[0]
        if 0 < off_at_4 < len(data):
            layout_b = True

    entries: List[Tuple[int, int, int, int, int]] = []
    pos = p3 + 12
    for _ in range(frame_count):
        if pos + 12 > len(data):
            break
        if layout_b:
            px, py, off = struct.unpack("<HHI", data[pos:pos + 8])
            w = struct.unpack(">H", data[pos + 8:pos + 10])[0]
            h = struct.unpack("<H", data[pos + 10:pos + 12])[0]
        else:
            w = struct.unpack(">H", data[pos:pos + 2])[0]
            h, px, py, off = struct.unpack("<HHHI", data[pos + 2:pos + 12])

        if 0 < w < 512 and 0 < h < 512:
            entries.append((w, h, px, py, off))
        pos += 12

    if output_dir is not None and entries:
        output_dir.mkdir(parents=True, exist_ok=True)
        for i, (w, h, px, py, off) in enumerate(entries):
            bpr = w // 2
            frame_bytes = data[pix_start + off : pix_start + off + bpr * h]
            if len(frame_bytes) < bpr * h:
                continue

            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            pix = im.load()
            for y in range(h):
                for x in range(0, w, 2):
                    b = frame_bytes[y * bpr + x // 2]
                    c0 = b & 0x0F
                    c1 = (b >> 4) & 0x0F
                    if c0 != 0:
                        val = c0 * 17
                        pix[x, y] = (val, val, val, 255)
                    if c1 != 0:
                        val = c1 * 17
                        pix[x + 1, y] = (val, val, val, 255)

            if scale > 1:
                im = im.resize((w * scale, h * scale), Image.NEAREST)
            im.save(output_dir / f"arc{archive_id:04d}_frame_{i:02d}.png")

    return entries


def extract_all_sprites(
    disc_path: Path = DEFAULT_DISC,
    output_base: Path | None = None,
    scale: int = 2
) -> Dict[str, Any]:
    """Scan and batch extract all combat sprite archives on Disc 1."""
    if output_base is None:
        output_base = _ROOT / "artifacts" / "so2-sprites"
    output_base.mkdir(parents=True, exist_ok=True)

    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))

    catalog: Dict[str, Any] = {
        "disc": 1,
        "total_archives_scanned": len(range(3111, 3208)),
        "archives": {}
    }

    print("Scanning archives 3111..3207 for battle sprites...")
    for idx in range(3111, 3208):
        if idx not in tbl:
            continue
        try:
            # Probe without saving
            frames = extract_sprite_frames(idx, disc_path, None, scale)
            if len(frames) >= 10 and frames[0][0] >= 16 and frames[0][1] >= 16:
                arc_dir = output_base / f"archive_{idx:04d}"
                # Full extraction
                extract_sprite_frames(idx, disc_path, arc_dir, scale)
                catalog["archives"][str(idx)] = {
                    "archive_id": idx,
                    "frame_count": len(frames),
                    "dimensions": f"{frames[0][0]}x{frames[0][1]}",
                    "pivot": f"{frames[0][2]},{frames[0][3]}",
                    "output_dir": str(arc_dir)
                }
                print(f"  [+] Archive {idx:04d}: Extracted {len(frames):2d} frames ({frames[0][0]}x{frames[0][1]}) -> {arc_dir.name}/")
        except Exception:
            continue

    cat_json = output_base / "sprites_catalog.json"
    import json
    cat_json.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"\nBatch sprite extraction complete! Extracted {len(catalog['archives'])} combat archives.")
    print(f"Catalog saved to {cat_json.name}")
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract SO2 PS1 combat sprites.")
    parser.add_argument("--archive", type=int, default=None, help="Specific Archive ID to extract (e.g. 3125)")
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

        print(f"Extracting battle sprites from Archive {args.archive}...")
        frames = extract_sprite_frames(args.archive, args.disc, out_dir, args.scale)
        print(f"Extracted {len(frames)} frames to {out_dir}:")
        for i, (w, h, px, py, off) in enumerate(frames):
            print(f"  Frame {i:2d}: {w:3d}x{h:3d} (pivot: {px:2d},{py:2d}) @ offset 0x{off:04X}")


if __name__ == "__main__":
    main()
