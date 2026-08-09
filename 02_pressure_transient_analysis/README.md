# Project 02 - Pressure Transient Analysis

## Objective

Interpret transient well-pressure behavior to identify flow regimes and estimate reservoir and near-wellbore parameters using conventional pressure-transient analysis.

## Engineering Questions

- What flow regimes are present in the pressure response?
- Is wellbore storage observable?
- Can infinite-acting radial flow be identified?
- What reservoir permeability or transmissibility is supported by the transient response?
- What skin factor is indicated by the pressure behavior?
- Are boundary effects visible within the recorded test duration?
- How sensitive are interpreted parameters to the selected analysis interval?

## Analysis Methods

The analysis will include:

- Pressure and time data quality control
- Rate-history review
- Pressure change, Δp
- Shut-in time and equivalent time where required
- Semilog pressure analysis
- Log-log pressure-change diagnostics
- Bourdet pressure derivative
- Flow-regime identification
- Wellbore-storage assessment
- Radial-flow interpretation
- Permeability or kh estimation
- Skin estimation
- Boundary-response assessment
- Parameter sensitivity

## Primary Diagnostic Relationships

Pressure change:

\[
\Delta p = p_{\mathrm{reference}} - p(t)
\]

For buildup analysis:

\[
\Delta p = p_{ws}(t)-p_{wf}
\]

The logarithmic pressure derivative is evaluated as:

\[
\frac{d(\Delta p)}{d\ln t}
\]

Radial flow is identified from an approximately horizontal pressure-derivative response over a sustained time interval.

## Data Requirements

A suitable transient dataset must contain, at minimum:

- elapsed time or timestamp
- pressure
- test type and operating sequence
- consistent engineering units
- the imposed flow disturbance

For conventional well tests, the imposed disturbance is represented by the production or injection rate history. For formation-tester pretests, it is represented by the tool withdrawal or pretest-volume sequence.

Reservoir, fluid, and tool parameters required for quantitative interpretation are documented separately.

## Tools

Python | pandas | NumPy | SciPy | Matplotlib | Git

## Pressure Reference

The LAS interpretation parameter `pPFOR` is stored in psi. Direct psi-to-bar conversion is approximately 1.01325 bar below the formation-pressure value reported in the accompanying Schlumberger FPWD report.

The report BAR value is reproduced by:

\[
P_{\mathrm{report,bar}}
=
P_{\mathrm{pPFOR,psi}}
\times
0.0689475729
+
1.01325
\]

The analysis therefore retains the original LAS value and applies the verified numerical reference reconciliation when comparing `pPFOR` with the quartz-gauge pressure channels expressed in bar.

## FPWD Formation-Pressure Analysis

Formation-pressure-while-drilling measurements from well `15/9-F-14` were evaluated using the quartz-gauge pressure response, source-interpreted formation pressure, drawdown mobility, test timing, and pretest withdrawal volume.

### Pressure-Depth Relationship

![FPWD pressure-gradient robustness](figures/15_9_F_14_fpwd_gradient_residual_analysis.png)

The formation-pressure measurements define a strong linear pressure-depth relationship. The vendor-qualified ordinary least-squares estimate gives a pressure gradient of approximately **0.07050 bar/m (7.05 bar/100 m)** with \(R^2 \approx 0.990\).

The gradient is insensitive to regression method and station screening: ordinary least squares using all stations and Theil-Sen robust regression produce closely comparable estimates.

Residual analysis is retained separately from measurement-quality classification. A pressure station may agree with the regional pressure-depth trend while still exhibit unsuitable transient behavior for formation-pressure interpretation.

### Pretest Response and Mobility

![FPWD mobility-response analysis](figures/15_9_F_14_fpwd_mobility_response.png)

The FPWD pretests used closely comparable withdrawal volumes and average withdrawal rates. Lower-mobility intervals generally required larger pressure drawdown, while high-mobility intervals produced small-amplitude pressure responses.

For vendor-qualified tests with drawdown amplitudes of at least 1 bar, the empirical response index \(q_{\mathrm{avg}}/\Delta P\) shows a strong log-log association with the source-interpreted mobility.

The empirical response index is used as a pressure-response diagnostic and is not treated as an independent permeability or mobility estimate.

### Measurement Quality

The accompanying FPWD interpretation identifies Test 10 as the non-quality pressure measurement because the very high mobility prevented sufficient pressure drawdown. It is therefore excluded from the vendor-qualified pressure-gradient interpretation but retained in diagnostic figures for comparison.

### Pressure Reference

The LAS `pPFOR` pressure values and the report formation-pressure values use a consistent numerical reference offset. Report-referenced pressure in bar is reproduced by

\[
P_{\mathrm{report,bar}}
=
P_{\mathrm{pPFOR,psi}}
\times 0.0689475729
+
1.01325
\]

Both the original source value and the reconciled pressure reference are retained in the reproducible workflow.
