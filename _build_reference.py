"""Generate the official 2026 reference: discipline->group mapping, event stage typing,
season stats. Also writes a clean CSV of valid club rows."""
import json, re, csv, unicodedata
from collections import defaultdict, Counter

events = json.load(open('_events_2026.json', encoding='utf-8'))
rows = json.load(open('_rows_2026.json', encoding='utf-8'))

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip().lower()

# ---- discipline -> group mapping (6 regulamento groups; Fuzil flagged) ----
GROUPS = {}
def add(group, names, flag=False):
    for n in names:
        GROUPS[norm(n)] = (group, flag)

add('ISSF', [
    'Carabina 3 Posições Masculino', 'Carabina 3 Posições Feminino', 'Carabina Deitado',
    'Carabina de Ar', 'Pistola de Ar', 'Pistola 25m feminino (Sport)',
    'Pistola 25m Masculino', 'Pistola 50m Masculino (Livre)', 'Pistola Standard Masculino',
    'Pistola de Fogo Central Masculino', 'Pistola de Tiro Rápido Masculino'])
add('Rifle Internacional', [
    'Carabina WRABF Ar Rifle - Heavy', 'Carabina WRABF Ar Rifle - Light',
    'Carabina WRABF Ar Rifle - Springer (mola)', 'Carabina WRABF Ar Rifle - Unlimited (50m)',
    'Carabina WRABF Rimfire - Heavy', 'Carabina WRABF Rimfire - Light',
    'Carabina WRABF Rimfire - Internacional Sporter',
    'Carabina Cmp Sporter - Mira Aberta', 'Carabina Cmp Sporter - Mira Fechada',
    'Carabina Nra - Mira Metalica', 'Carabina Nra - Mira Otica',
    'F-class Rimfire F/tr', 'F-class Rimfire Open'])
add('Provas Nacionais', [
    'Carabina Mira Aberta 10m', 'Carabina Mira Aberta 25m - Custom', 'Carabina Mira Aberta 25m - Sporter',
    'Carabina Mira Aberta 50m - Calibre Maior', 'Carabina Mira Aberta 50m - Calibre Menor Custom',
    'Carabina Mira Aberta 50m - Calibre Menor Sporter', 'F-class F/tr', 'F-class Open',
    'Duelo 20 segundos 10 metros - Pistola Maior (38/380/765/40/45/9mm)',
    'Duelo 20 segundos 10 metros - Pistola Menor',
    'Duelo 20 segundos 10 metros - Revólver Maior .32, .38, .357, 9mm,.454, .44 e .45',
    'Duelo 20 segundos 10 metros - Revólver Menor', 'Duelo 20 segundos 10 metros - Revólver Snub',
    'Duelo 20 Segundos 25 metros - Pistola Calibre Maior (38/380/765/40/45/9mm)',
    'Duelo 20 Segundos 25 metros - Pistola Calibre Menor (.22)',
    'Duelo 20 Segundos 25 metros - Revólver Calibre Maior (.32, .38, .357, 9mm,.454, .44 e .45)',
    'Duelo 20 Segundos 25 metros - Revólver Calibre Menor (.22)',
    'Duelo 20 Segundos 25 metros - Revólver Snub'])
add('Provas Estaduais', [
    'Baixa Luminosidade Maior', 'Baixa Luminosidade Menor', 'Caça Shotgun Maior', 'Caça Shotgun Menor',
    'Caça Shotgun Curta Cartucheira/pistolão', 'Carabina Mira Aberta 10m Cal. 5,5',
    'Carabina Mira Aberta de Ar 25M', 'Carabina Puma 7x3',
    'Copa FPTE - Carabina Repetição', 'Copa FPTE - Carabina Semi-Auto', 'Copa FPTE - Espingarda',
    'Copa FPTE - Pistola Maior', 'Copa FPTE - Pistola Menor', 'Copa FPTE - Revólver Maior',
    'Copa FPTE - Revólver Menor', 'Copa FPTE - Snub', 'Duelo 20 Segundos 10 metros - Red Dot',
    'Helice ZZ', 'Mini Trap', 'Perfect Shot Pistola', 'Perfect Shot Revolver',
    'Trap 25 Baixa Luminosidade', 'Baixa Luminosidade Maior'])
# FUZIL: not one of the 6 regulamento groups -> tentatively Provas Estaduais, FLAGGED
add('Provas Estaduais', [
    'Fuzil 20 Metros Intermediário', 'Fuzil 20 Metros Maior', 'Fuzil 20 Metros Menor',
    'Fuzil 50 Metros Maior Bancada', 'Fuzil 50 Metros Maior de Pé',
    'Fuzil 50 Metros Menor Bancada', 'Fuzil 50 Metros Menor Bancada - Armas Importadas',
    'Fuzil 50 Metros Menor Bancada - Armas Nacionais', 'Fuzil Esportivo 150m'], flag=True)
add('Prato Olímpico', [
    'Fossa Olimpica Masculino', 'Fossa Olimpica Feminino', 'Fossa Double Masculino',
    'Fossa Double Feminino', 'Skeet Masculino', 'Skeet Feminino'])
add('Trap', ['Trap 25', 'Trap 50', 'Trap Double', 'Trap Nacional'])

# ---- stage typing ----
def stage_type(name):
    n = norm(name)
    if 'final' in n and 'paulista' in n:
        return 'final'
    if 'presencial obrigatoria' in n:
        return 'regional'          # the official main-championship Regional
    if 'presencial' in n:
        return 'presencial_other'  # Trap/Prato own presencial etapas
    return 'online'

# ---- aggregate ----
disc_counts = Counter(r['discipline'] for r in rows)
valid_rows = [r for r in rows if r['valid']]
ev_valid = Counter(r['eid'] for r in valid_rows)

unmapped = sorted(set(r['discipline'] for r in rows if norm(r['discipline']) not in GROUPS))
flagged = sorted(set(d for d in disc_counts if GROUPS.get(norm(d), (None, False))[1]))

# group -> disciplines present in data
group_disc = defaultdict(list)
for d in sorted(disc_counts):
    g = GROUPS.get(norm(d), ('UNMAPPED', False))[0]
    group_disc[g].append(d)

# write clean CSV of valid rows
with open('data_valid_2026.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['eid', 'event', 'end_date', 'stage_type', 'discipline', 'group', 'club',
                'team_total', 'n_athletes'])
    for r in valid_rows:
        g = GROUPS.get(norm(r['discipline']), ('UNMAPPED', False))[0]
        w.writerow([r['eid'], r['event'], r['end'], stage_type(r['event']), r['discipline'],
                    g, r['club'], r['team_total_raw'], r['n_athletes']])

# stash computed bits for the markdown builder
json.dump({
    'group_disc': {k: v for k, v in group_disc.items()},
    'unmapped': unmapped, 'flagged': flagged,
    'stage_by_event': {str(e['eid']): stage_type(e['name']) for e in events if e['eid']},
    'ev_valid': {str(k): v for k, v in ev_valid.items()},
}, open('_refdata.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('valid rows:', len(valid_rows))
print('UNMAPPED disciplines:', unmapped)
print('FLAGGED (Fuzil etc):', flagged)
print()
for g in ['ISSF', 'Provas Nacionais', 'Provas Estaduais', 'Rifle Internacional', 'Trap', 'Prato Olímpico', 'UNMAPPED']:
    ds = group_disc.get(g, [])
    print(f'{g}: {len(ds)} disciplines in data')
print()
print('stage typing of events:')
for e in events:
    if e['eid'] and stage_type(e['name']) != 'online':
        print(f'  {e["eid"]} [{stage_type(e["name"])}] {e["name"][:70]}')
