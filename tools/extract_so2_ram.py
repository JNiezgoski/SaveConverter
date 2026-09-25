"""Extract main RAM from a DuckStation state using the disc EXE as an anchor.

Usage: python tools/extract_so2_ram.py STATE DISC_BIN NEW_RAM_FILE
Requires zstandard. Both source files are opened read-only.
"""
from pathlib import Path
import struct
import sys

import zstandard
from so2_disc_code import read_sectors


def main():
    state_path, disc_path, out = map(Path, sys.argv[1:])
    with disc_path.open('rb') as handle:
        exe = read_sectors(handle, 24, 2112)
    assert exe[:8] == b'PS-X EXE'
    address = struct.unpack_from('<I', exe, 0x18)[0] & 0x1fffff
    state = state_path.read_bytes()
    offset = 0
    while True:
        offset = state.find(bytes.fromhex('28 b5 2f fd'), offset)
        if offset < 0:
            raise ValueError('no state frame with the disc EXE anchor found')
        decoded = zstandard.ZstdDecompressor().decompress(
            state[offset:], max_output_size=32 * 1024 * 1024)
        match = decoded.find(exe[2048:2112])
        if match >= address and len(decoded) >= match - address + 0x200000:
            start = match - address
            with out.open('xb') as handle:
                handle.write(decoded[start:start + 0x200000])
            print(f'Zstd frame {offset:#x}, decoded size {len(decoded)}, RAM offset {start:#x}')
            return
        offset += 4


if __name__ == '__main__':
    main()
