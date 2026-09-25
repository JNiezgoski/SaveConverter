"""Read-only checksum audit. Usage: python tools/audit_so2_checksums.py SAVE_DIRECTORY"""
import collections
import hashlib
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import saveconv


def main():
    root = Path(sys.argv[1])
    seen = set()
    counts = collections.Counter()
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in (".mcd", ".mcs", ".gme"):
            continue
        try:
            saves = saveconv.read_saves(path)
        except (OSError, saveconv.SaveError) as error:
            print("SKIP", path, error)
            continue
        for save in saves:
            data = save.data
            digest = hashlib.sha256(data).hexdigest()
            if data[0x200:0x20A] != b"STAR OCEAN" or digest in seen:
                continue
            seen.add(digest)
            signed = saveconv.so2_sign(bytearray(data))
            stored = struct.unpack_from("<II", data, 0x210)
            expected = struct.unpack_from("<II", signed, 0x210)
            valid = stored == expected
            counts["valid" if valid else "invalid"] += 1
            if not valid:
                print(path.relative_to(root), save.name,
                      "stored A/B", tuple(hex(x) for x in stored),
                      "expected A/B", tuple(hex(x) for x in expected),
                      "sha256", digest)
    print("Distinct SO2 blocks:", len(seen), dict(counts))


if __name__ == "__main__":
    main()
