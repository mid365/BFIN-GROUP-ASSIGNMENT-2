# Initial Decision Record (Draft; pending team approval)

Date: 2026-10-22
Status: Draft for the 22 October 2026 checkpoint only. This is not a board-approved recommendation.

1. Candidate universe, benchmark, and estimation window
- Candidate equities: AAPL, MSFT, JPM, JNJ, UNH, XOM, PG, HD, NEE, CAT.
- ETFs: SPY, USMV.
- Benchmark: SPY.
- Estimation window: 2015-01 through 2022-12.
- Evaluation window: 2023-01 through 2025-12, used only for out-of-sample checks and not to select the initial recommendation.
- Consistency check: same universe and benchmark appear in `config.json`, `outputs/original/frozen_policy.json`, and the analysis notebook. The raw-data provenance is recorded in `data/raw/source_record.json`.
- Eligibility note: case-date eligibility and security selection evidence are not explicitly documented in this record; the raw files and hash records confirm data retrieval, but they do not by themselves certify the 31 Dec 2022 selection rationale.

2. Initial allocation and funding plan
- Total fund: USD 12,000,000.
- Fixed commitments: USD 2,400,000 due 31 Dec 2024; USD 3,600,000 due 31 Dec 2027.
- Goal: preserve purchasing power of USD 8,000,000 at 31 Dec 2030, using the case inflation assumption of 2.5% p.a.
- Initial allocation (from `outputs/original/T17_initial_allocation.csv`):
  - Beta 2-year zero-coupon bond: 2,172 units x USD 922.78 = USD 2,004,278.16.
  - Delta 5-year bond: 3,258 units x USD 986.07 = USD 3,212,616.06.
  - Bond sleeve total = USD 5,216,894.22.
  - Growth sleeve value = USD 6,533,105.78.
  - Cash buffer = USD 243,466.89.
  - Trading costs = USD 6,533.11.
  - Total = USD 5,216,894.22 + USD 6,533,105.78 + USD 243,466.89 + USD 6,533.11 = USD 12,000,000.00.
- No double counting: bond costs, growth-asset values, cash buffer, and trading costs are separate balance-sheet items and sum exactly to the full fund.

3. Material assumptions and initial policy
- Policy assumptions frozen in `outputs/original/frozen_policy.json`: inflation 2.5%; equity risk premium 5.0%; risk aversion 4; annual one-way trading cost 10bp; per-security cap 25% of growth sleeve; loss concern interpreted as a 15% one-year drawdown constraint.
- Bonds are priced at the case-date executable quotes in the assignment PDF and their contractual cash flows are treated as fixed and default-free for this case; no historical bond price series are fabricated.
- The recommendation is a policy decision to fund the commitments and preserve mission purchasing power, not a claim that the foundation has already approved a final portfolio.

4. Evaluation and rebalancing rule
- Initial decision basis: estimate returns and risk only using data that end no later than 31 Dec 2022.
- Evaluation period: 2023-01 through 2025-12; this period is a separate out-of-sample check and is not used to select the initial strategy.
- Rebalancing rule: each December, rebalance to the frozen target weights; trade only if the deviation exceeds 5 percentage points from target. Benchmark is SPY and is treated consistently with the same cost conventions.
- Freeze point: no parameter change after this 22 October 2026 record unless a later revised mandate is explicitly approved and documented.

Team confirmation required before any claim of final approval:
- confirm the final candidate universe and any 31 Dec 2022 eligibility evidence;
- confirm the benchmark and target weights are the official frozen policy;
- confirm the rebalancing rule and cost assumptions;
- confirm whether the draft remains the working record until formal team approval.

This document remains a draft record and does not assert board or trustee approval.
