#!/usr/bin/env python3
"""Build the validated cell-count SQLite database."""

import sys
from pathlib import Path

from cell_pipeline.loading import build_database as build_database_file


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "cell-count.csv"
DATABASE_PATH = ROOT / "cell-count.db"


def build_database() -> None:
    row_count = build_database_file(
        CSV_PATH, DATABASE_PATH,
        expected_rows=10_500,
        expected_treatment_days={0, 7, 14},
    )
    print(f"Created {DATABASE_PATH.name}: {row_count:,} population rows.")


def main() -> None:
    try:
        build_database()
    except Exception as error:
        print(f"Data load failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
