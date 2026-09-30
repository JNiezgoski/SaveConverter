"""Test suite for Star Ocean 2 (PS1) Item Graphics & 3D Models (Task C)."""
from pathlib import Path
import json
import pytest

_ROOT = Path(__file__).resolve().parents[1]
SPRITES_DIR = _ROOT / "artifacts" / "so2-items-sprites"
MANIFEST_PATH = SPRITES_DIR / "manifest.json"
DATABASE_PATH = _ROOT / "artifacts" / "so2-items" / "items_database.json"


def test_manifest_and_sprites_complete():
    """Verify that manifest.json exists and all 823 item icons are generated."""
    assert MANIFEST_PATH.exists(), f"Manifest file missing: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["total_active_items"] == 823
    assert len(manifest["items"]) == 823

    # Verify every item from 1 to 823 has a valid icon PNG on disk
    for iid in range(1, 824):
        key = str(iid)
        assert key in manifest["items"], f"Item {iid} missing from manifest"
        entry = manifest["items"][key]
        filename = entry["filename"]
        expected_name = f"item_{iid:04d}_icon.png"
        assert filename == expected_name

        icon_path = SPRITES_DIR / filename
        assert icon_path.exists(), f"Icon file missing: {icon_path}"
        assert icon_path.stat().st_size > 0, f"Icon file is empty: {icon_path}"


def test_items_database_icon_integration():
    """Verify that items_database.json embeds the native icon path for all 823 items."""
    assert DATABASE_PATH.exists(), f"Items database missing: {DATABASE_PATH}"
    with open(DATABASE_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    assert db["total_active_items"] == 823
    assert len(db["items"]) == 823

    for item in db["items"]:
        iid = item["id"]
        assert "icon" in item, f"Item {iid} missing 'icon' field"
        expected_path = f"artifacts/so2-items-sprites/item_{iid:04d}_icon.png"
        assert item["icon"] == expected_path

        full_path = _ROOT / item["icon"]
        assert full_path.exists(), f"Referenced icon file missing: {full_path}"


def test_spot_check_models():
    """Spot check verified 3D mesh geometry and textures for canonical test items."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    items = manifest["items"]

    # Item 1: Magic Canvas
    m1 = items["1"]
    assert m1["face_count"] == 396
    assert m1["vert_count"] == 200
    assert m1["has_custom_texture"] is True

    # Item 101: Reflection Ring (Task I - verified TIM 0x220 offset and >0 opaque pixels)
    m101 = items["101"]
    assert m101["face_count"] == 384
    assert m101["vert_count"] == 96
    assert m101["has_custom_texture"] is True
    from PIL import Image
    import numpy as np
    icon_101 = Image.open(SPRITES_DIR / m101["filename"])
    arr_101 = np.array(icon_101)
    assert np.count_nonzero(arr_101[:, :, 3] > 0) > 1000

    # Item 393: Bunny Shoe
    m393 = items["393"]
    assert m393["face_count"] == 368
    assert m393["vert_count"] == 186
    assert m393["has_custom_texture"] is True
    assert m393["texture_width"] == 128
    assert m393["texture_height"] == 128

    # Item 400: Squash Spring Rolls (Food)
    m400 = items["400"]
    assert m400["face_count"] == 216
    assert m400["vert_count"] == 110
    assert m400["has_custom_texture"] is True

    # Item 500: Heart Breaker (Sword - metallic untextured mesh)
    m500 = items["500"]
    assert m500["face_count"] == 316
    assert m500["vert_count"] == 186
    assert m500["has_custom_texture"] is False

    # Item 700: Core Plate (Armor)
    m700 = items["700"]
    assert m700["face_count"] == 368
    assert m700["vert_count"] == 195
    assert m700["has_custom_texture"] is True
