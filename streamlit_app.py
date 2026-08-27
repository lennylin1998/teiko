#!/usr/bin/env python3
"""Streamlit prototype for the immune cell-count analysis dashboard."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from cell_pipeline.cohort_analysis import available_filters, select_cohort, summarize_cohort


ROOT = Path(__file__).resolve().parent
DATA_DIRECTORY = ROOT / "docs" / "data"
FREQUENCY_PATH = DATA_DIRECTORY / "relative-frequency.csv"
STATISTICS_PATH = DATA_DIRECTORY / "responder-statistics.csv"
BOXPLOT_PATH = DATA_DIRECTORY / "responder-boxplots.png"
DATABASE_PATH = ROOT / "cell-count.db"


st.set_page_config(
    page_title="Loblaw Bio — Immune Cell Analysis",
    page_icon="🧬",
    layout="wide",
)


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Run `make pipeline` first.")
    return pd.read_csv(path)


def download_csv(label: str, frame: pd.DataFrame, filename: str) -> None:
    st.download_button(
        label,
        frame.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def cohort_bar_chart(
    frame: pd.DataFrame, category: str, value: str, y_label: str
) -> plt.Figure:
    """Build a compact chart whose horizontal labels remain within the frame."""
    figure, axis = plt.subplots(figsize=(4.5, 3.2), constrained_layout=True)
    axis.bar(frame[category].astype(str), frame[value], color="#2878B5")
    axis.set_ylabel(y_label)
    axis.tick_params(axis="x", labelrotation=0, labelsize=8)
    axis.margins(x=0.12)
    axis.grid(axis="y", alpha=0.25)
    return figure


def frequency_page() -> None:
    st.caption("PART 2 · INITIAL ANALYSIS")
    st.title("Cell population frequencies")
    st.write("Relative frequency of each immune cell population within every sample.")

    frequencies = load_csv(FREQUENCY_PATH)
    populations = sorted(frequencies["population"].unique())
    samples = frequencies["sample"].nunique()

    metric_columns = st.columns(3)
    metric_columns[0].metric("Samples", f"{samples:,}")
    metric_columns[1].metric("Populations", len(populations))
    metric_columns[2].metric("Measurements", f"{len(frequencies):,}")

    st.subheader("Explore measurements")
    filter_columns = st.columns([2, 1])
    search = filter_columns[0].text_input(
        "Search samples", placeholder="e.g. sample00042"
    ).strip()
    selected_populations = filter_columns[1].multiselect(
        "Populations", populations, default=populations
    )

    visible = frequencies[
        frequencies["sample"].str.contains(search, case=False, regex=False)
        & frequencies["population"].isin(selected_populations)
    ]
    st.dataframe(
        visible,
        width="stretch",
        hide_index=True,
        column_config={
            "total_count": st.column_config.NumberColumn(format="localized"),
            "count": st.column_config.NumberColumn(format="localized"),
            "percentage": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )
    download_csv("Download filtered CSV", visible, "relative-frequency.csv")


def responder_page() -> None:
    st.caption("PART 3 · STATISTICAL ANALYSIS")
    st.title("Responder comparison")
    st.write(
        "Subject-level relative frequencies for melanoma PBMC samples following "
        "miraclib treatment. Days 0, 7, and 14 are averaged before comparison."
    )

    statistics = load_csv(STATISTICS_PATH)
    metric_columns = st.columns(3)
    metric_columns[0].metric("Responders", int(statistics.iloc[0]["responder_n"]))
    metric_columns[1].metric(
        "Non-responders", int(statistics.iloc[0]["nonresponder_n"])
    )
    metric_columns[2].metric(
        "Significant populations", int(statistics["significant"].sum())
    )

    st.subheader("Relative-frequency distributions")
    st.caption(
        "Each boxplot contains one mean value per subject. Blue indicates "
        "responders; orange indicates non-responders."
    )
    if not BOXPLOT_PATH.is_file():
        raise FileNotFoundError(f"Missing {BOXPLOT_PATH}. Run `make pipeline` first.")
    st.image(str(BOXPLOT_PATH), width="stretch")

    st.subheader("Welch t-test results")
    st.caption("Five two-sided tests. Raw p-values below 0.05 are significant.")
    st.dataframe(
        statistics,
        width="stretch",
        hide_index=True,
        column_config={
            "responder_mean": st.column_config.NumberColumn(format="%.2f%%"),
            "nonresponder_mean": st.column_config.NumberColumn(format="%.2f%%"),
            "mean_difference": st.column_config.NumberColumn(format="%.2f pp"),
            "t_statistic": st.column_config.NumberColumn(format="%.3f"),
            "p_value": st.column_config.NumberColumn(format="%.4f"),
            "significant": st.column_config.CheckboxColumn(),
        },
    )
    download_csv("Download statistics", statistics, "responder-statistics.csv")


def baseline_page() -> None:
    st.caption("PART 4 · INTERACTIVE COHORT ANALYSIS")
    st.title("Cohort explorer")
    st.write("Choose sample characteristics, then explore project and subject summaries.")
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(f"Missing {DATABASE_PATH}. Run `make pipeline` first.")

    choices = available_filters(DATABASE_PATH)
    defaults = {
        "condition": "melanoma",
        "treatment": "miraclib",
        "sample_type": "PBMC",
        "time_from_treatment_start": 0,
    }
    labels = {
        "condition": "Condition",
        "treatment": "Treatment",
        "sample_type": "Sample type",
        "time_from_treatment_start": "Time from treatment start (days)",
    }
    columns = st.columns(4)
    selected: dict[str, object] = {}
    for column, name in zip(columns, defaults):
        values = choices[name]
        default_index = values.index(defaults[name]) if defaults[name] in values else 0
        selected[name] = column.selectbox(labels[name], values, index=default_index)

    cohort = select_cohort(DATABASE_PATH, **selected)
    summary = summarize_cohort(cohort)
    metrics = st.columns(2)
    metrics[0].metric("Samples", f"{summary['number_of_samples']:,}")
    metrics[1].metric("Subjects", f"{summary['number_of_subjects']:,}")

    sections = st.columns(3)
    tables = (
        ("Samples by project", "samples_by_project", "project", "number_of_samples", "Samples"),
        ("Subjects by response", "subjects_by_response", "response", "number_of_subjects", "Subjects"),
        ("Subjects by sex", "subjects_by_sex", "sex", "number_of_subjects", "Subjects"),
    )
    for column, (title, key, category, value, y_label) in zip(sections, tables):
        frame = summary[key]
        column.subheader(title)
        # Header plus two visible rows keeps charts aligned without excess blank space.
        column.dataframe(frame, width="stretch", height=110, hide_index=True)
        if not frame.empty:
            figure = cohort_bar_chart(frame, category, value, y_label)
            column.pyplot(figure, width="stretch")
            plt.close(figure)

    with st.expander("Selected samples"):
        st.dataframe(cohort, width="stretch", hide_index=True)
        download_csv("Download cohort CSV", cohort, "selected-cohort.csv")


page = st.navigation(
    [
        st.Page(frequency_page, title="Data overview", icon=":material/table_chart:", default=True),
        st.Page(responder_page, title="Statistical analysis", icon=":material/analytics:"),
        st.Page(baseline_page, title="Subset analysis", icon=":material/filter_alt:"),
    ]
)
page.run()
