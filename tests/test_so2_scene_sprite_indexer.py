"""Unit tests for tools/so2_scene_sprite_indexer.py scene sprite indexing."""
from pathlib import Path
import sys
import tempfile
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TOOLS = _ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from tools.so2_scene_sprite_indexer import (
    classify_selector,
    get_region_name,
    build_scene_sprite_index,
    DEFAULT_DISC1
)


def test_classify_selector():
    # Heroes 0..11
    cat, desc = classify_selector(0, 24, 45, 21)
    assert cat == "Playable Hero"
    assert "Claude Kenni" in desc

    cat, desc = classify_selector(4, 24, 47, 21)
    assert cat == "Playable Hero"
    assert "Dias Flac" in desc

    # Non-hero selectors are intentionally left unclassified - a prior version
    # guessed specific content ("switch monkey", "shadow/FX", etc.) purely from
    # selector ID / dimension coincidences, and every guess that was actually
    # checked against a real extracted frame turned out to be wrong. See
    # manager review, 2026-09-28.
    cat, desc = classify_selector(23, 20, 30, 21)
    assert cat == "Unclassified"
    assert "23" in desc

    cat, desc = classify_selector(32767, 8, 5, 7)
    assert cat == "Unclassified"
    assert "32767" in desc


def test_get_region_name():
    assert "Arlia" in get_region_name(3224)
    assert "Hoffman Ruins" in get_region_name(3418)
    assert "Four Fields" in get_region_name(3710)


@pytest.mark.skipif(not DEFAULT_DISC1.exists(), reason="Disc 1 binary not available")
def test_scene_sprite_index_single():
    # Verify build_scene_sprite_index produces expected structure
    with tempfile.TemporaryDirectory() as tmpdir:
        master_index = build_scene_sprite_index(DEFAULT_DISC1, disc_num=1)
        assert master_index["total_scenes_indexed"] > 600
        assert master_index["total_sprite_frames"] > 40000
        assert master_index["unique_entity_selectors"] >= 200
        # Check Hoffman Ruins Archive 3418 in indexed scenes
        assert "3418" in master_index["scenes"]
        sc3418 = master_index["scenes"]["3418"]
        assert sc3418["total_sections"] >= 20
        # Selector 23 appears in this archive (content not identified - see
        # tools/so2_scene_selector_evidence.json for visually-verified selectors)
        selectors_3418 = [s["selector_id"] for s in sc3418["sprites"]]
        assert 23 in selectors_3418
