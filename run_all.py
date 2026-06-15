# -*- coding: utf-8 -*-
"""One-shot update: scrape -> prepare data -> compute standings -> build dashboard.html.

Usage:  python run_all.py
Run this whenever new results are published on fpte.org.br, then commit & push.
"""
import subprocess, sys, time

STEPS = [
    ('scrape.py',           'Scrape FPTE 2026 (events, club tables, group map)'),
    ('_build_reference.py', 'Clean valid rows -> data_valid_2026.csv'),
    ('build_dashboard.py',  'Compute standings + evolution + requisites'),
    ('build_html.py',       'Render self-contained dashboard.html'),
]

def main():
    t0 = time.time()
    for script, desc in STEPS:
        print(f'\n=== {desc} ===')
        r = subprocess.run([sys.executable, script])
        if r.returncode != 0:
            print(f'\n!! {script} failed (exit {r.returncode}). Aborting.')
            sys.exit(r.returncode)
    print(f'\nDone in {time.time()-t0:.0f}s -> dashboard.html')

if __name__ == '__main__':
    main()
