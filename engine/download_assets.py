import json, os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'data', 'wiki')
ASSETS = os.path.join(ROOT, 'assets')
BASE = 'https://taskbarhero.wiki'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

def L(name):
    with open(os.path.join(W, name), encoding='utf-8') as f:
        return json.load(f)

                                     
paths = set()
def add(p):
    if isinstance(p, str) and p.startswith('/'):
        paths.add(p)

tree = L('rune_tree.json')
for n in tree['nodes']:
    add(n.get('icon'))
for r in L('runes.json'):
    add(r.get('icon'))
for h in L('heroes.json'):
    add(h.get('icon')); add(h.get('dead_icon'))
for it in L('items.json'):
    # all item icons — gear, materials, and boxes — so the Gear/Shop/Items tabs render them
    add(it.get('icon'))
for s in L('skills.json'):
    add(s.get('icon'))
for p in L('passive_skills.json'):
    add(p.get('icon'))
# representative monster portrait per stage (boss preferred) — the UI shows these on
# farm/stage cards. Mirrors build_bundle.py's selection so the bundle's monsterArt resolves.
_by_stage = {}
for m in L('monsters.json'):
    for s in m.get('stages', []):
        _by_stage.setdefault(s['key'], []).append((s.get('boss', False), m))
for lst in _by_stage.values():
    rep = next((m for b, m in lst if b), None) \
        or next((m for b, m in lst if m.get('MONSTERTYPE') == 'MONSTER' and 'Helm' not in (m.get('portrait') or '')), None) \
        or lst[0][1]
    add(rep.get('portrait'))

paths = sorted(paths)
print(f'{len(paths)} unique icon paths to fetch')

                                    
ok = [0]; skip = [0]; fail = []
def fetch(p):
    dest = os.path.join(ASSETS, p.lstrip('/').replace('/', os.sep))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skip[0] += 1; return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        r = subprocess.run(['curl', '-s', '-f', '-A', UA, '-m', '40', '-o', dest, BASE + p],
                           capture_output=True)
        if r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 0:
            ok[0] += 1
        else:
            fail.append(p)
            if os.path.exists(dest) and os.path.getsize(dest) == 0:
                os.remove(dest)
    except Exception as e:
        fail.append((p, str(e)[:60]))

with ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(fetch, paths))

print(f'downloaded={ok[0]} skipped={skip[0]} failed={len(fail)}')
if fail:
    print('first failures:', fail[:8])
             
total = 0
for dp, _, files in os.walk(ASSETS):
    for fn in files:
        total += os.path.getsize(os.path.join(dp, fn))
print(f'assets total: {total/1024/1024:.1f} MB')
