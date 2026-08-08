"""Production forecast and terminal-rate sensitivity for Volve 15/9-F-14.

Historical cumulative oil is taken directly from the production data through
March 2016. Future oil production is calculated from the accepted exponential
decline model under alternative terminal-rate assumptions.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

OPERATING_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_monthly_operating_summary.csv"
)

MODEL_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_final_exponential_model.csv"
)

REPORT_DIR = PROJECT_DIR / "report"
FIGURE_DIR = PROJECT_DIR / "figures"

FIT_START = pd.Timestamp("2013-05-01")
FIT_END = pd.Timestamp("2016-03-01")
FORECAST_START = pd.Timestamp("2016-04-01")

DAYS_PER_MONTH = 365.25 / 12.0
SM3_TO_STB = 6.28981

TERMINAL_RATES = [
    100.0,
    75.0,
    50.0,
    25.0,
]


def exponential(t, qi, d):
    """Continuous exponential decline model."""

    return qi * np.exp(
        -d * t
    )


def months_from_fit_start(date):
    """Return integer month index relative to May 2013."""

    return (
        (date.year - FIT_START.year) * 12
        + date.month
        - FIT_START.month
    )


def load_inputs():
    """Load production history and accepted model parameters."""

    history = pd.read_csv(
        OPERATING_FILE,
        parse_dates=["Month"],
    )

    model = pd.read_csv(
        MODEL_FILE,
    )

    if len(model) != 1:
        raise ValueError(
            "Expected one final-model record."
        )

    qi = float(
        model.loc[0, "qi Sm3/d"]
    )

    d = float(
        model.loc[0, "D 1/month"]
    )

    return history, qi, d


def cumulative_forecast(
    qi,
    d,
    t_start,
    t_end,
):
    """Analytical cumulative oil between two model times."""

    return (
        DAYS_PER_MONTH
        * qi
        / d
        * (
            np.exp(-d * t_start)
            - np.exp(-d * t_end)
        )
    )


def build_recovery_table(
    history,
    qi,
    d,
):
    """Calculate recovery to alternative terminal-rate assumptions."""

    historical = history.loc[
        history["Month"] <= FIT_END
    ].copy()

    historical_cumulative = float(
        historical["Oil Sm3"]
        .fillna(0.0)
        .sum()
    )

    selected_history = history.loc[
        (history["Month"] >= FIT_START)
        & (history["Month"] <= FIT_END)
    ]

    selected_actual_oil = float(
        selected_history["Oil Sm3"]
        .fillna(0.0)
        .sum()
    )

    t_forecast_start = float(
        months_from_fit_start(
            FORECAST_START
        )
    )

    forecast_start_rate = float(
        exponential(
            t_forecast_start,
            qi,
            d,
        )
    )

    rows = []

    for terminal_rate in TERMINAL_RATES:

        if terminal_rate >= forecast_start_rate:
            t_terminal = t_forecast_start
        else:
            t_terminal = float(
                np.log(
                    qi / terminal_rate
                )
                / d
            )

        forecast_months = max(
            0.0,
            t_terminal
            - t_forecast_start
        )

        future_oil = cumulative_forecast(
            qi,
            d,
            t_forecast_start,
            t_terminal,
        )

        projected_total = (
            historical_cumulative
            + future_oil
        )

        terminal_month = (
            FIT_START
            + pd.DateOffset(
                months=int(
                    np.ceil(
                        t_terminal
                    )
                )
            )
        )

        rows.append(
            {
                "Terminal Rate Sm3/d": terminal_rate,
                "Forecast Start Rate Sm3/d": (
                    forecast_start_rate
                ),
                "Forecast Months": forecast_months,
                "First Full Month Below Terminal Rate": (
                    terminal_month.strftime(
                        "%Y-%m"
                    )
                ),
                "Historical Oil to 2016-03 Sm3": (
                    historical_cumulative
                ),
                "Oil During Selected Fit Period Sm3": (
                    selected_actual_oil
                ),
                "Forecast Oil Sm3": future_oil,
                "Projected Cumulative Oil Sm3": (
                    projected_total
                ),
                "Projected Cumulative Oil MMsm3": (
                    projected_total
                    / 1.0e6
                ),
                "Projected Cumulative Oil MMstb": (
                    projected_total
                    * SM3_TO_STB
                    / 1.0e6
                ),
            }
        )

    result = pd.DataFrame(
        rows
    )

    numeric = result.select_dtypes(
        include=[np.number]
    ).columns

    result[numeric] = (
        result[numeric]
        .round(4)
    )

    return result


def create_figure(
    history,
    qi,
    d,
    recovery,
):
    """Create oil-rate forecast and terminal-rate recovery-sensitivity figure."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    t_forecast_start = float(
        months_from_fit_start(
            FORECAST_START
        )
    )

    minimum_rate = min(
        TERMINAL_RATES
    )

    t_final = float(
        np.log(
            qi / minimum_rate
        )
        / d
    )

    t_dense = np.linspace(
        0.0,
        t_final,
        600,
    )

    dates_dense = (
        FIT_START
        + pd.to_timedelta(
            t_dense
            * DAYS_PER_MONTH,
            unit="D",
        )
    )

    q_dense = exponential(
        t_dense,
        qi,
        d,
    )

    selected = history.loc[
        (history["Month"] >= FIT_START)
        & (history["Month"] <= FIT_END)
    ].copy()

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(11.5, 8.5),
        constrained_layout=True,
    )

    # ---------------------------------------------------------
    # A. Oil-rate forecast
    # ---------------------------------------------------------

    ax = axes[0]

    ax.scatter(
        selected["Month"],
        selected["Oil Rate Sm3/d"],
        color="black",
        s=30,
        label="Observed oil rate",
        zorder=5,
    )

    ax.plot(
        dates_dense,
        q_dense,
        color="#0072B2",
        linewidth=2.2,
        label="Exponential model",
    )

    ax.axvline(
        FIT_END,
        color="#666666",
        linestyle="--",
        linewidth=1.2,
    )

    terminal_colors = {
        100.0: "#0072B2",
        75.0: "#E69F00",
        50.0: "#009E73",
        25.0: "#D55E00",
    }

    for rate in TERMINAL_RATES:

        ax.axhline(
            rate,
            color=terminal_colors[rate],
            linestyle=":",
            linewidth=1.0,
            alpha=0.8,
        )

        ax.text(
            dates_dense[-1],
            rate,
            "{:.0f} Sm³/d".format(rate),
            va="bottom",
            ha="right",
            fontsize=8,
            color=terminal_colors[rate],
        )

    ax.set_title(
        "A. Oil-rate forecast",
        loc="left",
        fontweight="bold",
    )

    ax.set_ylabel(
        "Oil rate (Sm³/d)"
    )

    ax.set_ylim(
        bottom=0
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
    )

    # ---------------------------------------------------------
    # B. Incremental forecast recovery
    # ---------------------------------------------------------

    ax = axes[1]

    plotting = recovery.sort_values(
        "Terminal Rate Sm3/d",
        ascending=False,
    ).copy()

    colors = [
        terminal_colors[
            float(rate)
        ]
        for rate in plotting[
            "Terminal Rate Sm3/d"
        ]
    ]

    bars = ax.bar(
        plotting[
            "Terminal Rate Sm3/d"
        ].map(lambda value: "{:.0f}".format(value)),
        plotting[
            "Forecast Oil Sm3"
        ] / 1000.0,
        color=colors,
        width=0.62,
    )

    for bar, value in zip(
        bars,
        plotting[
            "Forecast Oil Sm3"
        ],
    ):

        ax.text(
            bar.get_x()
            + bar.get_width() / 2.0,
            bar.get_height(),
            "{:,.0f} Sm³".format(
                value
            ),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_title(
        "B. Incremental forecast oil versus terminal rate",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Terminal rate (Sm³/d)"
    )

    ax.set_ylabel(
        "Forecast oil (10³ Sm³)"
    )

    ax.grid(
        True,
        axis="y",
        alpha=0.25,
    )

    fig.suptitle(
        "15/9-F-14 — Production Forecast and Terminal-Rate Sensitivity",
        fontsize=15,
        fontweight="bold",
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_terminal_rate_forecast.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_terminal_rate_forecast.pdf"
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

    print(
        "Saved: {}".format(
            png_path
        )
    )

    print(
        "Saved: {}".format(
            pdf_path
        )
    )


def main():
    """Execute terminal-rate production forecast."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    history, qi, d = load_inputs()

    recovery = build_recovery_table(
        history,
        qi,
        d,
    )

    output_path = (
        REPORT_DIR
        / "f14_terminal_rate_sensitivity.csv"
    )

    recovery.to_csv(
        output_path,
        index=False,
    )

    create_figure(
        history,
        qi,
        d,
        recovery,
    )

    print()
    print(
        "15/9-F-14 TERMINAL-RATE RECOVERY SENSITIVITY"
    )
    print()

    print(
        recovery.to_string(
            index=False
        )
    )

    print()

    print(
        "Output: {}".format(
            output_path
        )
    )


if __name__ == "__main__":
    main()
