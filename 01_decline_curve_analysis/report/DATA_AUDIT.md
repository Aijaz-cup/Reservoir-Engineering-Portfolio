# Volve Production Data Audit

## Purpose

Quality-control review performed before decline-curve analysis. The raw Equinor workbook is preserved unchanged; cleaning and derived calculations are reproducible in `src/monthly_data_audit.py`.

## Source

- Workbook: `Volve production data.xlsx`
- Monthly sheet: `Monthly Production Data`
- Daily sheet: `Daily Production Data`
- SHA-256: `514d4e38763e09be7fbad12313429909b9799b1a6ec999bf5f36e0df1b6c9cae`

## Dataset Summary

- Clean monthly records: 526
- Wellbores: 7
- Date range: 2007-09-01 to 2016-12-01
- Producer-related wellbores: 6
- Injector-related wellbores: 2

## Verified Source Units

| Variable | Unit |
|---|---|
| On Stream | hrs |
| Oil | Sm3 |
| Gas | Sm3 |
| Water | Sm3 |
| Gas Injection | Sm3 |
| Water Injection | Sm3 |

## Quality-Control Result

| Check | Result |
|---|---:|
| Missing well names | 0 |
| Missing dates | 0 |
| Duplicate well-month records | 0 |
| Negative source values | 0 |
| On-stream records > nominal month by <= 1 h | 4 |
| On-stream records > nominal month by > 1 h | 0 |
| Production with non-positive on-stream time | 0 |
| Injection with non-positive on-stream time | 0 |
| Daily/monthly numeric mismatches | 0 |
| Unexpected daily/monthly missingness differences | 0 |
| Documented zero/null representation differences | 1 |

## Interpretation Notes

- The unit row in the monthly worksheet is metadata, not a well-month observation, and is removed programmatically.
- Monthly oil, gas, water, water-injection, and on-stream values numerically reconcile with independent aggregation of the daily worksheet within floating-point tolerance.
- A small number of on-stream records exceed `24 x calendar days` by no more than one hour. These source values are retained, not corrected, because they reconcile with the daily sheet. The workflow does not impose an unverified timezone correction.
- Zero-versus-null representation differences are documented separately from numerical mismatches so missing data are not silently converted to zero.

## Audit Status

**PASS - data are suitable for the next well-surveillance and DCA-screening stage.**
