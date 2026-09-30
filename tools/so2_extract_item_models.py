"""Star Ocean: The Second Story (PS1) - Item 3D Model & Icon Extractor.

Extracts real in-game 3D models and textures for all 823 active items directly
from Disc 1 Archive 4489 (LBA 127166) using the sector table in Archive 3000 Section 2
(offset 0x38B8), renders each model to a high-quality 128x128 RGBA icon, and outputs
a comprehensive manifest.json.

Engine & Disassembly Provenance:
- Master Container: Archive 4489 (LBA 127166, 8,633 sectors)
- Sector Directory: Archive 3000, Section 2 (offset 0x38B8, 1023 x 4-byte entries)
- Sector Loader: 0x80088370..0x80088468 (Archive 3001)
- Two-Part SLZ Unpacker: 0x80088818..0x800888DC (Archive 3001)
- Mesh Header Parser & Linker: 0x800897C4..0x800898CC (Archive 3001)
- Texture & CLUT VRAM Loader: 0x800898CC..0x80089B94 (Archive 3001)
- 3D Transform & Rasterizer: 0x80088BA8..0x80088F40 (Archive 3001)
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import struct
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tools.so2_disc_code import archive_table, read_sectors, slz

DEFAULT_DISC_PATH = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")
DEFAULT_OUT_DIR = _ROOT / "artifacts" / "so2-items-sprites"
ITEM_DATABASE_PATH = _ROOT / "artifacts" / "so2-items" / "items_database.json"


def decompress_model_part2(part2_raw: bytes, part1_data: bytes) -> bytes:
    """Decompresses Part 2 3D mesh geometry.
    
    If version is 2, standard SLZ2 decompression is performed.
    If version is 1, SLZ1 decompression is performed with Part 1 pre-seeded into the
    sliding window output buffer as verified in PS1 heap memory at 0x80088858..0x800888C4.
    """
    version = part2_raw[3]
    if version == 2:
        return slz(part2_raw)
    elif version == 1:
        t0 = 16
        out = bytearray(part1_data)
        t1 = 0
        t2 = 1
        raw_len = len(part2_raw)
        while t0 < raw_len:
            t2 -= 1
            if t2 == 0:
                t2 = 8
                t1 = part2_raw[t0]
                t0 += 1
            else:
                t1 = (t1 >> 1) & 0xFF
            if t1 & 1:
                if t0 >= raw_len:
                    break
                out.append(part2_raw[t0])
                t0 += 1
            else:
                if t0 + 1 >= raw_len:
                    break
                b0 = part2_raw[t0]
                b1 = part2_raw[t0 + 1]
                v1 = ((b1 & 0x0F) << 8) | b0
                if v1 == 0:
                    break
                length = (b1 >> 4) + 3
                for _ in range(length):
                    out.append(out[-v1])
                t0 += 2
        return bytes(out[len(part1_data):])
    else:
        raise ValueError(f"Unsupported Part 2 compression version: {version}")


def render_mesh_to_image(
    mesh: bytes,
    pitch_deg: float = -20.0,
    yaw_deg: float = 35.0,
    size: int = 128
) -> Tuple[Image.Image, Dict[str, Any]]:
    """Renders a Star Ocean 2 3D mesh to an RGBA Image using a software rasterizer."""
    words = struct.unpack_from("<8I", mesh, 0)
    off_faces = words[0]
    off_verts = words[1]
    off_cols  = words[4]  # offset 0x10 in mesh header: color array
    off_uvs   = words[5]  # offset 0x14 in mesh header: UV array
    fc, vc    = struct.unpack_from("<2H", mesh, 0x1C)
    uv_c      = struct.unpack_from("<H", mesh, 0x26)[0]

    # TIM image pixel data begins at 0x220 (offset 8 + clut_bnum 0x20C + 12-byte image chunk header)
    # as verified in PS1 Archive 3001 disassembly at 0x80089A2C: addiu $a2, $s1, 0xc
    has_texture = (words[6] != 0 and words[6] + 0x220 + 16384 <= len(mesh))
    if has_texture:
        sub = mesh[words[6]:]
        pal_bytes = sub[0x14:0x214]
        pal_words = struct.unpack_from("<256H", pal_bytes, 0)
        pal_rgba = np.zeros((256, 4), dtype=np.uint8)
        for i, w in enumerate(pal_words):
            if i == 0 and w == 0:
                pal_rgba[i] = [0, 0, 0, 0]
            else:
                r = ((w & 0x1F) * 255) // 31
                g = (((w >> 5) & 0x1F) * 255) // 31
                b = (((w >> 10) & 0x1F) * 255) // 31
                pal_rgba[i] = [r, g, b, 255]
        tex_raw = np.frombuffer(sub[0x220 : 0x220 + 16384], dtype=np.uint8).reshape((128, 128))
        tex_img = pal_rgba[tex_raw]
    else:
        tex_img = None

    raw_v = struct.unpack_from(f"<{vc*4}h", mesh, off_verts)
    verts = np.array([(raw_v[i*4], raw_v[i*4+1], raw_v[i*4+2]) for i in range(vc)], dtype=np.float32)

    raw_uv = struct.unpack_from(f"<{uv_c*2}B", mesh, off_uvs)
    uvs = np.array([(raw_uv[i*2], raw_uv[i*2+1]) for i in range(uv_c)], dtype=np.float32)

    # Center and normalize coordinates
    v_min = verts.min(axis=0)
    v_max = verts.max(axis=0)
    center = (v_min + v_max) / 2.0
    verts_c = verts - center
    extent = float((v_max - v_min).max())
    if extent <= 1e-4:
        extent = 1.0

    # Apply 3D rotation (pitch around X, yaw around Y)
    rad_pitch = np.radians(pitch_deg)
    rad_yaw = np.radians(yaw_deg)
    rx = np.array([
        [1, 0, 0],
        [0, np.cos(rad_pitch), -np.sin(rad_pitch)],
        [0, np.sin(rad_pitch), np.cos(rad_pitch)]
    ], dtype=np.float32)
    ry = np.array([
        [np.cos(rad_yaw), 0, np.sin(rad_yaw)],
        [0, 1, 0],
        [-np.sin(rad_yaw), 0, np.cos(rad_yaw)]
    ], dtype=np.float32)
    rot = rx @ ry
    verts_rot = (rot @ verts_c.T).T

    scale = (size * 0.40) / (extent / 2.0)
    verts_2d = np.zeros((vc, 2), dtype=np.float32)
    verts_2d[:, 0] = size / 2.0 + verts_rot[:, 0] * scale
    verts_2d[:, 1] = size / 2.0 + verts_rot[:, 1] * scale
    depths = verts_rot[:, 2]

    framebuffer = np.zeros((size, size, 4), dtype=np.uint8)
    zbuffer = np.full((size, size), -1e9, dtype=np.float32)

    # Directional light source
    light = np.array([0.4, -0.7, -0.6], dtype=np.float32)
    light /= np.linalg.norm(light)

    for i in range(fc):
        f_off = off_faces + i * 32
        v0, v1, v2 = struct.unpack_from("<3H", mesh, f_off + 2)
        uv0, uv1, uv2 = struct.unpack_from("<3H", mesh, f_off + 0x1A)

        p0 = verts_2d[v0]; p1 = verts_2d[v1]; p2 = verts_2d[v2]
        z0 = depths[v0]; z1 = depths[v1]; z2 = depths[v2]

        v_orig0 = verts_rot[v0]; v_orig1 = verts_rot[v1]; v_orig2 = verts_rot[v2]
        norm = np.cross(v_orig1 - v_orig0, v_orig2 - v_orig0)
        norm_len = float(np.linalg.norm(norm))
        if norm_len > 1e-6:
            norm /= norm_len
            diffuse = max(0.25, abs(float(np.dot(norm, light))) * 0.75 + 0.25)
        else:
            diffuse = 0.75

        min_x = max(0, int(np.floor(min(p0[0], p1[0], p2[0]))))
        max_x = min(size - 1, int(np.ceil(max(p0[0], p1[0], p2[0]))))
        min_y = max(0, int(np.floor(min(p0[1], p1[1], p2[1]))))
        max_y = min(size - 1, int(np.ceil(max(p0[1], p1[1], p2[1]))))

        if min_x > max_x or min_y > max_y:
            continue
        denom = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(denom) < 1e-5:
            continue
        inv_denom = 1.0 / denom

        is_textured = (has_texture and uv0 != 0xFFFF and uv0 < uv_c and uv1 < uv_c and uv2 < uv_c)
        if is_textured:
            t_uv0 = uvs[uv0]; t_uv1 = uvs[uv1]; t_uv2 = uvs[uv2]
        else:
            c_idx = struct.unpack_from("<H", mesh, f_off + 0x14)[0]
            if c_idx != 0xFFFF and off_cols + c_idx * 4 + 4 <= len(mesh):
                f_col = struct.unpack_from("<4B", mesh, off_cols + c_idx * 4)
            else:
                f_col = (200, 200, 200, 255)

        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                w0 = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (py - p2[1])) * inv_denom
                w1 = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (py - p2[1])) * inv_denom
                w2 = 1.0 - w0 - w1
                if w0 >= -1e-3 and w1 >= -1e-3 and w2 >= -1e-3:
                    pz = w0 * z0 + w1 * z1 + w2 * z2
                    if pz > zbuffer[py, px]:
                        if is_textured:
                            tu = int(round(w0 * t_uv0[0] + w1 * t_uv1[0] + w2 * t_uv2[0])) % 128
                            tv = int(round(w0 * t_uv0[1] + w1 * t_uv1[1] + w2 * t_uv2[1])) % 128
                            col = tex_img[tv, tu].copy()
                            if col[3] > 0:
                                zbuffer[py, px] = pz
                                col[:3] = np.clip(col[:3] * diffuse, 0, 255).astype(np.uint8)
                                framebuffer[py, px] = col
                        else:
                            zbuffer[py, px] = pz
                            c = np.clip(np.array(f_col[:3], dtype=np.float32) * diffuse, 0, 255).astype(np.uint8)
                            framebuffer[py, px] = [c[0], c[1], c[2], 255]

    meta = {
        "face_count": fc,
        "vert_count": vc,
        "uv_count": uv_c,
        "has_custom_texture": has_texture,
        "texture_width": 128 if has_texture else 0,
        "texture_height": 128 if has_texture else 0,
        "palette_colors": 256 if has_texture else 0
    }
    return Image.fromarray(framebuffer, "RGBA"), meta


def _worker_process_item(args: Tuple[int, str, int, int, int, int, str, str, int]) -> Optional[Dict[str, Any]]:
    iid, iname, sec_off, sec_cnt, lba89, arc_id, disc_path_str, out_dir_str, size = args
    if sec_cnt == 0:
        return None

    disc_path = Path(disc_path_str)
    out_dir = Path(out_dir_str)

    with open(disc_path, "rb") as f:
        raw = read_sectors(f, lba89 + sec_off, sec_cnt * 2048)

    part1 = slz(raw)
    comp_sz = struct.unpack_from("<I", raw, 4)[0]
    part2_off = 16 + ((comp_sz + 3) & ~3)
    part2_raw = raw[part2_off:]
    mesh = decompress_model_part2(part2_raw, part1)

    img, meta = render_mesh_to_image(mesh, pitch_deg=-20.0, yaw_deg=35.0, size=size)
    filename = f"item_{iid:04d}_icon.png"
    out_path = out_dir / filename
    img.save(out_path)

    manifest_entry = {
        "id": iid,
        "filename": filename,
        "item_name": iname,
        "archive_id": arc_id,
        "archive_lba": lba89,
        "sector_offset": sec_off,
        "sector_count": sec_cnt,
        "sector_lba": lba89 + sec_off,
        "byte_offset_on_disc": (lba89 + sec_off) * 2352 + 24,
        **meta
    }
    return manifest_entry


def extract_all_items(
    disc_path: Path = DEFAULT_DISC_PATH,
    out_dir: Path = DEFAULT_OUT_DIR,
    size: int = 128,
    workers: Optional[int] = None
) -> Dict[str, Any]:
    """Extracts, decompresses, and renders all 823 active items from Star Ocean 2 Disc 1."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load item names from items_database.json if present
    item_names = {}
    if ITEM_DATABASE_PATH.exists():
        with open(ITEM_DATABASE_PATH, "r", encoding="utf-8") as f:
            db_data = json.load(f)
            for it in db_data.get("items", []):
                item_names[it["id"]] = it.get("name", f"Item_{it['id']}")

    print(f"Reading master archives from {disc_path}...")
    with open(disc_path, "rb") as f:
        entries = {eid: (lba, sz) for eid, lba, sz in archive_table(f)}
        lba00, sz00 = entries[3000]
        arc3000 = slz(read_sectors(f, lba00, sz00))
        table_off = struct.unpack_from("<I", arc3000, 8)[0]
        lba89, sz89 = entries[4489]

        tasks = []
        for iid in range(1, 824):
            sec_off, sec_cnt = struct.unpack_from("<2H", arc3000, table_off + (iid - 1) * 4)
            iname = item_names.get(iid, f"Item_{iid:04d}")
            tasks.append((iid, iname, sec_off, sec_cnt, lba89, 4489, str(disc_path), str(out_dir), size))

    worker_count = workers or max(1, min(os.cpu_count() or 4, 12))
    print(f"Rendering all 823 item 3D models with {worker_count} worker processes...")

    start_time = time.time()
    manifest: Dict[str, Any] = {
        "title": "Star Ocean 2 (PS1) - Item 3D Graphics Manifest",
        "archive_container": 4489,
        "archive_lba": lba89,
        "directory_table_archive": 3000,
        "directory_section_offset": table_off,
        "total_active_items": len(tasks),
        "items": {}
    }

    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        for res in executor.map(_worker_process_item, tasks):
            if res:
                manifest["items"][str(res["id"])] = res
                if len(manifest["items"]) % 100 == 0 or len(manifest["items"]) == len(tasks):
                    print(f"  Processed {len(manifest['items'])} / {len(tasks)} items...")

    elapsed = time.time() - start_time
    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Done! Extracted and rendered {len(manifest['items'])} items in {elapsed:.2f}s.")
    print(f"Icons saved to: {out_dir}")
    print(f"Manifest saved to: {manifest_path}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Star Ocean 2 Item 3D Model & Icon Extractor")
    parser.add_argument("--disc", type=Path, default=DEFAULT_DISC_PATH, help="Path to Disc 1 .bin")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory")
    parser.add_argument("--size", type=int, default=128, help="Icon canvas size in pixels (default 128)")
    parser.add_argument("--workers", type=int, default=None, help="Worker process count")
    args = parser.parse_args()

    extract_all_items(args.disc, args.out_dir, args.size, args.workers)
