# Kappa Foundation — Dated Data Record

**Prepared:** 22 October 2026  
**For submission:** 22 October 2026  
**Case decision date:** 31 December 2022  
**Scope:** Data, retrieval, transformations, and eligibility evidence supporting the 22 October initial analysis. The frozen policy and outputs remain in `outputs/original/`; the evidence-only refresh is separately tagged.

## Raw downloads and provenance

The original downloaded files are preserved under `data/raw/`. `data/raw/source_record.json` is the file-level manifest: it records retrieval time, dataset/ticker identifiers, requested dates and settings, row counts, coverage, byte count where applicable, and SHA-256 hashes. `data/source_record.csv` is the tabular version. The raw files were not edited after retrieval.

| Source | Saved data and requested settings | Use in this project |
|---|---|---|
| Yahoo Finance, through `yfinance` | Daily history for AAPL, MSFT, JPM, JNJ, UNH, XOM, PG, HD, NEE, CAT, SPY, and USMV; requested 1 December 2014 through 1 January 2026 (exclusive end); `interval="1d"`, `auto_adjust=False`, `actions=True`. Actual saved observations end 31 December 2025. | Month-end total returns from `Adj Close`; price-only returns from `Close`. Dividend and split fields are retained in the raw responses. |
| Kenneth French Data Library | `F-F_Research_Data_5_Factors_2x3_CSV.zip`, saved as received; the exact URL, byte count, and SHA-256 are in the JSON manifest. | Monthly Mkt-RF, SMB, HML, RMW, CMA, and RF. Source percentages are converted once to decimal returns in the processed file. Source missing-value sentinels are treated as missing, not as returns. |

The retrieval script is `src/download_data.py`. It uses the Yahoo Finance history interface through `yfinance` and downloads the French ZIP with Python's standard-library HTTP client. The recorded retrieval environment was Python 3.13.15, `yfinance` 1.7.0, and pandas 3.0.6; the complete pinned environment is in `requirements-lock.txt`. The manifest records no failed downloads.

The Yahoo manifest entries identify Yahoo Finance via `yfinance`, the ticker, requested dates/settings, coverage, and raw-file hash, but do not record a per-ticker Yahoo URL; the `url` cells for those rows in `data/source_record.csv` are blank. `src/download_data.py` calls `Ticker.history`, so the exact underlying Yahoo request endpoint is not recorded. This is a provenance gap; no endpoint has been inferred or backfilled.

## Transformations, dates, and reproducibility

- The frozen estimation sample is January 2015–December 2022, with 96 common monthly observations ending in December 2022.
- January 2023–December 2025 is a separate retrospective evaluation window. It is not used to select the initial portfolio.
- Returns use adjusted closing prices for total-return construction and ordinary closing prices for the separate price-only series. They are aligned to month-end; the two series are retained rather than forced to agree.
- French factor observations are monthly and aligned to the same month as asset returns. Factors and returns are represented as decimal returns in processed files.
- No return observations are interpolated or invented. Validation failures stop the analysis when required observations, columns, hashes, or common dates are absent or malformed.
- Rebuild processed data and validate the frozen analysis offline from the repository root:

  ```powershell
  python scripts\validate_data.py
  python scripts\validate_analysis.py --tag eligibility_review_2026-10-22
  ```

  For a clean-kernel execution of the notebook, see the PowerShell command in `README.md`. Raw retrieval is not needed to reproduce the saved snapshot.

## Information-cutoff and evidence limitations

The estimation window ends at the case decision date, but the underlying Yahoo history and French archive were retrieved on 20 October 2026 (UTC), not preserved as contemporaneous 2022 vintages. Adjusted historical prices can reflect later corporate actions, and French historical factor data can be revised. The saved French archive identifies itself as using the 202608 CRSP database. The initial analysis therefore uses an estimation *date range* ending in 2022; it cannot claim every observation is an unrevised vintage that was available on 31 December 2022.

The 2023–2025 observations are used only for the explicitly retrospective evaluation. This is not an unseen live test. Security selection also has survivorship risk: the candidate list was assembled with knowledge of which securities survived.

`data/security_eligibility_evidence.csv` is the complete machine-readable register. It records each official SEC URL, document date, supported fact, verification status, and limitation; stock rows also link the secondary S&P 500 snapshot dated 28 December 2022.

| Ticker | SEC document date and source | What the cited source establishes |
|---|---|---|
| AAPL | 28 Oct 2022 · [2022 Form 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019322000108/aapl-20220924.htm) | Common-stock ticker AAPL, Nasdaq listing, and issuer business. |
| MSFT | 25 Oct 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/789019/000156459022035087/msft-10q_20220930.htm) | Common-stock ticker MSFT, Nasdaq listing, and issuer business. |
| JPM | 3 Nov 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/19617/000001961722000492/jpm-20220930.htm) | Common-stock ticker JPM, NYSE listing, and issuer business. |
| JNJ | 27 Oct 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/200406/000020040622000086/jnj-20221002.htm) | Common-stock ticker JNJ, NYSE listing, and issuer business. |
| UNH | 2 Nov 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/731766/000073176622000044/unh-20220930.htm) | Common-stock ticker UNH, NYSE listing, and issuer business. |
| XOM | 2 Nov 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/34088/000003408822000064/xom-20220930.htm) | Common-stock ticker XOM, NYSE listing, and issuer business. |
| PG | 19 Oct 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/80424/000008042422000102/pg-20220930.htm) | Common-stock ticker PG, NYSE listing, and issuer business. |
| HD | 22 Nov 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/354950/000035495022000239/hd-20221030.htm) | Common-stock ticker HD, NYSE listing, and issuer business. |
| NEE | 3 Nov 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/753308/000075330822000081/nee-20220930.htm) | Common-stock ticker NEE, NYSE listing, and issuer business. |
| CAT | 2 Nov 2022 · [2022 Form 10-Q](https://www.sec.gov/Archives/edgar/data/18230/000001823022000223/cat-20220930.htm) | Common-stock ticker CAT, NYSE listing, and issuer business. |
| SPY | 28 Jan 2022 · [SEC prospectus](https://www.sec.gov/Archives/edgar/data/884394/000119312522021785/d280704d497.htm) | SPY ticker, NYSE Arca as principal U.S. listing exchange, and an objective of tracking the S&P 500 Index before expenses. |
| USMV | 25 May 2021 · [SEC filing](https://www.sec.gov/Archives/edgar/data/886982/000156459021029583/gs-424b2.htm) | USMV ticker, Cboe BZX listing, 18 Oct 2011 inception, and an objective linked to the MSCI USA Minimum Volatility Index before fees and expenses. |

The ten stock filings and the ETF filings document facts as of their own document dates; they do not prove continued listing/eligibility on 31 December 2022. The secondary stock snapshot is not an official case-date listing record. Consequently, all 12 register rows are marked `partial`, not `verified`. Stock-business descriptions support sector/role context but do not establish an investment mandate. Yahoo trading history establishes price coverage only.

The eligibility-only rerun is saved under `outputs/eligibility_review_2026-10-22/`. The original decision record and PDF as they stood before this evidence review are retained in `docs/decisions/archive/`; the frozen policy and results in `outputs/original/` were not changed.

The fictional bond terms and executable case prices come from Exhibit 1 of `docs/assignment/BFIN-WS2026-Group_Assignment.pdf`. They are case inputs, not historical market quotes. The analysis uses contractual cash flows and explicit scenarios and does not create a historical bond-price series.

## Verification performed for this record

On 22 October 2026, `python scripts\validate_data.py` passed for the saved raw files, hashes, processed monthly returns, and factor data. The notebook executed offline to the separate `eligibility_review_2026-10-22` output tag; the regenerated Python export and `python scripts\validate_analysis.py --tag eligibility_review_2026-10-22` also passed. The validator compares the review policy and initial-dollar allocation with `outputs/original/`. No raw price/factor downloads or files in `outputs/original/` were changed. The individual raw-file hashes and retrieval metadata remain in `data/raw/source_record.json`; rerun these commands if any input or output is changed.
