import re, sys, collections, unicodedata
p = sys.argv[1]
seen = collections.defaultdict(list)
en = collections.defaultdict(list)
cur = None
for n, line in enumerate(open(p, encoding='utf-8'), 1):
    line = unicodedata.normalize('NFC', line.strip())
    if line.startswith('@'):
        cur = line.split('|')[0][1:].strip(); continue
    if ' = ' not in line or line.startswith('#'): continue
    sa, e = line.split(' = ', 1)
    e = e.split('##')[0]
    key = re.sub(r'[*.,?!]|\{[^}]*\}', '', sa).replace('ṃ', 'm').strip()
    seen[key].append(cur)
    en[e.strip().lower()].append(cur)
for k, v in seen.items():
    if len(v) > 1: print('DUP-SA', v, k)
for k, v in en.items():
    if len(v) > 1: print('DUP-EN', v, k)
