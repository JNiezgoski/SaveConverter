"""Read-only scene-bundle inspection; see SO2-MAP-TERRAIN-INVESTIGATION.md.

Explicit archive indices only: decoded byte 0x1769 is NOT a unique selector.
Extracts type-0 SLZ subchunk zero and its 88-byte triangle records. Overworld
type-3 data uses another format and is deliberately reported without decoding.
No game instructions are executed by this tool.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from so2_disc_code import archive_table, read_sectors, slz


def unpack(data, offset, fmt):
    return struct.unpack_from('<' + fmt, data, offset)


def inspect_bundle(data):
    count, = unpack(data, 0, 'I')
    if count > 13:
        raise ValueError('not a supported scene asset table')
    assets = []
    terrain = None
    for index in range(count):
        kind, offset = unpack(data, 4 + index * 8, 'II')
        if not 0 <= kind < 13 or not 4 + count * 8 <= offset < len(data):
            raise ValueError('invalid scene asset table')
        assets.append({'type': kind, 'offset': offset})
        if kind != 0:
            continue
        source = data[offset:]
        if source[:3] != b'SLZ':
            raise ValueError('type 0 lacks SLZ header')
        size, = unpack(source, 8, 'I')
        terrain = source[16:16 + size] if source[3] == 0 else slz(source)
        if len(terrain) != size:
            raise ValueError('short terrain subchunk')
    result = {'assets': assets, 'terrain': None}
    if terrain is None:
        return result, None
    base, = unpack(terrain, 0x80, 'I')
    count, = unpack(terrain, base + 0x20, 'H')
    relative, = unpack(terrain, base + 0x5c, 'I')
    start = base + relative
    if start + count * 88 > len(terrain):
        raise ValueError('triangle array exceeds decompressed terrain')
    triangles = []
    for index in range(count):
        offset = start + index * 88
        triangles.append({
            'index': index, 'offset': offset,
            'bounds_y_min_max_xz_min_max': unpack(terrain, offset, '6h'),
            'enabled': terrain[offset + 12],
            'vertices': [unpack(terrain, offset + v, '3h') for v in (16, 24, 32)],
            'plane_ABC': unpack(terrain, offset + 48, '3i'),
            'object_field_22_value': terrain[offset + 84],
        })
    result['terrain'] = {
        'length': len(terrain), 'sha256': hashlib.sha256(terrain).hexdigest(),
        'TB_offset': base, 'triangle_array_offset': start,
        'triangle_count': count, 'triangles': triangles,
    }
    return result, terrain


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('disc', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--entries', nargs='+', type=int, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    with args.disc.open('rb') as handle:
        table = {index: (lba, size) for index, lba, size in archive_table(handle)}
        for index in args.entries:
            lba, size = table[index]
            bundle = read_sectors(handle, lba, size)
            result, terrain = inspect_bundle(bundle)
            result.update(entry=index, lba=lba, size=size,
                          bundle_sha256=hashlib.sha256(bundle).hexdigest())
            (args.out / f'entry-{index}.bin').write_bytes(bundle)
            if terrain is not None:
                (args.out / f'terrain-{index}.bin').write_bytes(terrain)
            results.append(result)
    report = json.dumps(results, indent=2) + '\n'
    (args.out / 'report.json').write_text(report, encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
