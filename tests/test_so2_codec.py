import os
import random
import struct
import sys
import unittest

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "scripts"))
import saveconv
import so2_codec as codec


class CodecTests(unittest.TestCase):
    def block(self):
        state = bytearray(codec.STATE_SIZE)
        state[:16] = bytes.fromhex('40 00 20 00 10 00 80 00 04 00 08 00 01 00 02 00')
        encoded = codec.encode(state)
        block = bytearray(8192)
        block[0x200:0x210] = b'STAR OCEAN 03/01'
        block[0x218:0x21A] = b'UU'
        struct.pack_into('<H', block, 0x21A, 0x382 + len(encoded))
        struct.pack_into('<H', block, 0x380, len(encoded))
        block[0x382:0x382 + len(encoded)] = encoded
        return bytes(saveconv.so2_sign(block))

    def test_zero_run_boundaries(self):
        for length in (0, 1, 2, 3, 254, 255, 256, 257, 258, 512, 1025):
            data = b'A' + bytes(length) + b'B' + bytes(length)
            self.assertEqual(codec.decode(codec.encode(data)), data)
        self.assertEqual(codec.encode(bytes(256)), b'\0\0\xfe')
        self.assertEqual(codec.decode(b'\0\0\xff'), bytes(257))

    def test_mixed_data(self):
        rng = random.Random(13)
        data = bytes(rng.choice((0, 0, 0, rng.randrange(256))) for _ in range(codec.STATE_SIZE))
        self.assertEqual(codec.decode(codec.encode(data)), data)

    def test_reject_bad_input(self):
        with self.assertRaises(saveconv.SaveError):
            codec.decode(b'\0\0')
        bad = bytearray(self.block())
        bad[0x380] ^= 1
        with self.assertRaises(saveconv.SaveError):
            codec.state(bad)


if __name__ == '__main__':
    unittest.main()
