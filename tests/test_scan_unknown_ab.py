import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.scan_unknown_ab import classify_triplet, scan_file


class TestScanUnknownAB(unittest.TestCase):
    def test_classify_triplet(self):
        self.assertEqual(classify_triplet((16, 16, 16)), 'Flat (16,16,16)')
        self.assertEqual(classify_triplet((15, 0, 0)), 'Zeroed (15,0,0)')
        self.assertEqual(classify_triplet((16, 18, 18)), 'Diverged (+2) (16,18,18)')
        self.assertEqual(classify_triplet((6, 16, 16)), 'Diverged (+10,+10) (6,16,16)')

    def test_scan_real_save(self):
        mcd_path = ROOT.parent / 'StarOcean2/SaveGames/Star Ocean - The Second Story (USA)_1.mcd'
        if not mcd_path.exists():
            self.skipTest(f'Save file not found at {mcd_path}')
        results = scan_file(mcd_path)
        self.assertGreaterEqual(len(results), 1)
        save1 = results[0]
        self.assertEqual(save1['members'][0]['name'], 'Claude')
        self.assertEqual(save1['members'][0]['level'], 255)
        self.assertEqual(save1['members'][0]['a'], (16, 18, 18))
        self.assertEqual(save1['members'][0]['b'], (9, 9, 9))


if __name__ == '__main__':
    unittest.main()
