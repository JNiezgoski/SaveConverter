import urllib.request
import re

url = 'https://claude.ai/artifact/9bm3DMdVEPpPaVJACqU15n'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Search for all strings matching endpoints or urls
print("Matches:")
for m in re.finditer(r'https?://[^\s"\'<>]+', html):
    print(m.group(0))

# Search for /api/
for m in re.finditer(r'\/api\/[^\s"\'<>]+', html):
    print(m.group(0))
