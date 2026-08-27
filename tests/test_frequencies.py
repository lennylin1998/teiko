import csv
import math
import sqlite3

import pytest

from cell_pipeline.frequencies import (
    OUTPUT_COLUMNS,
    calculate_relative_frequencies,
    export_relative_frequencies,
)
from cell_pipeline.loading import build_database


@pytest.fixture
def sample_database(valid_source_frame, tmp_path):
    source = tmp_path / "cell-count.csv"
    database = tmp_path / "cell-count.db"
    valid_source_frame.to_csv(source, index=False)
    build_database(source, database)
    return database


def test_frequency_calculation_has_correct_totals_and_percentages(sample_database):
    with sqlite3.connect(sample_database) as connection:
        rows = calculate_relative_frequencies(connection)

    sample_rows = [row for row in rows if row[0] == "sample-1"]
    assert len(sample_rows) == 5
    assert {row[1] for row in sample_rows} == {150}
    assert sum(row[3] for row in sample_rows) == 150
    assert math.isclose(sum(row[4] for row in sample_rows), 100.0)
    assert sample_rows == sorted(sample_rows, key=lambda row: (row[0], row[2]))


def test_frequency_export_writes_expected_csv(sample_database, tmp_path):
    output = tmp_path / "relative-frequency.csv"

    row_count = export_relative_frequencies(sample_database, output)

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        assert handle.closed is False
    assert row_count == 15
    assert list(rows[0]) == OUTPUT_COLUMNS
    assert rows[0] == {
        "sample": "sample-1",
        "total_count": "150",
        "population": "b_cell",
        "count": "10",
        "percentage": str(10 * 100.0 / 150),
    }


def test_frequency_export_requires_database(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_relative_frequencies(tmp_path / "missing.db", tmp_path / "output.csv")
