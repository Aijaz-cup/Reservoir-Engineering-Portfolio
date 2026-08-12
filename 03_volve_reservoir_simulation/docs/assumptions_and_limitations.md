# Assumptions and Limitations

## Released model versus new history match

The publicly released Volve model already contains the calibration and history-matching work associated with the reference model.

This project reproduces, audits and extends that released model. It does not claim to perform a new history match.

## Cross-simulator reproduction is not reservoir validation

Close agreement between OPM Flow and the released ECLIPSE response demonstrates cross-simulator consistency for the model being studied.

It does not independently validate the geological interpretation, petrophysical properties, PVT description, relative permeability, fault interpretation or actual reservoir behaviour.

## Simulator implementations are not exactly identical

The released model contains ECLIPSE-specific or incompletely supported constructs.

The OPM Flow implementation therefore required documented compatibility corrections and reduced parser strictness.

The resulting comparison should be interpreted as reproduction of the dominant reservoir response, not proof of exact internal numerical equivalence.

## Grid-geometry compatibility

`ADDZCORN` was identified as an important compatibility limitation because it can modify grid geometry.

Differences in simulator handling of geometry-related operations mean that complete cell-by-cell equivalence should not be assumed.

## Aggregated and local responses behave differently

Field totals combine the response of many grid cells and wells and can therefore smooth local differences.

Individual wells are more sensitive to local transmissibility, saturation, completion behaviour, pressure and control transitions.

For this reason, the project compares both field-scale and well-scale quantities.

## Water-cut sensitivity

Water cut depends strongly on local saturation evolution and water-front arrival.

Small differences in saturation-front timing can therefore produce larger relative discrepancies in water cut than in cumulative field production or field pressure.

## Deterministic sensitivity screening

The Low/Base/High cases are controlled deterministic sensitivity scenarios.

They are not probability distributions and should not be interpreted as P10/P50/P90 uncertainty cases.

## Range-dependent sensitivity ranking

Sensitivity ranking depends on the magnitude and physical definition of each perturbation.

The reported ranking therefore applies only to the parameter ranges investigated in this study.

## End-point metrics are incomplete

Final cumulative production is useful for comparing long-term outcomes but does not indicate when differences develop.

Time-dependent response was therefore also examined for the dominant pore-volume sensitivity.

## Well controls affect interpretation

Reservoir-property changes do not necessarily translate directly into proportional rate changes.

For a rate-constrained producer, reduced permeability may instead require greater pressure drawdown to maintain the scheduled production rate.

The P-F-12 permeability sensitivity demonstrates this interaction.

## Public repository scope

Large simulator output directories, restart files, complete grid files and the full released reservoir archive are intentionally excluded from the public project package.

The repository contains compact derived datasets, reproducible analysis scripts, figures and technical documentation required to understand the workflow and results.
