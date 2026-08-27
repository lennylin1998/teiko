#!/usr/bin/env python3
"""Export per-sample immune-cell relative frequencies."""

import sys
from pathlib import Path

from cell_pipeline.frequencies import export_relative_frequencies as export_frequency_file


ROOT = Path(__file__).resolve().parent
DATABASE_PATH = ROOT / "cell-count.db"
OUTPUT_PATH = ROOT / "docs" / "data" / "relative-frequency.csv"


def export_relative_frequencies() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row_count = export_frequency_file(DATABASE_PATH, OUTPUT_PATH)
    print(f"Created docs/data/{OUTPUT_PATH.name}: {row_count:,} rows.")


def main() -> None:
    try:
        export_relative_frequencies()
    except Exception as error:
        print(f"Relative-frequency export failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
