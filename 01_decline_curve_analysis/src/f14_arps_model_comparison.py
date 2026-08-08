"""Arps decline-model comparison for Volve producer 15/9-F-14.

Exponential, harmonic, and hyperbolic decline models are calibrated on the
selected terminal decline regime and evaluated against a chronological
six-month validation interval.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_monthly_operating_summary.csv"
)

REPORT_DIR = PROJECT_DIR / "report"
FIGURE_DIR = PROJECT_DIR / "figures"

FIT_START = pd.Timestamp("2013-05-01")
FIT_END = pd.Timestamp("2016-03-01")

VALIDATION_START = pd.Timestamp("2015-10-01")


def exponential(t, qi, di):
    """Arps exponential decline."""

    return qi * np.exp(-di * t)


def harmonic(t, qi, di):
    """Arps harmonic decline."""

    return qi / (1.0 + di * t)


def hyperbolic(t, qi, di, b):
    """Arps hyperbolic decline."""

    return qi / np.power(
        1.0 + b * di * t,
        1.0 / b,
    )


def load_decline_data():
    """Load the selected F-14 decline interval."""

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["Month"],
    )

    df = (
        df.loc[
            (df["Month"] >= FIT_START)
            & (df["Month"] <= FIT_END)
            & df["Oil Rate Sm3/d"].notna()
        ]
        .copy()
        .sort_values("Month")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError(
            "No observations found in the selected decline interval."
        )

    df["t_months"] = np.arange(
        len(df),
        dtype=float,
    )

    df["Dataset"] = np.where(
        df["Month"] < VALIDATION_START,
        "Calibration",
        "Validation",
    )

    return df


def fit_models(calibration):
    """Fit exponential, harmonic, and hyperbolic models."""

    t = calibration["t_months"].to_numpy(
        dtype=float
    )

    q = calibration["Oil Rate Sm3/d"].to_numpy(
        dtype=float
    )

    qi_guess = float(q[0])

    # Initial exponential decline estimate from log-rate regression.
    slope = np.polyfit(
        t,
        np.log(q),
        1,
    )[0]

    di_guess = max(
        1.0e-4,
        -float(slope),
    )

    exp_parameters, _ = curve_fit(
        exponential,
        t,
        q,
        p0=[
            qi_guess,
            di_guess,
        ],
        bounds=(
            [0.0, 0.0],
            [np.inf, 5.0],
        ),
        maxfev=50000,
    )

    harm_parameters, _ = curve_fit(
        harmonic,
        t,
        q,
        p0=[
            qi_guess,
            di_guess,
        ],
        bounds=(
            [0.0, 0.0],
            [np.inf, 5.0],
        ),
        maxfev=50000,
    )

    hyp_parameters, _ = curve_fit(
        hyperbolic,
        t,
        q,
        p0=[
            qi_guess,
            di_guess,
            0.5,
        ],
        bounds=(
            [0.0, 0.0, 1.0e-6],
            [np.inf, 5.0, 1.0],
        ),
        maxfev=100000,
    )

    return {
        "Exponential": {
            "function": exponential,
            "parameters": exp_parameters,
            "n_parameters": 2,
        },
        "Harmonic": {
            "function": harmonic,
            "parameters": harm_parameters,
            "n_parameters": 2,
        },
        "Hyperbolic": {
            "function": hyperbolic,
            "parameters": hyp_parameters,
            "n_parameters": 3,
        },
    }


def error_metrics(observed, predicted):
    """Calculate deterministic prediction-error statistics."""

    observed = np.asarray(
        observed,
        dtype=float,
    )

    predicted = np.asarray(
        predicted,
        dtype=float,
    )

    residuals = observed - predicted

    rmse = float(
        np.sqrt(
            np.mean(
                residuals ** 2
            )
        )
    )

    mae = float(
        np.mean(
            np.abs(residuals)
        )
    )

    mape = float(
        np.mean(
            np.abs(
                residuals / observed
            )
        )
        * 100.0
    )

    ss_res = float(
        np.sum(
            residuals ** 2
        )
    )

    ss_tot = float(
        np.sum(
            (
                observed
                - np.mean(observed)
            )
            ** 2
        )
    )

    r_squared = (
        1.0 - ss_res / ss_tot
        if ss_tot > 0
        else np.nan
    )

    return {
        "RMSE Sm3/d": rmse,
        "MAE Sm3/d": mae,
        "MAPE %": mape,
        "R2": r_squared,
        "RSS": ss_res,
    }


def aicc_from_rss(
    rss,
    n,
    k,
):
    """Calculate corrected Akaike Information Criterion."""

    if rss <= 0:
        return -np.inf

    aic = (
        n * np.log(rss / n)
        + 2.0 * k
    )

    denominator = (
        n - k - 1
    )

    if denominator <= 0:
        return np.nan

    correction = (
        2.0
        * k
        * (k + 1)
        / denominator
    )

    return float(
        aic + correction
    )


def build_comparison(
    data,
    models,
):
    """Evaluate calibration and chronological validation performance."""

    rows = []

    calibration = data.loc[
        data["Dataset"] == "Calibration"
    ]

    validation = data.loc[
        data["Dataset"] == "Validation"
    ]

    for model_name, model in models.items():

        function = model["function"]

        parameters = model[
            "parameters"
        ]

        k = model[
            "n_parameters"
        ]

        calibration_prediction = function(
            calibration["t_months"].to_numpy(
                dtype=float
            ),
            *parameters
        )

        validation_prediction = function(
            validation["t_months"].to_numpy(
                dtype=float
            ),
            *parameters
        )

        calibration_metrics = error_metrics(
            calibration["Oil Rate Sm3/d"],
            calibration_prediction,
        )

        validation_metrics = error_metrics(
            validation["Oil Rate Sm3/d"],
            validation_prediction,
        )

        row = {
            "Model": model_name,
            "qi Sm3/d": float(
                parameters[0]
            ),
            "Di 1/month": float(
                parameters[1]
            ),
            "b": (
                float(parameters[2])
                if len(parameters) == 3
                else (
                    0.0
                    if model_name == "Exponential"
                    else 1.0
                )
            ),
            "Calibration RMSE Sm3/d": (
                calibration_metrics[
                    "RMSE Sm3/d"
                ]
            ),
            "Calibration MAE Sm3/d": (
                calibration_metrics[
                    "MAE Sm3/d"
                ]
            ),
            "Calibration MAPE %": (
                calibration_metrics[
                    "MAPE %"
                ]
            ),
            "Calibration R2": (
                calibration_metrics["R2"]
            ),
            "Calibration AICc": aicc_from_rss(
                calibration_metrics["RSS"],
                len(calibration),
                k,
            ),
            "Validation RMSE Sm3/d": (
                validation_metrics[
                    "RMSE Sm3/d"
                ]
            ),
            "Validation MAE Sm3/d": (
                validation_metrics[
                    "MAE Sm3/d"
                ]
            ),
            "Validation MAPE %": (
                validation_metrics[
                    "MAPE %"
                ]
            ),
            "Validation R2": (
                validation_metrics["R2"]
            ),
        }

        rows.append(row)

    comparison = pd.DataFrame(
        rows
    )

    numeric_columns = comparison.select_dtypes(
        include=[np.number]
    ).columns

    comparison[numeric_columns] = (
        comparison[numeric_columns]
        .round(5)
    )

    comparison = comparison.sort_values(
        [
            "Validation RMSE Sm3/d",
            "Calibration AICc",
        ]
    ).reset_index(
        drop=True
    )

    return comparison


def create_figure(
    data,
    models,
):
    """Plot historical data, calibration interval, validation interval, and fits."""

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(11.5, 9.0),
        constrained_layout=True,
    )

    calibration = data.loc[
        data["Dataset"] == "Calibration"
    ]

    validation = data.loc[
        data["Dataset"] == "Validation"
    ]

    colors = {
        "Exponential": "#0072B2",
        "Harmonic": "#D55E00",
        "Hyperbolic": "#009E73",
    }

    # ---------------------------------------------------------
    # A. Rate-space comparison
    # ---------------------------------------------------------

    ax = axes[0]

    ax.scatter(
        calibration["Month"],
        calibration["Oil Rate Sm3/d"],
        color="black",
        s=30,
        label="Calibration data",
        zorder=5,
    )

    ax.scatter(
        validation["Month"],
        validation["Oil Rate Sm3/d"],
        color="#CC79A7",
        marker="s",
        s=38,
        label="Validation data",
        zorder=6,
    )

    for model_name, model in models.items():

        prediction = model["function"](
            data["t_months"].to_numpy(
                dtype=float
            ),
            *model["parameters"]
        )

        ax.plot(
            data["Month"],
            prediction,
            linewidth=2.0,
            color=colors[model_name],
            label=model_name,
        )

    ax.axvline(
        VALIDATION_START,
        color="#666666",
        linestyle="--",
        linewidth=1.2,
    )

    ax.set_title(
        "A. Arps model comparison",
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
        ncol=2,
    )

    # ---------------------------------------------------------
    # B. Log-rate comparison
    # ---------------------------------------------------------

    ax = axes[1]

    ax.scatter(
        calibration["Month"],
        calibration["Oil Rate Sm3/d"],
        color="black",
        s=30,
        label="Calibration data",
        zorder=5,
    )

    ax.scatter(
        validation["Month"],
        validation["Oil Rate Sm3/d"],
        color="#CC79A7",
        marker="s",
        s=38,
        label="Validation data",
        zorder=6,
    )

    for model_name, model in models.items():

        prediction = model["function"](
            data["t_months"].to_numpy(
                dtype=float
            ),
            *model["parameters"]
        )

        ax.plot(
            data["Month"],
            prediction,
            linewidth=2.0,
            color=colors[model_name],
            label=model_name,
        )

    ax.axvline(
        VALIDATION_START,
        color="#666666",
        linestyle="--",
        linewidth=1.2,
    )

    ax.set_yscale(
        "log"
    )

    ax.set_title(
        "B. Log-rate comparison",
        loc="left",
        fontweight="bold",
    )

    ax.set_ylabel(
        "Oil rate (Sm³/d)"
    )

    ax.set_xlabel(
        "Date"
    )

    ax.grid(
        True,
        which="both",
        alpha=0.25,
    )

    fig.suptitle(
        "15/9-F-14 — Arps Decline-Model Comparison",
        fontsize=15,
        fontweight="bold",
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_arps_model_comparison.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_arps_model_comparison.pdf"
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
    """Run the Arps calibration and validation comparison."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = load_decline_data()

    calibration = data.loc[
        data["Dataset"] == "Calibration"
    ]

    models = fit_models(
        calibration
    )

    comparison = build_comparison(
        data,
        models,
    )

    output_path = (
        REPORT_DIR
        / "f14_arps_model_comparison.csv"
    )

    comparison.to_csv(
        output_path,
        index=False,
    )

    create_figure(
        data,
        models,
    )

    print()
    print(
        "15/9-F-14 ARPS MODEL COMPARISON"
    )
    print()

    print(
        "Calibration period : {} to {}".format(
            FIT_START.date(),
            (
                VALIDATION_START
                - pd.offsets.MonthBegin(1)
            ).date(),
        )
    )

    print(
        "Validation period  : {} to {}".format(
            VALIDATION_START.date(),
            FIT_END.date(),
        )
    )

    print(
        "Calibration months : {}".format(
            len(calibration)
        )
    )

    print(
        "Validation months  : {}".format(
            int(
                (
                    data["Dataset"]
                    == "Validation"
                ).sum()
            )
        )
    )

    print()

    print(
        comparison.to_string(
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
