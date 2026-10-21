# Data and Factor-Regression Audit

## Scope and publication note

This report summarizes checks previously performed against the local working copy of the Kappa Foundation BFIN WS2026 analysis. Paths are relative to the repository root.

The assignment brief, raw Yahoo and Kenneth French source snapshot, processed datasets, source records, and generated analysis outputs are included in this repository. The project owner confirmed permission to redistribute these materials here. The validation record below describes checks performed against this project snapshot; rerun the checks after changing any input or output.

## Requirement coverage and open limitations

| Requirement area | Local analysis status | Evidence generated locally | Limitation |
|---|---|---|---|
| Full USD 12 million allocation, payment funding, quantitative risk/return comparison, and real-value goal | Partial | `T06`, `T09`, `T10`, `T14`, `T17`, `T23`, and `T24` | The 15% loss interpretation and investment assumptions are team-selected, not trustee-approved. The cash residuals after the planned payments are small. |
| Bond valuation, yield, incomplete term structure, duration/convexity, and rate scenarios | Partial | `T03`–`T08` | Non-quoted rates use linear spot-rate interpolation and excess cash earns 0%; these are assumptions, not observed market facts. |
| Candidate stocks and ETFs with case-date eligibility evidence | Partial | `T02`; `data/security_eligibility_evidence.csv` | Ten stocks and two ETFs are configured. The cited stock snapshot is dated 28 December 2022 rather than the 31 December case date; dated listing and mandate evidence for SPY and USMV is absent. |
| Investable benchmark and alternative risk estimates | Satisfied in local analysis | SPY benchmark; `T11`–`T13`, `T16`, and `T17` | Expected returns, risk aversion, security caps, and transaction costs are team assumptions. |
| Market-only and multifactor regressions | Satisfied in local analysis | `T18`–`T21` | CAPM, FF3, and FF5 use 96 monthly observations. Alpha estimates are uncertain and do not establish persistent skill. |
| Out-of-sample strategy comparison and quantified reversal threshold | Satisfied in local analysis | `T22`, `T25`, and `T26` | The 2023–2025 market evaluation does not establish achievement of the longer-term real-value goal. |
| Reproduction, data retrieval, and output traceability | Satisfied for the included snapshot | `notebooks/`, `scripts/`, `src/download_data.py`, `data/raw/`, `data/processed/`, and `outputs/original/` | The included snapshot is reproducible offline. Check applicable source terms before redistributing materials outside this project. |
| Complete course submission package | Incomplete | Draft decision record in `docs/decisions/` | The final memo, slides and editable source, decision log, contribution statement, and AI-use disclosure remain outstanding. |

## Local validation record

The following checks passed on the local project copy; the verified data and outputs are included in this repository:

- Raw-source hashes, required data columns, monthly dates, units, and common observations.
- Candidate-universe and eligibility-register coverage.
- Allocation reconciliation, long-only limits, payment funding, bond contract inputs, and duration checks.
- Regression windows and monthly evaluation dates.
- Both notebooks executed from clean kernels; the audited copy's additional submission assertions passed.
- The offline analysis validator passed with the original generated outputs.
- The frozen policy snapshot remained unchanged during notebook runs (SHA-256 `e18c44a0831fb993237fd0f6d618642cb077f4c665c4b6b9c60e7a34791b14e5`).

Re-run these checks from the repository root:

```powershell
python scripts\validate_data.py
python -m jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 --output-dir "$env:TEMP\kappa_execution" .\notebooks\analysis.ipynb
python scripts\validate_analysis.py --tag original
```

The included raw snapshot is sufficient for offline data preparation, notebook execution, and validation. `src/download_data.py` is only for a new online retrieval and refuses to overwrite an existing snapshot.

## Data and methods recorded locally

The local analysis used daily Yahoo Finance history for AAPL, MSFT, JPM, JNJ, UNH, XOM, PG, HD, NEE, CAT, SPY, and USMV, from 2014-12-01 through 2025-12-31. The original retrieval settings were daily bars, `auto_adjust=False`, and `actions=True`. Adjusted closes were used for total-return construction; closes were retained as a price-only comparison.

The local factor input was the Kenneth French monthly five-factor archive. Its `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA`, and `RF` percentage values were converted once to decimal returns. The saved local archive identified a 202608 CRSP vintage. CAPM, FF3, and FF5 regressions used monthly observations from 2015-01 through 2022-12 (96 observations), with 2023-01 through 2025-12 reserved for evaluation. Regressions used HAC standard errors with three lags; monthly alpha was annualized by multiplying by 12, while its t-statistic was not annualized.

Bond prices and terms were fictional assignment-case inputs rather than a historical market series. The model uses contractual cash flows and does not fabricate bond price history.

## Additional findings and limitations

- The funding plan reconciled to USD 12,000,000, but the locally generated cash-flow table showed only USD 60 remaining after the 2024 payment and USD 150 after the 2027 payment under the stated assumptions. These should not be presented as a substantial liquidity cushion.
- The recommended frozen growth strategy triggered one December rebalance in the 2023–2025 evaluation; the SPY benchmark triggered none. The historical backtest is retrospective and is not an unseen live test.
- Case-date eligibility remains unverified for full compliance. Yahoo trading history does not establish security eligibility or ETF mandate.
- The source snapshot, processed tables, assignment brief, and generated outputs are included in this repository. A newly retrieved snapshot may have a different vintage; record its provenance and rerun all validations before relying on updated results.
