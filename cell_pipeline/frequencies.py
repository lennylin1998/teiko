"""Calculate and export per-sample immune-cell relative frequencies."""

import csv
import sqlite3
from pathlib import Path


OUTPUT_COLUMNS = ["sample", "total_count", "population", "count", "percentage"]

RELATIVE_FREQUENCY_SQL = """
WITH population_totals AS (
    SELECT sample, population, count,
           SUM(count) OVER (PARTITION BY sample) AS total_count
    FROM samples
)
SELECT sample, total_count, population, count,
       count * 100.0 / total_count AS percentage
FROM population_totals
ORDER BY sample, population
"""


def calculate_relative_frequencies(
    connection: sqlite3.Connection,
) -> list[tuple[str, int, str, int, float]]:
    return list(connection.execute(RELATIVE_FREQUENCY_SQL))


def export_relative_frequencies(database_path: Path, output_path: Path) -> int:
    if not database_path.is_file():
        raise FileNotFoundError(f"Database not found: {database_path}")

    with sqlite3.connect(database_path) as connection:
        rows = calculate_relative_frequencies(connection)

    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.unlink(missing_ok=True)
    try:
        with temporary_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(OUTPUT_COLUMNS)
            writer.writerows(rows)
        temporary_path.replace(output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return len(rows)
