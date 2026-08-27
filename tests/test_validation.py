import pandas as pd
import pytest

from cell_pipeline.validation import validate_source


def test_valid_source_is_accepted(valid_source_frame):
    validate_source(
        valid_source_frame,
        expected_rows=3,
        expected_treatment_days={0, 7, 14},
    )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("b_cell", "not-a-number", "non-numeric"),
        ("b_cell", 1.5, "non-integer"),
        ("b_cell", -1, "nonnegative"),
        ("response", "maybe", "Unexpected response"),
    ],
)
def test_invalid_values_are_rejected(valid_source_frame, column, value, message):
    valid_source_frame[column] = valid_source_frame[column].astype("object")
    valid_source_frame.loc[0, column] = value
    with pytest.raises(ValueError, match=message):
        validate_source(valid_source_frame)


def test_missing_required_value_is_rejected(valid_source_frame):
    valid_source_frame.loc[0, "sample"] = pd.NA
    with pytest.raises(ValueError, match="missing values"):
        validate_source(valid_source_frame)


def test_duplicate_sample_is_rejected(valid_source_frame):
    valid_source_frame.loc[1, "sample"] = "sample-1"
    with pytest.raises(ValueError, match="duplicate sample"):
        validate_source(valid_source_frame)


def test_zero_population_total_is_rejected(valid_source_frame):
    valid_source_frame.loc[0, ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]] = 0
    with pytest.raises(ValueError, match="positive total"):
        validate_source(valid_source_frame)


def test_wrong_columns_are_rejected(valid_source_frame):
    frame = valid_source_frame.drop(columns="project")
    with pytest.raises(ValueError, match="Unexpected CSV columns"):
        validate_source(frame)
