# Data dictionary

## Scope
This package supports the Kappa Foundation BFIN WS2026 assignment. The data are restricted to the information available no later than 31 December 2022 for the estimation sample, with a separate evaluation period for 2023–2025.

## Raw data sources

### Yahoo Finance (`data/raw/yahoo/*.csv`)
- Source: Yahoo Finance via yfinance
- Tickers: AAPL, MSFT, JPM, JNJ, UNH, XOM, PG, HD, NEE, CAT, SPY, USMV
- Coverage: start `2014-12-01`, end `2026-01-01`
- Interval: daily, `auto_adjust=False`, `actions=True`
- Units: price in USD, volume in shares, split/dividend-adjusted metrics where applicable
- Variable conventions: `Adj Close` is used for total-return construction; `Close` is retained as a price-only comparison series
- Missing-data treatment: no interpolation; missing rows are treated as data integrity failures if they appear in the raw files

### Kenneth French (`data/raw/french/*.zip`)
- Source: Kenneth French Data Library
- File: `F-F_Research_Data_5_Factors_2x3_CSV.zip` (member `F-F_Research_Data_5_Factors_2x3.csv`) for `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA`, `RF`
- Source URLs and SHA-256 hashes are recorded in `data/raw/source_record.json`; retrieval was `2026-10-20T10:51:08.923437Z` UTC.
- The saved archive identifies itself as created using the 202608 CRSP database; monthly coverage is 1963-07–2026-08.
- Definitions: `Mkt-RF` is the market excess return; `SMB` is small minus big; `HML` is high minus low book-to-market; `RMW` is robust minus weak operating profitability; `CMA` is conservative minus aggressive investment; `RF` is the one-month Treasury bill return. For the five-factor construction details, see the [Kenneth French Data Library description](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html). The archive notes that its monthly T-bill series uses Ibbotson data through 2024-05 and the ICE BofA US 1-Month Treasury Bill Index beginning 2024-06.
- Units: source archives report percentages; the notebook converts them once to decimal monthly returns.
- Missing values: French archives encode missing observations as `-99.99`/`-999`, which are not silently filled in the raw data

### Fictional bond data
- Source: assignment PDF, Exhibit 1
- Data are not historical market quotes; they are fictional executable quotes at the decision date
- Bond cash flows are annual on 31 December; settlement is immediately after the 2022 coupon date with zero accrued interest
- Bond IDs: Alpha, Beta, Gamma, Delta, Epsilon

### Security eligibility evidence (`data/security_eligibility_evidence.csv`)
- One row per candidate ticker, with the primary official SEC `source_url`, `document_date`, relevant `relevant_evidence`, `verification_status`, and explicit `limitation`
- Stock rows also include a corroborating secondary S&P 500 constituent `corroborating_source_url` and `corroborating_document_date`
- All candidates currently have `partial` status: the cited documents establish the recorded facts on their document dates, not continued listing/eligibility on 31 December 2022
- The register feeds the refreshed `T02_universe.csv` under `outputs/eligibility_review_2026-10-22/`; the original output remains preserved

## Processed data files

### `data/processed/monthly_returns.csv`
- Rows: one row per asset per month for the total-return and price-only return series
- Columns:
  - `ticker`
  - `date`
  - `monthly_return_total`
  - `monthly_return_price_only`
- Date conventions: month-end dates, aligned to the underlying adjusted-close monthly return

### `data/processed/french_factors.csv`
- Rows: monthly factor observations
- Columns: `date`, `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA`, `RF`
- Units: decimal returns (not percentages)

## Missing-data and integrity handling
- Raw files are never edited after download.
- Hashes are checked against the raw source record.
- Any missing or malformed observations trigger validation failures instead of silent imputation.
- All date alignment, period splitting, and evaluation-window logic is traceable to `config.json` and the raw source record.
