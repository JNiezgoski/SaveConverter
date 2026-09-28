"""Unit tests for tools/so2_terrain_extract.py geometry extraction and cross-checks."""
import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
_TOOLS = _ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import so2_terrain_extract as te


def test_resolve_scene_archive():
    # Overworld Scene 1 (Expel): 0x1014 + cell
    assert te.resolve_scene_archive(1, cell_id=9) == 4125
    assert te.resolve_scene_archive(1, cell_id=0) == 4116

    # Overworld Scene 2 (Nede): 0x109F + cell
    assert te.resolve_scene_archive(2, cell_id=15) == 4270
    assert te.resolve_scene_archive(2, cell_id=0) == 4255

    # Dungeon/field scenes: scene + 0xC87 (scene + 3207)
    assert te.resolve_scene_archive(183) == 3390
    assert te.resolve_scene_archive(402) == 3609
    assert te.resolve_scene_archive(671) == 3878
    assert te.resolve_scene_archive(704) == 3911
    assert te.resolve_scene_archive(716) == 3923
    assert te.resolve_scene_archive(727) == 3934
    assert te.resolve_scene_archive(740) == 3947
    assert te.resolve_scene_archive(794) == 4001
    assert te.resolve_scene_archive(811) == 4018
    assert te.resolve_scene_archive(820) == 4027


def test_classify_normal():
    # Flat horizontal floor
    cls, norm = te.classify_normal(0, 128, 0)
    assert cls == "floor"
    assert norm == (0.0, 1.0, 0.0)

    # Steep wall
    cls, norm = te.classify_normal(100, 10, 0)
    assert cls == "wall"

    # Moderate slope
    cls, norm = te.classify_normal(50, 100, 0)
    assert cls == "slope"


def test_2d_triangle_math():
    p0 = (0, 0, 0)
    p1 = (10, 0, 0)
    p2 = (0, 0, 10)

    # Inside
    assert te.pt_in_tri_2d(2, 2, p0, p1, p2) is True
    assert te.dist_pt_to_tri_2d(2, 2, p0, p1, p2) == 0.0

    # Outside along edge
    assert te.pt_in_tri_2d(-2, 2, p0, p1, p2) is False
    assert abs(te.dist_pt_to_tri_2d(-2, 2, p0, p1, p2) - 2.0) < 1e-5


def test_2d_quad_math():
    v0 = (10, 0, 0)
    v1 = (0, 0, 0)
    v2 = (10, 0, 10)
    v3 = (0, 0, 10)

    assert te.pt_in_quad_2d(5, 5, v0, v1, v2, v3) is True
    assert te.dist_pt_to_quad_2d(5, 5, v0, v1, v2, v3) == 0.0

    assert te.pt_in_quad_2d(15, 5, v0, v1, v2, v3) is False
    assert abs(te.dist_pt_to_quad_2d(15, 5, v0, v1, v2, v3) - 5.0) < 1e-5


def test_generated_geometry_artifacts():
    out_dir = _ROOT / "artifacts" / "so2-terrain-map"
    assert out_dir.is_dir()

    expected_files = [
        "area_0_scene_1.json",
        "area_0_scene_2.json",
        "area_118_scene_704.json",
        "area_128_scene_183.json",
        "area_128_scene_402.json",
        "area_128_scene_671.json",
        "area_128_scene_727.json",
        "area_128_scene_740.json",
        "area_128_scene_744.json",
        "area_128_scene_788.json",
        "area_128_scene_807.json",
        "area_128_scene_808.json",
        "area_128_scene_820.json",
        "area_138_scene_794.json",
        "area_140_scene_751.json",
        "area_140_scene_756.json",
        "area_140_scene_777.json",
        "area_148_scene_716.json",
        "area_150_scene_811.json",
        "area_160_scene_760.json",
        "area_160_scene_766.json",
    ]

    total_sightings = 0
    pass_sightings = 0

    for fname in expected_files:
        path = out_dir / fname
        assert path.exists(), f"Missing expected output file {fname}"
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert "area_id" in data
        assert "scene_id" in data
        assert "archive_index" in data
        assert "format_type" in data
        assert "metadata" in data
        assert "polygons" in data
        assert "cross_checks" in data

        for poly in data["polygons"]:
            assert "type" in poly
            assert "vertices" in poly
            assert "raw_vertices" in poly
            # Check coordinate scaling: raw / 4096 == scaled
            for (sx, sy, sz), (rx, ry, rz) in zip(poly["vertices"], poly["raw_vertices"]):
                assert abs(sx - rx / 4096.0) < 0.001
                assert abs(sy - ry / 4096.0) < 0.001
                assert abs(sz - rz / 4096.0) < 0.001

        for cc in data["cross_checks"]:
            total_sightings += 1
            if cc["status"] == "pass":
                pass_sightings += 1

    assert total_sightings == 24
    assert pass_sightings == 14


def test_batch_enumeration_artifacts():
    out_dir = _ROOT / "artifacts" / "so2-terrain-map"
    assert out_dir.is_dir()

    # Verify all 63 cells for Expel (scene 1)
    for c in range(63):
        cell_file = out_dir / f"area_0_scene_1_cell_{c}.json"
        assert cell_file.exists(), f"Missing Expel cell file {cell_file.name}"
        with cell_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["area_id"] == 0
        assert data["scene_id"] == 1
        assert data["format_type"] == "overworld_mesh"
        assert data["metadata"]["cell_id"] == c
        assert len(data["polygons"]) > 0

    # Verify all 63 cells for Nede (scene 2)
    for c in range(63):
        cell_file = out_dir / f"area_0_scene_2_cell_{c}.json"
        assert cell_file.exists(), f"Missing Nede cell file {cell_file.name}"
        with cell_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["area_id"] == 0
        assert data["scene_id"] == 2
        assert data["format_type"] == "overworld_mesh"
        assert data["metadata"]["cell_id"] == c
        assert len(data["polygons"]) > 0

    # Verify at least 390 dungeon scenes exist
    dungeon_files = [f for f in out_dir.glob("area_*_scene_*.json") if "_cell_" not in f.name]
    assert len(dungeon_files) >= 390

