#!/usr/bin/env python3
"""Build the validated cell-count SQLite database."""

import sqlite3
import sys
from pathlib import Path

from cell_pipeline.schema import CREATE_TABLE_SQL
from cell_pipeline.transform import read_source, reshape_population_counts_to_rows
from cell_pipeline.validation import validate_database


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "cell-count.csv"
DATABASE_PATH = ROOT / "cell-count.db"


def build_database() -> None:
    source_frame = read_source(CSV_PATH)
    long_frame = reshape_population_counts_to_rows(source_frame)
    DATABASE_PATH.unlink(missing_ok=True)

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(CREATE_TABLE_SQL)
            long_frame.to_sql(
                "samples",
                connection,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=5_000,
            )
            validate_database(connection, source_frame, long_frame)
    except Exception:
        DATABASE_PATH.unlink(missing_ok=True)
        raise

    print(
        f"Created {DATABASE_PATH.name}: {len(long_frame):,} population rows, "
        f"{source_frame['sample'].nunique():,} unique samples, validated successfully."
    )


def main() -> None:
    try:
        build_database()
    except Exception as error:
        print(f"Data load failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
