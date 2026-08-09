"""Pressure-response reconstruction for Volve 15/9-F-14 FPWD tests.

The script reconstructs the measured quartz-gauge pressure response for all
14 formation-tester pretests and marks the source-reported drawdown and
buildup intervals. Source interpretation values are displayed only as
references and are not treated as independent calculations.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from f14_fpwd_data_audit import (
    phase_data,
    phase_definition,
    numeric_value,
    header_value,
    interpretation_blocks,
    test_number,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "15_9-F-14"
)

REPORT_DIR = PROJECT_DIR / "report"
FIGURE_DIR = PROJECT_DIR / "figures"

PSI_TO_BAR = 0.0689475729

# Reference reconciliation established from the source LAS and the
# Schlumberger FPWD report.
STANDARD_ATMOSPHERE_BAR = 1.01325

NULL_DEFAULT = -999.25


def load_test(path):
    """Read one FPWD LAS test and return data plus interpretation metadata."""

    text = path.read_text(
        encoding="latin-1",
        errors="replace",
    )

    lines = text.splitlines()

    null_value = numeric_value(
        header_value(
            lines,
            "NULL",
        )
    )

    if not np.isfinite(null_value):
        null_value = NULL_DEFAULT

    channels = phase_definition(
        lines
    )

    data = phase_data(
        lines,
        channels,
        null_value,
    )

    blocks = interpretation_blocks(
        lines,
        null_value,
    )

    source = (
        blocks[-1]
        if blocks
        else {}
    )

    metadata = {
        "Test": test_number(path),
        "MD m": numeric_value(
            header_value(
                lines,
                "MD",
            )
        ),
        "TVD m": numeric_value(
            header_value(
                lines,
                "TVD",
            )
        ),
        "Drawdown Start s": source.get(
            "pDDS",
            np.nan,
        ),
        "Buildup Start s": source.get(
            "pBUS",
            np.nan,
        ),
        "Buildup End s": source.get(
            "pBUE",
            np.nan,
        ),
        "Formation Pressure bar": (
            (
                source.get(
                    "pPFOR",
                    np.nan,
                )
                * PSI_TO_BAR
                + STANDARD_ATMOSPHERE_BAR
            )
            if np.isfinite(
                source.get(
                    "pPFOR",
                    np.nan,
                )
            )
            else np.nan
        ),
        "Source Mobility mD/cP": source.get(
            "pDDM",
            np.nan,
        ),
    }

    return data, metadata


def selected_pressure_channel(data):
    """Use filtered quartz pressure when available, otherwise raw pressure."""

    if (
        "AQAP_F" in data.columns
        and data["AQAP_F"].notna().any()
    ):
        return (
            "AQAP_F",
            "Filtered quartz pressure",
        )

    return (
        "AQAP",
        "Raw quartz pressure",
    )


def build_response_summary(records):
    """Calculate observational pressure-response metrics."""

    rows = []

    for data, meta in records:

        channel, _ = selected_pressure_channel(
            data
        )

        pressure = data[channel]

        drawdown_start = meta[
            "Drawdown Start s"
        ]

        buildup_start = meta[
            "Buildup Start s"
        ]

        buildup_end = meta[
            "Buildup End s"
        ]

        drawdown = data.loc[
            (
                data["TIME"]
                >= drawdown_start
            )
            & (
                data["TIME"]
                <= buildup_start
            )
        ].copy()

        buildup = data.loc[
            (
                data["TIME"]
                >= buildup_start
            )
            & (
                data["TIME"]
                <= buildup_end
            )
        ].copy()

        pre_drawdown = data.loc[
            (
                data["TIME"]
                < drawdown_start
            )
            & (
                data["TIME"]
                >= drawdown_start - 10.0
            )
        ].copy()

        initial_pressure = (
            float(
                pre_drawdown[
                    channel
                ].median()
            )
            if not pre_drawdown.empty
            else np.nan
        )

        minimum_drawdown_pressure = (
            float(
                drawdown[
                    channel
                ].min()
            )
            if not drawdown.empty
            else np.nan
        )

        final_buildup_pressure = (
            float(
                buildup.loc[
                    buildup["TIME"]
                    >= (
                        buildup_end
                        - 5.0
                    ),
                    channel,
                ].median()
            )
            if not buildup.empty
            else np.nan
        )

        observed_drawdown = (
            initial_pressure
            - minimum_drawdown_pressure
            if (
                np.isfinite(
                    initial_pressure
                )
                and np.isfinite(
                    minimum_drawdown_pressure
                )
            )
            else np.nan
        )

        recovery = (
            final_buildup_pressure
            - minimum_drawdown_pressure
            if (
                np.isfinite(
                    final_buildup_pressure
                )
                and np.isfinite(
                    minimum_drawdown_pressure
                )
            )
            else np.nan
        )

        source_pressure = meta[
            "Formation Pressure bar"
        ]

        final_pressure_difference = (
            final_buildup_pressure
            - source_pressure
            if (
                np.isfinite(
                    final_buildup_pressure
                )
                and np.isfinite(
                    source_pressure
                )
            )
            else np.nan
        )

        rows.append(
            {
                "Test": meta["Test"],
                "MD m": meta["MD m"],
                "TVD m": meta["TVD m"],
                "Pressure Channel": channel,
                "Initial Pressure bar": (
                    initial_pressure
                ),
                "Minimum Drawdown Pressure bar": (
                    minimum_drawdown_pressure
                ),
                "Final Buildup Pressure bar": (
                    final_buildup_pressure
                ),
                "Observed Drawdown bar": (
                    observed_drawdown
                ),
                "Observed Recovery bar": (
                    recovery
                ),
                "Source Formation Pressure bar": (
                    source_pressure
                ),
                "Final minus Source Pressure bar": (
                    final_pressure_difference
                ),
                "Source Mobility mD/cP": (
                    meta[
                        "Source Mobility mD/cP"
                    ]
                ),
                "Drawdown Duration s": (
                    buildup_start
                    - drawdown_start
                ),
                "Buildup Duration s": (
                    buildup_end
                    - buildup_start
                ),
            }
        )

    summary = pd.DataFrame(
        rows
    )

    numeric = summary.select_dtypes(
        include=[np.number]
    ).columns

    summary[numeric] = (
        summary[numeric]
        .round(4)
    )

    return summary


def create_response_atlas(records):
    """Plot all 14 FPWD pressure responses."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, axes = plt.subplots(
        4,
        4,
        figsize=(16, 13),
        constrained_layout=True,
    )

    axes = axes.flatten()

    for ax, (data, meta) in zip(
        axes,
        records,
    ):

        channel, channel_label = (
            selected_pressure_channel(
                data
            )
        )

        drawdown_start = meta[
            "Drawdown Start s"
        ]

        buildup_start = meta[
            "Buildup Start s"
        ]

        buildup_end = meta[
            "Buildup End s"
        ]

        plotting = data.loc[
            (
                data["TIME"]
                >= drawdown_start - 10.0
            )
            & (
                data["TIME"]
                <= buildup_end
            )
        ].copy()

        relative_time = (
            plotting["TIME"]
            - drawdown_start
        )

        ax.plot(
            relative_time,
            plotting[channel],
            color="#0072B2",
            linewidth=1.2,
        )

        ax.axvline(
            0.0,
            color="#D55E00",
            linestyle="--",
            linewidth=1.0,
        )

        ax.axvline(
            buildup_start
            - drawdown_start,
            color="#009E73",
            linestyle="--",
            linewidth=1.0,
        )

        ax.axvline(
            buildup_end
            - drawdown_start,
            color="#666666",
            linestyle=":",
            linewidth=1.0,
        )

        formation_pressure = meta[
            "Formation Pressure bar"
        ]

        if np.isfinite(
            formation_pressure
        ):

            ax.axhline(
                formation_pressure,
                color="#CC79A7",
                linestyle=":",
                linewidth=1.0,
            )

        ax.set_title(
            "Test {} | TVD {:.1f} m".format(
                meta["Test"],
                meta["TVD m"],
            ),
            fontsize=10,
            fontweight="bold",
        )

        ax.grid(
            True,
            alpha=0.22,
        )

    # Remove unused panels.
    for ax in axes[
        len(records):
    ]:
        ax.remove()

    fig.supxlabel(
        "Time from drawdown start (s)"
    )

    fig.supylabel(
        "Quartz-gauge pressure (bar)"
    )

    fig.suptitle(
        "15/9-F-14 — FPWD Pressure-Response Atlas",
        fontsize=16,
        fontweight="bold",
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_pressure_response_atlas.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_pressure_response_atlas.pdf"
    )

    fig.savefig(
        png_path,
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        pdf_path,
        bbox_inches="tight",
    )

    plt.close(fig)

    return png_path, pdf_path


def main():
    """Reconstruct and summarize the 14 FPWD pressure responses."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        RAW_DIR.glob(
            "FM_PRESS_RAW_RUN5_MWD_*.LAS"
        ),
        key=test_number,
    )

    if len(files) != 14:
        raise ValueError(
            "Expected 14 LAS tests; found {}.".format(
                len(files)
            )
        )

    records = [
        load_test(path)
        for path in files
    ]

    summary = build_response_summary(
        records
    )

    output_path = (
        REPORT_DIR
        / "f14_fpwd_pressure_response_summary.csv"
    )

    summary.to_csv(
        output_path,
        index=False,
    )

    png_path, pdf_path = (
        create_response_atlas(
            records
        )
    )

    print()
    print(
        "15/9-F-14 FPWD PRESSURE-RESPONSE SUMMARY"
    )
    print()

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        "Outputs:"
    )
    print(
        "  {}".format(
            output_path
        )
    )
    print(
        "  {}".format(
            png_path
        )
    )
    print(
        "  {}".format(
            pdf_path
        )
    )


if __name__ == "__main__":
    main()
