import csv
import sqlite3

from cell_pipeline.frequencies import export_relative_frequencies
from cell_pipeline.loading import build_database


def test_source_to_frequency_csv_pipeline(valid_source_frame, tmp_path):
    source = tmp_path / "cell-count.csv"
    database = tmp_path / "cell-count.db"
    output = tmp_path / "relative-frequency.csv"
    valid_source_frame.to_csv(source, index=False)

    build_database(source, database, expected_rows=3)
    export_relative_frequencies(database, output)

    with sqlite3.connect(database) as connection:
        database_counts = dict(connection.execute(
            "SELECT sample || ':' || population, count FROM samples"
        ))
    with output.open(newline="", encoding="utf-8") as handle:
        output_rows = list(csv.DictReader(handle))

    assert len(output_rows) == 15
    assert all(
        int(row["count"]) == database_counts[f'{row["sample"]}:{row["population"]}']
        for row in output_rows
    )
