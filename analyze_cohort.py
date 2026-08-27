#!/usr/bin/env python3
"""Export the required default Part 4 cohort summaries."""

import sys
from pathlib import Path

from cell_pipeline.cohort_analysis import export_default_cohort


ROOT = Path(__file__).resolve().parent


def main() -> None:
    try:
        summary = export_default_cohort(ROOT / "cell-count.db", ROOT / "docs" / "data")
        print(
            "Created Part 4 cohort tables: "
            f"{summary['number_of_samples']:,} samples, "
            f"{summary['number_of_subjects']:,} subjects."
        )
    except Exception as error:
        print(f"Cohort analysis failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
