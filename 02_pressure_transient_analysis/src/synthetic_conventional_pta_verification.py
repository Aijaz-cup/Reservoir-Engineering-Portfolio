#!/usr/bin/env python3
"""
Synthetic conventional pressure-transient-analysis verification benchmark.

Purpose
-------
Verify that the conventional PTA workflow can recover known reservoir
properties from analytically generated drawdown and buildup data.

This is a synthetic verification benchmark, not field data.

Model assumptions
-----------------
- single-phase slightly compressible liquid;
- homogeneous isotropic reservoir;
- infinite-acting radial flow;
- constant production rate before shut-in;
- line-source radial diffusivity solution;
- ideal sandface buildup;
- constant skin during flowing conditions;
- no wellbore storage;
- no reservoir boundaries;
- small Gaussian pressure-measurement noise.

Outputs
-------
- synthetic drawdown and buildup data;
- Bourdet-style logarithmic pressure derivative;
- radial-flow permeability estimate;
- Horner buildup permeability and pressure estimate;
- skin estimate;
- verification summary;
- publication-quality diagnostic figure.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.special import exp1
from scipy.stats import linregress


PROJECT = Path(__file__).resolve().parents[1]

REPORT = PROJECT / "report"
FIGURES = PROJECT / "figures"


# ------------------------------------------------------------
# Unit conversions
# ------------------------------------------------------------

BAR_TO_PA = 1.0e5
MD_TO_M2 = 9.869233e-16
DAY_TO_S = 86400.0
HOUR_TO_S = 3600.0


# ------------------------------------------------------------
# Synthetic truth
# ------------------------------------------------------------

PI_BAR = 300.0

Q_SC_SM3_D = 500.0
BO = 1.20

MU_CP = 1.00
MU_PA_S = MU_CP * 1.0e-3

K_TRUE_MD = 100.0
K_TRUE_M2 = K_TRUE_MD * MD_TO_M2

H_M = 20.0
PHI = 0.20
CT_PA_INV = 1.0e-9
RW_M = 0.10

SKIN_TRUE = 3.0

PRODUCTION_TIME_H = 240.0
BUILDUP_DURATION_H = 72.0

DRAWDOWN_NOISE_BAR = 0.03
BUILDUP_NOISE_BAR = 0.02

SEED = 20260810


# ------------------------------------------------------------
# Derived quantities
# ------------------------------------------------------------

Q_RES_M3_S = (
    Q_SC_SM3_D
    * BO
    / DAY_TO_S
)

A_TRUE_PA = (
    Q_RES_M3_S
    * MU_PA_S
    / (
        4.0
        * np.pi
        * K_TRUE_M2
        * H_M
    )
)

A_TRUE_BAR = (
    A_TRUE_PA
    / BAR_TO_PA
)


def dimensionless_u(
    time_s,
    permeability_m2,
):
    """
    Line-source diffusivity variable.

    u = phi * mu * ct * rw^2 / (4 k t)
    """

    time_s = np.asarray(
        time_s,
        dtype=float,
    )

    return (
        PHI
        * MU_PA_S
        * CT_PA_INV
        * RW_M**2
        / (
            4.0
            * permeability_m2
            * time_s
        )
    )


def drawdown_pressure_exact(
    time_h,
):
    """
    Exact flowing well pressure for the synthetic line-source model.
    """

    time_s = (
        np.asarray(
            time_h,
            dtype=float,
        )
        * HOUR_TO_S
    )

    u = dimensionless_u(
        time_s,
        K_TRUE_M2,
    )

    pressure_drop_bar = (
        A_TRUE_BAR
        * (
            exp1(u)
            + 2.0 * SKIN_TRUE
        )
    )

    return (
        PI_BAR
        - pressure_drop_bar
    )


def buildup_pressure_exact(
    shutin_time_h,
):
    """
    Exact ideal sandface buildup pressure from superposition.
    """

    shutin_time_h = np.asarray(
        shutin_time_h,
        dtype=float,
    )

    total_time_s = (
        (
            PRODUCTION_TIME_H
            + shutin_time_h
        )
        * HOUR_TO_S
    )

    shutin_time_s = (
        shutin_time_h
        * HOUR_TO_S
    )

    u_total = dimensionless_u(
        total_time_s,
        K_TRUE_M2,
    )

    u_shutin = dimensionless_u(
        shutin_time_s,
        K_TRUE_M2,
    )

    remaining_drawdown_bar = (
        A_TRUE_BAR
        * (
            exp1(u_total)
            - exp1(u_shutin)
        )
    )

    return (
        PI_BAR
        - remaining_drawdown_bar
    )


def bourdet_derivative(
    time,
    pressure_change,
):
    """
    Three-point logarithmic pressure derivative.

    The derivative is evaluated with respect to ln(t) using
    neighbouring slopes weighted by their logarithmic spacing.
    """

    time = np.asarray(
        time,
        dtype=float,
    )

    pressure_change = np.asarray(
        pressure_change,
        dtype=float,
    )

    log_time = np.log(
        time
    )

    derivative = np.full(
        pressure_change.shape,
        np.nan,
        dtype=float,
    )

    for i in range(
        1,
        len(time) - 1,
    ):

        h_left = (
            log_time[i]
            - log_time[i - 1]
        )

        h_right = (
            log_time[i + 1]
            - log_time[i]
        )

        slope_left = (
            pressure_change[i]
            - pressure_change[i - 1]
        ) / h_left

        slope_right = (
            pressure_change[i + 1]
            - pressure_change[i]
        ) / h_right

        derivative[i] = (
            slope_left * h_right
            + slope_right * h_left
        ) / (
            h_left
            + h_right
        )

    return derivative


def permeability_from_radial_slope(
    slope_bar,
):
    """
    Recover permeability from radial-flow derivative plateau.

    slope = q * mu / (4 pi k h)
    """

    slope_pa = (
        slope_bar
        * BAR_TO_PA
    )

    permeability_m2 = (
        Q_RES_M3_S
        * MU_PA_S
        / (
            4.0
            * np.pi
            * H_M
            * slope_pa
        )
    )

    return (
        permeability_m2
        / MD_TO_M2
    )


def percent_error(
    estimate,
    truth,
):
    return (
        100.0
        * (
            estimate
            - truth
        )
        / truth
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

    rng = np.random.default_rng(
        SEED
    )

    # ==========================================================
    # Drawdown benchmark
    # ==========================================================

    drawdown_time_h = np.logspace(
        -3,
        np.log10(
            PRODUCTION_TIME_H
        ),
        140,
    )

    drawdown_exact_bar = (
        drawdown_pressure_exact(
            drawdown_time_h
        )
    )

    drawdown_pressure_bar = (
        drawdown_exact_bar
        + rng.normal(
            0.0,
            DRAWDOWN_NOISE_BAR,
            size=len(
                drawdown_time_h
            ),
        )
    )

    pressure_change_bar = (
        PI_BAR
        - drawdown_pressure_bar
    )

    pressure_derivative_bar = (
        bourdet_derivative(
            drawdown_time_h,
            pressure_change_bar,
        )
    )

    # Predefined radial-flow interpretation window for
    # this verification benchmark.
    radial_mask = (
        (drawdown_time_h >= 0.1)
        & (drawdown_time_h <= 100.0)
        & np.isfinite(
            pressure_derivative_bar
        )
        & (
            pressure_derivative_bar
            > 0.0
        )
    )

    radial_plateau_bar = float(
        np.median(
            pressure_derivative_bar[
                radial_mask
            ]
        )
    )

    k_derivative_md = (
        permeability_from_radial_slope(
            radial_plateau_bar
        )
    )

    # ==========================================================
    # Buildup benchmark
    # ==========================================================

    shutin_time_h = np.logspace(
        -3,
        np.log10(
            BUILDUP_DURATION_H
        ),
        120,
    )

    buildup_exact_bar = (
        buildup_pressure_exact(
            shutin_time_h
        )
    )

    buildup_pressure_bar = (
        buildup_exact_bar
        + rng.normal(
            0.0,
            BUILDUP_NOISE_BAR,
            size=len(
                shutin_time_h
            ),
        )
    )

    horner_ratio = (
        PRODUCTION_TIME_H
        + shutin_time_h
    ) / shutin_time_h

    ln_horner = np.log(
        horner_ratio
    )

    # Late-time Horner interpretation window.
    buildup_fit_mask = (
        (shutin_time_h >= 0.2)
        & (
            shutin_time_h
            <= BUILDUP_DURATION_H
        )
    )

    fit = linregress(
        ln_horner[
            buildup_fit_mask
        ],
        buildup_pressure_bar[
            buildup_fit_mask
        ],
    )

    horner_slope_bar = float(
        fit.slope
    )

    horner_intercept_bar = float(
        fit.intercept
    )

    horner_r2 = float(
        fit.rvalue**2
    )

    radial_coefficient_horner_bar = (
        abs(
            horner_slope_bar
        )
    )

    k_horner_md = (
        permeability_from_radial_slope(
            radial_coefficient_horner_bar
        )
    )

    # Pre-shut-in flowing pressure from the synthetic
    # drawdown sequence.
    pwf_before_shutin_bar = float(
        drawdown_pressure_bar[-1]
    )

    k_horner_m2 = (
        k_horner_md
        * MD_TO_M2
    )

    u_tp_est = float(
        dimensionless_u(
            PRODUCTION_TIME_H
            * HOUR_TO_S,
            k_horner_m2,
        )
    )

    skin_est = 0.5 * (
        (
            horner_intercept_bar
            - pwf_before_shutin_bar
        )
        / radial_coefficient_horner_bar
        - exp1(
            u_tp_est
        )
    )

    # ==========================================================
    # Save synthetic data
    # ==========================================================

    drawdown = pd.DataFrame(
        {
            "Time h":
                drawdown_time_h,

            "Pressure Exact bar":
                drawdown_exact_bar,

            "Pressure Observed bar":
                drawdown_pressure_bar,

            "Pressure Change bar":
                pressure_change_bar,

            "Log Pressure Derivative bar":
                pressure_derivative_bar,

            "Radial Flow Window":
                radial_mask.astype(int),
        }
    )

    buildup_fit_bar = (
        fit.intercept
        + fit.slope
        * ln_horner
    )

    buildup = pd.DataFrame(
        {
            "Shut-in Time h":
                shutin_time_h,

            "Horner Ratio":
                horner_ratio,

            "ln Horner Ratio":
                ln_horner,

            "Pressure Exact bar":
                buildup_exact_bar,

            "Pressure Observed bar":
                buildup_pressure_bar,

            "Horner Fit bar":
                buildup_fit_bar,

            "Horner Fit Window":
                buildup_fit_mask.astype(int),
        }
    )

    input_parameters = pd.DataFrame(
        [
            [
                "Initial pressure",
                PI_BAR,
                "bar",
            ],
            [
                "Surface oil rate",
                Q_SC_SM3_D,
                "Sm3/d",
            ],
            [
                "Formation volume factor",
                BO,
                "rm3/Sm3",
            ],
            [
                "Oil viscosity",
                MU_CP,
                "cP",
            ],
            [
                "Permeability",
                K_TRUE_MD,
                "mD",
            ],
            [
                "Net thickness",
                H_M,
                "m",
            ],
            [
                "Porosity",
                PHI,
                "fraction",
            ],
            [
                "Total compressibility",
                CT_PA_INV,
                "1/Pa",
            ],
            [
                "Wellbore radius",
                RW_M,
                "m",
            ],
            [
                "Skin",
                SKIN_TRUE,
                "dimensionless",
            ],
            [
                "Production time",
                PRODUCTION_TIME_H,
                "h",
            ],
            [
                "Buildup duration",
                BUILDUP_DURATION_H,
                "h",
            ],
        ],
        columns=[
            "Parameter",
            "Value",
            "Unit",
        ],
    )

    summary = pd.DataFrame(
        [
            [
                "Permeability from derivative plateau",
                K_TRUE_MD,
                k_derivative_md,
                percent_error(
                    k_derivative_md,
                    K_TRUE_MD,
                ),
                "mD",
            ],
            [
                "Permeability from Horner slope",
                K_TRUE_MD,
                k_horner_md,
                percent_error(
                    k_horner_md,
                    K_TRUE_MD,
                ),
                "mD",
            ],
            [
                "Initial pressure from Horner intercept",
                PI_BAR,
                horner_intercept_bar,
                percent_error(
                    horner_intercept_bar,
                    PI_BAR,
                ),
                "bar",
            ],
            [
                "Skin",
                SKIN_TRUE,
                skin_est,
                percent_error(
                    skin_est,
                    SKIN_TRUE,
                ),
                "dimensionless",
            ],
        ],
        columns=[
            "Quantity",
            "True Value",
            "Estimated Value",
            "Error %",
            "Unit",
        ],
    )

    qc = pd.DataFrame(
        [
            [
                "True radial-flow derivative plateau",
                A_TRUE_BAR,
            ],
            [
                "Estimated derivative plateau",
                radial_plateau_bar,
            ],
            [
                "Horner slope magnitude",
                radial_coefficient_horner_bar,
            ],
            [
                "Horner R2",
                horner_r2,
            ],
            [
                "Pre-shut-in flowing pressure bar",
                pwf_before_shutin_bar,
            ],
            [
                "Drawdown pressure noise std bar",
                DRAWDOWN_NOISE_BAR,
            ],
            [
                "Buildup pressure noise std bar",
                BUILDUP_NOISE_BAR,
            ],
            [
                "Random seed",
                SEED,
            ],
        ],
        columns=[
            "Metric",
            "Value",
        ],
    )

    drawdown.to_csv(
        REPORT
        / "synthetic_pta_drawdown.csv",
        index=False,
        float_format="%.8f",
    )

    buildup.to_csv(
        REPORT
        / "synthetic_pta_buildup.csv",
        index=False,
        float_format="%.8f",
    )

    input_parameters.to_csv(
        REPORT
        / "synthetic_pta_input_parameters.csv",
        index=False,
    )

    summary.to_csv(
        REPORT
        / "synthetic_pta_verification_summary.csv",
        index=False,
        float_format="%.6f",
    )

    qc.to_csv(
        REPORT
        / "synthetic_pta_qc.csv",
        index=False,
        float_format="%.8f",
    )

    # ==========================================================
    # Figure
    # ==========================================================

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
            8.3,
        ),
    )

    # ----------------------------------------------------------
    # A. Drawdown pressure
    # ----------------------------------------------------------

    ax = axes[0, 0]

    ax.semilogx(
        drawdown_time_h,
        drawdown_pressure_bar,
        "o",
        markersize=3.2,
        alpha=0.65,
        label="Synthetic observations",
    )

    ax.semilogx(
        drawdown_time_h,
        drawdown_exact_bar,
        color="black",
        linewidth=1.7,
        label="Analytical solution",
    )

    ax.set_title(
        "A. Constant-rate drawdown"
    )

    ax.set_xlabel(
        "Elapsed time (h)"
    )

    ax.set_ylabel(
        "Flowing pressure (bar)"
    )

    ax.grid(
        alpha=0.20,
    )

    ax.legend(
        frameon=False,
    )

    # ----------------------------------------------------------
    # B. Pressure and derivative diagnostic
    # ----------------------------------------------------------

    ax = axes[0, 1]

    ax.loglog(
        drawdown_time_h,
        pressure_change_bar,
        color="#3182bd",
        linewidth=1.4,
        label="Pressure change",
    )

    valid_derivative = (
        np.isfinite(
            pressure_derivative_bar
        )
        & (
            pressure_derivative_bar
            > 0.0
        )
    )

    ax.loglog(
        drawdown_time_h[
            valid_derivative
        ],
        pressure_derivative_bar[
            valid_derivative
        ],
        color="#d95f0e",
        linewidth=1.4,
        label="Logarithmic derivative",
    )

    ax.axhline(
        radial_plateau_bar,
        color="black",
        linestyle="--",
        linewidth=1.2,
        label=(
            "Radial-flow plateau "
            f"{radial_plateau_bar:.3f} bar"
        ),
    )

    ax.axvspan(
        0.1,
        100.0,
        color="#31a354",
        alpha=0.08,
        label="Interpretation window",
    )

    ax.set_title(
        "B. Log-log pressure diagnostic"
    )

    ax.set_xlabel(
        "Elapsed time (h)"
    )

    ax.set_ylabel(
        "Pressure response (bar)"
    )

    ax.grid(
        alpha=0.20,
        which="both",
    )

    ax.legend(
        frameon=False,
        fontsize=8,
    )

    # ----------------------------------------------------------
    # C. Horner buildup
    # ----------------------------------------------------------

    ax = axes[1, 0]

    ax.scatter(
        ln_horner,
        buildup_pressure_bar,
        s=16,
        alpha=0.60,
        label="Synthetic buildup",
    )

    order = np.argsort(
        ln_horner
    )

    ax.plot(
        ln_horner[
            order
        ],
        buildup_fit_bar[
            order
        ],
        color="#d7301f",
        linewidth=1.8,
        label="Late-time Horner fit",
    )

    ax.scatter(
        [0.0],
        [
            horner_intercept_bar
        ],
        marker="*",
        s=110,
        color="#238b45",
        label=(
            "Extrapolated "
            f"$p_i$={horner_intercept_bar:.2f} bar"
        ),
        zorder=5,
    )

    ax.set_title(
        "C. Pressure-buildup Horner analysis"
    )

    ax.set_xlabel(
        r"$\ln[(t_p+\Delta t)/\Delta t]$"
    )

    ax.set_ylabel(
        "Shut-in pressure (bar)"
    )

    ax.grid(
        alpha=0.20,
    )

    ax.legend(
        frameon=False,
        fontsize=8,
    )

    # ----------------------------------------------------------
    # D. Verification against known truth
    # ----------------------------------------------------------

    ax = axes[1, 1]

    labels = [
        "k, derivative",
        "k, Horner",
        "Initial pressure",
        "Skin",
    ]

    ratios = np.array(
        [
            k_derivative_md
            / K_TRUE_MD,

            k_horner_md
            / K_TRUE_MD,

            horner_intercept_bar
            / PI_BAR,

            skin_est
            / SKIN_TRUE,
        ]
    )

    colors = [
        "#3182bd",
        "#6baed6",
        "#31a354",
        "#756bb1",
    ]

    bars = ax.barh(
        labels,
        ratios,
        color=colors,
        alpha=0.85,
    )

    ax.axvline(
        1.0,
        color="black",
        linestyle="--",
        linewidth=1.2,
        label="Known truth",
    )

    for bar, ratio in zip(
        bars,
        ratios,
    ):

        ax.text(
            ratio + 0.002,
            bar.get_y()
            + bar.get_height() / 2.0,
            f"{ratio:.4f}",
            va="center",
            fontsize=8,
        )

    ax.set_title(
        "D. Parameter-recovery verification"
    )

    ax.set_xlabel(
        "Estimated / true value"
    )

    ax.set_xlim(
        0.96,
        1.04,
    )

    ax.grid(
        axis="x",
        alpha=0.20,
    )

    ax.legend(
        frameon=False,
    )

    fig.suptitle(
        "Synthetic Conventional PTA Verification Benchmark"
    )

    fig.text(
        0.5,
        0.012,
        (
            "Homogeneous infinite-acting reservoir; constant-rate "
            "production; line-source solution; ideal sandface buildup; "
            "small Gaussian gauge noise; no wellbore-storage or boundary effects."
        ),
        ha="center",
        fontsize=8,
        color="#444444",
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
        / "synthetic_conventional_pta_verification.png",
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        FIGURES
        / "synthetic_conventional_pta_verification.pdf",
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    # ==========================================================
    # Terminal summary
    # ==========================================================

    print(
        "=== Synthetic conventional PTA verification complete ==="
    )

    print()

    print(
        f"True permeability            : "
        f"{K_TRUE_MD:.4f} mD"
    )

    print(
        f"Derivative permeability      : "
        f"{k_derivative_md:.4f} mD"
    )

    print(
        f"Horner permeability          : "
        f"{k_horner_md:.4f} mD"
    )

    print()

    print(
        f"True initial pressure         : "
        f"{PI_BAR:.4f} bar"
    )

    print(
        f"Horner initial pressure       : "
        f"{horner_intercept_bar:.4f} bar"
    )

    print()

    print(
        f"True skin                     : "
        f"{SKIN_TRUE:.4f}"
    )

    print(
        f"Estimated skin                : "
        f"{skin_est:.4f}"
    )

    print()

    print(
        f"Horner linear-fit R2          : "
        f"{horner_r2:.6f}"
    )

    print()

    print(
        summary.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
