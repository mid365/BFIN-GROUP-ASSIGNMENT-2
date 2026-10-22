# Kappa Foundation — Initial Decision Record

**Checkpoint:** 22 October 2026 · **Case date:** 31 December 2022 · **Status:** Initial team policy for discussion; not trustee or board approval.

## Decision

Match the two fixed commitments with the case bonds, then invest the remaining fund in the risk-aversion-4 single-index growth portfolio below. The portfolio is designed to fund the stated payments and pursue the real-value goal; neither the return nor the goal is guaranteed.

| Obligation or goal | Amount and date |
|---|---:|
| Scholarship programme | $2,400,000 · 31 Dec 2024 |
| Learning centre | $3,600,000 · 31 Dec 2027 |
| Remaining-fund goal | Preserve the 2022 purchasing power of $8,000,000 · 31 Dec 2030 |

## Initial allocation

| Use of $12 million | Amount | % of fund |
|---|---:|---:|
| Beta 2-year zero-coupon bond (2,172 units) | $2,004,278.16 | 16.70% |
| Delta 5-year, 3.5% coupon bond (3,258 units) | $3,212,616.06 | 26.77% |
| **Total bonds** | **$5,216,894.22** | **43.47%** |
| **Growth portfolio** | **$6,533,105.78** | **54.44%** |
| Net cash reserve | $243,466.89 | 2.03% |
| Initial growth-purchase costs | $6,533.11 | 0.05% |
| **Total** | **$12,000,000.00** | **100.00%** |

### Growth portfolio — target holdings

Weights are percentages of the **growth sleeve**, not of the total fund. Dollar amounts use the initial $6,533,105.78 sleeve and are rounded independently to cents; “fund” shows each position as a share of the full $12 million.

| Holding | Growth weight | Initial dollars | % of fund |
|---|---:|---:|---:|
| MSFT | 0.669% | $43,725.83 | 0.36% |
| JNJ | 15.309% | $1,000,149.57 | 8.33% |
| UNH | 6.003% | $392,170.47 | 3.27% |
| PG | 15.516% | $1,013,672.75 | 8.45% |
| HD | 1.816% | $118,668.62 | 0.99% |
| NEE | 10.687% | $698,165.66 | 5.82% |
| SPY | 25.00% | $1,633,276.45 | 13.61% |
| USMV | 25.00% | $1,633,276.45 | 13.61% |
| **Total growth sleeve** | **100.00%** | **$6,533,105.78** | **54.44%** |

AAPL, JPM, XOM, and CAT have 0% target weights. SPY is the investable US-market benchmark; USMV is the minimum-volatility ETF. Each ETF is at the 25% per-security cap.

## Bond matching to the commitments

Buy Beta at $922.78 per unit and Delta at $986.07 per unit. Beta pays $2,172,000 principal at its 2024 maturity. Delta pays a $114,030 annual coupon on the 3,258 units and $3,258,000 principal at its 2027 maturity. Carry coupons as cash at the assumed 0% return. The 2024 amount also includes the $114,030 Delta coupon received in 2023.

| Year | Bond cash flow | Payment | Closing cash after payment |
|---|---:|---:|---:|
| 2023 | $114,030 | — | $114,030 |
| 2024 | $2,286,030 | $2,400,000 | $60 |
| 2025 | $114,030 | — | $114,090 |
| 2026 | $114,030 | — | $228,120 |
| 2027 | $3,372,030 | $3,600,000 | $150 |

Cash balances include prior coupons and assume no interest on cash. The match is close but not exact; it leaves small positive residuals under these assumptions.

<div class="page-break"></div>

## Portfolio basis and operating rules

**Growth target:** the risk-aversion-4 single-index solution, estimated on monthly data from January 2015 through December 2022 (96 observations). The universe is ten stocks—AAPL, MSFT, JPM, JNJ, UNH, XOM, PG, HD, NEE, CAT—and two ETFs, SPY and USMV. The separately reported January 2023–December 2025 period is an out-of-sample evaluation, not an input to this initial choice.

**Rebalancing:** hold the target weights fixed; each December, rebalance only if any position has drifted by more than 5 percentage points. Apply 10 basis points of one-way trading cost, including to the SPY benchmark. Preserve the original policy and outputs for comparison; any approved revision should be logged rather than overwrite the baseline.

## Assumptions, risk, and limitations

The assignment does not prescribe these policy inputs. The team-selected base case uses 2.5% annual inflation, 5% equity risk premium, risk aversion \(A=4\), a 25% growth-sleeve cap per security, 10 bp one-way trading costs, and 0% cash carry. “Losses approaching 15%” is treated as a one-year 95% total-fund loss diagnostic—not as an optimizer constraint or approved limit.

At \(A=4\), modeled annual growth-portfolio return is 7.59%, volatility 11.57%, and modeled 95% total-fund loss 6.23%. The growth sleeve's historical maximum drawdown is 16.06%; it is a different measure and not a forecast. At 2.5% inflation, the $8 million real-value goal corresponds to about $9.75 million in 2030 and requires approximately 4.80% annual growth on the modeled goal basis. These are model estimates, not promises.

The 2023–2025 retrospective reports 35.45% cumulative return for the proposed growth strategy versus 85.31% for SPY. This short period did not determine the initial weights and does not establish whether the 2030 goal will be met. The case bonds are fictional instruments treated as default-free and held to maturity; unquoted spot rates are linearly interpolated. Eligibility is only partially evidenced: 2022 SEC filings document each stock's common-stock ticker, exchange, and business on its filing date, and a secondary S&P 500 constituent snapshot is dated 28 December 2022. The SEC prospectus dated 28 January 2022 documents SPY's NYSE Arca listing, ticker, and S&P 500 objective; the SEC filing dated 25 May 2021 documents USMV's Cboe BZX listing, ticker, inception date, and minimum-volatility index mandate. These dated sources do not establish continued listing or eligibility on 31 December 2022; the stock snapshot is also not an official case-date listing record. The evidence register records each source and limitation.

**Team confirmation required:** validate security eligibility, approve or revise the stated assumptions and target weights, and record member contributions and critiques. This is an initial team policy, not a final or trustee-approved recommendation.

**Supporting record:** [Dated data record](Dated_Data_Record_2026-10-22.md) · [Decision log](Decision_Log_2026-10-22.md) · Frozen allocation and funding tables: `outputs/original/T17_initial_allocation.csv`, `T06_funding_cashflows.csv`, and `T07_bond_holdings.csv`.
