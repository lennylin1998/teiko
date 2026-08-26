"""Source-column definitions and the SQLite schema."""

TEXT_COLUMNS = [
    "sample", "project", "subject", "condition", "sex", "treatment", "response", "sample_type"
]
DATABASE_TEXT_COLUMNS = [column for column in TEXT_COLUMNS if column != "response"]
CELL_POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
INTEGER_COLUMNS = ["age", "time_from_treatment_start", *CELL_POPULATIONS]
METADATA_COLUMNS = [
    column for column in TEXT_COLUMNS + INTEGER_COLUMNS if column not in CELL_POPULATIONS
]
SOURCE_COLUMNS = [
    "project", "subject", "condition", "age", "sex", "treatment", "response", "sample",
    "sample_type", "time_from_treatment_start", *CELL_POPULATIONS,
]

CREATE_TABLE_SQL = """
CREATE TABLE samples (
    sample TEXT NOT NULL,                    -- Unique sample identifier
    population TEXT NOT NULL,                -- Immune cell population name
    count INTEGER NOT NULL,                  -- Cells observed for the population
    project TEXT NOT NULL,                   -- Clinical project identifier
    subject TEXT NOT NULL,                   -- Trial subject identifier
    condition TEXT NOT NULL,                 -- Disease or clinical condition
    age INTEGER NOT NULL,                    -- Subject age in years
    sex TEXT NOT NULL,                       -- Recorded subject sex
    treatment TEXT NOT NULL,                 -- Treatment administered
    response INTEGER,                        -- 1=yes, 0=no, NULL=unknown
    sample_type TEXT NOT NULL,                -- Biological specimen type
    time_from_treatment_start INTEGER NOT NULL, -- Collection day from treatment start
    PRIMARY KEY (sample, population),
    CHECK (population IN ('b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte')),
    CHECK (count >= 0),
    CHECK (response IN (0, 1) OR response IS NULL)
)
"""
