# Data notes, provenance and caveats

This repository rebuilds the analysis from a published Power BI dashboard rather than from raw case
surveillance data. Everything below documents how each number was obtained and where the source is
ambiguous, so that anyone reusing the dataset knows exactly what they are holding.

## Source of record

| Item | Detail |
| --- | --- |
| Publication | *Nigeria Disease Prevalence Dashboard: Key Insights from 10 States* |
| Author | Christian Iyayi |
| Published | 21 October 2026 (Medium) |
| Artifact analysed | Power BI "Nigeria Disease Prevalence Dashboard" with 4 disease KPIs, a state slicer, a top-3 breakdown and a Nigeria map |
| Scope | 10 states, 4 diseases |

The article prose and the embedded dashboard screenshot (`assets/original/powerbi-dashboard.png`)
are the only sources. No underlying CSV, database extract or API was published.

## How the numbers were captured

1. **Disease totals** — read directly from the four KPI cards at the top of the dashboard and
   cross-checked against the article prose. Both agree exactly: 71,490 / 23,750 / 5,400 / 4,980.
2. **COVID-19 by state** — taken from the article prose where a figure is stated, and from the map
   tooltips in the dashboard screenshot where the prose is silent. Each row in
   `data/covid19_by_state.csv` records which source was used and a confidence rating.
3. **Boundaries** — Nigeria ADM1 geometry from geoBoundaries (release of GRID3 state boundaries,
   CC BY 4.0), reduced to three decimal places for repository size.

## Known inconsistencies

These are properties of the source, not errors introduced here. They are listed so the repository can
be used responsibly.

### 1. State figures do not sum to the COVID-19 KPI

The dashboard KPI card reports **5,400 COVID-19 cases**, but the published state-level values add up
to **46,140**. The two cannot both describe the same measure. Possible explanations include a measure
filtered differently on the KPI card, a scale mismatch, or tooltip values that represent a different
aggregation entirely.

**How this repository treats it:** the KPI card is used for the national disease-burden totals (because
all four disease totals were quoted from it consistently), while state values are used **only for
relative ranking and geography**. Do not sum the state column and expect it to reconcile.

See `assets/figures/fig05_reconciliation.png`.

### 2. Kaduna: 4,980 in the prose vs 9,480 on the map

The prose lists Kaduna at 4,980 COVID-19 cases — the same figure as the national TB total, which
suggests a copy error. The map label reads **9,480**. This repository uses 9,480 and flags the row as
`Medium` confidence.

### 3. Kano never appears in the prose

Kano is included in the dashboard state slicer and carries a map label of **10,620** — the largest
single state value — yet it is absent from the article narrative and from the prose list of top three
states. It is included here from the map label, flagged `Medium` confidence.

### 4. Oyo has no published value

Oyo appears in the state slicer but carries neither a prose figure nor a legible map label. The row is
kept with an empty `cases` field and `Not reported` as its source, so the gap is visible rather than
silently dropped.

### 5. Abuja's map label is only partially legible

The FCT tooltip is compressed by the label box in the screenshot. The prose figure of **6,500** is
used.

### 6. "10 states" is a fixed scope, not a national total

Every figure describes the ten states in the dashboard filter, not Nigeria as a whole. The repository
never extrapolates to a national burden.

## What the numbers do not tell you

- **No denominators.** Without state populations, case counts cannot be turned into prevalence or
  incidence rates, so a large state will look worse than a small one almost by construction.
- **No time dimension.** The dashboard shows a single snapshot; no trend, seasonality or reporting
  delay can be read from it.
- **No case definitions.** Test availability differs by state and strongly shapes COVID-19 counts in
  particular.
- **Different diseases are not comparable in severity.** Case counts say nothing about mortality,
  disability or cost, only reported volume.

## Suggested next steps for a stronger version

1. Replace hand-read tooltip values with the underlying table exported from Power BI.
2. Attach population denominators (e.g. NPC 2006 census projections or WorldPop) and report cases per
   100,000.
3. Add a reporting-period column and retain historical extracts so trends become measurable.
4. Publish the DAX measures alongside the dashboard so KPI and visual filters can be audited.
