"""Extract SO2 terrain geometry from disc archives and cross-check save sightings.

Extracts:
  - Dungeon/field scenes (outside 1..3): 88-byte triangle records from type 0 asset.
  - Overworld scenes (1..3): streaming-cache 4x4 sub-cell meshes (packed triangles and quads).

Coordinates are emitted in both:
  - scaled units (X, Y, Z / 4096.0), matching the coordinate system in area_data.json.
  - raw integer units (PS1 grid units).

Outputs structured JSON to artifacts/so2-terrain-map/area_<id>_scene_<scene>.json.
No game instructions or emulators are executed. Read-only against discs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[1]
_TOOLS = _ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from so2_disc_code import archive_table, read_sectors, slz

DEFAULT_DISC1 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")
DEFAULT_DISC2 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
DEFAULT_OUT_DIR = _ROOT / "artifacts" / "so2-terrain-map"
DEFAULT_AREA_DATA = _ROOT / "area_data.json"

# Known scene mappings for sightings recorded before scene tracking was active
KNOWN_SIGHTING_SCENES: Dict[Tuple[str, str], int] = {
    ("0", "0sNone"): 2,
    ("0", "1sNone"): 1,
    ("118", "1sNone"): 704,
    ("128", "1sNone"): 671,
    ("140", "1sNone"): 751,
    ("148", "1sNone"): 716,
}


def unpack(data: bytes, offset: int, fmt: str) -> tuple:
    return struct.unpack_from("<" + fmt, data, offset)


def classify_normal(nx: float, ny: float, nz: float) -> Tuple[str, Tuple[float, float, float]]:
    """Classify polygon orientation based on surface normal."""
    norm = math.hypot(nx, ny, nz)
    if norm == 0.0:
        return "unknown", (0.0, 1.0, 0.0)
    ux, uy, uz = nx / norm, ny / norm, nz / norm
    if uy < 0:
        ux, uy, uz = -ux, -uy, -uz
    if uy > 0.999:
        cls = "floor"
    elif uy > 0.7071:
        cls = "slope"
    else:
        cls = "wall"
    return cls, (round(ux, 4), round(uy, 4), round(uz, 4))


# ---------------------------------------------------------------------------
# 2D Geometry & Distance Helpers
# ---------------------------------------------------------------------------

def pt_in_tri_2d(px: float, pz: float, p0: Tuple[float, float, float],
                 p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> bool:
    x0, z0 = p0[0], p0[2]
    x1, z1 = p1[0], p1[2]
    x2, z2 = p2[0], p2[2]

    d1 = (px - x1) * (z0 - z1) - (x0 - x1) * (pz - z1)
    d2 = (px - x2) * (z1 - z2) - (x1 - x2) * (pz - z2)
    d3 = (px - x0) * (z2 - z0) - (x2 - x0) * (pz - z0)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


def dist_pt_to_seg(px: float, pz: float, x1: float, z1: float, x2: float, z2: float) -> float:
    dx, dz = x2 - x1, z2 - z1
    if dx == 0.0 and dz == 0.0:
        return math.hypot(px - x1, pz - z1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (pz - z1) * dz) / (dx * dx + dz * dz)))
    proj_x = x1 + t * dx
    proj_z = z1 + t * dz
    return math.hypot(px - proj_x, pz - proj_z)


def dist_pt_to_tri_2d(px: float, pz: float, p0: Tuple[float, float, float],
                      p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    if pt_in_tri_2d(px, pz, p0, p1, p2):
        return 0.0
    return min(
        dist_pt_to_seg(px, pz, p0[0], p0[2], p1[0], p1[2]),
        dist_pt_to_seg(px, pz, p1[0], p1[2], p2[0], p2[2]),
        dist_pt_to_seg(px, pz, p2[0], p2[2], p0[0], p0[2]),
    )


def pt_in_quad_2d(px: float, pz: float, v0: Tuple[float, float, float],
                  v1: Tuple[float, float, float], v2: Tuple[float, float, float],
                  v3: Tuple[float, float, float]) -> bool:
    """A SO2 quad has vertices v0, v1, v2, v3 where v0..v1 is top edge and v2..v3 is bottom edge."""
    return pt_in_tri_2d(px, pz, v0, v1, v2) or pt_in_tri_2d(px, pz, v1, v3, v2)


def dist_pt_to_quad_2d(px: float, pz: float, v0: Tuple[float, float, float],
                       v1: Tuple[float, float, float], v2: Tuple[float, float, float],
                       v3: Tuple[float, float, float]) -> float:
    if pt_in_quad_2d(px, pz, v0, v1, v2, v3):
        return 0.0
    return min(
        dist_pt_to_tri_2d(px, pz, v0, v1, v2),
        dist_pt_to_tri_2d(px, pz, v1, v3, v2)
    )


# ---------------------------------------------------------------------------
# Disc Reader Cache
# ---------------------------------------------------------------------------

class DiscManager:
    def __init__(self, disc1_path: Path = DEFAULT_DISC1, disc2_path: Path = DEFAULT_DISC2):
        self.disc1_path = disc1_path
        self.disc2_path = disc2_path
        self._f1 = open(disc1_path, "rb") if disc1_path.exists() else None
        self._f2 = open(disc2_path, "rb") if disc2_path.exists() else None
        self._table1 = {i: (lba, sz) for i, lba, sz in archive_table(self._f1)} if self._f1 else {}
        self._table2 = {i: (lba, sz) for i, lba, sz in archive_table(self._f2)} if self._f2 else {}

    def close(self):
        if self._f1:
            self._f1.close()
        if self._f2:
            self._f2.close()

    def read_archive(self, entry_index: int, prefer_disc: int = 1) -> Tuple[bytes, int]:
        """Read archive entry by index. Returns (bytes, disc_num)."""
        discs = [(1, self._f1, self._table1), (2, self._f2, self._table2)]
        if prefer_disc == 2:
            discs.reverse()
        for dnum, handle, table in discs:
            if handle and entry_index in table:
                lba, sz = table[entry_index]
                data = read_sectors(handle, lba, sz)
                return data, dnum
        raise KeyError(f"Archive entry {entry_index} not found on available discs")


# ---------------------------------------------------------------------------
# Dungeon Geometry Decoding (Type 0 Asset)
# ---------------------------------------------------------------------------

def decode_dungeon_terrain(bundle_bytes: bytes) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Decode 88-byte triangle records from dungeon scene bundle."""
    count, = unpack(bundle_bytes, 0, "I")
    if count > 13:
        raise ValueError("Not a supported scene asset table")

    terrain_chunk = None
    for index in range(count):
        kind, offset = unpack(bundle_bytes, 4 + index * 8, "II")
        if kind == 0:
            source = bundle_bytes[offset:]
            if source[:3] != b"SLZ":
                raise ValueError("Type 0 lacks SLZ header")
            size, = unpack(source, 8, "I")
            terrain_chunk = source[16:16 + size] if source[3] == 0 else slz(source)
            break

    if terrain_chunk is None:
        return [], {"error": "No type-0 terrain asset found in bundle"}

    base, = unpack(terrain_chunk, 0x80, "I")
    tri_count, = unpack(terrain_chunk, base + 0x20, "H")
    relative, = unpack(terrain_chunk, base + 0x5C, "I")
    start = base + relative

    polygons: List[Dict[str, Any]] = []
    for idx in range(tri_count):
        off = start + idx * 88
        bounds_raw = unpack(terrain_chunk, off, "6h")
        enabled = terrain_chunk[off + 12]
        v0 = unpack(terrain_chunk, off + 16, "3h")
        v1 = unpack(terrain_chunk, off + 24, "3h")
        v2 = unpack(terrain_chunk, off + 32, "3h")
        plane_ABC = unpack(terrain_chunk, off + 48, "3i")
        field22 = terrain_chunk[off + 84]

        cls, norm = classify_normal(plane_ABC[0], plane_ABC[1], plane_ABC[2])

        v_raw = [list(v0), list(v1), list(v2)]
        v_scaled = [[round(coord / 4096.0, 4) for coord in v] for v in v_raw]

        polygons.append({
            "index": idx,
            "type": "triangle",
            "classification": cls,
            "surface_flag": field22,
            "enabled": enabled,
            "plane_ABC": list(plane_ABC),
            "normal": list(norm),
            "bounds_raw": {
                "y_min": bounds_raw[0], "y_max": bounds_raw[1],
                "x_min": bounds_raw[2], "z_min": bounds_raw[3],
                "x_max": bounds_raw[4], "z_max": bounds_raw[5],
            },
            "raw_vertices": v_raw,
            "vertices": v_scaled,
        })

    meta = {
        "terrain_byte_length": len(terrain_chunk),
        "terrain_sha256": hashlib.sha256(terrain_chunk).hexdigest(),
        "TB_offset": base,
        "triangle_array_offset": start,
        "polygon_count": len(polygons),
    }
    return polygons, meta


# ---------------------------------------------------------------------------
# Overworld Geometry Decoding (Type 3 Streaming Cache & 4x4 Subcells)
# ---------------------------------------------------------------------------

def extract_overworld_cache(bundle_bytes: bytes) -> Dict[int, bytes]:
    """Parse Type 3 tagged stream (Tag 5) and return dict of {cell_id: decompressed_chunk_bytes}."""
    base = 20  # asset 0 payload
    p = base
    chunks: Dict[int, bytes] = {}
    while p + 4 <= len(bundle_bytes):
        tag = int.from_bytes(bundle_bytes[p:p + 4], "little")
        p += 4
        if tag == 0:
            break
        if tag in (1, 2, 6, 7):
            p += 8
        elif tag == 3:
            p += 4
            while p + 4 <= len(bundle_bytes) and int.from_bytes(bundle_bytes[p:p + 4], "little"):
                p += 12
            p += 4
        elif tag in (4, 5):
            off = int.from_bytes(bundle_bytes[p:p + 4], "little")
            p += 4
            if tag == 5:
                q = base + off
                for _ in range(9):
                    cell = int.from_bytes(bundle_bytes[q:q + 4], "little", signed=True)
                    q += 4
                    if cell == -1:
                        continue
                    rel = int.from_bytes(bundle_bytes[q:q + 4], "little")
                    q += 4
                    src = bundle_bytes[base + rel:]
                    csize = int.from_bytes(src[8:12], "little")
                    out = src[16:16 + csize] if src[3] == 0 else slz(src)
                    chunks[cell] = out
    return chunks


def decode_overworld_chunk(chunk_bytes: bytes, cell_id: int) -> List[Dict[str, Any]]:
    """Decode all sub-cell polygons for one 12288x12288 overworld cell chunk."""
    V = struct.unpack_from("<I", chunk_bytes, 0)[0]
    subcell_v_offsets = [struct.unpack_from("<I", chunk_bytes, 0x28 + 4 * i)[0] for i in range(16)]
    table_base = 0x68 + V * 8

    cell_x = cell_id % 9
    cell_z = cell_id // 9
    world_origin_x = cell_x * 12288 + 6144
    world_origin_z = cell_z * 12288 + 6144

    polygons: List[Dict[str, Any]] = []

    for sub_idx in range(16):
        hdr = struct.unpack_from("<16H", chunk_bytes, table_base + sub_idx * 32)
        P = hdr[0]
        if P == 0:
            continue
        poly_data_rel = struct.unpack_from("<I", chunk_bytes, table_base + 0x200 + sub_idx * 4)[0]
        poly_base = table_base + 0x280 + poly_data_rel
        v_base = 0x68 + subcell_v_offsets[sub_idx]

        attrs = chunk_bytes[poly_base:poly_base + P]
        cur = poly_base + ((P + 3) & ~3)

        def read_v(off: int) -> Tuple[List[float], List[int]]:
            h0, y, z, x = struct.unpack_from("<4h", chunk_bytes, v_base + off)
            wx = world_origin_x + x
            wy = y
            wz = world_origin_z + z
            return [round(wx / 4096.0, 4), round(wy / 4096.0, 4), round(wz / 4096.0, 4)], [wx, wy, wz]

        # Pool 3: Packed triangles (16 bytes)
        c3 = hdr[3]
        for i in range(c3):
            w0, w1, w2, w3 = struct.unpack_from("<4I", chunk_bytes, cur + i * 16)
            v0_off = ((w1 >> 14) & 0x3FC) << 1
            v1_off = ((w0 >> 22) & 0x3FC) << 1
            v2_off = ((w1 >> 22) & 0x3FC) << 1
            sv0, rv0 = read_v(v0_off)
            sv1, rv1 = read_v(v1_off)
            sv2, rv2 = read_v(v2_off)

            # Compute normal via cross product
            ax, ay, az = rv1[0] - rv0[0], rv1[1] - rv0[1], rv1[2] - rv0[2]
            bx, by, bz = rv2[0] - rv0[0], rv2[1] - rv0[1], rv2[2] - rv0[2]
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            cls, norm = classify_normal(nx, ny, nz)

            attr = attrs[len(polygons) % P] if attrs else 0
            polygons.append({
                "index": len(polygons),
                "type": "triangle",
                "pool": 3,
                "cell": cell_id,
                "subcell": sub_idx,
                "classification": cls,
                "surface_flag": attr,
                "normal": list(norm),
                "raw_vertices": [rv0, rv1, rv2],
                "vertices": [sv0, sv1, sv2],
            })
        cur += c3 * 16

        # Pool 4: Packed triangles (16 bytes)
        c4 = hdr[4]
        for i in range(c4):
            w0, w1, w2, w3 = struct.unpack_from("<4I", chunk_bytes, cur + i * 16)
            v0_off = (w1 & 0x3FC) << 1
            v1_off = ((w0 >> 16) & 0x3FC) << 1
            v2_off = ((w1 >> 16) & 0x3FC) << 1
            sv0, rv0 = read_v(v0_off)
            sv1, rv1 = read_v(v1_off)
            sv2, rv2 = read_v(v2_off)

            ax, ay, az = rv1[0] - rv0[0], rv1[1] - rv0[1], rv1[2] - rv0[2]
            bx, by, bz = rv2[0] - rv0[0], rv2[1] - rv0[1], rv2[2] - rv0[2]
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            cls, norm = classify_normal(nx, ny, nz)

            attr = attrs[len(polygons) % P] if attrs else 0
            polygons.append({
                "index": len(polygons),
                "type": "triangle",
                "pool": 4,
                "cell": cell_id,
                "subcell": sub_idx,
                "classification": cls,
                "surface_flag": attr,
                "normal": list(norm),
                "raw_vertices": [rv0, rv1, rv2],
                "vertices": [sv0, sv1, sv2],
            })
        cur += c4 * 16

        # Pool 7: Packed quads (20 bytes)
        c7 = hdr[7]
        for i in range(c7):
            w4 = struct.unpack_from("<I", chunk_bytes, cur + i * 20 + 16)[0]
            v0_off = ((w4 << 2) & 0x3FC) << 1
            v1_off = ((w4 >> 6) & 0x3FC) << 1
            v2_off = ((w4 >> 14) & 0x3FC) << 1
            v3_off = ((w4 >> 22) & 0x3FC) << 1
            sv0, rv0 = read_v(v0_off)
            sv1, rv1 = read_v(v1_off)
            sv2, rv2 = read_v(v2_off)
            sv3, rv3 = read_v(v3_off)

            ax, ay, az = rv1[0] - rv0[0], rv1[1] - rv0[1], rv1[2] - rv0[2]
            bx, by, bz = rv2[0] - rv0[0], rv2[1] - rv0[1], rv2[2] - rv0[2]
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            cls, norm = classify_normal(nx, ny, nz)

            attr = attrs[len(polygons) % P] if attrs else 0
            polygons.append({
                "index": len(polygons),
                "type": "quad",
                "pool": 7,
                "cell": cell_id,
                "subcell": sub_idx,
                "classification": cls,
                "surface_flag": attr,
                "normal": list(norm),
                "raw_vertices": [rv0, rv1, rv2, rv3],
                "vertices": [sv0, sv1, sv2, sv3],
            })
        cur += c7 * 20

        # Pool 9: Packed quads (16 bytes)
        c9 = hdr[9]
        for i in range(c9):
            w3 = struct.unpack_from("<I", chunk_bytes, cur + i * 16 + 12)[0]
            v0_off = ((w3 << 2) & 0x3FC) << 1
            v1_off = ((w3 >> 6) & 0x3FC) << 1
            v2_off = ((w3 >> 14) & 0x3FC) << 1
            v3_off = ((w3 >> 22) & 0x3FC) << 1
            sv0, rv0 = read_v(v0_off)
            sv1, rv1 = read_v(v1_off)
            sv2, rv2 = read_v(v2_off)
            sv3, rv3 = read_v(v3_off)

            ax, ay, az = rv1[0] - rv0[0], rv1[1] - rv0[1], rv1[2] - rv0[2]
            bx, by, bz = rv2[0] - rv0[0], rv2[1] - rv0[1], rv2[2] - rv0[2]
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            cls, norm = classify_normal(nx, ny, nz)

            attr = attrs[len(polygons) % P] if attrs else 0
            polygons.append({
                "index": len(polygons),
                "type": "quad",
                "pool": 9,
                "cell": cell_id,
                "subcell": sub_idx,
                "classification": cls,
                "surface_flag": attr,
                "normal": list(norm),
                "raw_vertices": [rv0, rv1, rv2, rv3],
                "vertices": [sv0, sv1, sv2, sv3],
            })
        cur += c9 * 16

    return polygons


# ---------------------------------------------------------------------------
# Sighting Cross-Check Evaluation
# ---------------------------------------------------------------------------

def cross_check_sighting(sighting: Dict[str, Any], polygons: List[Dict[str, Any]],
                         is_overworld: bool = False) -> Dict[str, Any]:
    """Test whether sighting coordinates fall on or near the decoded geometry."""
    ref_hex = sighting.get("teleport_ref")
    if ref_hex:
        raw_x, raw_y, raw_z = struct.unpack_from("<iii", bytes.fromhex(ref_hex), 0)
    else:
        raw_x = int(round(sighting["x"] * 4096.0))
        raw_y = int(round(sighting["y"] * 4096.0))
        raw_z = int(round(sighting["z"] * 4096.0))

    pos_scaled = [sighting["x"], sighting["y"], sighting["z"]]
    pos_raw = [raw_x, raw_y, raw_z]

    if not polygons:
        return {
            "sighting_key": sighting.get("key", "unknown"),
            "first_seen_title": sighting.get("first_seen_title"),
            "position_scaled": pos_scaled,
            "position_raw": pos_raw,
            "contained": False,
            "min_distance_raw": None,
            "min_distance_scaled": None,
            "y_elevation_diff": None,
            "status": "no_triangles",
            "notes": "Scene contains 0 triangles in disc asset (empty hub)",
        }

    # Evaluate distance and containment
    min_dist = float("inf")
    hit_poly = None

    for p in polygons:
        rv = p["raw_vertices"]
        if p["type"] == "triangle":
            d = dist_pt_to_tri_2d(raw_x, raw_z, rv[0], rv[1], rv[2])
        else:
            d = dist_pt_to_quad_2d(raw_x, raw_z, rv[0], rv[1], rv[2], rv[3])

        if d < min_dist:
            min_dist = d
            if d == 0.0:
                hit_poly = p
                break

    contained = (min_dist == 0.0)
    y_diff = None

    if contained and hit_poly is not None:
        if not is_overworld:
            # Dungeon plane formula: objectY = Y0*4096 - (A*(objectX-X0*4096) + C*(objectZ-Z0*4096)) / B
            A, B, C = hit_poly["plane_ABC"]
            v0 = hit_poly["raw_vertices"][0]
            if B != 0:
                y_calc = v0[1] - (A * (raw_x - v0[0]) + C * (raw_z - v0[2])) / B
                y_diff = round(raw_y - y_calc, 2)
        else:
            # Overworld: average/quad plane elevation
            y_pts = [v[1] for v in hit_poly["raw_vertices"]]
            y_diff = round(raw_y - (sum(y_pts) / len(y_pts)), 2)

    # Status classification:
    # pass: strictly contained or within 2 raw grid units (< 0.0005 scaled)
    # close-but-off: within 200 raw grid units (< 0.05 scaled units)
    # fail: > 200 grid units away
    if min_dist <= 2.0:
        status = "pass"
    elif min_dist <= 200.0:
        status = "close-but-off"
    else:
        status = "fail"

    return {
        "sighting_key": sighting.get("key", "unknown"),
        "first_seen_title": sighting.get("first_seen_title"),
        "position_scaled": pos_scaled,
        "position_raw": pos_raw,
        "contained": contained,
        "min_distance_raw": round(min_dist, 2),
        "min_distance_scaled": round(min_dist / 4096.0, 4),
        "y_elevation_diff": y_diff,
        "status": status,
        "notes": f"Distance: {min_dist:.2f} raw grid units ({min_dist/4096.0:.4f} scaled units)",
    }


# ---------------------------------------------------------------------------
# Core Extraction Pipeline
# ---------------------------------------------------------------------------

def resolve_scene_archive(scene_id: int, cell_id: Optional[int] = None) -> int:
    """Resolve archive index for a given scene ID and optional overworld cell."""
    if scene_id == 1:
        cell = cell_id if cell_id is not None else 9
        return 0x1014 + cell
    elif scene_id == 2:
        cell = cell_id if cell_id is not None else 15
        return 0x109F + cell
    elif scene_id == 3:
        return 0x10E0
    else:
        return scene_id + 0xC87


def extract_area_scene(disc_mgr: DiscManager, area_id: int, scene_id: int,
                       sightings: List[Dict[str, Any]],
                       all_cache_cells: bool = False) -> Dict[str, Any]:
    """Extract geometry and cross-check for a single area and scene combination."""
    is_overworld = (scene_id in (1, 2, 3))

    if is_overworld:
        # Determine target cell from sightings if available
        target_cell = 9 if scene_id == 1 else (15 if scene_id == 2 else 0)
        for s in sightings:
            ref_hex = s.get("teleport_ref")
            if ref_hex:
                rx, _, rz = struct.unpack_from("<iii", bytes.fromhex(ref_hex), 0)
            else:
                rx = int(round(s["x"] * 4096.0))
                rz = int(round(s["z"] * 4096.0))
            cx = rx // 12288
            cz = rz // 12288
            target_cell = cx + 9 * cz
            break

        archive_idx = resolve_scene_archive(scene_id, target_cell)
        prefer_disc = 2 if scene_id == 2 else 1
        bundle_bytes, disc_num = disc_mgr.read_archive(archive_idx, prefer_disc=prefer_disc)

        cache = extract_overworld_cache(bundle_bytes)
        polygons: List[Dict[str, Any]] = []

        if all_cache_cells:
            for cid, chunk_data in sorted(cache.items()):
                polygons.extend(decode_overworld_chunk(chunk_data, cid))
        else:
            if target_cell in cache:
                polygons.extend(decode_overworld_chunk(cache[target_cell], target_cell))
            elif cache:
                first_cid = next(iter(cache.keys()))
                polygons.extend(decode_overworld_chunk(cache[first_cid], first_cid))

        meta: Dict[str, Any] = {
            "format": "overworld_mesh",
            "active_cell": target_cell,
            "available_cache_cells": sorted(list(cache.keys())),
            "polygon_count": len(polygons),
        }
    else:
        archive_idx = resolve_scene_archive(scene_id)
        bundle_bytes, disc_num = disc_mgr.read_archive(archive_idx, prefer_disc=1)
        polygons, meta = decode_dungeon_terrain(bundle_bytes)
        meta["format"] = "dungeon_triangles"

    # Compute bounding boxes across decoded polygons
    if polygons:
        all_raw_x = [v[0] for p in polygons for v in p["raw_vertices"]]
        all_raw_y = [v[1] for p in polygons for v in p["raw_vertices"]]
        all_raw_z = [v[2] for p in polygons for v in p["raw_vertices"]]
        bounds_raw = {
            "x_min": min(all_raw_x), "x_max": max(all_raw_x),
            "y_min": min(all_raw_y), "y_max": max(all_raw_y),
            "z_min": min(all_raw_z), "z_max": max(all_raw_z),
        }
        bounds_scaled = {
            "x_min": round(bounds_raw["x_min"] / 4096.0, 4),
            "x_max": round(bounds_raw["x_max"] / 4096.0, 4),
            "y_min": round(bounds_raw["y_min"] / 4096.0, 4),
            "y_max": round(bounds_raw["y_max"] / 4096.0, 4),
            "z_min": round(bounds_raw["z_min"] / 4096.0, 4),
            "z_max": round(bounds_raw["z_max"] / 4096.0, 4),
        }
    else:
        bounds_raw = {"x_min": None, "x_max": None, "y_min": None, "y_max": None, "z_min": None, "z_max": None}
        bounds_scaled = {"x_min": None, "x_max": None, "y_min": None, "y_max": None, "z_min": None, "z_max": None}

    # Cross-check each sighting
    cross_checks = [cross_check_sighting(s, polygons, is_overworld) for s in sightings]

    return {
        "area_id": area_id,
        "scene_id": scene_id,
        "archive_index": archive_idx,
        "disc": disc_num,
        "format_type": meta["format"],
        "metadata": {
            "polygon_count": len(polygons),
            "bounds_raw": bounds_raw,
            "bounds_scaled": bounds_scaled,
            **meta,
        },
        "polygons": polygons,
        "cross_checks": cross_checks,
    }


def load_area_data_sightings(area_data_path: Path = DEFAULT_AREA_DATA) -> Dict[Tuple[int, int], List[Dict[str, Any]]]:
    """Load area_data.json and group sightings by (area_id, resolved_scene_id)."""
    with area_data_path.open("r", encoding="utf-8") as f:
        db = json.load(f)

    groups: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}

    for aid_str, area in db.items():
        aid = int(aid_str)
        for sk, s in area.get("sightings", {}).items():
            sc = s.get("scene")
            if sc is None:
                sc = KNOWN_SIGHTING_SCENES.get((aid_str, sk))
                if sc is None:
                    continue
            s_copy = dict(s)
            s_copy["key"] = sk
            s_copy["area_id"] = aid
            s_copy["resolved_scene"] = sc
            groups.setdefault((aid, sc), []).append(s_copy)

    return groups


# ---------------------------------------------------------------------------
# CLI & Execution
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc1", type=Path, default=DEFAULT_DISC1, help="Path to Disc 1 bin")
    parser.add_argument("--disc2", type=Path, default=DEFAULT_DISC2, help="Path to Disc 2 bin")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory")
    parser.add_argument("--area", type=int, help="Extract specific area ID")
    parser.add_argument("--scene", type=int, help="Extract specific scene ID")
    parser.add_argument("--all", action="store_true", help="Extract all distinct area+scene pairs from area_data.json")
    parser.add_argument("--all-cache-cells", action="store_true", help="Include all 9 cache cells for overworld")
    parser.add_argument("--report", action="store_true", help="Print summary report to stdout")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    disc_mgr = DiscManager(args.disc1, args.disc2)

    sightings_by_pair = load_area_data_sightings()

    pairs_to_process = []
    if args.all or (args.area is None and args.scene is None):
        pairs_to_process = sorted(sightings_by_pair.keys())
    elif args.area is not None:
        if args.scene is not None:
            pairs_to_process = [(args.area, args.scene)]
        else:
            pairs_to_process = sorted([pair for pair in sightings_by_pair.keys() if pair[0] == args.area])
            if not pairs_to_process:
                raise ValueError(f"No recorded sightings for area {args.area}")
    else:
        raise ValueError("Must specify --all or --area")

    results = []
    for aid, sc in pairs_to_process:
        sightings = sightings_by_pair.get((aid, sc), [])
        data = extract_area_scene(disc_mgr, aid, sc, sightings, all_cache_cells=args.all_cache_cells)
        out_file = args.out_dir / f"area_{aid}_scene_{sc}.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        results.append(data)
        print(f"Wrote {out_file.name}: {len(data['polygons'])} polygons, {len(data['cross_checks'])} cross-checks")

    disc_mgr.close()

    if args.report or True:
        print("\n" + "=" * 80)
        print(f"{'Area':<6} {'Scene':<7} {'Polys':<7} {'Sighting':<10} {'Contained':<10} {'Min Dist':<12} {'Status':<15}")
        print("=" * 80)
        pass_count = 0
        close_count = 0
        fail_count = 0
        empty_count = 0
        total_sightings = 0

        for r in results:
            aid = r["area_id"]
            sc = r["scene_id"]
            poly_cnt = r["metadata"]["polygon_count"]
            for cc in r["cross_checks"]:
                total_sightings += 1
                sk = cc["sighting_key"]
                cont = "Yes" if cc["contained"] else "No"
                d_str = f"{cc['min_distance_raw']:.1f} grid" if cc["min_distance_raw"] is not None else "N/A"
                st = cc["status"]
                if st == "pass":
                    pass_count += 1
                elif st == "close-but-off":
                    close_count += 1
                elif st == "fail":
                    fail_count += 1
                elif st == "no_triangles":
                    empty_count += 1
                print(f"{aid:<6} {sc:<7} {poly_cnt:<7} {sk:<10} {cont:<10} {d_str:<12} {st:<15}")

        print("=" * 80)
        print(f"Summary: {len(results)} area/scene files generated across {len(set(r['area_id'] for r in results))} areas.")
        print(f"Total sightings evaluated: {total_sightings}")
        print(f"  PASS:          {pass_count}")
        print(f"  CLOSE-BUT-OFF: {close_count}")
        print(f"  FAIL:          {fail_count}")
        print(f"  NO_TRIANGLES:  {empty_count}")


if __name__ == "__main__":
    main()
