# FPTE 2026 — Club Championship Tracker · Reference (current & correct)

Authoritative reference for the STAH club-championship dashboard. Supersedes the scoring
sections of `FPTE_PROJECT_REFERENCE.md` (that older file is still valid for raw HTML/
scraping mechanics). Last reviewed against live 2026 data.

---

## 1. Goal

Track, **round by round over the season**, the FPTE 2026 club championship: the top-5 clubs
plus **STAH** in each sub-championship and overall, including an evolution line chart and
flags for missing mandatory requirements. Built as a **self-contained static HTML**
dashboard (no server), updated manually by re-running the pipeline.

## 2. Vocabulary (use consistently)

- **score** — what athletes/clubs actually shoot in a round. A club's per-round score in a
  discipline = sum of its **3 best athletes** (the website's `team_total`, col 5).
- **points** — the **5/4/3/2/1** a club earns per discipline from its season ranking.

## 3. Scoring rule (LOCKED)

Per **discipline**, a club's **season score** =
> **(3 best online scores) + (best regional score) + (final score)** — **no multipliers.**

Then, within each discipline, **rank clubs by season score** (min-rank; ties share the best
rank) and award **points**: 1st→5, 2nd→4, 3rd→3, 4th→2, 5th→1, 6th+→0 (also 0 if score 0).
A club's **group points** = sum of its discipline points across that group.
Recomputed at **every snapshot** (event by event, ordered by `end_date`), so "the current
leader holds 5 until someone overtakes" emerges naturally.

Note: the federation's **individual** ranking uses multipliers (`Camp. = Soma(3 best online)
+ Reg.×2 + Final×3`, confirmed from the campeonatos page column headers). The **club** model
above intentionally uses **no multipliers** per project decision.

### Parametric config (so the rule can be changed in one place)
`build_dashboard.py → SCORING`:
```python
{"mode":"stage_based", "n_best_online":3, "regional_weight":1, "final_weight":1,
 "second_regional_as_online":True, "top_n_overall":5, "fallback_top_n":3}
```
- Current default = the locked rule (scenario "a").
- `second_regional_as_online`: there are two Regional options (May / Sept); the **best**
  counts as the Regional, the **other** is treated as an online result.
- Disciplines/groups with **no** regional/final fall back to `top fallback_top_n` online scores.

## 4. Groups (7) and the Overall

Source of truth: the federation's classification page
`fpte.org.br/template.php?pagina=campeonatos/2026` ("Modalidade" column), scraped into
`group_map.json`. The website lists 8 labels; we map them to **7 dashboard groups**:

| Dashboard group | From website Modalidade |
|---|---|
| Provas ISSF | Carabina ISSF **+** Pistola ISSF (merged) |
| Provas Nacionais | Provas Nacionais |
| Provas Estaduais | Provas Estaduais |
| Provas Rifle Internacional | Rifle Internacional |
| Provas Trap | Trap Nacional |
| Provas Prato Olímpico | Tiro ao Prato Olímpico |
| Fuzil Esportivo | Fuzil Esportivo (kept separate) |

- The regulamento's team-formation list names **6** groups (no Fuzil). We keep **Fuzil as a
  7th group** and let the user **toggle** which groups count in the **Overall ("Geral")** via
  checkboxes (default: all on; untick Fuzil for the strict-6 reading). `REMAP` in
  `build_dashboard.py` controls the mapping.
- **Overall = sum of a club's points across the selected groups.**
- **Trap Nacional has no club data in 2026** — those events publish only individual
  (`mytables`) tables, no club tables — so the Trap tab won't appear until club tables exist.

## 5. Mandatory requirements (flag, don't filter)

Per **(club, discipline)**: **≥3 online + 1 regional + 1 final** participations (3 athletes
each). Points are always computed; the dashboard **flags** what's missing **per discipline**
(click a club → bottom panel shows `✓ Apto` or `Falta: …`). The Final is in December, so it's
"pending" for everyone now — that's expected, not a failure.

## 6. Data source & scraping (verified 2026)

- Event list: `…?pagina=resultados/2026`; event page: `…/resultados/2026/{eid}`.
- **A `User-Agent` header is required** — bare requests return **403**.
- Encoding **ISO-8859-1**; strip `\xa0`.
- **Club tables** = `class="display"` **without** `mytables`; header ends with `" - Clubes"`.
  Skip the `"Resultado Geral"` summary table.
- Columns: 0 PS · 1 CL · 2 Club · 3 athletes · 4 individual scores · 5 **team_total** ·
  6 **PT** (per-event 5/4/3/2/1, **ignored** — we compute season points ourselves).
- **A row counts only if PT (col 6) is non-empty** (club had 3+ athletes) → `valid=True`.
- **Numbers are dot-decimal with 2 places** in 2026 (e.g. `103.03`); **no commas** seen.
  Parser still handles pt-BR `1.699,00` defensively.
- **Stage typing from event name**: `presencial obrigatória` → `regional` (event 1125 is the
  May option); `final`+`paulista` → `final` (December, not yet published); other `presencial`
  → `presencial_other` (Trap/Prato own etapas; treated as online); else `online`.

## 7. Pipeline (run in order)

1. `_recon_scrape.py` → scrapes all 2026 events → `_events_2026.json`, `_rows_2026.json`.
2. `_build_reference.py` → `data_valid_2026.csv` (clean valid rows + stage_type).
3. `group_map.json` ← scraped from the campeonatos page (official grouping).
4. `build_dashboard.py` → standings + evolution + per-discipline requisites → `_dashboard_data.json`.
5. `build_html.py` → self-contained **`dashboard.html`**.

(A single `run_all.py` wrapper will be added when the dashboard is finalized.)

## 8. Deployment (chosen: Option A — static)

- Host `dashboard.html` on **GitHub Pages** (Cloudflare Pages / Netlify are equivalent).
- **Update flow:** run the pipeline **locally on the PC** → `git push` → Pages redeploys.
  The scraper runs locally; only the finished HTML is online. The "database" is just the
  small committed data file. (Optional later: a GitHub Action cron to scrape in the cloud.)

## 9. Snapshot (informational, regenerate on each run)

49 events on the calendar · 658 valid club rows · STAH is the most active club (token `STAH`).
Current Overall (all groups): STAH 72 · CCT 58 · INTERARMAS 52 · CTA 37 · CTCLINS 34.
