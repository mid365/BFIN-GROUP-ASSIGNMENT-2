# Initial Decision Record (Draft, pending team approval)

Date: 2026-10-22
Status: draft for 22 October 2026 checkpoint only; not a final governance-approved recommendation.

## 1) Decision context and mandate

At the case date (31 Dec 2022), Kappa Foundation held USD 12,000,000 in unrestricted cash. The case requires the foundation to fund two fixed nominal commitments and preserve purchasing power for the mission beyond 2030.

- Scholarship programme payment: USD 2,400,000 on 31 Dec 2024
- Learning centre payment: USD 3,600,000 on 31 Dec 2027
- Goal: preserve purchasing power of USD 8,000,000 at 31 Dec 2030, using the case assumption of 2.5% inflation per annum

This record is based strictly on the frozen policy snapshot preserved in `outputs/original/frozen_policy.json` and the project data package. No later mandate changes are assumed or claimed.

## 2) Candidate universe and estimation window

The asset universe and benchmark are those recorded in `config.json` and the frozen policy snapshot:

- Candidate equities: AAPL, MSFT, JPM, JNJ, UNH, XOM, PG, HD, NEE, CAT
- ETFs: SPY, USMV
- Benchmark: SPY
- Estimation window: 2015-01 through 2022-12
- Evaluation window: 2023-01 through 2025-12, used only for out-of-sample checks and not for the initial decision

The project’s raw data provenance is recorded in `data/raw/source_record.json` and the corresponding hash-validated files are in `data/raw/yahoo/` and `data/raw/french/`.

## 3) Initial funding plan and allocation

The original policy snapshot records the following structure:

- Total fund: USD 12,000,000
- Bond sleeve: USD 5,216,894.22 (Beta 2-year zero-coupon: 2,172 units at USD 922.78; Delta 5-year bond: 3,258 units at USD 986.07)
- Growth sleeve: USD 6,533,105.78
- Cash buffer / liquidity reserve: USD 243,466.89
- Rebalancing rule: each December to target weights; trade only if drift exceeds 5 percentage points

The recorded frozen weights and initial allocation are preserved in `outputs/original/T17_initial_allocation.csv` and `outputs/original/frozen_policy.json`.

## 4) Material assumptions and risk policy

This checkpoint uses the assumptions explicitly frozen in the notebook and JSON snapshot:

- Inflation: 2.5% p.a.
- Equity risk premium: 5.0%
- Risk aversion: 4
- Annual 10bp one-way trading cost for stock/ETF trades
- Per-security max weight: 25% in the growth sleeve
- Loss concern: 15% one-year drawdown interpretation
- Bond treatment: fixed contractual cash flows and executable prices from the assignment PDF; no fabricated historical bond price series

These assumptions are documented in the frozen policy snapshot and are the assumption set used for this record. Any change after this date requires explicit revision and comparison against the original policy.

## 5) Evaluation and rebalancing rule

The project records the following policy rule:

- Estimate expected returns, risk, and factor relationships only with data ending 31 Dec 2022.
- Evaluate the market-traded growth allocation over 2023-01 through 2025-12 only.
- Rebalance each December to the frozen target weights; trade only if the drift exceeds 5 percentage points.
- Benchmark: SPY; benchmark and growth sleeve are evaluated under the same cost conventions.

## 6) Approval status and limitations

This draft is a factual reconstruction of the frozen policy and source record. It is not an assertion that board or trustee approval has been obtained. Any decision that requires governance approval should be formally ratified before being treated as final.

The original policy and source record remain preserved for later comparison with any revised mandate.
