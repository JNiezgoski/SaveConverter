from pathlib import Path
import struct

def find_16bit_strings(data):
    strings = []
    cur = []
    i = 0
    while i < len(data) - 1:
        c = struct.unpack_from('<H', data, i)[0]
        i += 2
        ch = None
        if 0x01B6 <= c <= 0x01CF:
            ch = chr(c - 0x01B6 + ord('A'))
        elif 0x01D0 <= c <= 0x01E9:
            ch = chr(c - 0x01D0 + ord('a'))
        elif 0x01AA <= c <= 0x01B3:
            ch = chr(c - 0x01AA + ord('0'))
        elif c in (0x0185, 0x0285):
            ch = ' '
        elif c in (0x0183, 0x0283):
            ch = '.'
        elif c in (0x0184, 0x0284):
            ch = ','
        elif c in (0x0186, 0x0286):
            ch = "'"
        elif c == 0x01B5:
            ch = '-'
        
        if ch is not None:
            cur.append(ch)
        else:
            if len(cur) >= 4:
                s = ''.join(cur).strip()
                if len(s) >= 4:
                    strings.append(s)
            cur = []
    if len(cur) >= 4:
        strings.append(''.join(cur).strip())
    return strings

def main():
    root = Path('artifacts/so2-specialty')
    for p in sorted(root.glob('*.bin')):
        b = p.read_bytes()
        s = find_16bit_strings(b)
        if s:
            print(f"{p.name} ({len(b)} bytes): {s[:6]}")

if __name__ == '__main__':
    main()
