import urllib.request
import re

url = 'https://claude.ai/artifact/9bm3DMdVEPpPaVJACqU15n'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print('Status:', resp.status)
        m = re.search(r'data-frame-uuid="([^"]+)"', html)
        uuid = m.group(1) if m else None
        print('UUID:', uuid)
        if uuid:
            frame_url = f'https://claude.ai/api/frame/{uuid}?bk=initial&actor=id&via=user_open'
            req2 = urllib.request.Request(frame_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'X-Frame-CP': 'go',
                'X-Frame-Platform': 'web',
                'Referer': url
            })
            try:
                with urllib.request.urlopen(req2) as resp2:
                    print('Frame API status:', resp2.status)
                    print('Frame API content:', resp2.read()[:500])
            except Exception as e:
                print('Frame API error:', e)
except Exception as e:
    print('Error:', e)
