# FPTE Championship Tracker — Project Reference

This document contains all the information needed to rebuild the FPTE club championship tracker from scratch: data sources, HTML structure, business rules, classification logic, and output schemas.

---

## 1. Context

**FPTE** (Federação Paulista de Tiro Esportivo) is the São Paulo state shooting sports federation. It runs a season-long **club championship** across multiple shooting disciplines. Throughout the year, clubs compete in events. The federation tallies cumulative points per discipline to determine which club wins each sub-championship at the end of the season.

The goal of this project is to:
1. Scrape all club results from the FPTE website for a given year.
2. Apply the championship classification rules to compute standings.
3. Track how standings evolve over the season (event by event).
4. Produce a dashboard-ready dataset.

---

## 2. Data Source

**Website:** `https://fpte.org.br`

**Event list page:** `https://fpte.org.br/template.php?pagina=resultados/{YEAR}`

**Individual event page:** `https://fpte.org.br/template.php?pagina=resultados/{YEAR}/{EVENT_ID}`

The event ID is the numeric suffix in the event's URL (e.g., `/resultados/2025/981` → event ID `981`).

### Page encoding

All pages use **ISO-8859-1** (Latin-1) encoding. Set this explicitly when fetching, otherwise accented characters (ã, ç, é, etc.) will be garbled.

---

## 3. Scraping: Event List Page

URL: `https://fpte.org.br/template.php?pagina=resultados/{YEAR}`

Find the HTML element: `<table id="tabela_resultado">` → `<tbody>` → each `<tr>`.

Each row has 5 `<td>` cells:

| Cell index | Content | Example |
|---|---|---|
| 0 | Start date `DD/MM` | `31/01` |
| 1 | End date `DD/MM` | `01/02` |
| 2 | Event name (as `<a>` link with `href`) | `1ª Etapa Copa FPTE` |
| 3 | Month/year `MM/YYYY` | `01/2025` |
| 4 | Scope (`Estadual` or `Nacional`) | `Estadual` |

**Full date construction:** combine cell 0 or 1 with the year from cell 3.
- `"31/01"` + `"01/2025"` → `"31/01/2025"`

**Event URL:** prepend `https://fpte.org.br` to the `href` from the `<a>` in cell 2.

---

## 4. Scraping: Individual Event Page (Club Results)

URL: `https://fpte.org.br/template.php?pagina=resultados/{YEAR}/{EVENT_ID}`

Each event page contains **two types of tables**, both with `class="display"`:
- **Athlete tables** — have `class="mytables"` among their classes. These show individual athlete results. **Ignore these.**
- **Club tables** — have `class="display"` but **NOT** `class="mytables"`. These are what we need.

### Identifying club tables

A club table's `<thead>` has a first `<tr>` containing a single `<th colspan="7">` whose text follows the pattern `"{Discipline Name} - Clubes"`. Skip any table whose header contains `"Resultado Geral"` (that is the overall summary table).

To get the discipline name: strip the ` - Clubes` suffix from the header text.

### Club table columns (7 columns)

| Col index | Label | Content |
|---|---|---|
| 0 | PS | Overall position in listing (e.g. `1ª`) |
| 1 | CL | Championship classification rank (only filled if the club had 3+ athletes) |
| 2 | Club | Club abbreviation (e.g. `INTERARMAS`, `.556`) |
| 3 | Athletes | Athlete registry number + name, one per line (br-separated). Format: `"18856  Rodrigo de Andrade Oliveira"` |
| 4 | RF scores | Individual score per athlete, one per line (br-separated) |
| 5 | TT (Team Total) | Sum of the 3 best individual scores for this club in this discipline |
| 6 | PT (Points) | Championship points awarded to this club. **Empty if the club did not have 3+ athletes.** |

### Validity rule

**A club result is VALID only if column 6 (PT) is non-empty.** An empty PT cell means the club had fewer than 3 eligible athletes competing in that discipline at that event, so the result does not count for the championship.

### Score parsing

The website uses **Portuguese/Brazilian number formatting**:
- Comma as decimal separator: `"108,06"` → `108.06`
- Dot as thousands separator: `"1.699"` → `1699.0`
- Both: `"1.699,00"` → `1699.0`

Always handle all three cases when converting score strings to floats.

---

## 5. Raw Data Schema

One row per club per discipline per event.

| Field | Type | Description |
|---|---|---|
| `event_id` | int | Numeric event ID from URL |
| `event_name` | str | Full event name |
| `start_date` | str `DD/MM/YYYY` | Event start date |
| `end_date` | str `DD/MM/YYYY` | Event end date |
| `month_year` | str `MM/YYYY` | Month/year label from the listing page |
| `scope` | str | `Estadual` or `Nacional` |
| `discipline` | str | Discipline name (stripped of " - Clubes") |
| `club` | str | Club abbreviation |
| `position` | str | Position in event listing (e.g. `1ª`) |
| `num_athletes` | int | Number of athletes who competed for this club |
| `athletes` | str | Pipe-separated athlete names (e.g. `"Name A \| Name B \| Name C"`) |
| `individual_scores` | str | Pipe-separated individual scores |
| `team_total` | float | Sum of the 3 best individual scores |
| `championship_points` | float | Points awarded (as per event-level ranking) |
| `valid` | bool | `True` if PT column was non-empty (3+ athletes) |

---

## 6. Championship Classification Rules

### 6.1 Validity filter

Only rows with `valid = True` enter the championship calculation. Rows where the club had fewer than 3 athletes are excluded entirely.

### 6.2 Sub-championship grouping

Disciplines are grouped into **sub-championships**. A club's standing is computed separately per sub-championship. The mapping is fixed and provided in a lookup table (see Section 8).

There are **8 sub-championships**:

| Sub-championship | Description |
|---|---|
| ISSF | Olympic shooting disciplines (air rifle, pistol, 3-position, etc.) |
| Fuzil Esportivo | Sporting rifle disciplines (20m and 50m categories) |
| Provas Estaduais | State-level specialty disciplines |
| Provas Nacionais | National-level specialty disciplines (Duelo, F-class, etc.) |
| Rifle Internacional | International rifle disciplines (CMP, NRA, WRABF) |
| Tiro ao Prato Olímpico | Olympic clay target (Skeet, Fossa Olímpica, Fossa Double) |
| Trap Nacional | National trap disciplines (Trap 25, Trap 50, Trap Double, Trap Nacional) |

### 6.3 Standings calculation (per sub-championship)

For each unique combination of `(sub_championship, discipline, club)` across the full season:

**Step 1 — Top-5 score sum:**
Take the club's valid `team_total` scores across all events for that discipline and sum the **5 highest** values. If a club has fewer than 5 valid results, sum all of them.

**Step 2 — Rank within discipline:**
Rank clubs within each discipline by their top-5 score sum (highest = rank 1). Use `min` rank method (ties share the best rank).

**Step 3 — Convert rank to points:**

| Discipline rank | Championship points |
|---|---|
| 1st | 5 |
| 2nd | 4 |
| 3rd | 3 |
| 4th | 2 |
| 5th | 1 |
| 6th and beyond | 0 |

Clubs with a top-5 score sum of 0 always receive 0 points regardless of rank.

**Step 4 — Sub-championship total (for the dashboard ranking):**
Sum all `discipline_points` a club earned across all disciplines within that sub-championship.

### 6.4 Summary of standings output schema

One row per `(sub_championship, discipline, club)`:

| Field | Description |
|---|---|
| `sub_championship` | Sub-championship name |
| `discipline` | Discipline name |
| `club` | Club abbreviation |
| `valid_participations` | Count of valid events this club competed in for this discipline |
| `top5_score_sum` | Sum of the 5 highest team_total scores |
| `discipline_rank` | Club's rank within the discipline |
| `discipline_points` | Points earned (0–5) |

---

## 7. Evolution (Season Progression) Calculation

This tracks how the standings change over the course of the season, event by event.

**For each event** (ordered chronologically by `end_date`):
1. Take all valid results up to and including that event's `end_date`.
2. Run the full standings calculation (Steps 1–4 from Section 6.3) on this subset.
3. For each `(sub_championship, club)`, record the cumulative `total_points` at that snapshot.

### Evolution output schema

One row per `(event, sub_championship, club)`:

| Field | Description |
|---|---|
| `snapshot_date` | `end_date` of the event that triggered this snapshot (`DD/MM/YYYY`) |
| `event_id` | Event ID |
| `event_name` | Event name |
| `sub_championship` | Sub-championship name |
| `club` | Club abbreviation |
| `total_points` | Cumulative championship points at this point in the season |

---

## 8. Discipline → Sub-Championship Mapping

This is the full mapping table used to assign each discipline to a sub-championship.

```
discipline,sub_championship
Carabina 3 Posições Feminino,ISSF
Carabina 3 Posições Masculino,ISSF
Carabina de Ar,ISSF
Carabina Deitado,ISSF
Pistola 25m feminino (Sport),ISSF
Pistola 25m Masculino,ISSF
Pistola 50m Masculino (Livre),ISSF
Pistola de Ar,ISSF
Pistola de Fogo Central Masculino,ISSF
Pistola de Tiro Rápido Masculino,ISSF
Pistola Standard Masculino,ISSF
Fuzil 20 Metros Intermediário,Fuzil Esportivo
Fuzil 20 Metros Maior,Fuzil Esportivo
Fuzil 20 Metros Menor,Fuzil Esportivo
Fuzil 50 Metros Maior Bancada,Fuzil Esportivo
Fuzil 50 Metros Maior de Pé,Fuzil Esportivo
Fuzil 50 Metros Menor Bancada,Fuzil Esportivo
Fuzil Esportivo 150m,Fuzil Esportivo
Baixa Luminosidade Maior,Provas Estaduais
Baixa Luminosidade Menor,Provas Estaduais
Caça Shotgun Curta Cartucheira/pistolão,Provas Estaduais
Caça Shotgun Maior,Provas Estaduais
Caça Shotgun Menor,Provas Estaduais
Carabina Mira Aberta 10m Cal. 5,5,Provas Estaduais
Carabina Mira Aberta de Ar 25m,Provas Estaduais
Carabina Puma 7x3,Provas Estaduais
Copa FPTE - Carabina,Provas Estaduais
Copa FPTE - Espingarda,Provas Estaduais
Copa FPTE - Pistola Maior,Provas Estaduais
Copa FPTE - Pistola Menor,Provas Estaduais
Copa FPTE - Revólver Maior,Provas Estaduais
Copa FPTE - Revólver Menor,Provas Estaduais
Copa FPTE - Snub,Provas Estaduais
Duelo 20 Segundos 10 metros - Red Dot,Provas Estaduais
Helice ZZ,Provas Estaduais
Mini Trap,Provas Estaduais
Perfect Shot Pistola,Provas Estaduais
Perfect Shot Revolver,Provas Estaduais
Trap 25 Baixa Luminosidade,Provas Estaduais
Carabina Mira Aberta 10m,Provas Nacionais
Carabina Mira Aberta 25m - Custom,Provas Nacionais
Carabina Mira Aberta 25m - Sporter,Provas Nacionais
Carabina Mira Aberta 50m - Calibre Maior,Provas Nacionais
Carabina Mira Aberta 50m - Calibre Menor Custom,Provas Nacionais
Carabina Mira Aberta 50m - Calibre Menor Sporter,Provas Nacionais
Duelo 20 segundos 10 metros - Pistola Maior (38/380/765/40/45/9mm),Provas Nacionais
Duelo 20 segundos 10 metros - Pistola Menor,Provas Nacionais
Duelo 20 segundos 10 metros - Revólver Maior .32 .38 .357 9mm .454 .44 e .45,Provas Nacionais
Duelo 20 segundos 10 metros - Revólver Menor,Provas Nacionais
Duelo 20 segundos 10 metros - Revólver Snub,Provas Nacionais
Duelo 20 Segundos 25 metros - Pistola Calibre Maior (38/380/765/40/45/9mm),Provas Nacionais
Duelo 20 Segundos 25 metros - Pistola Calibre Menor (.22),Provas Nacionais
Duelo 20 Segundos 25 metros - Revólver Calibre Maior (.32 .38 .357 9mm .454 .44 e .45),Provas Nacionais
Duelo 20 Segundos 25 metros - Revólver Calibre Menor (.22),Provas Nacionais
Duelo 20 Segundos 25 metros - Revólver Snub,Provas Nacionais
F-class F/tr,Provas Nacionais
F-class Open,Provas Nacionais
Carabina Cmp Sporter - Mira Aberta,Rifle Internacional
Carabina Cmp Sporter - Mira Fechada,Rifle Internacional
Carabina Nra - Mira Metalica,Rifle Internacional
Carabina Nra - Mira Otica,Rifle Internacional
Carabina WRABF Ar Rifle - Heavy,Rifle Internacional
Carabina WRABF Ar Rifle - Light,Rifle Internacional
Carabina WRABF Ar Rifle - Springer (mola),Rifle Internacional
Carabina WRABF Ar Rifle - Unlimited (50m),Rifle Internacional
Carabina WRABF Rimfire - Heavy,Rifle Internacional
Carabina WRABF Rimfire - Internacional Sporter,Rifle Internacional
Carabina WRABF Rimfire - Light,Rifle Internacional
F-class Rimfire F/tr,Rifle Internacional
F-class Rimfire Open,Rifle Internacional
Fossa Double Feminino,Tiro ao Prato Olímpico
Fossa Double Masculino,Tiro ao Prato Olímpico
Fossa Olimpica Feminino,Tiro ao Prato Olímpico
Fossa Olimpica Masculino,Tiro ao Prato Olímpico
Skeet Feminino,Tiro ao Prato Olímpico
Skeet Masculino,Tiro ao Prato Olímpico
Trap 25,Trap Nacional
Trap 50,Trap Nacional
Trap Double,Trap Nacional
Trap Nacional,Trap Nacional
```

**Important matching note:** When joining discipline names from scraped data to this table, normalize both sides: lowercase, strip leading/trailing whitespace, collapse internal multiple spaces. Discipline names on the website can have minor capitalization or spacing differences.

---

## 9. Known Edge Cases and Gotchas

- **Decimal separators:** The website uses Portuguese formatting (comma = decimal, dot = thousands). Parse all score strings explicitly.
- **Non-breaking spaces:** The website uses `\xa0` (non-breaking space) extensively. Strip these before processing text.
- **"Resultado Geral por Clubes" table:** Each event page includes an aggregate summary table whose header contains "Resultado Geral". Skip it — it's not a per-discipline table.
- **Discipline name in HTML:** The raw header is `"{Discipline} - Clubes"`. Strip the ` - Clubes` suffix to get the clean discipline name.
- **Events with no club tables:** Some events have only individual athlete results (no club-level competition). These pages simply won't have any matching club tables and should be silently skipped.
- **Clubs with < 3 athletes:** They appear in the raw table but their PT cell is empty. Exclude them from all championship calculations.
- **Ties in discipline rank:** Use `min` rank method — if two clubs tie for 1st, both receive rank 1 and 5 points; the next club receives rank 3.
- **Discipline matching may diverge over seasons:** New disciplines may appear on the website that are not yet in the mapping table. These should be flagged/logged but should not crash the pipeline. They receive no sub-championship assignment and are excluded from standings.

---

## 10. Dashboard Data Requirements

To build a complete championship dashboard, the following views are useful:

### Standings view
- Filter by `sub_championship`
- Group by `club`, sum `discipline_points` → `total_points`
- Sort descending by `total_points`
- Optionally drill down to individual discipline contributions per club

### Discipline leaderboard
- Filter by `sub_championship` and `discipline`
- Show: `club`, `valid_participations`, `top5_score_sum`, `discipline_rank`, `discipline_points`

### Evolution / season progression chart
- X-axis: `snapshot_date` or `event_name` (ordered chronologically)
- Y-axis: `total_points`
- Series: one line per `club`
- Filter by `sub_championship`

### Event results view (raw data)
- Filter by `event_name` and `discipline`
- Show: `club`, `num_athletes`, `athletes`, `individual_scores`, `team_total`
- Useful for verifying source data

---

## 11. Update Workflow (Manual)

Since this project is updated manually (not automated):

1. Navigate to `https://fpte.org.br/template.php?pagina=resultados/{YEAR}` to confirm new events have been published.
2. Run the scraper to fetch all event data for the year (it will re-scrape all events from scratch — no incremental mode needed given the small dataset size).
3. Apply validity filter (keep only `valid = True` rows).
4. Run the standings and evolution calculations.
5. Refresh the dashboard data source.

The entire dataset for a full season is small (hundreds to low thousands of rows), so full re-scraping from scratch each update is practical and simpler than incremental approaches.

---

## 12. Python Dependencies (reference implementation)

```
requests
beautifulsoup4
pandas
tqdm
```

For Google Sheets upload (optional, only if using Sheets as output):
```
gspread
gspread-dataframe
```
