"""Unit tests for tools/so2_scene_npc_extract.py 2D scene NPC extraction."""
from pathlib import Path
import sys
import tempfile
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TOOLS = _ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

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
