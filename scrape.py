# -*- coding: utf-8 -*-
"""Scrape the FPTE 2026 season: event list, per-event club tables, and the official
discipline->group map. Writes the JSON caches the rest of the pipeline reads.

Outputs: _events_2026.json, _rows_2026.json, group_map.json
"""
import requests, re, json, sys, time, unicodedata
from bs4 import BeautifulSoup

YEAR = 2026
BASE = 'https://www.fpte.org.br'
H = {'User-Agent': 'Mozilla/5.0'}        # REQUIRED: bare requests get HTTP 403
NB = u'\xa0'

def clean(s):
    return re.sub(r'\s+', ' ', (s or '').replace(NB, ' ')).strip()

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip().lower()

def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=40)
            r.encoding = 'ISO-8859-1'
            return r.text
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2)

def scrape_events():
    soup = BeautifulSoup(get(f'{BASE}/template.php?pagina=resultados/{YEAR}'), 'html.parser')
    t = soup.find('table', id='tabela_resultado')
    events = []
    for tr in t.find('tbody').find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 5:
            continue
        a = tds[2].find('a')
        href = a['href'] if a else ''
        m = re.search(r'/(\d+)$', href)
        events.append({'eid': int(m.group(1)) if m else None,
                       'start': clean(tds[0].get_text()), 'end': clean(tds[1].get_text()),
                       'my': clean(tds[3].get_text()), 'scope': clean(tds[4].get_text()),
                       'name': clean(tds[2].get_text())})
    return events

def scrape_event_rows(ev):
    eid = ev['eid']
    if eid is None:
        return []
    soup = BeautifulSoup(get(f'{BASE}/template.php?pagina=resultados/{YEAR}/{eid}'), 'html.parser')
    out = []
    for tb in soup.find_all('table', class_='display'):
        if 'mytables' in tb.get('class', []):
            continue
        thead = tb.find('thead')
        if not thead or not thead.find('th'):
            continue
        htext = clean(thead.find('th').get_text())
        if 'Resultado Geral' in htext or not htext.endswith('- Clubes'):
            continue
        discipline = htext[:-len('- Clubes')].strip()
        body = tb.find('tbody')
        if not body:
            continue
        for tr in body.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 7:
                continue
            cells = [clean(td.get_text(' ')) for td in tds]
            if not cells[2]:
                continue
            out.append({'eid': eid, 'event': ev['name'], 'end': ev['end'],
                        'discipline': discipline, 'club': cells[2],
                        'team_total_raw': cells[5], 'pt_raw': cells[6],
                        'n_athletes': len([x for x in cells[3].split('  ') if x.strip()]),
                        'valid': bool(cells[6].strip())})
    return out

def scrape_group_map():
    soup = BeautifulSoup(get(f'{BASE}/template.php?pagina=campeonatos/{YEAR}'), 'html.parser')
    gmap = {}
    for tr in soup.find_all('tr'):
        tds = [clean(td.get_text(' ')) for td in tr.find_all('td')]
        if len(tds) >= 2 and tds[0] and tds[1] and tds[0] != 'Modalidade':
            gmap[norm(tds[1])] = {'group': tds[0], 'discipline_label': tds[1]}
    return gmap

def main():
    print('Scraping event list...')
    events = scrape_events()
    json.dump(events, open('_events_2026.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  {len(events)} events')

    print('Scraping club tables...')
    rows = []
    for i, ev in enumerate(events, 1):
        try:
            rows += scrape_event_rows(ev)
            sys.stderr.write(f'  [{i}/{len(events)}] {ev["eid"]} ok\n')
        except Exception as e:
            sys.stderr.write(f'  [{i}/{len(events)}] {ev["eid"]} ERROR {e}\n')
    json.dump(rows, open('_rows_2026.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'  {len(rows)} rows ({sum(1 for r in rows if r["valid"])} valid)')

    print('Scraping official group map...')
    gmap = scrape_group_map()
    json.dump(gmap, open('group_map.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  {len(gmap)} disciplines mapped')

if __name__ == '__main__':
    main()
