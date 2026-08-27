import sqlite3

from cell_pipeline.cohort_analysis import select_cohort, summarize_cohort
from cell_pipeline.loading import build_database


def test_cohort_filters_and_counts_distinct_subjects(valid_source_frame, tmp_path):
    source = tmp_path / "cell-count.csv"
    database = tmp_path / "cell-count.db"
    frame = valid_source_frame.copy()
    frame.loc[:, "treatment"] = "miraclib"
    frame.to_csv(source, index=False)
    build_database(source, database, expected_rows=3)

    cohort = select_cohort(
        database,
        condition="MELANOMA",
        treatment="miraclib",
        sample_type="pbmc",
        time_from_treatment_start=0,
    )
    summary = summarize_cohort(cohort)

    assert list(cohort["sample"]) == ["sample-1"]
    assert summary["number_of_samples"] == 1
    assert summary["number_of_subjects"] == 1
    assert summary["subjects_by_response"].to_dict("records") == [
        {"response": "Responder", "number_of_subjects": 1}
    ]


def test_subject_summaries_do_not_count_repeat_samples(valid_source_frame, tmp_path):
    source = tmp_path / "cell-count.csv"
    database = tmp_path / "cell-count.db"
    valid_source_frame.to_csv(source, index=False)
    build_database(source, database, expected_rows=3)

    summary = summarize_cohort(select_cohort(database, condition="melanoma"))

    assert summary["number_of_samples"] == 3
    assert summary["number_of_subjects"] == 1
    assert summary["subjects_by_sex"].iloc[0].to_dict() == {
        "sex": "F", "number_of_subjects": 1
    }
