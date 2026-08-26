# Immune Cell-Count Analysis

This repository currently implements Part 1 of the analysis pipeline: converting
the supplied CSV into a validated SQLite database that subsequent analyses can
use as their trusted data source.

## Setup and data loading

From the repository root, run:

```bash
make setup
make pipeline
```

Equivalently, after installing `requirements.txt`, run `python load_data.py`.
The loader creates `cell-count.db` in the repository root. It is deterministic
and safe to rerun: each run deletes the existing database and builds a clean one
from scratch, so rows never accumulate between runs.

The loader verifies the source column layout, allowed nullability and integer values. It
also checks the expected 10,500 source rows, 52,500 database measurement rows,
10,500 unique sample IDs, five populations, treatment days 0/7/14, database row
and distinct-sample counts, treatment-day bounds, the sum
of `b_cell`, declared SQLite types, and the primary key. Source responses are
converted from `yes`/`no`/blank to `1`/`0`/SQL `NULL`. Any failure exits with
a nonzero status and removes the incomplete database.

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

The pipeline established here is:

```text
cell-count.csv -> load_data.py -> validated cell-count.db -> Parts 2-4
```

As later parts are implemented, their analysis commands can be appended to the
`pipeline` target after the loader so downstream work only runs after validation.

## Code structure

`load_data.py` coordinates the clean database rebuild and provides the required
root executable. The `cell_pipeline` package separates its supporting concerns:
`schema.py` defines the source columns and SQLite schema, `transform.py` reads
and reshapes the CSV, and `validation.py` verifies the loaded database. This
keeps the loading workflow visible in the required script while making its
supporting operations independently reusable and testable.
