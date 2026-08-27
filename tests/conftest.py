import pandas as pd
import pytest

from cell_pipeline.schema import SOURCE_COLUMNS


@pytest.fixture
def valid_source_frame() -> pd.DataFrame:
    rows = [
        ["p1", "subject-1", "melanoma", 40, "F", "drug", "yes", "sample-1", "PBMC", 0, 10, 20, 30, 40, 50],
        ["p1", "subject-1", "melanoma", 40, "F", "drug", "no", "sample-2", "PBMC", 7, 5, 10, 15, 20, 50],
        ["p1", "subject-1", "melanoma", 40, "F", "drug", pd.NA, "sample-3", "PBMC", 14, 1, 2, 3, 4, 10],
    ]
    return pd.DataFrame(rows, columns=SOURCE_COLUMNS)
