"""Read, validate, and reshape the source CSV."""

from pathlib import Path

import pandas as pd

from .schema import CELL_POPULATIONS, INTEGER_COLUMNS, METADATA_COLUMNS, SOURCE_COLUMNS, TEXT_COLUMNS


def read_source(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Source CSV not found: {path}")

    frame = pd.read_csv(path, dtype={column: "string" for column in TEXT_COLUMNS})
    if list(frame.columns) != SOURCE_COLUMNS:
        raise ValueError("Unexpected CSV columns. Expected, in order: " + ", ".join(SOURCE_COLUMNS))

    missing = [
        column for column in frame.columns
        if column != "response" and frame[column].isna().any()
    ]
    if missing:
        raise ValueError(f"CSV contains missing values in: {', '.join(missing)}")

    for column in INTEGER_COLUMNS:
        numeric = pd.to_numeric(frame[column], errors="raise")
        if not (numeric % 1 == 0).all():
            raise ValueError(f"Column {column!r} contains non-integer values")
        frame[column] = numeric.astype("int64")

    invalid_responses = set(frame["response"].dropna().unique()) - {"yes", "no"}
    if invalid_responses:
        raise ValueError(f"Unexpected response values: {sorted(invalid_responses)}")
    frame["response"] = frame["response"].map({"yes": 1, "no": 0}).astype("Int64")

    if len(frame) != 10_500:
        raise ValueError(f"Expected 10,500 CSV rows, found {len(frame):,}")
    if frame["sample"].nunique() != 10_500:
        raise ValueError("Expected 10,500 unique sample values")

    treatment_days = set(frame["time_from_treatment_start"].unique())
    if treatment_days != {0, 7, 14}:
        raise ValueError(f"Expected treatment days 0, 7, and 14; found {sorted(treatment_days)}")
    return frame


def reshape_population_counts_to_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.melt(
        id_vars=METADATA_COLUMNS,
        value_vars=CELL_POPULATIONS,
        var_name="population",
        value_name="count",
    )
