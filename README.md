# Kappa Foundation — BFIN WS2026 Group Assignment

Portfolio analysis for the Kappa Foundation case, with a decision date of 31 December 2022. This public repository contains the analysis code, notebooks, validation scripts, and project documentation.

To respect third-party redistribution terms, the repository does not contain the course assignment PDF, downloaded market/factor datasets, processed data, or generated result files. Obtain the assignment brief from the course materials. Download data into your local working copy and generate results by following the instructions below.

## Repository layout

```text
.
├── data/                 # Data dictionary and candidate-eligibility evidence
├── docs/
│   ├── audit/            # Data and factor-regression audit
│   └── decisions/        # Draft decision record and its archived prior draft
├── notebooks/
│   ├── analysis.ipynb    # Canonical analysis notebook
│   └── analysis_audited.ipynb
├── outputs/               # Generated locally by the analysis notebook
├── scripts/               # Offline data and analysis validators
├── src/                   # Data retrieval code
├── config.json
├── requirements.txt
└── requirements-lock.txt
```

`notebooks/analysis_audited.ipynb` is a preserved audited copy with an additional submission-check cell. Use `notebooks/analysis.ipynb` as the canonical notebook; the analysis validator checks that copy.

## Assignment requirements and current status

| Requirement area | Current status |
|---|---|
| USD 12 million allocation, funding of the two commitments, risk/return comparison, and real-value goal | Implemented in the analysis. Risk tolerance and reinvestment/cash assumptions are team-selected and require approval; locally generated funding results show small residuals. |
| Bond valuation, yield and term-structure analysis, duration/convexity, and scenarios | Implemented in the analysis. Non-quoted spot rates are interpolated and surplus cash is assumed to earn 0%; present these as assumptions/scenarios. |
| 8–12 US stocks across at least four sectors and two equity ETFs, with evidence of case-date eligibility | The configured universe has 10 stocks and 2 ETFs, but eligibility is **not fully verified**. The stock evidence is a 28 December 2022 secondary snapshot, not the 31 December case date; dated listing/mandate evidence for SPY and USMV is absent. |
| Investable benchmark and comparison of sample-covariance versus single-index risk estimates | Implemented in the analysis; SPY is the configured benchmark. |
| Market-only and multifactor regression analysis | CAPM, FF3, and FF5 analyses are implemented for the growth portfolio and selected securities. The locally audited results use a 96-month window and have the limitations described in the audit report. |
| Frozen-strategy out-of-sample comparison and quantified reversal threshold | 2023–2025 evaluation and threshold analyses are implemented. This short retrospective period does not establish achievement of the longer-term real-value goal. |
| Reproduction and output traceability | Retrieval code, validators, and notebooks are included. A first run requires internet access to retrieve inputs; after retrieval, data preparation, analysis, and validation run locally. Data and generated outputs are intentionally not tracked in this public repository. |
| Complete course submission package | **Not complete in this repository.** The final committee memo, slide deck and editable source, decision log, contribution statement, and AI-use disclosure still need to be prepared. The decision record is a draft and must not be presented as approved. |

See [the detailed audit and evidence map](docs/audit/DATA_AUDIT_REPORT.md) and [the draft decision record](docs/decisions/Initial_Decision_Record_2026-10-22.md) before relying on the results or treating the policy as approved. The assignment brief is distributed separately through the course.

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

Open `notebooks/analysis.ipynb` in VS Code, select the `.venv` Python kernel, and run all cells. `requirements.txt` lists the direct dependencies without pins; use it only if intentionally resolving a different environment.

## Reproduce and validate

The public repository does not include the third-party data snapshot. On the first setup, from the repository root, retrieve the inputs (internet required):

```powershell
python src\download_data.py
python scripts\validate_data.py
```

After retrieval, the source files are saved locally and the raw-source manifest records their hashes. The data validator rebuilds the processed tables from those saved files. Run the analysis notebook in VS Code or execute it with `nbconvert` as shown below. Once data are present locally, analysis and validation do not require internet access. Then run:

```powershell
python scripts\validate_analysis.py --tag original
```

The analysis validator checks the frozen inputs and generated outputs; it makes no network requests. Result files are written under `outputs/<TAG>/` and are excluded from version control.

For a clean-kernel notebook run from PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$env:TEMP\kappa_execution" | Out-Null
python -m jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 --output-dir "$env:TEMP\kappa_execution" .\notebooks\analysis.ipynb
```

Outputs are written under `outputs/<TAG>/`; the notebook's default tag is `original`. Outputs and the frozen-policy snapshot are generated locally and are not checked into this public repository. To create a separate run, change the notebook's `TAG` and mandate parameters only when an approved revision is intended. Preserve the original policy and compare revised results against the locally generated `outputs/original/`.

## Data handling

- Downloaded inputs and generated results are excluded from this public repository. Check each data provider's terms before using or redistributing data.
- Do not edit files in `data/raw/`. Their source URLs, retrieval details, and SHA-256 hashes are recorded in the locally generated `data/raw/source_record.json`.
- `python src/download_data.py` requires internet access for a first retrieval. It refuses to overwrite any existing raw snapshot; archive the snapshot before starting another retrieval.
- No missing observations are silently interpolated or filled. The validators fail when required source data or generated outputs are missing or inconsistent.
- Yahoo price history establishes trading coverage, not security eligibility or ETF mandate on the case date.
- See [the data dictionary](data/data_dictionary.md) for source descriptions, units, and date conventions.

## Assignment schedule

Check the separately distributed assignment brief and confirm current team deadlines before submitting; the decision record in this repository remains a draft.