# FPTE 2026 — Campeonato por Clubes (STAH)

Season-long tracker for the FPTE 2026 **club** championship (São Paulo state shooting),
focused on club **STAH**. Shows, round by round, the **top 5 + STAH** per sub-championship and
overall, with an evolution chart and per-discipline mandatory-requirement flags.

The output is a **single self-contained `dashboard.html`** (no server, no database — all data is
baked into the file). Open it by double-click, host it on GitHub Pages, or embed it in Streamlit.

## How it works

- **score** = what a club shoots in a round (sum of its 3 best athletes).
- **points** = the 5/4/3/2/1 a club earns per discipline from its season ranking.
- Per discipline, season score = **(3 best online) + (best regional) + (final)** (no multipliers)
  → rank clubs → points → summed per group. Recomputed at every weekly snapshot.
- Scoring is parametric (`SCORING` block in `build_dashboard.py`).

See `FPTE_2026_REFERENCE.md` for the full rules, grouping, and scraping notes.

## Update the data

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python run_all.py
```

`run_all.py` runs the whole pipeline (`scrape.py` → `_build_reference.py` → `build_dashboard.py`
→ `build_html.py`) and regenerates `dashboard.html` (~1–2 min; ~50 event pages). Then commit and
push.

## Publish — Option A: GitHub Pages (recommended)

1. Create a GitHub repo and push this folder (see steps below).
2. Repo **Settings → Pages → Build and deployment → Source: Deploy from a branch**, branch
   `main`, folder `/ (root)`, Save.
3. Your dashboard is live at `https://<user>.github.io/<repo>/dashboard.html`.
4. **To update:** `python run_all.py`, then `git add dashboard.html && git commit && git push`.

## Publish — Option B: Streamlit Community Cloud

1. Push this repo (incl. `dashboard.html`, `streamlit_app.py`, `requirements.txt`).
2. Go to share.streamlit.io → New app → pick the repo → main file `streamlit_app.py` → Deploy.
3. The app renders the committed `dashboard.html`. It does **not** scrape — refresh data locally
   with `python run_all.py`, then push; Streamlit redeploys automatically.

## Files

| File | Role |
|---|---|
| `run_all.py` | one-shot update orchestrator |
| `scrape.py` | scrapes events, club tables, official group map |
| `_build_reference.py` | cleans valid rows → `data_valid_2026.csv` |
| `build_dashboard.py` | standings, evolution, per-discipline requisites (parametric scoring) |
| `build_html.py` | renders `dashboard.html` |
| `streamlit_app.py` | optional Streamlit wrapper around `dashboard.html` |
| `dashboard.html` | the published dashboard (committed artifact) |
| `FPTE_2026_REFERENCE.md` | rules, grouping, scraping reference |
