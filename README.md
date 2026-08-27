# Immune Cell-Count Analysis

This repository implements Parts 1–3 of the analysis pipeline: converting the
supplied CSV into a validated SQLite database, exporting immune-cell relative
frequencies, and comparing miraclib responders with non-responders.

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

Open `http://localhost:8000`. To choose another port, run `make dashboard
PORT=3000`. In GitHub Codespaces, open the forwarded port from the Ports panel.
The static website is live on GitHub Pages:
[https://lennylin1998.github.io/teiko/](https://lennylin1998.github.io/teiko/).

Equivalently, after installing `requirements.txt`, run `python load_data.py`.
The loader creates `cell-count.db` in the repository root. It is deterministic
and safe to rerun: each run builds a temporary database and replaces the old
one only after a successful load, so rows never accumulate.

Runtime validation is limited to the external input, `cell-count.csv`. It checks
the source column layout, required values, integer fields, nonnegative population
counts, positive per-sample totals, response values, 10,500 unique sample IDs,
and treatment days 0/7/14. Source responses are converted from
`yes`/`no`/blank to `1`/`0`/SQL `NULL`. The generated database also enforces its
schema through SQLite constraints.

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
repeated across population rows to avoid joins at the current scale. At substantially larger scale, reusable
entities such as projects, subjects, and samples could be normalized into
separate relational tables, with cell measurements stored in a related fact
table. Indexes and partitioning could then be chosen for measured query patterns.

The pipeline is:

```text
cell-count.csv -> load_data.py -> validated cell-count.db
                                      |
                                      v
                    docs/data/relative-frequency.csv
```

`make pipeline` runs the relative-frequency analysis only after Part 1 succeeds.
It writes `docs/data/relative-frequency.csv` for direct use by the static
dashboard. The output has the columns `sample`, `total_count`, `population`,
`count`, and `percentage`, with 52,500 rows (five populations for each of 10,500
samples). `analyze_frequencies.py` calculates totals with `SUM(count) OVER
(PARTITION BY sample)`. Pipeline correctness—including database shape,
source-to-database mapping, frequency totals, percentage sums, and CSV
output—is covered by pytest.

Part 3 filters to melanoma subjects treated with miraclib with PBMC samples,
then averages days 0, 7, and 14 within each subject and population. It writes
`docs/data/responder-boxplots.png` (five response-group boxplot pairs) and
`docs/data/responder-statistics.csv` (five Welch t-tests with raw p-values,
group means, differences, and subject counts), ready for the static dashboard.
A p-value below 0.05 is reported as significant. The same subject-level table
supplies both the plot and tests.

## Code structure

`load_data.py`, `analyze_frequencies.py`, and `analyze_responders.py` are thin
executable entry points.
The `cell_pipeline` package separates source validation, transformations,
database loading, schema definitions, and frequency analysis into reusable
modules. The `tests/` directory verifies those modules with small fixtures and
temporary databases and files. Run the tests with `make test`, or run tests and
the production pipeline together with `make check`.
