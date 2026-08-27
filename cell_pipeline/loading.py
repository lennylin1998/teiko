"""Build the SQLite database from the validated source CSV."""

import sqlite3
from pathlib import Path

from .schema import CREATE_TABLE_SQL
from .transform import normalize_source_types, read_source_csv, reshape_population_counts_to_rows
from .validation import validate_source


def build_database(
    source_path: Path,
    database_path: Path,
    *,
    expected_rows: int | None = None,
    expected_treatment_days: set[int] | None = None,
) -> int:
    source_frame = read_source_csv(source_path)
    validate_source(
        source_frame,
        expected_rows=expected_rows,
        expected_treatment_days=expected_treatment_days,
    )
    normalized_frame = normalize_source_types(source_frame)
    long_frame = reshape_population_counts_to_rows(normalized_frame)

    temporary_path = database_path.with_suffix(database_path.suffix + ".tmp")
    temporary_path.unlink(missing_ok=True)
    try:
        with sqlite3.connect(temporary_path) as connection:
            connection.execute(CREATE_TABLE_SQL)
            long_frame.to_sql(
                "samples", connection, if_exists="append", index=False,
                method="multi", chunksize=5_000,
            )
        temporary_path.replace(database_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return len(long_frame)
