# Kappa Foundation — BFIN WS2026 Group Assignment

Portfolio analysis for the Kappa Foundation case, with a decision date of 31 December 2022. The [current GitHub repository](https://github.com/mid365/BFIN-GROUP-ASSIGNMENT-2) contains the assignment brief, analysis code and notebooks, the project data snapshot, generated results, validators, and documentation. Redistribution permission for the included course and data materials was confirmed by the project owner.

## Repository layout

```text
.
├── data/
│   ├── raw/              # Downloaded Yahoo and Kenneth French source snapshot
│   ├── processed/        # Monthly asset returns and factor data
│   └── *.csv, *.md       # Provenance and data documentation
├── docs/
│   ├── assignment/       # Assignment brief
│   ├── audit/            # Data and factor-regression audit
│   └── decisions/        # Initial decision, decision log, and archived prior draft
├── notebooks/
│   ├── analysis_audited.ipynb
│   └── analysis_explained.ipynb # Code-cell explanations and requirement mapping
├── Bài nộp cho 2210/
│   └── analysis.ipynb           # Canonical analysis and checkpoint deliverables
├── outputs/original/      # Frozen-policy tables, figures, and JSON snapshot
├── outputs/eligibility_review_2026-10-22/ # Same policy, refreshed eligibility evidence
├── scripts/               # Offline data and analysis validators
├── src/                   # Data retrieval code
├── config.json
├── requirements.txt
└── requirements-lock.txt
```

`notebooks/analysis_audited.ipynb` is a preserved audited copy with an additional submission-check cell. Use [`Bài nộp cho 2210/analysis.ipynb`](<Bài nộp cho 2210/analysis.ipynb>) as the canonical notebook; the analysis validator checks that copy.

The canonical analysis explains its assumptions, outputs, and limitations in plain language around its code cells. [`scripts/analysis.py`](scripts/analysis.py) is the runnable Python export of that notebook; regenerate it after notebook code changes with `python -m jupyter nbconvert --to script --output-dir scripts --output analysis "Bài nộp cho 2210\analysis.ipynb"`. [`notebooks/analysis_explained.ipynb`](notebooks/analysis_explained.ipynb) remains available as a navigable, more detailed cell-by-cell guide and explicit assessment against the professor's requirements, including the remaining eligibility and submission gaps.

## Assignment requirements and current status

| Requirement area | Current status |
|---|---|
| USD 12 million allocation, funding of the two commitments, risk/return comparison, and real-value goal | Implemented in the analysis. Risk tolerance and reinvestment/cash assumptions are team-selected and require approval; locally generated funding results show small residuals. |
| Bond valuation, yield and term-structure analysis, duration/convexity, and scenarios | Implemented in the analysis. Non-quoted spot rates are interpolated and surplus cash is assumed to earn 0%; present these as assumptions/scenarios. |
| 8–12 US stocks across at least four sectors and two equity ETFs, with evidence of case-date eligibility | The configured universe has 10 stocks across eight sectors and two ETFs. Dated SEC filings document listing/business facts for all stocks and listing/objective facts for SPY and USMV; the 28 December stock snapshot is secondary. The files do not establish continued case-date eligibility on 31 December 2022, so all status values remain partial. |
| Investable benchmark and comparison of sample-covariance versus single-index risk estimates | Implemented in the analysis; SPY is the configured benchmark. |
| Market-only and multifactor regression analysis | CAPM, FF3, and FF5 analyses are implemented for the growth portfolio and selected securities. The locally audited results use a 96-month window and have the limitations described in the audit report. |
| Frozen-strategy out-of-sample comparison and quantified reversal threshold | 2023–2025 evaluation and threshold analyses are implemented. This short retrospective period does not establish achievement of the longer-term real-value goal. |
| Reproduction and output traceability | Source data, provenance hashes, processed tables, generated outputs, retrieval code, validators, and notebooks are included. Rebuild and validate offline with the commands below. |
| 22 October checkpoint | Initial decision record, dated data record, decision log, working notebook and Python export, retrieval code, package lock, raw data, and reproducible outputs are present. Team confirmation of assumptions and eligibility evidence remains outstanding. |
| 29 October final submission | **Not complete in this repository.** The committee memo, slide deck and editable source, contribution statement, member critiques, and complete AI-use disclosure remain to be prepared and checked by the team. |

The 22 October checkpoint documents are the [initial decision record](docs/decisions/Initial_Decision_Record_2026-10-22.md) ([two-page PDF](docs/decisions/Initial_Decision_Record_2026-10-22.pdf)), [dated data record](docs/decisions/Dated_Data_Record_2026-10-22.md), and [decision log](docs/decisions/Decision_Log_2026-10-22.md). The decision is an initial team policy, not trustee approval. Pre-review decision files are retained in `docs/decisions/archive/`. Record the 23 October revised mandate as a change and compare it with this preserved baseline; do not overwrite `outputs/original/`.

See [the detailed audit and evidence map](docs/audit/DATA_AUDIT_REPORT.md) and [the assignment brief](docs/assignment/BFIN-WS2026-Group_Assignment.pdf) for the full requirements and known limitations.

## Setup

Use Python 3.13 for the pinned environment. In a terminal opened at the repository root:

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

Open `Bài nộp cho 2210/analysis.ipynb` in VS Code, select the `.venv` Python kernel, and run all cells. `requirements.txt` lists the direct dependencies without pins; use it only if intentionally resolving a different environment.

## Reproduce and validate

The raw source snapshot and its provenance record are included. From the repository root, rebuild processed data and verify the raw-file hashes offline:

```powershell
python scripts\validate_data.py
python scripts\validate_analysis.py --tag eligibility_review_2026-10-22
```

The data validator rebuilds `data/processed/` and `data/source_record.csv` from the saved raw files. The analysis validator checks the frozen inputs and generated outputs. Neither validator makes network requests.

For a clean-kernel notebook run from PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$env:TEMP\kappa_execution" | Out-Null
python -m jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 --output-dir "$env:TEMP\kappa_execution" ".\Bài nộp cho 2210\analysis.ipynb"
```

The runnable export can also be executed with the noninteractive plotting backend in PowerShell:

```powershell
$env:MPLBACKEND = "Agg"
python scripts\analysis.py
```

Its eligibility-review tag writes tables and figures under `outputs/eligibility_review_2026-10-22/`. The checked-in frozen run remains `outputs/original/`. This evidence-only refresh changes no policy assumptions or weights; for an approved policy revision, use a new output tag and compare its results with `outputs/original/`.

## Data handling

- The current raw inputs and generated results are included in this repository. Confirm applicable source terms before redistributing them outside this project.
- Do not edit the saved raw price/factor files in `data/raw/`. Their identifiers, retrieval settings, coverage, and SHA-256 hashes are recorded in `data/raw/source_record.json`. The French source URL is recorded; Yahoo entries identify the provider and `yfinance` method but lack per-ticker URLs, as documented in the dated data record.
- `python src/download_data.py` requires internet access and is only for a new retrieval. It refuses to overwrite the included raw snapshot; archive it before starting another retrieval.
- No missing observations are silently interpolated or filled. The validators fail when required source data or generated outputs are missing or inconsistent.
- Yahoo price history establishes trading coverage, not security eligibility or ETF mandate on the case date.
- See [the data dictionary](data/data_dictionary.md) for source descriptions, units, and date conventions.

## Assignment schedule

Check the assignment brief and confirm current team deadlines before submitting; the decision record in this repository remains a draft.