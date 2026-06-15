# -*- coding: utf-8 -*-
"""Compute club standings + season evolution from the per-event club data and
render a single self-contained static HTML dashboard. Parametric scoring."""
import json, csv, re, unicodedata
from collections import defaultdict

TODAY = '15/06/2026'
MY_CLUB = 'STAH'

# ----- parametric scoring (scenario a by default) -----
SCORING = {
    "mode": "stage_based",          # "stage_based" (a,b) | "top_n_overall" (c,d)
    "n_best_online": 3,
    "regional_weight": 1,           # 1 = scenario a ; 2 = scenario b
    "final_weight": 1,              # 1 = scenario a ; 3 = scenario b
    "second_regional_as_online": True,
    "top_n_overall": 5,             # scenario c = 5 ; scenario d = 3
    "fallback_top_n": 3,            # groups/disciplines with no regional/final
}

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip().lower()

def to_float(s):
    s = (s or '').strip()
    if not s:
        return None
    if ',' in s:                      # pt-BR: dot=thousands, comma=decimal
        s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None

def date_key(dmy):                    # "DD/MM" -> (mm, dd)
    d, m = dmy.split('/')[:2]
    return (int(m), int(d))

gmap = json.load(open('group_map.json', encoding='utf-8'))

# website's 8 display groups -> 7 groups: the 6 official "equipe" groups from the
# regulamento (Carabina+Pistola ISSF merged into Provas ISSF) PLUS Fuzil Esportivo kept
# separate. The Overall tab lets the user toggle which groups count.
REMAP = {
    'Carabina ISSF': 'Provas ISSF',
    'Pistola ISSF': 'Provas ISSF',
    'Fuzil Esportivo': 'Fuzil Esportivo',           # kept separate (7th group)
    'Provas Estaduais': 'Provas Estaduais',
    'Provas Nacionais': 'Provas Nacionais',
    'Rifle Internacional': 'Provas Rifle Internacional',
    'Tiro ao Prato Olímpico': 'Provas Prato Olimpico',
    'Trap Nacional': 'Provas Trap',
}
GROUP_ORDER = ['Provas ISSF', 'Provas Nacionais', 'Provas Estaduais',
               'Provas Rifle Internacional', 'Provas Trap', 'Provas Prato Olimpico',
               'Fuzil Esportivo']
# groups included in the Overall by default (rules list 6; Fuzil default-on, user can toggle)
OVERALL_DEFAULT = [g for g in GROUP_ORDER]

def group_of(disc):
    g = gmap.get(norm(disc))
    raw = g['group'] if g else 'UNMAPPED'
    return REMAP.get(raw, raw)

# ----- load valid rows -----
rows = []
with open('data_valid_2026.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        tt = to_float(r['team_total'])
        if tt is None:
            continue
        rows.append({
            'eid': r['eid'], 'end': r['end_date'], 'dk': date_key(r['end_date']),
            'stage': r['stage_type'], 'discipline': r['discipline'],
            'group': group_of(r['discipline']), 'club': r['club'], 'tt': tt,
        })

unmapped = sorted(set(r['discipline'] for r in rows if r['group'] == 'UNMAPPED'))

# ----- discipline score for one club given its rows (already date-filtered) -----
def discipline_score(club_rows):
    online = sorted([r['tt'] for r in club_rows if r['stage'] in ('online', 'presencial_other')], reverse=True)
    regional = sorted([r['tt'] for r in club_rows if r['stage'] == 'regional'], reverse=True)
    final = sorted([r['tt'] for r in club_rows if r['stage'] == 'final'], reverse=True)
    if SCORING['mode'] == 'top_n_overall':
        alls = sorted([r['tt'] for r in club_rows], reverse=True)
        return sum(alls[:SCORING['top_n_overall']])
    # stage_based
    if not regional and not final:
        return sum(online[:SCORING['fallback_top_n']])
    reg_val = 0.0
    if regional:
        reg_val = regional[0] * SCORING['regional_weight']
        if SCORING['second_regional_as_online']:
            online = sorted(online + regional[1:], reverse=True)
    fin_val = final[0] * SCORING['final_weight'] if final else 0.0
    return sum(online[:SCORING['n_best_online']]) + reg_val + fin_val

# ----- snapshots (cumulative by date) -----
snap_dates = sorted(set(r['dk'] for r in rows))
def dk_label(dk):
    return f'{dk[1]:02d}/{dk[0]:02d}'

# standings per snapshot: group -> club -> points
def standings_upto(dk_max):
    sub = [r for r in rows if r['dk'] <= dk_max]
    # group -> discipline -> club -> [rows]
    gdc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in sub:
        gdc[r['group']][r['discipline']][r['club']].append(r)
    group_club_pts = defaultdict(lambda: defaultdict(float))
    disc_detail = {}   # (group,discipline) -> list of (club, score, rank, pts)
    for g, discs in gdc.items():
        for disc, clubs in discs.items():
            scored = [(c, discipline_score(rs)) for c, rs in clubs.items()]
            scored.sort(key=lambda x: -x[1])
            detail = []
            rank = 0
            for i, (c, sc) in enumerate(scored):
                if i == 0 or sc < scored[i-1][1]:
                    rank = i + 1                  # min-rank ties
                pts = (6 - rank) if (rank <= 5 and sc > 0) else 0
                group_club_pts[g][c] += pts
                detail.append({'club': c, 'score': round(sc, 2), 'rank': rank, 'pts': pts})
            disc_detail[(g, disc)] = detail
    return group_club_pts, disc_detail

# evolution: group -> club -> [pts per snapshot]
present = set(r['group'] for r in rows)
groups = [g for g in GROUP_ORDER if g in present] + sorted(present - set(GROUP_ORDER))
evolution = {g: defaultdict(lambda: [0]*len(snap_dates)) for g in groups}
for si, dk in enumerate(snap_dates):
    gcp, _ = standings_upto(dk)
    for g in groups:
        for c, p in gcp[g].items():
            evolution[g][c][si] = p

# current = last snapshot
cur_gcp, cur_detail = standings_upto(snap_dates[-1])

# ----- eligibility (per group, for MY_CLUB): online/regional/final participation -----
def my_eligibility(group):
    discs = defaultdict(lambda: {'online': 0, 'regional': 0, 'final': 0})
    for r in rows:
        if r['group'] == group and r['club'] == MY_CLUB:
            key = 'online' if r['stage'] in ('online', 'presencial_other') else r['stage']
            discs[r['discipline']][key] += 1
    return discs

# ----- per (club, discipline) requisite tracking (distinct stages) -----
# The mandatory requirement is per discipline, so we track it at that level.
def stage_bucket(st):
    return 'online' if st in ('online', 'presencial_other') else st
REQ = {'online': 3, 'regional': 1, 'final': 1}   # mandatory minimums
req_cd = defaultdict(lambda: {'online': set(), 'regional': set(), 'final': set()})  # (club,disc)->sets
for r in rows:
    req_cd[(r['club'], r['discipline'])][stage_bucket(r['stage'])].add(r['eid'])

def req_flags(buckets):
    return {
        'online': len(buckets['online']), 'regional': len(buckets['regional']),
        'final': len(buckets['final']),
        'online_ok': len(buckets['online']) >= REQ['online'],
        'regional_ok': len(buckets['regional']) >= REQ['regional'],
        'final_ok': len(buckets['final']) >= REQ['final'],
    }

def build_group(g):
    cur_pts = cur_gcp[g]
    full = sorted(cur_pts.items(), key=lambda x: -x[1])
    ranks = {}
    for i, (c, p) in enumerate(full):              # min-rank (ties share best rank)
        ranks[c] = (i + 1) if (i == 0 or p < full[i-1][1]) else ranks[full[i-1][0]]
    top5 = [c for c, _ in full[:5]]
    show = list(dict.fromkeys(top5 + ([MY_CLUB] if MY_CLUB in cur_pts else [])))
    standings = [{'club': c, 'pts': cur_pts[c], 'rank': ranks[c], 'is_me': c == MY_CLUB}
                 for c in show]
    series = {c: evolution[g][c] for c in show}
    return {'standings': standings, 'series': series}

# per-(group, club) -> list of that club's disciplines with score/points + per-discipline requisites
club_detail = defaultdict(lambda: defaultdict(list))
for (gg, disc), detail in cur_detail.items():
    n = len(detail)
    for d in detail:
        club_detail[gg][d['club']].append({
            'discipline': disc, 'score': d['score'], 'rank': d['rank'], 'pts': d['pts'],
            'n_clubs': n, 'req': req_flags(req_cd[(d['club'], disc)]),
        })
for gg in club_detail:
    for c in club_detail[gg]:
        club_detail[gg][c].sort(key=lambda x: -x['pts'])

# full per-group matrix (ALL clubs, all snapshots) so the client can recompute the Overall
matrix = {g: {c: evolution[g][c] for c in evolution[g]} for g in groups}

# ----- assemble payload -----
payload = {'today': TODAY, 'my_club': MY_CLUB, 'scoring': SCORING,
           'dates': [dk_label(d) for d in snap_dates],
           'group_order': groups, 'overall_default': [g for g in OVERALL_DEFAULT if g in groups],
           'groups': {g: build_group(g) for g in groups},
           'matrix': matrix,
           'club_detail': {g: dict(club_detail[g]) for g in groups}}

json.dump(payload, open('_dashboard_data.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('snapshots:', len(snap_dates), '| groups:', groups)
print('UNMAPPED disciplines:', unmapped)
for g in payload['groups']:
    st = payload['groups'][g]['standings'][:6]
    print(f'\n[{g}]')
    for s in st:
        print(f"   {s['pts']:>5}  {s['club']}{'  <= STAH' if s['is_me'] else ''}")
