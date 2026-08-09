"""Station-level QC and pressure-depth analysis for Volve 15/9-F-14 FPWD tests.

Observed pressure closure is evaluated before estimating vertical pressure
gradients. Source-interpreted formation pressure and directly observed final
buildup pressure are retained as separate quantities.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress


PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_fpwd_pressure_response_summary.csv"
)

REPORT_DIR = PROJECT_DIR / "report"
FIGURE_DIR = PROJECT_DIR / "figures"

# Analysis screening criteria.
# These are explicit project QC thresholds, not vendor specifications.
CLOSURE_TOLERANCE_BAR = 0.10
LOW_DRAWDOWN_BAR = 1.00

BAR_TO_PSI = 14.5037738
M_TO_FT = 3.280839895
GRAVITY = 9.80665


def load_data():
    """Load station-level pressure-response summary."""

    df = pd.read_csv(
        INPUT_FILE
    )

    required = [
        "Test",
        "TVD m",
        "Initial Pressure bar",
        "Minimum Drawdown Pressure bar",
        "Final Buildup Pressure bar",
        "Observed Drawdown bar",
        "Observed Recovery bar",
        "Source Formation Pressure bar",
        "Source Mobility mD/cP",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: {}".format(
                missing
            )
        )

    return df


def calculate_qc(df):
    """Calculate transparent station-level QC metrics."""

    result = df.copy()

    result["Closure Error bar"] = (
        result["Final Buildup Pressure bar"]
        - result["Initial Pressure bar"]
    )

    result["Absolute Closure Error bar"] = (
        result["Closure Error bar"].abs()
    )

    result["Recovery Fraction"] = np.where(
        result["Observed Drawdown bar"] > 0.0,
        (
            result["Observed Recovery bar"]
            / result["Observed Drawdown bar"]
        ),
        np.nan,
    )

    result["Pressure Closure"] = np.where(
        result["Absolute Closure Error bar"]
        <= CLOSURE_TOLERANCE_BAR,
        "Within criterion",
        "Outside criterion",
    )

    result["Drawdown Amplitude"] = np.where(
        result["Observed Drawdown bar"]
        < LOW_DRAWDOWN_BAR,
        "Low amplitude",
        "Resolved amplitude",
    )

    result["Use for Observed Gradient"] = (
        result["Absolute Closure Error bar"]
        <= CLOSURE_TOLERANCE_BAR
    )

    return result


def gradient_statistics(
    depth,
    pressure,
    name,
):
    """Calculate linear pressure-depth regression statistics."""

    regression = linregress(
        depth,
        pressure,
    )

    gradient_bar_per_m = float(
        regression.slope
    )

    gradient_bar_per_100m = (
        gradient_bar_per_m
        * 100.0
    )

    gradient_psi_per_ft = (
        gradient_bar_per_m
        * BAR_TO_PSI
        / M_TO_FT
    )

    equivalent_density = (
        gradient_bar_per_m
        * 100000.0
        / GRAVITY
    )

    return {
        "Pressure Basis": name,
        "Stations": len(depth),
        "Gradient bar/m": (
            gradient_bar_per_m
        ),
        "Gradient bar/100m": (
            gradient_bar_per_100m
        ),
        "Gradient psi/ft": (
            gradient_psi_per_ft
        ),
        "Equivalent Density kg/m3": (
            equivalent_density
        ),
        "Intercept bar": float(
            regression.intercept
        ),
        "R2": float(
            regression.rvalue ** 2
        ),
        "p-value": float(
            regression.pvalue
        ),
        "Slope Std Error bar/m": float(
            regression.stderr
        ),
    }


def build_gradient_summary(qc):
    """Compare source and observed pressure-depth gradients."""

    accepted = qc.loc[
        qc["Use for Observed Gradient"]
    ].copy()

    rows = []

    rows.append(
        gradient_statistics(
            qc["TVD m"],
            qc["Source Formation Pressure bar"],
            "Source formation pressure - all stations",
        )
    )

    rows.append(
        gradient_statistics(
            accepted["TVD m"],
            accepted["Source Formation Pressure bar"],
            "Source formation pressure - closure-screened",
        )
    )

    rows.append(
        gradient_statistics(
            accepted["TVD m"],
            accepted["Final Buildup Pressure bar"],
            "Observed final buildup pressure - closure-screened",
        )
    )

    summary = pd.DataFrame(
        rows
    )

    numeric = summary.select_dtypes(
        include=[np.number]
    ).columns

    summary[numeric] = (
        summary[numeric]
        .round(6)
    )

    return summary


def create_figure(
    qc,
    gradient_summary,
):
    """Create pressure-depth and station-QC diagnostics."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    accepted = qc.loc[
        qc["Use for Observed Gradient"]
    ].copy()

    rejected = qc.loc[
        ~qc["Use for Observed Gradient"]
    ].copy()

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13, 7),
        constrained_layout=True,
    )

    # ---------------------------------------------------------
    # A. Pressure versus TVD
    # ---------------------------------------------------------

    ax = axes[0]

    ax.scatter(
        qc["Source Formation Pressure bar"],
        qc["TVD m"],
        color="#0072B2",
        s=50,
        label="Source formation pressure",
        zorder=5,
    )

    ax.scatter(
        accepted["Final Buildup Pressure bar"],
        accepted["TVD m"],
        facecolors="none",
        edgecolors="#009E73",
        linewidths=1.6,
        s=65,
        label="Observed final buildup",
        zorder=6,
    )

    if not rejected.empty:
        ax.scatter(
            rejected["Final Buildup Pressure bar"],
            rejected["TVD m"],
            marker="x",
            color="#D55E00",
            s=65,
            linewidths=1.8,
            label="Closure-screened station",
            zorder=7,
        )

    depth_line = np.linspace(
        qc["TVD m"].min(),
        qc["TVD m"].max(),
        300,
    )

    source_fit = linregress(
        qc["TVD m"],
        qc["Source Formation Pressure bar"],
    )

    source_pressure_line = (
        source_fit.intercept
        + source_fit.slope
        * depth_line
    )

    observed_fit = linregress(
        accepted["TVD m"],
        accepted["Final Buildup Pressure bar"],
    )

    observed_pressure_line = (
        observed_fit.intercept
        + observed_fit.slope
        * depth_line
    )

    ax.plot(
        source_pressure_line,
        depth_line,
        color="#0072B2",
        linewidth=1.6,
    )

    ax.plot(
        observed_pressure_line,
        depth_line,
        color="#009E73",
        linestyle="--",
        linewidth=1.6,
    )

    for _, row in qc.iterrows():
        ax.annotate(
            str(int(row["Test"])),
            (
                row["Source Formation Pressure bar"],
                row["TVD m"],
            ),
            xytext=(4, -2),
            textcoords="offset points",
            fontsize=8,
        )

    ax.invert_yaxis()

    ax.set_title(
        "A. Formation pressure versus TVD",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Pressure (bar)"
    )

    ax.set_ylabel(
        "TVD (m)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
        fontsize=9,
    )

    # ---------------------------------------------------------
    # B. Pressure closure
    # ---------------------------------------------------------

    ax = axes[1]

    ax.axhline(
        CLOSURE_TOLERANCE_BAR,
        color="#666666",
        linestyle="--",
        linewidth=1.1,
        label="Closure criterion",
    )

    ax.scatter(
        qc["Test"],
        qc["Absolute Closure Error bar"],
        color=np.where(
            qc["Use for Observed Gradient"],
            "#0072B2",
            "#D55E00",
        ),
        s=55,
        zorder=5,
    )

    for _, row in qc.iterrows():

        if not row[
            "Use for Observed Gradient"
        ]:

            ax.annotate(
                "Test {}".format(
                    int(row["Test"])
                ),
                (
                    row["Test"],
                    row[
                        "Absolute Closure Error bar"
                    ],
                ),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
            )

    ax.set_yscale(
        "log"
    )

    ax.set_title(
        "B. End-of-buildup pressure closure",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Test"
    )

    ax.set_ylabel(
        "|Final - initial pressure| (bar)"
    )

    ax.set_xticks(
        qc["Test"]
    )

    ax.grid(
        True,
        which="both",
        alpha=0.25,
    )

    fig.suptitle(
        "15/9-F-14 — FPWD Station QC and Pressure-Depth Analysis",
        fontsize=15,
        fontweight="bold",
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_station_qc_gradient.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_station_qc_gradient.pdf"
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
    """Execute station QC and pressure-gradient analysis."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    qc = calculate_qc(
        df
    )

    gradient_summary = (
        build_gradient_summary(
            qc
        )
    )

    qc_path = (
        REPORT_DIR
        / "f14_fpwd_station_qc.csv"
    )

    gradient_path = (
        REPORT_DIR
        / "f14_fpwd_pressure_gradient.csv"
    )

    qc.to_csv(
        qc_path,
        index=False,
    )

    gradient_summary.to_csv(
        gradient_path,
        index=False,
    )

    png_path, pdf_path = create_figure(
        qc,
        gradient_summary,
    )

    print()
    print(
        "15/9-F-14 FPWD STATION QC"
    )
    print()

    print(
        qc[
            [
                "Test",
                "TVD m",
                "Observed Drawdown bar",
                "Recovery Fraction",
                "Closure Error bar",
                "Absolute Closure Error bar",
                "Pressure Closure",
                "Drawdown Amplitude",
                "Source Mobility mD/cP",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "PRESSURE-GRADIENT SUMMARY"
    )
    print()

    print(
        gradient_summary.to_string(
            index=False
        )
    )

    print()
    print(
        "Outputs:"
    )
    print(
        "  {}".format(
            qc_path
        )
    )
    print(
        "  {}".format(
            gradient_path
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
