# Data and Factor-Regression Audit

## Scope and publication note

This report summarizes checks previously performed against the local working copy of the Kappa Foundation BFIN WS2026 analysis. Paths are relative to the repository root.

The assignment brief, raw Yahoo and Kenneth French source snapshot, processed datasets, source records, and generated analysis outputs are included in this repository. The project owner confirmed permission to redistribute these materials here. The validation record below describes checks performed against this project snapshot; rerun the checks after changing any input or output.

## Requirement coverage and open limitations

| Requirement area | Local analysis status | Evidence generated locally | Limitation |
|---|---|---|---|
| Full USD 12 million allocation, payment funding, quantitative risk/return comparison, and real-value goal | Partial | `T06`, `T09`, `T10`, `T14`, `T17`, `T23`, and `T24` | The 15% loss interpretation and investment assumptions are team-selected, not trustee-approved. The cash residuals after the planned payments are small. |
| Bond valuation, yield, incomplete term structure, duration/convexity, and rate scenarios | Partial | `T03`–`T08` | Non-quoted rates use linear spot-rate interpolation and excess cash earns 0%; these are assumptions, not observed market facts. |
| Candidate stocks and ETFs with case-date eligibility evidence | Partial | `T02`; `data/security_eligibility_evidence.csv` | Dated SEC filings document each stock's common-stock ticker/exchange and business on its filing date. The 28 Dec 2022 S&P snapshot is secondary. The specified SPY prospectus and USMV SEC filing document ticker, exchange, and ETF objective/mandate on their document dates. No source establishes continued listing/eligibility for every security on 31 Dec 2022; all are explicitly marked partial. |
| Investable benchmark and alternative risk estimates | Satisfied in local analysis | SPY benchmark; `T11`–`T13`, `T16`, and `T17` | Expected returns, risk aversion, security caps, and transaction costs are team assumptions. |
| Market-only and multifactor regressions | Satisfied in local analysis | `T18`–`T21` | CAPM, FF3, and FF5 use 96 monthly observations. Alpha estimates are uncertain and do not establish persistent skill. |
| Out-of-sample strategy comparison and quantified reversal threshold | Satisfied in local analysis | `T22`, `T25`, and `T26` | The 2023–2025 market evaluation does not establish achievement of the longer-term real-value goal. |
| Reproduction, data retrieval, and output traceability | Satisfied for the included snapshot | `notebooks/`, `scripts/`, `src/download_data.py`, `data/raw/`, `data/processed/`, and `outputs/original/` | The included snapshot is reproducible offline. Check applicable source terms before redistributing materials outside this project. |
| Complete course submission package | In progress | The 22 October initial decision, dated data record, and decision log are in `docs/decisions/` and `data/`. | The 29 October memo, presentation PDF and editable source, contribution statement, member critiques, and complete AI-use disclosure remain outstanding. |

## Local validation record

The following checks passed during the 22 October review on the local project copy; the verified data and outputs are included in this repository:

- Raw-source hashes, required data columns, monthly dates, units, and common observations.
- Candidate-universe and eligibility-register coverage.
- Official source URLs, document dates through the information cutoff, source-to-`T02` consistency, and explicit partial case-date verification status.
- Allocation reconciliation, long-only limits, payment funding, bond contract inputs, and duration checks.
- Regression windows and monthly evaluation dates.
- Independent bond recalculation recovered all five quoted prices from YTM and the bootstrapped spot curve with maximum price residual below \(4.3\times10^{-10}\); numerical duration/convexity checks and exact repricing under all six rate scenarios passed. Duration-convexity approximation error is reported rather than treated as exact.
- The funded payment schedule leaves only USD 60 after 2024 and USD 150 after 2027. The fixed $12 million allocation and growth weights match the baseline.
- The canonical notebook in `Bài nộp cho 2210/` executed offline from the saved raw data and wrote the evidence refresh to `outputs/eligibility_review_2026-10-22/`.
- The regenerated Python export ran, and the analysis validator passed for the review output tag. It compares policy parameters, holdings, growth weights, rebalancing rule, and initial-dollar allocation with `outputs/original/`.
- Every CSV output except the intentionally refreshed `T02_universe.csv` matches the original generated table values; the policy and allocation checks pass. `outputs/original/` was not written.
- CAPM, FF3, and FF5 outputs contain 96 monthly observations for the growth portfolio and two selected securities; the 2023–2025 comparison contains 36 months and applies the one-rebalance frozen rule (SPY: none). Reversal-threshold calculations are retained in `T26`.
- The updated decision PDF is two pages and retains the required universe, estimation/evaluation windows, benchmark, initial allocation, assumptions, and rebalancing rule.
- The original frozen policy snapshot hash remains `e18c44a0831fb993237fd0f6d618642cb077f4c665c4b6b9c60e7a34791b14e5`.

Re-run these checks from the repository root:

```powershell
python scripts\validate_data.py
python -m jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 --output-dir "$env:TEMP\kappa_execution" ".\Bài nộp cho 2210\analysis.ipynb"
python scripts\validate_analysis.py --tag eligibility_review_2026-10-22
```

The included raw snapshot is sufficient for offline data preparation, notebook execution, and validation. `src/download_data.py` is only for a new online retrieval and refuses to overwrite an existing snapshot. The manifest and validator agree on saved file hashes, identifiers, ranges, settings, and coverage. Yahoo entries lack per-ticker URLs in `data/source_record.csv`; retrieval uses `yfinance.Ticker.history`, but the exact internal request URL was not captured. This is a provenance gap, not a URL to infer.

## Data and methods recorded locally

The local analysis used daily Yahoo Finance history for AAPL, MSFT, JPM, JNJ, UNH, XOM, PG, HD, NEE, CAT, SPY, and USMV, from 2014-12-01 through 2025-12-31. The original retrieval settings were daily bars, `auto_adjust=False`, and `actions=True`. Adjusted closes were used for total-return construction; closes were retained as a price-only comparison.

The local factor input was the Kenneth French monthly five-factor archive. Its `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA`, and `RF` percentage values were converted once to decimal returns. The saved local archive identified a 202608 CRSP vintage. CAPM, FF3, and FF5 regressions used monthly observations from 2015-01 through 2022-12 (96 observations), with 2023-01 through 2025-12 reserved for evaluation. Regressions used HAC standard errors with three lags; monthly alpha was annualized by multiplying by 12, while its t-statistic was not annualized.

Bond prices and terms were fictional assignment-case inputs rather than a historical market series. The model uses contractual cash flows and does not fabricate bond price history.

## Additional findings and limitations

- The funding plan reconciled to USD 12,000,000, but the locally generated cash-flow table showed only USD 60 remaining after the 2024 payment and USD 150 after the 2027 payment under the stated assumptions. These should not be presented as a substantial liquidity cushion.
- The recommended frozen growth strategy triggered one December rebalance in the 2023–2025 evaluation; the SPY benchmark triggered none. The historical backtest is retrospective and is not an unseen live test.
- Case-date eligibility remains partially evidenced for all candidates. SEC filings verify the facts cited on their document dates, but do not establish continued listing on 31 Dec 2022. The S&P constituent snapshot is secondary and dated 28 Dec. Yahoo trading history does not establish eligibility or mandate.
- The refreshed evidence outputs are written to `outputs/eligibility_review_2026-10-22/`; `outputs/original/` remains the frozen baseline. The pre-review initial decision record files are preserved in `docs/decisions/archive/`.
- The source snapshot, processed tables, assignment brief, and generated outputs are included in this repository. A newly retrieved snapshot may have a different vintage; record its provenance and rerun all validations before relying on updated results.
