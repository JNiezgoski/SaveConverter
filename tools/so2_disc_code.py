"""Read-only SO2 Disc 1 archive inspection, derived from its EXE.

Supports SLZ1 and SLZ2. Writes selected code artifacts to
the explicitly supplied output directory, never to the disc/source directory.
"""
from pathlib import Path
import struct


def read_sectors(handle, lba, size):
    out = bytearray()
    for sector in range(lba, lba + (size + 2047) // 2048):
        handle.seek(sector * 2352 + 24)
        out.extend(handle.read(2048))
    return bytes(out[:size])


def archive_table(handle):
    # EXE 80011CCC..80011D1C: XOR word table and byte size table.
    table = bytearray(read_sectors(handle, 300, 0x6000))
    key = 0x13578642
    for i in range(0x1200):
        word = struct.unpack_from('<I', table, 4 * i)[0]
        struct.pack_into('<I', table, 4 * i, word ^ key)
        key = (key ^ (key << 1)) & 0xffffffff
        table[0x4800 + i] ^= key & 255
        key = (~key ^ 0x13578642) & 0xffffffff
    assert table[:4] == bytes.fromhex('14 93 82 34')
    bcd = lambda x: (x >> 4) * 10 + (x & 15)
    for i in range(1, 0x1200):
        a, b, c, high = table[4*i:4*i+4]
        lba = (bcd(a) * 60 + bcd(b)) * 75 + bcd(c) - 150
        size = (high * 256 + table[0x4800 + i]) * 2048
        if size and lba >= 0:
            yield i, lba, size


def slz(data):
    # EXE 800122B4..80012758: LSB-first flags, backward distance,
    # high nibble + 3 length; zero distance terminates.
    assert data[:3] == b'SLZ' and data[3] in (1, 2)
    version = data[3]
    length = struct.unpack_from('<I', data, 8)[0]
    out = bytearray()
    pos = 16
    while True:
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if version == 2 and len(out) >= length:
                assert len(out) == length
                return bytes(out)
            if flags & (1 << bit):
                out.append(data[pos])
                pos += 1
            else:
                word = int.from_bytes(data[pos:pos+2], 'little')
                pos += 2
                distance = word & 0xfff
                if version == 1 and not distance:
                    assert len(out) == length
                    return bytes(out)
                if version == 2 and word >> 12 == 15:
                    # EXE 80012BA4: repeated-byte token, not a backreference.
                    if distance < 256:
                        count = distance + 19
                        value = data[pos]
                        pos += 1
                    else:
                        count = (distance >> 8) + 3
                        value = distance & 255
                    out.extend(bytes([value]) * count)
                    continue
                for _ in range((word >> 12) + 3):
                    out.append(out[-distance])


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('disc', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--entries', type=int, nargs='+',
                        default=[2576, 2982, 2985, 2986, 2998])
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with args.disc.open('rb') as handle:
        entries = list(archive_table(handle))
        for index, lba, size in entries:
            if index not in args.entries:
                continue
            head = read_sectors(handle, lba, 16)
            if head[:3] != b'SLZ' or head[3] not in (1, 2):
                continue
            data = slz(read_sectors(handle, lba, size))
            path = args.out / f'code-{index:04d}-lba-{lba}.bin'
            path.write_bytes(data)
            print(index, lba, hex(len(data)))


if __name__ == '__main__':
    main()
