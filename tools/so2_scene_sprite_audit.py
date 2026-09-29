"""Audit scene descriptor bounds and every extracted scene PNG; outputs local evidence."""
import json
import struct
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from tools.so2_scene_npc_extract import DEFAULT_DISC1, OUT_BASE
from tools.so2_disc_code import archive_table, read_sectors, slz


def main():
    counts = Counter()
    dimensions = Counter()
    anomalies = []
    changes = []
    expected = set()
    with DEFAULT_DISC1.open('rb') as disc:
        table = list(archive_table(disc))
        for aid, lba, size in table:
            if not 3207 <= aid <= 4154:
                continue
            counts['archives_scanned'] += 1
            raw = read_sectors(disc, lba, size)
            n = struct.unpack_from('<I', raw)[0]
            if n > 30:
                counts['invalid_container'] += 1
                continue
            offsets = [off for tag, off in struct.iter_unpack('<II', raw[4:4+8*n]) if tag == 2]
            if not offsets:
                counts['no_tag2'] += 1
                continue
            counts['tag2_archives'] += 1
            dec = slz(raw[offsets[0]:])
            ns = struct.unpack_from('<I', dec)[0]
            if ns == 0:
                counts['empty_tag2_archives'] += 1
                continue
            if ns > 100:
                counts['invalid_section_count'] += 1
                anomalies.append([aid, 'section_count', ns])
                continue
            for si in range(ns):
                so = struct.unpack_from('<I', dec, 4+4*si)[0]
                sel = struct.unpack_from('<I', dec, so+4)[0]
                ao, sp = struct.unpack_from('<II', dec, so+24)
                mode = dec[so+ao+2]
                counts[f'mode_{mode}_sections'] += 1
                p = so+sp
                _, po, _, fc = struct.unpack_from('<IIHH', dec, p)
                if not 0 < fc <= 256:
                    counts['rejected_frame_count_sections'] += 1
                    anomalies.append([aid, si, sel, 'frame_count', fc])
                    continue
                totals = []
                for header in [12, 12 if mode == 1 else 16]:
                    valid = 0
                    current = len(totals) == 1
                    if p+header+12*fc+36 > len(dec):
                        if current: anomalies.append([aid, si, sel, 'palette_bounds'])
                        totals.append(0)
                        continue
                    for fi in range(fc):
                        pos=p+header+12*fi
                        _, w, h, _, px, py, off=struct.unpack_from('<BBBBhhI', dec, pos)
                        start=p+po+off; end=start+(w//2)*h
                        reason = 'zero_dimension' if not w or not h else 'pixel_bounds' if end>len(dec) else 'zero_pixels' if not any(dec[start:end]) else 'accepted'
                        if current:
                            counts[reason] += 1
                            dimensions[f'{w}x{h}'] += 1
                            if reason == 'accepted': expected.add(f'scene_{aid}/sec{si:02d}_f{fi:02d}.png')
                            if w%2: counts['odd_width_frames'] += 1
                            if reason != 'accepted': anomalies.append([aid, si, sel, fi, reason, w, h])
                        valid += reason == 'accepted'
                    totals.append(valid)
                if totals[0]!=totals[1]: changes.append({'archive':aid,'section':si,'selector':sel,'old_header_frames':totals[0],'fixed_header_frames':totals[1]})
    blank=[]; black=[]; files=0; observed=set()
    for path in sorted(OUT_BASE.glob('scene_*/*.png')):
        with Image.open(path) as image:
            rgba=image.convert('RGBA'); files+=1
            observed.add(path.relative_to(OUT_BASE).as_posix())
            if rgba.getchannel('A').getbbox() is None: blank.append(path.relative_to(OUT_BASE).as_posix())
            if rgba.convert('RGB').getbbox() is None: black.append(path.relative_to(OUT_BASE).as_posix())
    result={'counts':dict(counts),'dimensions':dict(dimensions),'anomalies':anomalies,'header_changes':changes,'png_scan':{'files':files,'fully_transparent':blank,'all_rgb_black':black,'not_in_current_decode':sorted(observed-expected),'missing_current_frames':sorted(expected-observed)}}
    (OUT_BASE/'scene_extraction_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'counts':dict(counts),'changed_sections':len(changes),'png_files':files,'transparent':len(blank),'black':len(black)},indent=2))

if __name__=='__main__': main()
