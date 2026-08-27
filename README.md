# Immune Cell-Count Analysis

This repository implements Parts 1–4 of the analysis pipeline: converting the
supplied CSV into a validated SQLite database, exporting immune-cell relative
frequencies, comparing miraclib responders with non-responders, and exploring
filtered cohorts.

## Setup and data loading

This project supports Python 3.12.

From the repository root, run:

```bash
make setup
make pipeline
```

Start the interactive dashboard after generating the outputs:

```bash
make dashboard
```

Streamlit prints the local URL; in GitHub Codespaces, open its forwarded port
from the Ports panel. There's also a hosted version on Streamlit Cloud [here
](http://localhost:8501/).

The Streamlit dashboard reads the generated Part 2–3 files and queries SQLite
for Part 4. Its cohort explorer defaults to melanoma, miraclib, PBMC, and day 0,
while allowing any available condition, treatment (including quintazide), sample
type, and treatment day to be selected.

Equivalently, after installing `requirements.txt`, run `python load_data.py`.
The loader creates `cell-count.db` in the repository root.

## Database schema

The database contains one long-form `samples` table:

| Column | SQLite type | Description |
| --- | --- | --- |
| `sample` | `TEXT` | Unique sample identifier and first part of the primary key. |
| `population` | `TEXT` | Immune cell population and second part of the primary key. |
| `count` | `INTEGER` | Cell count for the sample and population. |
| `project` | `TEXT` | Clinical project identifier. |
| `subject` | `TEXT` | Trial subject identifier. |
| `condition` | `TEXT` | Subject's disease or clinical condition. |
| `age` | `INTEGER` | Subject age in years. |
| `sex` | `TEXT` | Recorded subject sex. |
| `treatment` | `TEXT` | Treatment administered to the subject. |
| `response` | `INTEGER` | Nullable response: `1` for yes, `0` for no, or `NULL`. |
| `sample_type` | `TEXT` | Biological specimen type, such as PBMC. |
| `time_from_treatment_start` | `INTEGER` | Collection day relative to treatment start. |

The five source count columns are normalized into `population` and `count`, so
each sample produces five rows. `(sample, population)` is the composite primary
key: a sample can contain several populations, but each population occurs only
once for that sample. This shape supports population-level filtering and aggregation
without repeating query logic for five separate count columns. Treatment time is an integer because the source contains only
the integral days 0, 7, and 14. `response` is a nullable Boolean represented by
SQLite integers: `yes` becomes `1`, `no` becomes `0`, and blank becomes `NULL`.
A check constraint permits only `0`, `1`, or `NULL`; all other columns are
`NOT NULL`. No secondary indexes are
added because Part 1 has no measured query-performance need for them.

A single table keeps this modest, analysis-oriented dataset easy to query while
normalizing its repeated cell-measurement concept. Sample metadata is intentionally
repeated across population rows to avoid joins at the current scale. 

At a larger scale, projects, subjects, and samples could use separate linked tables, cell counts could live in a measurement fact table, a composite index on condition, treatment, sample type, and treatment day could accelerate cohort filters, and data could be partitioned by project when project-specific queries dominate.


`make pipeline` runs the entire data-analysis pipeline in order and generates
all required outputs:

- **Part 1:** `cell-count.db`, the validated SQLite database.
- **Part 2:** `docs/data/relative-frequency.csv`, the per-sample cell-population frequencies.
- **Part 3:** `docs/data/responder-boxplots.png` and `docs/data/responder-statistics.csv`, the response-group visualization and Welch t-test results.
- **Part 4:** `docs/data/cohort-summary.csv`, `docs/data/samples-by-project.csv`, `docs/data/subjects-by-response.csv`, and `docs/data/subjects-by-sex.csv`, the default baseline-cohort summaries.

Part 1 validates `cell-count.csv`, reshapes its five population columns into
long-form measurement rows, and loads them into `cell-count.db`; later pipeline
steps run only after this database is created successfully.

Part 2 calculates each sample total with `SUM(count) OVER (PARTITION BY sample)`
and exports the columns `sample`, `total_count`, `population`, `count`, and
`percentage`, producing 52,500 rows—five populations for each of 10,500 samples.

Part 3 selects melanoma subjects receiving miraclib with PBMC samples, averages
days 0, 7, and 14 within each subject and population, creates five responder
versus non-responder boxplot pairs, and runs a two-sided Welch t-test for every
population, reporting raw p-values below 0.05 as significant.

Part 4 queries one distinct metadata row per sample for the default melanoma,
miraclib, PBMC, day-0 cohort, then counts samples by project and distinct
subjects by response and sex; the dashboard reuses these functions with
interactive condition, treatment, sample-type, and treatment-day filters.

Pytest covers the pipeline's database shape, source mapping, frequency totals,
percentage sums, cohort filtering, distinct-subject summaries, and output data.

## Code structure

`load_data.py`, `analyze_frequencies.py`, `analyze_responders.py`, and
`analyze_cohort.py` are thin
executable entry points.
The `cell_pipeline` package separates source validation, transformations,
database loading, schema definitions, and frequency analysis into reusable
modules. The `tests/` directory verifies those modules with small fixtures and
temporary databases and files. Run the tests with `make test`, or run tests and
the production pipeline together with `make check`.
