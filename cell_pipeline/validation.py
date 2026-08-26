"""Validation of the loaded SQLite database."""

import sqlite3

import pandas as pd

from .schema import CELL_POPULATIONS, DATABASE_TEXT_COLUMNS, INTEGER_COLUMNS


def validate_database(
    connection: sqlite3.Connection,
    source_frame: pd.DataFrame,
    long_frame: pd.DataFrame,
) -> None:
    actual = tuple(connection.execute("""
        SELECT COUNT(*), COUNT(DISTINCT sample), COUNT(DISTINCT population),
               MIN(time_from_treatment_start), MAX(time_from_treatment_start),
               SUM(CASE WHEN population = 'b_cell' THEN count ELSE 0 END)
        FROM samples
    """).fetchone())
    expected = (
        len(long_frame), source_frame["sample"].nunique(), len(CELL_POPULATIONS),
        int(source_frame["time_from_treatment_start"].min()),
        int(source_frame["time_from_treatment_start"].max()),
        int(source_frame["b_cell"].sum()),
    )
    if actual != expected:
        raise ValueError(f"Database validation failed: expected {expected}, found {actual}")

    schema = {
        row[1]: (row[2], row[5]) for row in connection.execute("PRAGMA table_info(samples)")
    }
    expected_types = {
        **{column: "TEXT" for column in DATABASE_TEXT_COLUMNS},
        "population": "TEXT",
        **{column: "INTEGER" for column in INTEGER_COLUMNS if column not in CELL_POPULATIONS},
        "count": "INTEGER",
        "response": "INTEGER",
    }
    key_positions = {"sample": 1, "population": 2}
    for column, expected_type in expected_types.items():
        actual_type, key_position = schema.get(column, (None, None))
        if actual_type != expected_type:
            raise ValueError(
                f"Database column {column!r} has type {actual_type!r}, expected {expected_type}"
            )
        if key_position != key_positions.get(column, 0):
            raise ValueError(f"Database column {column!r} has an incorrect primary-key position")
