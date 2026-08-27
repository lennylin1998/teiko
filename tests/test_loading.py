import sqlite3

import pytest

from cell_pipeline.loading import build_database


def test_build_database_loads_validated_source(valid_source_frame, tmp_path):
    source = tmp_path / "cell-count.csv"
    database = tmp_path / "cell-count.db"
    valid_source_frame.to_csv(source, index=False)

    row_count = build_database(
        source,
        database,
        expected_rows=3,
        expected_treatment_days={0, 7, 14},
    )

    with sqlite3.connect(database) as connection:
        actual = connection.execute(
            "SELECT COUNT(*), COUNT(DISTINCT sample), SUM(count) FROM samples"
        ).fetchone()
    assert row_count == 15
    assert actual == (15, 3, 270)


def test_database_constraints_reject_duplicate_population(valid_source_frame, tmp_path):
    source = tmp_path / "cell-count.csv"
    database = tmp_path / "cell-count.db"
    valid_source_frame.to_csv(source, index=False)
    build_database(source, database)

    with sqlite3.connect(database) as connection:
        row = connection.execute("SELECT * FROM samples LIMIT 1").fetchone()
        placeholders = ", ".join("?" for _ in row)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"INSERT INTO samples VALUES ({placeholders})", row)


def test_invalid_source_does_not_replace_existing_database(valid_source_frame, tmp_path):
    source = tmp_path / "cell-count.csv"
    database = tmp_path / "cell-count.db"
    database.write_bytes(b"existing database")
    valid_source_frame.loc[0, "b_cell"] = -1
    valid_source_frame.to_csv(source, index=False)

    with pytest.raises(ValueError):
        build_database(source, database)

    assert database.read_bytes() == b"existing database"
