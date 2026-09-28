import os
import random
import struct
import sys
import unittest

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "scripts"))
import saveconv
import so2_fol as fol


class FolTests(unittest.TestCase):
    def block(self, money=40):
        state = bytearray(fol.STATE_SIZE)
        state[:16] = bytes.fromhex('40 00 20 00 10 00 80 00 04 00 08 00 01 00 02 00')
        struct.pack_into('<IIII', state, 16, 250, 3, money, 5)
        encoded = fol.encode(state)
        block = bytearray(8192)
        block[0x200:0x210] = b'STAR OCEAN 03/01'
        block[0x218:0x21A] = b'UU'
        struct.pack_into('<H', block, 0x21A, 0x382 + len(encoded))
        struct.pack_into('<H', block, 0x380, len(encoded))
        block[0x382:0x382 + len(encoded)] = encoded
        return bytes(saveconv.so2_sign(block))

    def test_reported_corruption(self):
        original = self.block()
        self.assertEqual(original[0x39A:0x39E], bytes.fromhex('28 00 00 01'))
        broken = bytearray(original)
        struct.pack_into('<H', broken, 0x39A, 5000)
        saveconv.so2_sign(broken)
        self.assertTrue(saveconv.so2_valid(broken))
        self.assertEqual(struct.unpack_from('<I', fol.state(broken), fol.FOL)[0], 16_782_216)

    def test_set_preserves_every_other_decoded_byte(self):
        block = self.block()
        original = fol.state(block)
        for amount in (0, 1, 40, 90, 210, 255, 256, 330, 730, 5000,
                       65535, 65536, 0x1000000, 999_999_999):
            with self.subTest(amount=amount):
                changed = fol.set_fol(block, amount)
                decoded = fol.state(changed)
                self.assertEqual(decoded[:24], original[:24])
                self.assertEqual(decoded[28:], original[28:])
                self.assertEqual(int.from_bytes(decoded[24:28], 'little'), amount)
                self.assertTrue(saveconv.so2_valid(changed))

    def test_zero_run_boundaries(self):
        for length in (0, 1, 2, 3, 254, 255, 256, 257, 258, 512, 1025):
            data = b'A' + bytes(length) + b'B' + bytes(length)
            self.assertEqual(fol.decode(fol.encode(data)), data)
        self.assertEqual(fol.encode(bytes(256)), b'\0\0\xfe')
        self.assertEqual(fol.decode(b'\0\0\xff'), bytes(257))

    def test_mixed_data(self):
        rng = random.Random(13)
        data = bytes(rng.choice((0, 0, 0, rng.randrange(256))) for _ in range(fol.STATE_SIZE))
        self.assertEqual(fol.decode(fol.encode(data)), data)

    def test_reject_bad_input(self):
        with self.assertRaises(saveconv.SaveError):
            fol.decode(b'\0\0')
        for value in (-1, 1_000_000_000):
            with self.assertRaises(saveconv.SaveError):
                fol.set_fol(self.block(), value)
        bad = bytearray(self.block())
        bad[0x214] ^= 1
        with self.assertRaises(saveconv.SaveError):
            fol.set_fol(bad, 5000)
        bad = bytearray(self.block())
        bad[0x380] ^= 1
        with self.assertRaises(saveconv.SaveError):
            fol.state(bad)


if __name__ == '__main__':
    unittest.main()
