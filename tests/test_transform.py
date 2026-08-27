import pandas as pd

from cell_pipeline.transform import normalize_source_types, reshape_population_counts_to_rows


def test_normalize_source_types_converts_response_without_mutating_input(valid_source_frame):
    normalized = normalize_source_types(valid_source_frame)

    assert normalized["response"].iloc[:2].tolist() == [1, 0]
    assert pd.isna(normalized["response"].iloc[2])
    assert valid_source_frame["response"].tolist()[0:2] == ["yes", "no"]
    assert str(normalized["age"].dtype) == "int64"


def test_reshape_creates_five_rows_per_sample(valid_source_frame):
    normalized = normalize_source_types(valid_source_frame)
    reshaped = reshape_population_counts_to_rows(normalized)

    first_sample = reshaped[reshaped["sample"] == "sample-1"]
    assert len(reshaped) == 15
    assert dict(zip(first_sample["population"], first_sample["count"])) == {
        "b_cell": 10,
        "cd8_t_cell": 20,
        "cd4_t_cell": 30,
        "nk_cell": 40,
        "monocyte": 50,
    }
