import sqlite3

import pandas as pd
import pytest

from cell_pipeline.responder_analysis import (
    STATISTICS_DECIMAL_PLACES,
    STATISTICS_FLOAT_COLUMNS,
    STATISTICS_COLUMNS,
    build_subject_level_cohort,
    calculate_statistics,
    run_responder_analysis,
)
from cell_pipeline.schema import CELL_POPULATIONS, CREATE_TABLE_SQL


@pytest.fixture
def responder_inputs(tmp_path):
    database = tmp_path / "cell-count.db"
    frequencies = tmp_path / "relative-frequency.csv"
    database_rows = []
    frequency_rows = []
    for response, prefix in ((1, "r"), (0, "n")):
        for subject_number in range(3):
            subject = f"{prefix}{subject_number}"
            for day in (0, 7, 14):
                sample = f"{subject}-{day}"
                for population_number, population in enumerate(CELL_POPULATIONS):
                    database_rows.append((
                        sample, population, 1, "p", subject, "melanoma", 50, "F",
                        "miraclib", response, "PBMC", day,
                    ))
                    base = 10 + population_number + subject_number
                    percentage = base + day / 7 + (5 if response else 0)
                    frequency_rows.append({
                        "sample": sample, "population": population, "percentage": percentage,
                    })
    with sqlite3.connect(database) as connection:
        connection.execute(CREATE_TABLE_SQL)
        connection.executemany("INSERT INTO samples VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", database_rows)
    pd.DataFrame(frequency_rows).to_csv(frequencies, index=False)
    return database, frequencies


def test_subject_level_cohort_averages_repeated_visits(responder_inputs):
    subject_level = build_subject_level_cohort(*responder_inputs)

    assert len(subject_level) == 6 * 5
    assert not subject_level.duplicated(["subject", "population"]).any()
    assert set(subject_level["population"]) == set(CELL_POPULATIONS)
    value = subject_level.query("subject == 'r0' and population == 'b_cell'")["percentage"].item()
    assert value == pytest.approx(16.0)


def test_statistics_runs_exactly_five_welch_tests(responder_inputs):
    subject_level = build_subject_level_cohort(*responder_inputs)
    statistics = calculate_statistics(subject_level)

    assert list(statistics.columns) == STATISTICS_COLUMNS
    assert len(statistics) == 5
    assert (statistics[["responder_n", "nonresponder_n"]] == 3).all().all()
    assert statistics["mean_difference"].tolist() == pytest.approx([5.0] * 5)
    assert statistics["significant"].all()
    for column in STATISTICS_FLOAT_COLUMNS:
        assert statistics[column].map(
            lambda value: value == round(value, STATISTICS_DECIMAL_PLACES)
        ).all()


def test_analysis_writes_csv_and_combined_figure(responder_inputs, tmp_path):
    statistics_path = tmp_path / "statistics.csv"
    figure_path = tmp_path / "boxplots.png"

    returned = run_responder_analysis(
        *responder_inputs, statistics_path, figure_path,
    )

    written = pd.read_csv(statistics_path)
    assert len(returned) == len(written) == 5
    assert figure_path.read_bytes().startswith(b"\x89PNG")
