#!/usr/bin/env python3
"""
Probabilistic decline forecasting for Volve 15/9-F-14.

Residual-bootstrap uncertainty is propagated through the validated
exponential decline model.

Scope:
- parameter/calibration uncertainty conditional on the selected
  exponential decline model;
- probabilistic future rate;
- uncertainty in time to technical terminal-rate thresholds;
- uncertainty in incremental forecast oil.

Not included:
- future interventions;
- economic uncertainty;
- facility constraints;
- decline-model-form uncertainty.
"""

from pathlib import Path
import importlib.util
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


PROJECT = Path(__file__).resolve().parents[1]

MODEL = (
    PROJECT
    / "src"
    / "f14_final_exponential_model.py"
)

REPORT = PROJECT / "report"
FIGURES = PROJECT / "figures"

NBOOT = 5000
BLOCK = 3
SEED = 20260810

FORECAST_MONTHS = 60

TERMINAL_RATES = (
    100.0,
    75.0,
    50.0,
    25.0,
)

DAYS_PER_MONTH = 365.25 / 12.0


def import_model():
    """Import the validated deterministic F-14 model."""

    spec = importlib.util.spec_from_file_location(
        "f14_final",
        MODEL,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to import {MODEL}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def block_bootstrap(
    values,
    n,
    block,
    rng,
):
    """Circular moving-block residual bootstrap."""

    values = np.asarray(
        values,
        dtype=float,
    )

    starts = rng.integers(
        0,
        len(values),
        size=math.ceil(
            n / block
        ),
    )

    sampled = np.concatenate(
        [
            values[
                (
                    start
                    + np.arange(block)
                )
                % len(values)
            ]
            for start in starts
        ]
    )

    return sampled[:n]


def annual_decline(d):
    """Effective annual decline fraction."""

    return (
        1.0
        - np.exp(
            -12.0
            * np.asarray(
                d,
                dtype=float,
            )
        )
    )


def terminal_metrics(
    qi,
    d,
    t0,
    terminal_rate,
):
    """
    Forecast time and incremental oil from the
    forecast start to a technical terminal rate.
    """

    qi = np.asarray(
        qi,
        dtype=float,
    )

    d = np.asarray(
        d,
        dtype=float,
    )

    q0 = (
        qi
        * np.exp(
            -d * t0
        )
    )

    months = np.zeros_like(
        q0
    )

    oil = np.zeros_like(
        q0
    )

    valid = (
        (qi > 0.0)
        & (d > 0.0)
        & (terminal_rate < q0)
    )

    t_terminal = (
        np.log(
            qi[valid]
            / terminal_rate
        )
        / d[valid]
    )

    months[valid] = np.maximum(
        t_terminal - t0,
        0.0,
    )

    oil[valid] = (
        DAYS_PER_MONTH
        * qi[valid]
        / d[valid]
        * (
            np.exp(
                -d[valid] * t0
            )
            - np.exp(
                -d[valid]
                * t_terminal
            )
        )
    )

    return (
        q0,
        months,
        oil,
    )


def distribution_row(
    name,
    values,
    deterministic,
    unit,
):
    """Summarize one probabilistic quantity."""

    values = np.asarray(
        values,
        dtype=float,
    )

    return {
        "Quantity": name,
        "Deterministic": deterministic,
        "Mean": np.mean(values),
        "Std Dev": np.std(
            values,
            ddof=1,
        ),
        "10th Percentile": np.quantile(
            values,
            0.10,
        ),
        "50th Percentile": np.quantile(
            values,
            0.50,
        ),
        "90th Percentile": np.quantile(
            values,
            0.90,
        ),
        "Unit": unit,
    }


def lag1(values):
    """Simple lag-1 residual correlation."""

    values = np.asarray(
        values,
        dtype=float,
    )

    if len(values) < 3:
        return np.nan

    x = values[:-1]
    y = values[1:]

    if (
        np.std(x) == 0.0
        or np.std(y) == 0.0
    ):
        return np.nan

    return float(
        np.corrcoef(
            x,
            y,
        )[0, 1]
    )


def main():

    REPORT.mkdir(
        parents=True,
        exist_ok=True,
    )

    FIGURES.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = import_model()

    df = model.load_data().copy()

    t = df[
        "t_months"
    ].to_numpy(
        dtype=float
    )

    observed = df[
        "Oil Rate Sm3/d"
    ].to_numpy(
        dtype=float
    )

    # Use the persisted final-model summary as the
    # authoritative deterministic forecast parameter source.
    #
    # This keeps the probabilistic workflow numerically aligned
    # with the existing terminal-rate forecast workflow.
    model_summary = pd.read_csv(
        REPORT
        / "f14_final_exponential_model.csv"
    )

    qi0 = float(
        model_summary.loc[
            0,
            "qi Sm3/d",
        ]
    )

    d0 = float(
        model_summary.loc[
            0,
            "D 1/month",
        ]
    )

    fitted = np.asarray(
        model.exponential(
            t,
            qi0,
            d0,
        ),
        dtype=float,
    )

    residuals = (
        observed
        - fitted
    )

    centered_residuals = (
        residuals
        - residuals.mean()
    )

    # Next month after the final historical month.
    forecast_start_t = float(
        t.max()
        + 1.0
    )

    forecast_start_date = (
        pd.Timestamp(
            df["Month"].max()
        )
        + pd.offsets.MonthBegin(1)
    )

    forecast_dates = pd.date_range(
        forecast_start_date,
        periods=FORECAST_MONTHS,
        freq="MS",
    )

    forecast_t = (
        forecast_start_t
        + np.arange(
            FORECAST_MONTHS,
            dtype=float,
        )
    )

    deterministic_rate = (
        model.exponential(
            forecast_t,
            qi0,
            d0,
        )
    )

    rng = np.random.default_rng(
        SEED
    )

    qi_samples = []
    d_samples = []

    attempts = 0

    while (
        len(qi_samples) < NBOOT
        and attempts < 20 * NBOOT
    ):

        attempts += 1

        bootstrap_residuals = (
            block_bootstrap(
                centered_residuals,
                len(observed),
                BLOCK,
                rng,
            )
        )

        synthetic_rate = np.maximum(
            fitted
            + bootstrap_residuals,
            1.0e-6,
        )

        bootstrap_df = df.copy()

        bootstrap_df[
            "Oil Rate Sm3/d"
        ] = synthetic_rate

        try:

            result = (
                model.fit_final_model(
                    bootstrap_df
                )
            )

            qi = float(
                result["qi"]
            )

            d = float(
                result["d"]
            )

        except (
            RuntimeError,
            ValueError,
            FloatingPointError,
            np.linalg.LinAlgError,
        ):
            continue

        if (
            np.isfinite(qi)
            and np.isfinite(d)
            and qi > 0.0
            and d > 0.0
        ):

            qi_samples.append(
                qi
            )

            d_samples.append(
                d
            )

    if len(qi_samples) != NBOOT:

        raise RuntimeError(
            "Bootstrap failed to generate "
            f"{NBOOT} valid realizations. "
            f"Accepted {len(qi_samples)} "
            f"after {attempts} attempts."
        )

    qi_samples = np.asarray(
        qi_samples
    )

    d_samples = np.asarray(
        d_samples
    )

    annual_samples = annual_decline(
        d_samples
    )

    annual0 = float(
        annual_decline(
            d0
        )
    )

    qstart_samples = (
        qi_samples
        * np.exp(
            -d_samples
            * forecast_start_t
        )
    )

    qstart0 = (
        qi0
        * np.exp(
            -d0
            * forecast_start_t
        )
    )

    rate_realizations = (
        qi_samples[:, None]
        * np.exp(
            -d_samples[:, None]
            * forecast_t[None, :]
        )
    )

    (
        rate_p10,
        rate_p50,
        rate_p90,
    ) = np.quantile(
        rate_realizations,
        [
            0.10,
            0.50,
            0.90,
        ],
        axis=0,
    )

    parameter_summary = pd.DataFrame(
        [
            distribution_row(
                "Initial rate qi",
                qi_samples,
                qi0,
                "Sm3/d",
            ),
            distribution_row(
                "Nominal decline D",
                d_samples,
                d0,
                "1/month",
            ),
            distribution_row(
                "Effective annual decline",
                annual_samples,
                annual0,
                "fraction/year",
            ),
            distribution_row(
                "Forecast-start rate",
                qstart_samples,
                qstart0,
                "Sm3/d",
            ),
        ]
    )

    samples = pd.DataFrame(
        {
            "Realization": np.arange(
                1,
                NBOOT + 1,
            ),
            "qi Sm3/d": qi_samples,
            "D 1/month": d_samples,
            "Effective Annual Decline":
                annual_samples,
            "Forecast Start Rate Sm3/d":
                qstart_samples,
        }
    )

    forecast_summary = []

    deterministic_by_limit = {}

    for terminal_rate in TERMINAL_RATES:

        (
            _,
            months_samples,
            oil_samples,
        ) = terminal_metrics(
            qi_samples,
            d_samples,
            forecast_start_t,
            terminal_rate,
        )

        (
            _,
            months0,
            oil0,
        ) = terminal_metrics(
            [qi0],
            [d0],
            forecast_start_t,
            terminal_rate,
        )

        deterministic_by_limit[
            terminal_rate
        ] = (
            months0[0],
            oil0[0],
        )

        forecast_summary.append(
            {
                "Terminal Rate Sm3/d":
                    terminal_rate,

                "Deterministic Forecast Months":
                    months0[0],

                "Forecast Months P90":
                    np.quantile(
                        months_samples,
                        0.10,
                    ),

                "Forecast Months P50":
                    np.quantile(
                        months_samples,
                        0.50,
                    ),

                "Forecast Months P10":
                    np.quantile(
                        months_samples,
                        0.90,
                    ),

                "Deterministic Forecast Oil Sm3":
                    oil0[0],

                "Forecast Oil P90 Sm3":
                    np.quantile(
                        oil_samples,
                        0.10,
                    ),

                "Forecast Oil P50 Sm3":
                    np.quantile(
                        oil_samples,
                        0.50,
                    ),

                "Forecast Oil P10 Sm3":
                    np.quantile(
                        oil_samples,
                        0.90,
                    ),

                "Probability Convention":
                    (
                        "Mathematical percentiles: "
                        "10th=low numerical outcome, "
                        "90th=high numerical outcome"
                    ),
            }
        )

        samples[
            f"Forecast Months to "
            f"{terminal_rate:g} Sm3/d"
        ] = months_samples

        samples[
            f"Forecast Oil to "
            f"{terminal_rate:g} Sm3/d Sm3"
        ] = oil_samples

    forecast_summary = pd.DataFrame(
        forecast_summary
    )

    forecast_percentiles = pd.DataFrame(
        {
            "Date":
                forecast_dates,

            "t_months":
                forecast_t,

            "Deterministic Rate Sm3/d":
                deterministic_rate,

            "Rate P90 Sm3/d":
                rate_p10,

            "Rate P50 Sm3/d":
                rate_p50,

            "Rate P10 Sm3/d":
                rate_p90,
        }
    )

    parameter_correlation = float(
        np.corrcoef(
            qi_samples,
            d_samples,
        )[0, 1]
    )

    qc = pd.DataFrame(
        [
            [
                "Requested bootstrap realizations",
                NBOOT,
            ],
            [
                "Accepted bootstrap realizations",
                len(qi_samples),
            ],
            [
                "Bootstrap fitting attempts",
                attempts,
            ],
            [
                "Acceptance fraction",
                len(qi_samples)
                / attempts,
            ],
            [
                "Residual block length months",
                BLOCK,
            ],
            [
                "Random seed",
                SEED,
            ],
            [
                "Residual mean Sm3/d",
                residuals.mean(),
            ],
            [
                "Residual std Sm3/d",
                residuals.std(
                    ddof=1
                ),
            ],
            [
                "Residual lag-1 correlation",
                lag1(
                    residuals
                ),
            ],
            [
                "Bootstrap correlation qi versus D",
                parameter_correlation,
            ],
        ],
        columns=[
            "Metric",
            "Value",
        ],
    )

    parameter_summary.to_csv(
        REPORT
        / "f14_probabilistic_parameter_summary.csv",
        index=False,
        float_format="%.6f",
    )

    forecast_summary.to_csv(
        REPORT
        / "f14_probabilistic_forecast_summary.csv",
        index=False,
        float_format="%.6f",
    )

    forecast_percentiles.to_csv(
        REPORT
        / "f14_probabilistic_forecast_percentiles.csv",
        index=False,
        float_format="%.6f",
        date_format="%Y-%m-%d",
    )

    samples.to_csv(
        REPORT
        / "f14_probabilistic_bootstrap_samples.csv",
        index=False,
        float_format="%.6f",
    )

    qc.to_csv(
        REPORT
        / "f14_probabilistic_bootstrap_qc.csv",
        index=False,
        float_format="%.6f",
    )

    # ============================================================
    # Figure
    # ============================================================

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "figure.titlesize": 13,
        }
    )

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(
            12,
            8.2,
        ),
    )

    ax = axes[0, 0]

    ax.scatter(
        df["Month"],
        df["Oil Rate Sm3/d"],
        s=28,
        color="#4c78a8",
        edgecolor="white",
        linewidth=0.4,
        label="Observed monthly rate",
        zorder=3,
    )

    ax.plot(
        df["Month"],
        fitted,
        color="black",
        linewidth=1.8,
        label="Final exponential model",
        zorder=4,
    )

    ax.set_title(
        "A. Historical decline and final model"
    )

    ax.set_ylabel(
        "Oil rate (Sm³/d)"
    )

    ax.set_xlabel(
        "Date"
    )

    ax.grid(
        alpha=0.20
    )

    ax.legend(
        frameon=False
    )

    ax = axes[0, 1]

    ax.fill_between(
        forecast_dates,
        rate_p10,
        rate_p90,
        color="#9ecae1",
        alpha=0.60,
        label="P90–P10 forecast range",
    )

    ax.plot(
        forecast_dates,
        rate_p50,
        color="#08519c",
        linewidth=2.0,
        label="P50",
    )

    ax.plot(
        forecast_dates,
        deterministic_rate,
        "k--",
        linewidth=1.5,
        label="Deterministic",
    )

    ax.axhline(
        50.0,
        color="gray",
        linestyle=":",
        linewidth=1.2,
        label="Technical rate limit: 50 Sm³/d",
    )

    ax.set_title(
        "B. Probabilistic rate extrapolation"
    )

    ax.set_ylabel(
        "Oil rate (Sm³/d)"
    )

    ax.set_xlabel(
        "Date"
    )

    ax.grid(
        alpha=0.20
    )

    ax.legend(
        frameon=False
    )

    oil50 = samples[
        "Forecast Oil to 50 Sm3/d Sm3"
    ].to_numpy()

    (
        oil_p10,
        oil_p50,
        oil_p90,
    ) = np.quantile(
        oil50,
        [
            0.10,
            0.50,
            0.90,
        ],
    )

    ax = axes[1, 0]

    ax.hist(
        oil50 / 1000.0,
        bins=35,
        color="#74a9cf",
        edgecolor="white",
    )

    for value, label, color in [
        (
            oil_p10,
            "P90",
            "#cb181d",
        ),
        (
            oil_p50,
            "P50",
            "#08519c",
        ),
        (
            oil_p90,
            "P10",
            "#238b45",
        ),
    ]:

        ax.axvline(
            value / 1000.0,
            color=color,
            linewidth=1.8,
            label=(
                f"{label}: "
                f"{value / 1000.0:.1f}"
            ),
        )

    ax.set_title(
        "C. Forecast oil to 50 Sm³/d technical rate limit"
    )

    ax.set_xlabel(
        "Incremental forecast oil (10³ Sm³)"
    )

    ax.set_ylabel(
        "Realizations"
    )

    ax.grid(
        axis="y",
        alpha=0.18,
    )

    ax.legend(
        frameon=False
    )

    ax = axes[1, 1]

    ax.scatter(
        100.0 * annual_samples,
        oil50 / 1000.0,
        s=9,
        alpha=0.16,
        color="#3182bd",
        edgecolors="none",
    )

    ax.scatter(
        [
            100.0
            * annual0
        ],
        [
            deterministic_by_limit[
                50.0
            ][1]
            / 1000.0
        ],
        marker="*",
        s=120,
        color="#d7301f",
        label="Deterministic",
    )

    ax.set_title(
        "D. Decline uncertainty vs incremental forecast oil"
    )

    ax.set_xlabel(
        "Effective annual decline (%)"
    )

    ax.set_ylabel(
        "Forecast oil to 50 Sm³/d (10³ Sm³)"
    )

    ax.grid(
        alpha=0.20
    )

    ax.legend(
        frameon=False
    )

    fig.suptitle(
        "15/9-F-14 — Probabilistic Decline Forecast and Uncertainty"
    )

    fig.text(
        0.5,
        0.012,
        (
            "5,000-realization moving-block residual bootstrap "
            "conditional on the selected exponential model. "
            "P90/P50/P10 denote 90%/50%/10% probability-of-exceedance "
            "forecast cases; operational, economic and model-form "
            "uncertainty are not included."
        ),
        ha="center",
        fontsize=8,
        color="#444444",
    )

    # Explicit date formatting is used because the date
    # panels occupy the upper row of the 2 x 2 layout.
    for date_axis in (
        axes[0, 0],
        axes[0, 1],
    ):

        date_axis.xaxis.set_major_locator(
            mdates.YearLocator()
        )

        date_axis.xaxis.set_major_formatter(
            mdates.DateFormatter("%Y")
        )

        date_axis.tick_params(
            axis="x",
            labelbottom=True,
        )

        date_axis.set_xlabel(
            "Date"
        )

    fig.tight_layout(
        rect=(
            0,
            0.04,
            1,
            0.95,
        )
    )

    fig.savefig(
        FIGURES
        / "15_9_F_14_probabilistic_forecast.png",
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        FIGURES
        / "15_9_F_14_probabilistic_forecast.pdf",
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    print(
        "=== Probabilistic DCA complete ==="
    )

    print(
        f"Deterministic qi = "
        f"{qi0:.4f} Sm3/d"
    )

    print(
        f"Deterministic D = "
        f"{d0:.6f} 1/month"
    )

    print(
        "Effective annual decline = "
        f"{100.0 * annual0:.3f}%"
    )

    print(
        "Forecast-start rate = "
        f"{qstart0:.4f} Sm3/d"
    )

    print(
        f"Accepted = "
        f"{len(qi_samples)} / "
        f"{attempts}"
    )

    print(
        "Bootstrap qi-D correlation = "
        f"{parameter_correlation:.4f}"
    )

    print()

    print(
        "FORECAST SUMMARY"
    )

    print(
        forecast_summary.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
