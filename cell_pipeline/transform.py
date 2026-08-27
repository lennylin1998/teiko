"""Read and transform the source CSV."""

from pathlib import Path

import pandas as pd

from .schema import CELL_POPULATIONS, INTEGER_COLUMNS, METADATA_COLUMNS, TEXT_COLUMNS


def read_source_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Source CSV not found: {path}")
    return pd.read_csv(path, dtype={column: "string" for column in TEXT_COLUMNS})


def normalize_source_types(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in INTEGER_COLUMNS:
        frame[column] = pd.to_numeric(frame[column]).astype("int64")
    frame["response"] = frame["response"].map({"yes": 1, "no": 0}).astype("Int64")
    return frame


def reshape_population_counts_to_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.melt(
        id_vars=METADATA_COLUMNS,
        value_vars=CELL_POPULATIONS,
        var_name="population",
        value_name="count",
    )
