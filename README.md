# Reservoir Engineering Portfolio

## Aijaz Ali

M.Sc. Petroleum Engineering Candidate

This repository contains technical reservoir-engineering projects focused on production analysis, pressure interpretation, reservoir simulation, forecasting, uncertainty screening, and reservoir-development decision making.

The projects combine petroleum-engineering fundamentals with reproducible Python workflows and numerical reservoir modelling.

---

## Technical Projects

### 01 — Decline Curve Analysis and Production Forecasting

[View Project 01](01_decline_curve_analysis/)

Production-surveillance and forecasting workflow using historical well-production data.

Main topics include:

- production-data quality control;
- decline-curve fitting;
- exponential, harmonic, and hyperbolic decline;
- forecast validation;
- production forecasting;
- threshold-based forecast analysis;
- uncertainty assessment; and
- reservoir-engineering interpretation.

---

### 02 — Pressure Transient Analysis

[View Project 02](02_pressure_transient_analysis/)

Pressure-analysis workflow covering formation-pressure interpretation, mobility evaluation, and pressure-transient-analysis concepts.

Main topics include:

- formation-pressure interpretation;
- pressure-gradient estimation;
- fluid-density interpretation;
- mobility analysis;
- pressure-transient diagnostics;
- permeability estimation;
- skin interpretation; and
- numerical verification of PTA calculations.

---

### 03 — Volve Reservoir Simulation Reproduction and Sensitivity Analysis

[View Project 03](03_volve_reservoir_simulation/)

Cross-simulator reproduction of the publicly released Volve ECLIPSE reservoir model using OPM Flow, followed by controlled deterministic reservoir-sensitivity analysis.

The workflow includes:

- simulation-deck and compatibility auditing;
- ECLIPSE-to-OPM Flow model adaptation;
- 339 aligned report-time comparisons;
- field-scale production and pressure comparison;
- individual-well oil-rate, BHP, and water-cut comparison;
- quantitative cross-simulator error analysis;
- fault-connectivity sensitivity;
- local permeability sensitivity;
- regional pore-volume sensitivity; and
- physical interpretation of production, pressure, and well-control responses.

Field production-rate NRMSE values are approximately 1.8–1.9%, while cumulative production and field-pressure NRMSE values are approximately 0.4–0.5%.

Within the parameter ranges investigated, north-side pore volume produced the largest final cumulative-oil response, followed by local P-F-12 permeability and the selected fault-connectivity perturbation.

The study reproduces and extends an already calibrated released model; it does not claim to perform a new Volve history match.

---

## Planned Technical Projects

### 04 — Infill-Well Evaluation

Reservoir-development screening and candidate-well evaluation using production, pressure, connectivity, and remaining-potential indicators.

### 05 — Improved Recovery and Reservoir Management

Evaluation of reservoir-management and improved-recovery scenarios using production response, pressure support, displacement behaviour, and engineering constraints.

### 06 — Pore-Scale Multiphase Flow Modelling

Pore-scale numerical investigation of multiphase flow and fine-particle behaviour, including capillary effects, particle detachment, and near-wall migration.

---

## Technical Focus

Reservoir Engineering | Reservoir Simulation | Pressure Transient Analysis | Production Analysis | Multiphase Flow | Numerical Modelling | Python

---

## Software and Computational Tools

Python | OPM Flow | ECLIPSE | CMG | Petrel | PROSPER | MBAL

---

## Repository Philosophy

Each project is structured around a traceable engineering workflow:

**data or model input → quality control → analysis or simulation → quantitative verification → sensitivity assessment → physical interpretation → engineering conclusions**

The emphasis is on reproducible analysis, technically defensible assumptions, and interpretation of results rather than software execution alone.
