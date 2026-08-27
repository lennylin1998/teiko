"""Database-backed cohort filtering and demographic summaries."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


FILTER_COLUMNS = {
    "condition": "condition",
    "treatment": "treatment",
    "sample_type": "sample_type",
    "time_from_treatment_start": "time_from_treatment_start",
}


def available_filters(database_path: Path) -> dict[str, list[object]]:
    """Return the distinct database values offered by the cohort controls."""
    if not database_path.is_file():
        raise FileNotFoundError(f"Database not found: {database_path}")
    with sqlite3.connect(database_path) as connection:
        return {
            name: [row[0] for row in connection.execute(
                f"SELECT DISTINCT {column} FROM samples ORDER BY {column}"
            )]
            for name, column in FILTER_COLUMNS.items()
        }


def select_cohort(database_path: Path, **filters: object) -> pd.DataFrame:
    """Select one metadata row per sample matching all supplied filters."""
    unknown = set(filters) - set(FILTER_COLUMNS)
    if unknown:
        raise ValueError(f"Unknown cohort filters: {', '.join(sorted(unknown))}")
    if not database_path.is_file():
        raise FileNotFoundError(f"Database not found: {database_path}")

    clauses: list[str] = []
    parameters: list[object] = []
    for name, value in filters.items():
        if value is None:
            continue
        column = FILTER_COLUMNS[name]
        if isinstance(value, str):
            clauses.append(f"lower({column}) = lower(?)")
        else:
            clauses.append(f"{column} = ?")
        parameters.append(value)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with sqlite3.connect(database_path) as connection:
        return pd.read_sql_query(
            f"""
            SELECT DISTINCT sample, project, subject, condition, treatment,
                            sample_type, time_from_treatment_start, response, sex
            FROM samples
            {where}
            ORDER BY sample
            """,
            connection,
            params=parameters,
        )


def summarize_cohort(cohort: pd.DataFrame) -> dict[str, object]:
    """Calculate sample totals and distinct-subject group counts."""
    projects = (
        cohort.groupby("project", dropna=False)["sample"].nunique()
        .rename("number_of_samples").reset_index()
    )
    response_labels = cohort["response"].map({1: "Responder", 0: "Non-responder"}).fillna("Unknown")
    responses = (
        cohort.assign(response=response_labels)
        .groupby("response", dropna=False)["subject"].nunique()
        .rename("number_of_subjects").reset_index()
    )
    sexes = (
        cohort.assign(sex=cohort["sex"].fillna("Unknown"))
        .groupby("sex", dropna=False)["subject"].nunique()
        .rename("number_of_subjects").reset_index()
    )
    return {
        "number_of_samples": int(cohort["sample"].nunique()),
        "number_of_subjects": int(cohort["subject"].nunique()),
        "samples_by_project": projects,
        "subjects_by_response": responses,
        "subjects_by_sex": sexes,
    }


def export_default_cohort(database_path: Path, output_directory: Path) -> dict[str, object]:
    """Export the required melanoma/miraclib/PBMC/baseline Part 4 tables."""
    cohort = select_cohort(
        database_path,
        condition="melanoma",
        treatment="miraclib",
        sample_type="PBMC",
        time_from_treatment_start=0,
    )
    summary = summarize_cohort(cohort)
    output_directory.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        "number_of_samples": summary["number_of_samples"],
        "number_of_subjects": summary["number_of_subjects"],
    }]).to_csv(output_directory / "cohort-summary.csv", index=False)
    for key, filename in (
        ("samples_by_project", "samples-by-project.csv"),
        ("subjects_by_response", "subjects-by-response.csv"),
        ("subjects_by_sex", "subjects-by-sex.csv"),
    ):
        summary[key].to_csv(output_directory / filename, index=False)
    return summary
