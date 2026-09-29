"""Unit tests for tools/so2_scene_npc_extract.py 2D scene NPC extraction."""
from pathlib import Path
import sys
import tempfile
import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.so2_scene_npc_extract import extract_scene_npc_sprites, DEFAULT_DISC1


@pytest.mark.skipif(not DEFAULT_DISC1.exists(), reason="Disc 1 binary not available")
def test_extract_hoffman_scene_npc():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir)
        res = extract_scene_npc_sprites(DEFAULT_DISC1, 3418, scale=1, out_dir=out_path, verbose=False)
        assert res.get("num_sections") == 25
        assert res.get("extracted_frames", 0) > 300
        # Section 4 has 21 frames in this archive. What it actually depicts is not
        # verified - visual review found ordinary humanoid NPCs here, not the
        # "switch monkey" an earlier draft of this test claimed. This assertion
        # only checks the frame count is stable, not the content.
        sec4_files = list(out_path.glob("sec04_f*.png"))
        assert len(sec4_files) == 21
        # Test Mode 0 sections (16 and 17) previously broken by 12B fixed header
        sec16_files = list(out_path.glob("sec16_f*.png"))
        assert len(sec16_files) == 21
        sec17_files = list(out_path.glob("sec17_f*.png"))
        assert len(sec17_files) == 26


@pytest.mark.skipif(not DEFAULT_DISC1.exists(), reason="Disc 1 binary not available")
def test_extract_8bpp_selector501():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir)
        res = extract_scene_npc_sprites(DEFAULT_DISC1, 3224, scale=1, out_dir=out_path, verbose=False)
        sec17 = next(s for s in res["sections"] if s["section_index"] == 17)
        assert sec17["selector_id"] == 501
        assert sec17["bpp"] == 8
        assert sec17["extracted_count"] == 4
        sec17_files = list(out_path.glob("sec17_f*.png"))
        assert len(sec17_files) == 4


@pytest.mark.skipif(not DEFAULT_DISC1.exists(), reason="Disc 1 binary not available")
def test_extract_multi_row_palette_section():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir)
        res = extract_scene_npc_sprites(DEFAULT_DISC1, 3217, scale=1, out_dir=out_path, verbose=False)
        sec13 = next(s for s in res["sections"] if s["section_index"] == 13)
        assert sec13["color_count"] == 96
        assert sec13["palette_rows"] == 6
        assert sec13["extracted_count"] == 4
        # Verify specific frame palette rows match descriptor byte 0
        frame_rows = {f["frame_index"]: f["palette_row"] for f in sec13["frames"]}
        assert frame_rows[0] == 0
        assert frame_rows[2] == 3
        assert frame_rows[3] == 4
        assert frame_rows[4] == 2
        sec13_files = list(out_path.glob("sec13_f*.png"))
        assert len(sec13_files) == 4
