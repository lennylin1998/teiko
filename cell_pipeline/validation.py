"""Runtime validation for the external cell-count CSV."""

from collections.abc import Collection

import pandas as pd

from .schema import CELL_POPULATIONS, INTEGER_COLUMNS, SOURCE_COLUMNS


def validate_source(
    frame: pd.DataFrame,
    *,
    expected_rows: int | None = None,
    expected_treatment_days: Collection[int] | None = None,
) -> None:
    """Validate the untrusted source data before transformation and loading."""
    if list(frame.columns) != SOURCE_COLUMNS:
        raise ValueError(
            "Unexpected CSV columns. Expected, in order: " + ", ".join(SOURCE_COLUMNS)
        )

    required = [column for column in SOURCE_COLUMNS if column != "response"]
    missing = [column for column in required if frame[column].isna().any()]
    if missing:
        raise ValueError(f"CSV contains missing values in: {', '.join(missing)}")

    numeric_columns: dict[str, pd.Series] = {}
    for column in INTEGER_COLUMNS:
        try:
            numeric = pd.to_numeric(frame[column], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(f"Column {column!r} contains non-numeric values") from error
        if numeric.isna().any() or not (numeric % 1 == 0).all():
            raise ValueError(f"Column {column!r} contains non-integer values")
        numeric_columns[column] = numeric

    negative_populations = [
        column for column in CELL_POPULATIONS if (numeric_columns[column] < 0).any()
    ]
    if negative_populations:
        raise ValueError(
            "Population counts must be nonnegative in: " + ", ".join(negative_populations)
        )
    population_totals = sum(numeric_columns[column] for column in CELL_POPULATIONS)
    if (population_totals <= 0).any():
        raise ValueError("Every sample must have a positive total population count")

    invalid_responses = set(frame["response"].dropna().unique()) - {"yes", "no"}
    if invalid_responses:
        raise ValueError(f"Unexpected response values: {sorted(invalid_responses)}")

    if expected_rows is not None and len(frame) != expected_rows:
        raise ValueError(f"Expected {expected_rows:,} CSV rows, found {len(frame):,}")
    if frame["sample"].duplicated().any():
        raise ValueError("Source CSV contains duplicate sample values")

    if expected_treatment_days is not None:
        actual_days = set(numeric_columns["time_from_treatment_start"].astype(int))
        expected_days = set(expected_treatment_days)
        if actual_days != expected_days:
            raise ValueError(
                f"Expected treatment days {sorted(expected_days)}; found {sorted(actual_days)}"
            )
