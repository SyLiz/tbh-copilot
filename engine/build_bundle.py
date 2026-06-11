import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'data', 'wiki')

def L(name):
    p = os.path.join(W, name)
    with open(p, encoding='utf-8') as f:
        return json.load(f)

LOCALES = ['en-US','pt-BR','es-ES','fr-FR','de-DE','it-IT','ja-JP','ko-KR','zh-Hans','zh-Hant',
           'ru-RU','pl-PL','tr-TR','uk-UA','id-ID','th-TH','vi-VN']
                                                                                             
GAME_LOCALES = ['en-US','pt-BR','es-ES','fr-FR','de-DE','ja-JP','ko-KR','zh-Hans','zh-Hant',
                'ru-RU','pl-PL','tr-TR','uk-UA','id-ID','th-TH','vi-VN']

def i18n(d):
    """Keep only game locales from an i18n dict; ensure en-US present."""
    if not isinstance(d, dict):
        return {'en-US': str(d)} if d is not None else {}
    out = {k: d[k] for k in GAME_LOCALES if k in d and d[k]}
    if 'en-US' not in out and d.get('en-US'):
        out['en-US'] = d['en-US']
    return out

# wiki = the data version this bundle is built from (manifest); save = newest game/save
# version those tables describe. The dashboard's drift badge fires when a player's save
# is newer than 'save'. The wiki publishes the game's own version, so they move together.
_manifest_v = L('manifest.json').get('version', '?')
DB = {'locales': GAME_LOCALES, 'version': {'wiki': _manifest_v, 'save': _manifest_v}}

                  
DB['heroes'] = {}
for h in L('heroes.json'):
    DB['heroes'][str(h['HeroKey'])] = {
        'cls': h['ClassType'], 'mainW': h['MainWeaponGearType'], 'subW': h['SubWeaponGearType'],
        'AttackDamage': h['AttackDamage'], 'AttackSpeed': h['AttackSpeed'], 'CastSpeed': h.get('CastSpeed', 0),
        'CriticalChance': h['CriticalChance'], 'CriticalDamage': h['CriticalDamage'],
        'MaxHp': h['MaxHp'], 'Armor': h['Armor'], 'MovementSpeed': h.get('MovementSpeed', 0),
        'CooldownReduction': h.get('CooldownReduction', 0),
        'name': i18n(h.get('HeroNameKey_i18n')), 'skillKey': h.get('SkillKey'), 'icon': h.get('icon'),
    }

                                                        
DB['gearTypes'] = {}
for g in L('gear_types.json'):
    DB['gearTypes'][g['GearType']] = {
        'b1s': g.get('BaseStat1_STATTYPE'), 'b1m': g.get('BaseStat1_MODTYPE'),
        'b2s': g.get('BaseStat2_STATTYPE'), 'b2m': g.get('BaseStat2_MODTYPE'),
    }

                                                         
DB['gear'] = {}
for g in L('t/gear.json'):
    inh = []
    for i in (1, 2, 3):
        st = g.get(f'InherentStat{i}_STATTYPE')
        if st and st != 'NONE':
            inh.append([st, g[f'InherentStat{i}_MODTYPE'], g[f'InherentStat{i}_Value']])
    DB['gear'][str(g['GearKey'])] = {
        'b1': g.get('BaseStat1_Value'), 'b2': g.get('BaseStat2_Value'),
        'inh': inh, 'uniq': g.get('UniqueModKey') or 0,
    }

                                                                                  
DB['items'] = {}
for it in L('items.json'):
    DB['items'][str(it['id'])] = {
        'gt': it.get('gear'), 'grade': it.get('grade'), 'lvl': it.get('level'), 'type': it.get('type'),
        'icon': it.get('icon'),
    }

                                                                                     
DB['skills'] = {}
for s in L('skills.json'):
    DB['skills'][str(s['SkillKey'])] = {
        'act': s.get('ACTIVATIONTYPE'), 'cd': s.get('ActivationValue'), 'lvlKey': s.get('SkillLevelKey'),
        'delivery': s.get('DamageDeliveryType'), 'base': s.get('Value'), 'slot': s.get('SLOTTYPE'),
        'dmgType': s.get('DamageType'),
    }
_slv = {}
for r in L('t/skill_levels.json'):
    _slv.setdefault(str(r['SkillLevelKey']), {})[str(r['Level'])] = r['Value']
DB['skillLevels'] = _slv

                                                
DB['passives'] = {}
for p in L('passive_skills.json'):
    DB['passives'][str(p['PassiveSkillKey'])] = {'st': p['STATTYPE'], 'mt': p['MODTYPE'], 'v': p['Value']}

                                           
DB['attributes'] = {}
for a in L('attributes.json'):
    DB['attributes'][str(a['AttributeKey'])] = {
        'hero': a['HeroKey'], 'grp': a['GroupKey'], 'atype': a['ATTRIBUTETYPE'],
        'val': a['Value'], 'req': a['RequiredPoint'], 'max': a['MaxLevel'],
    }
DB['attributeGroups'] = {str(g['AttributeGroupKey']): g['RequiredAllocatedPoint']
                         for g in L('t/attribute_groups.json')}

                                                
DB['runes'] = {}
for r in L('runes.json'):
    DB['runes'][str(r['RuneKey'])] = {
        'max': r['MaxLevel'], 'prevReq': r.get('PrevNodeRequiredLevel'),
        'ldk': r.get('LevelDataKey'), 'next': r.get('NextRuneKey'),
        'name': i18n(r.get('NameKey_i18n')),
    }
tree = L('rune_tree.json')
DB['runeTree'] = {
    'starts': tree.get('startNodes', []),
    'edges': [[e['from'], e['to']] for e in tree.get('edges', []) if 'from' in e and 'to' in e],
}
                                                 
rl = {}
for r in L('t/rune_levels.json'):
    rl.setdefault(str(r['LevelKey']), {})[str(r['Level'])] = {
        'cost': r['CostValue'], 'costItem': r['CostItemKey'], 'st': r['STATTYPE'], 'v': r.get('Value', 0),
    }
DB['runeLevels'] = rl

                                                                                             
def rune_cat(st):
    s = st or ''
    if s.startswith('AllHero') or 'AttackDamage' in s or 'AttackSpeed' in s or 'Armor' in s or 'Critical' in s or 'MoveSpeed' in s:
        return 'combat'
    if 'OfflineReward' in s: return 'offline'
    if 'Gold' in s: return 'gold'
    if 'Exp' in s: return 'exp'
    if 'Chest' in s or 'Drop' in s or 'AutoOpen' in s or s.startswith('Open') or 'Cube' in s: return 'loot'
    return 'qol'
DB['runeNodes'] = {}
for n in tree['nodes']:
    lvs = n.get('levels') or []
    st = (lvs[0].get('stat') if lvs else n.get('stat')) or ''
    DB['runeNodes'][str(n['key'])] = {'x': n['x'], 'y': n['y'], 'cat': rune_cat(st), 'icon': n.get('icon')}
DB['runeBounds'] = tree['bounds']

                             
lv = {r['Level']: r['ExpForLevelUp'] for r in L('t/levels.json')}
DB['levels'] = [lv.get(i, 0) for i in range(1, 101)]                                     

                                                                                                    
                                                                                                          
stages_wiki = L('stages.json')
stage_names = {str(s['key']): i18n(s.get('name')) for s in stages_wiki}
farm = json.load(open(os.path.join(ROOT, 'data', 'farm_stages.json'), encoding='utf-8'))
DB['stages'] = {}
for s in farm:
    k = str(s['key'])
    DB['stages'][k] = {
        'label': s['label'], 'act': s['act'], 'no': s.get('stageNo'), 'lvl': s['level'],
        'diff': s['difficulty'], 'waves': s['waves'], 'totalHP': s['totalHP'],
        'gold': s['expectedGold'], 'exp': s['expectedEXP'],
        'goldPerHP': s.get('goldPerHP'), 'expPerHP': s.get('expPerHP'),
        'name': stage_names.get(k, {'en-US': s['label']}),
    }
                                                                      
DB['stageOrder'] = sorted(int(s['key']) for s in stages_wiki)

                                                                                                     
monsters = L('monsters.json')
sl_atk = {r['StageLevel']: r['MonsterAtkDmgMultiplier'] for r in L('t/stage_levels.json')}
DB['stageThreat'] = {}
for s in farm:
    key = s['key']; lvl = s['level']
    mons = [m for m in monsters if any((st.get('key') == key) for st in (m.get('stages') or []))]
    if not mons:
        continue
    atk = (sl_atk.get(lvl, 100)) / 100.0
    rep = max(mons, key=lambda m: m.get('AttackDamage', 0))
    hit = rep.get('AttackDamage', 0) * atk
    DB['stageThreat'][str(key)] = {
        'hit': round(hit, 1), 'dps': round(hit * (rep.get('AttackSpeed', 100) / 100.0), 1),
        'elem': rep.get('attackElements') or None, 'nmon': len(mons), 'perWave': s.get('perWave', 1),
    }

                                   
DB['stageLevels'] = {str(r['StageLevel']): {'atk': r['MonsterAtkDmgMultiplier'], 'hp': r['MonsterHpMultiplier'],
                                            'gold': r['MonsterGoldMultiplier'], 'exp': r['MonsterExpMultiplier']}
                     for r in L('t/stage_levels.json')}
DB['offlineRewards'] = {str(r['StageLevel']): {'gold': r['BaseGold'], 'exp': r['BaseExp'],
                                               'kills': r['KillCount'], 'clears': r['ClearCount']}
                        for r in L('t/offline_rewards.json')}

                                                           
ss = L('stat_strings.json')
DB['statStrings'] = {}
for k, v in ss.items():
    entry = {}
    if isinstance(v, dict):
        if isinstance(v.get('name'), dict):
            entry['name'] = i18n(v['name'])
                                                                                  
        for fld in ('line', 'template', 'desc', 'format'):
            if isinstance(v.get(fld), dict):
                entry[fld] = i18n(v[fld])
    DB['statStrings'][k] = entry

                                                             
DB['grades'] = [g['GRADE'] for g in L('grades.json')]
DB['gradeSlots'] = {}
for g in L('grades.json'):
    deco = g.get('ExtraSlotAmount_Decoration', 0); engr = g.get('ExtraSlotAmount_Engraving', 0)
    inscr = g.get('ExtraSlotAmount_Inscription', 0)
    DB['gradeSlots'][g['GRADE']] = {'inherent': g.get('InherentSlotAmount', 0), 'deco': deco, 'engr': engr,
                                    'inscr': inscr, 'extra': deco + engr + inscr}
                                                                                             
                                                                                               
sm = L('t/stat_mods.json')
affix_rep = {}
for r in sm:
    st = r['STATTYPE']; v = r.get('MaxValue', 0); tier = r.get('Tier', 99)
    cur = affix_rep.get(st)
    if r.get('Tier') == 4:
        if cur is None or cur.get('tier') != 4 or v > cur['value']:
            affix_rep[st] = {'value': v, 'mod': r['MODTYPE'], 'tier': 4}
    elif cur is None or (cur.get('tier') != 4 and tier < cur.get('tier', 99)):
        affix_rep[st] = {'value': v, 'mod': r['MODTYPE'], 'tier': tier}
DB['affixRep'] = affix_rep

                                               
DB['statMods'] = {}
for r in L('t/stat_mods.json'):
    DB['statMods'][f"{r['StatModKey']}:{r['Tier']}"] = {'st': r['STATTYPE'], 'mt': r['MODTYPE'],
                                                        'min': r['MinValue'], 'max': r['MaxValue']}

                                                          
DB['petStats'] = {}
for r in L('t/pet_stats.json'):
    DB['petStats'].setdefault(str(r['PetStatKey']), []).append({'st': r['STATTYPE'], 'mt': r['MODTYPE'], 'v': r['Value']})
DB['pets'] = {}
for p in L('t/pets.json'):
    DB['pets'][str(p['PetKey'])] = {'name': i18n(p.get('NameKey_i18n')), 'statKey': p.get('StatDataKey'),
                                    'unlock': p.get('UnlockCondition'), 'param1': p.get('Param1')}
                                                            
idt = L('items_detail.json')
DB['itemSell'] = {}; DB['itemCubeExp'] = {}
for k, v in idt.items():
    if isinstance(v, dict):
        if v.get('sellGold'): DB['itemSell'][str(k)] = v['sellGold']
        if v.get('cubeExp'): DB['itemCubeExp'][str(k)] = v['cubeExp']
                                                                             
DB['synthesis'] = {}
for r in L('t/synthesis_recipes.json'):
    g = r['GRADE']
    cur = DB['synthesis'].get(g)
    if cur is None or r['RecipeTier'] < cur.get('tier', 99):
        DB['synthesis'][g] = {'amount': r['MaterialAmount'], 'tier': r['RecipeTier'],
                              'minLvl': r['MinResultLevel'], 'maxLvl': r['MaxResultLevel']}

# ── drop finder: normal monster boxes (one per 5-level band) → weighted item groups ──
# Monsters drop the STAGEBOX of their stage's level band (item 910LL1 = "Normal Monster
# Box LvLL"); opening it rolls the drops table (DropKey = boxId*10+1) for an ITEMGROUP,
# and item_groups lists the concrete items. Rows with HeroKeyCondition only roll when
# the player owns that (DLC) hero.
_items = L('items.json')
band_dk = {}
for it in _items:
    if it.get('type') == 'STAGEBOX' and str(it['id']).startswith('910') and len(str(it['id'])) == 6:
        band_dk[it['id'] * 10 + 1] = int(str(it['id'])[3:5])
g2items = {}
for r in L('t/item_groups.json'):
    g2items.setdefault(r['ItemGroupKey'], []).append(r['ItemKey'])
gear_ids = {it['id'] for it in _items if it.get('gear') is not None}
DB['boxDrops'] = {}
_used = set()
for d in L('t/drops.json'):
    band = band_dk.get(d['DropKey'])
    if band is None:
        continue
    DB['boxDrops'].setdefault(str(band), []).append([d['RewardKey'], d['Weight'], d.get('HeroKeyCondition') or 0])
    _used.add(d['RewardKey'])
# gear items only; non-gear groups stay as empty lists so the weight totals stay honest
DB['dropGroups'] = {str(g): [k for k in g2items.get(g, []) if k in gear_ids] for g in _used}

                
payload = json.dumps(DB, ensure_ascii=False, separators=(',', ':'))
out = os.path.join(ROOT, 'engine', 'gamedata.js')
with open(out, 'w', encoding='utf-8') as f:
    f.write('// AUTO-GENERATED by engine/build_bundle.py — do not edit by hand. Source: data/wiki/*.json\n')
    f.write(';(function(g){\n')
    f.write('  var DB = ')
    f.write(payload)
    f.write(';\n')
    f.write('  g.TBH_DB = DB;\n')
    f.write('  if (typeof module !== "undefined" && module.exports) module.exports = DB;\n')
    f.write('})(typeof globalThis !== "undefined" ? globalThis : this);\n')

size = os.path.getsize(out)
counts = {k: (len(v) if hasattr(v, '__len__') else v) for k, v in DB.items()}
print(f'wrote {out}  ({size/1024:.0f} KB)')
print('counts:', json.dumps({k: counts[k] for k in ['heroes','gear','items','runes','runeLevels',
      'stages','stageLevels','offlineRewards','statStrings','passives','attributes','statMods']}))
