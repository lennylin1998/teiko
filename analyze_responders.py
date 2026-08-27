#!/usr/bin/env python3
"""Generate the Part 3 responder versus non-responder outputs."""

import sys
from pathlib import Path

from cell_pipeline.responder_analysis import run_responder_analysis


ROOT = Path(__file__).resolve().parent
STATIC_DATA = ROOT / "docs" / "data"


def main() -> None:
    try:
        statistics = run_responder_analysis(
            ROOT / "cell-count.db",
            STATIC_DATA / "relative-frequency.csv",
            STATIC_DATA / "responder-statistics.csv",
            STATIC_DATA / "responder-boxplots.png",
        )
        responder_n = int(statistics["responder_n"].iloc[0])
        nonresponder_n = int(statistics["nonresponder_n"].iloc[0])
        print(
            "Created docs/data/responder-statistics.csv and "
            "docs/data/responder-boxplots.png: "
            f"5 tests, {responder_n} responders, {nonresponder_n} non-responders."
        )
    except Exception as error:
        print(f"Responder analysis failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
