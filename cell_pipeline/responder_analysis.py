"""Responder versus non-responder analysis on subject-level frequencies."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import ttest_ind

from .schema import CELL_POPULATIONS


ANALYTICAL_COLUMNS = [
    "subject", "sample", "response", "time_from_treatment_start", "population", "percentage"
]
STATISTICS_COLUMNS = [
    "population", "responder_n", "nonresponder_n", "responder_mean",
    "nonresponder_mean", "mean_difference", "t_statistic", "p_value",
    "significant",
]
STATISTICS_DECIMAL_PLACES = 6
STATISTICS_FLOAT_COLUMNS = [
    "responder_mean", "nonresponder_mean", "mean_difference",
    "t_statistic", "p_value",
]


def build_subject_level_cohort(
    database_path: Path, frequency_path: Path,
) -> pd.DataFrame:
    """Filter the requested cohort and average repeated visits per subject."""
    if not database_path.is_file():
        raise FileNotFoundError(f"Database not found: {database_path}")
    if not frequency_path.is_file():
        raise FileNotFoundError(f"Relative-frequency CSV not found: {frequency_path}")

    with sqlite3.connect(database_path) as connection:
        metadata = pd.read_sql_query(
            """
            SELECT DISTINCT subject, sample, response, time_from_treatment_start
            FROM samples
            WHERE lower(condition) = 'melanoma'
              AND lower(treatment) = 'miraclib'
              AND upper(sample_type) = 'PBMC'
              AND response IS NOT NULL
            """,
            connection,
        )
    frequencies = pd.read_csv(
        frequency_path, usecols=["sample", "population", "percentage"]
    )
    cohort = metadata.merge(frequencies, on="sample", how="inner", validate="one_to_many")
    cohort = cohort[ANALYTICAL_COLUMNS]

    expected_rows = len(metadata) * len(CELL_POPULATIONS)
    if len(cohort) != expected_rows:
        raise ValueError(
            "Relative-frequency data do not contain exactly five populations for every cohort sample"
        )
    if set(cohort["population"]) != set(CELL_POPULATIONS):
        raise ValueError("Analytical cohort does not contain all five immune-cell populations")
    if cohort.duplicated(["sample", "population"]).any():
        raise ValueError("Relative-frequency data contain duplicate sample/population rows")

    # A subject's response must be stable across the treatment timepoints being averaged.
    if cohort.groupby("subject")["response"].nunique().gt(1).any():
        raise ValueError("A cohort subject has conflicting response values")

    subject_level = (
        cohort.groupby(["subject", "response", "population"], as_index=False)["percentage"]
        .mean()
        .sort_values(["population", "response", "subject"])
        .reset_index(drop=True)
    )
    if subject_level.duplicated(["subject", "population"]).any():
        raise AssertionError("Each subject must contribute at most one value per population")
    return subject_level


def calculate_statistics(subject_level: pd.DataFrame) -> pd.DataFrame:
    """Run one Welch test for each of the five cell populations."""
    rows: list[dict[str, object]] = []
    for population in CELL_POPULATIONS:
        population_rows = subject_level[subject_level["population"] == population]
        responders = population_rows.loc[population_rows["response"] == 1, "percentage"]
        nonresponders = population_rows.loc[population_rows["response"] == 0, "percentage"]
        if len(responders) < 2 or len(nonresponders) < 2:
            raise ValueError(f"Population {population!r} needs at least two subjects per group")
        test = ttest_ind(responders, nonresponders, equal_var=False)
        responder_mean = responders.mean()
        nonresponder_mean = nonresponders.mean()
        rows.append({
            "population": population,
            "responder_n": len(responders),
            "nonresponder_n": len(nonresponders),
            "responder_mean": responder_mean,
            "nonresponder_mean": nonresponder_mean,
            "mean_difference": responder_mean - nonresponder_mean,
            "t_statistic": float(test.statistic),
            "p_value": float(test.pvalue),
        })
    statistics = pd.DataFrame(rows)
    statistics[STATISTICS_FLOAT_COLUMNS] = statistics[STATISTICS_FLOAT_COLUMNS].round(
        STATISTICS_DECIMAL_PLACES
    )
    statistics["significant"] = statistics["p_value"] < 0.05
    return statistics[STATISTICS_COLUMNS]


def plot_subject_level_boxplots(subject_level: pd.DataFrame, output_path: Path) -> None:
    """Write one figure containing a responder/non-responder pair per population."""
    labels = [population.replace("_", " ").title() for population in CELL_POPULATIONS]
    fig, axes = plt.subplots(1, 5, figsize=(17, 5), sharey=True, constrained_layout=True)
    for axis, population, label in zip(axes, CELL_POPULATIONS, labels):
        rows = subject_level[subject_level["population"] == population]
        values = [
            rows.loc[rows["response"] == response, "percentage"].to_numpy()
            for response in (1, 0)
        ]
        boxes = axis.boxplot(values, tick_labels=["Responder", "Non-responder"], patch_artist=True)
        for patch, color in zip(boxes["boxes"], ["#2878B5", "#E07A5F"]):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        axis.set_title(label)
        axis.tick_params(axis="x", rotation=25)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Mean relative frequency across visits (%)")
    fig.suptitle("Miraclib melanoma PBMC: response-group comparison", fontsize=14)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    fig.savefig(temporary_path, format=output_path.suffix.lstrip("."), dpi=180)
    plt.close(fig)
    temporary_path.replace(output_path)


def run_responder_analysis(
    database_path: Path,
    frequency_path: Path,
    statistics_path: Path,
    figure_path: Path,
) -> pd.DataFrame:
    """Create both Part 3 deliverables from one subject-level dataset."""
    statistics_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    subject_level = build_subject_level_cohort(database_path, frequency_path)
    statistics = calculate_statistics(subject_level)
    temporary_path = statistics_path.with_suffix(statistics_path.suffix + ".tmp")
    statistics.to_csv(temporary_path, index=False)
    temporary_path.replace(statistics_path)
    plot_subject_level_boxplots(subject_level, figure_path)
    return statistics
