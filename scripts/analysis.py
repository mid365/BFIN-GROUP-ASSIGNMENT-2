#!/usr/bin/env python
# coding: utf-8

# # Kappa Foundation - Investment Policy Analysis
#
# ## Purpose and decision context
#
# This notebook presents our team's initial investment-policy analysis for Kappa Foundation. The case starts with USD 12 million on 31 December 2022, two fixed nominal payments, and a longer-term goal of preserving purchasing power.
#
# We first set aside assets to meet the two payments, then invest the remaining amount in a growth portfolio. We compare risk estimates, review market and factor exposures, and test the frozen policy against SPY over 2023-2025. The code and output files show how we reached each result.
#
# Run the notebook from top to bottom after installing `requirements-lock.txt`. The saved data allow it to run offline. `outputs/original/` remains the frozen baseline. This evidence review writes to `outputs/eligibility_review_2026-10-22/` and does not change the policy or allocation.
#
# The case does not specify several inputs, so we selected values for inflation, ERP, risk aversion, the interpretation of the 15% loss concern, the security cap, cash carry, and trading costs. These are assumptions for the team to justify, not trustee-approved limits. The eligibility register now cites dated SEC filings for all candidates and records the evidence gaps: the sources establish facts on their document dates, not every security's eligibility on 31 December 2022. The notebook does not replace the required committee memo, presentation, decision log, contribution and check statements, team critiques, or AI-use disclosure. `analysis_explained.ipynb` contains the detailed rubric assessment.

# ## Project setup and policy assumptions
#
# This cell loads the project data and analysis libraries, finds the project root, and sets the input and output paths. It also defines the policy assumptions and the helpers used to save tables and figures.
#
# Keeping the assumptions together makes it easier to see which values drive the results. Our base case uses 2.5% inflation, a 5% ERP, risk aversion of 4, a 25% maximum weight per security, and 10 bp one-way trading costs. We interpret the stated 15% loss concern as a one-year 95% loss on the total fund. These are team choices, not values prescribed by the case, and the loss measure is not an approved hard limit.

# In[1]:


import json
from pathlib import Path
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import brentq, minimize, linprog
from scipy.stats import norm
from IPython.display import display

cwd = Path.cwd()
ROOT = next(
    (candidate for base in (cwd, *cwd.parents) for candidate in (base, base / "kappa")
     if (candidate / "config.json").is_file() and (candidate / "data" / "raw").is_dir()),
    None,
)
if ROOT is None:
    raise FileNotFoundError("Could not find config.json and data/raw from the notebook working directory")
RAW = ROOT / "data" / "raw"
with (ROOT / "config.json").open(encoding="utf-8") as f:
    cfg = json.load(f)
STOCKS, ETFS = cfg["stocks"], cfg["etfs"]; ASSETS = STOCKS + ETFS

# ---------------- ALL ASSUMPTIONS (freeze these on 22 Oct) ----------------
P = dict(
    TAG="eligibility_review_2026-10-22",
    FUND=12_000_000, PAY={2: 2_400_000, 5: 3_600_000},      # year -> USD (2024, 2027)
    GOAL_REAL=8_000_000, GOAL_YEARS=8,                       # Dec-2022 purchasing power, at 31 Dec 2030
    INFLATION=0.025,                                         # base CPI assumption (scenarios 2-4% below)
    ERP=0.05,                                                # forward-looking US equity risk premium
    RISK_AVERSION=4,                                         # A in U = mu - 0.5*A*var
    LOSS_LIMIT=0.15,                                         # 1-yr 95% loss diagnostic threshold, as % of TOTAL fund (our interpretation)
    CASH_BUFFER=250_000,                                     # liquidity / trading-cost reserve, earns 0%
    MAX_W=0.25,                                              # per-security cap in growth sleeve
    TC=0.001,                                                # 10 bp one-way on stocks/ETFs
    WIN=("2015-01", "2022-12"),                              # estimation window (96 months)
    EVAL=("2023-01", "2025-12"),                             # evaluation window, never used for decisions
    BENCH="SPY", FACTOR_STOCKS=["AAPL", "XOM"],
)
OUT = ROOT/"outputs"/P["TAG"]; OUT.mkdir(parents=True, exist_ok=True)
def save_table(df, name):
    df.to_csv(OUT/f"{name}.csv"); display(df.round(4)); return df
def save_fig(name):
    plt.tight_layout(); plt.savefig(OUT/f"{name}.png", dpi=150); plt.show()


# Setup does not create output files. The remaining cells use the paths and assumptions defined here.

# ## 1. Data and return construction
#
# Total returns use month-end `Adj Close` from the saved daily Yahoo files, which reflects reinvested dividends. We show price-only returns based on `Close` separately. The factor data are the monthly Kenneth French five-factor file; source percentages are converted to decimals, and `-99.99` is treated as missing. FF3 uses Mkt-RF, SMB, and HML; FF5 also includes RMW and CMA. Returns are aligned with factors for the same month.

# ## Market data, factor data, and sample checks
#
# We read the saved Yahoo CSVs, check their dates and closing prices, and calculate month-end total and price-only returns. We then read the monthly observations in the saved Kenneth French ZIP file, convert factor percentages to decimals, and handle the source's missing-value marker.
#
# The estimation window is fixed at January 2015 through December 2022 (96 months); 2023-2025 is kept separate for evaluation. The cell checks that dates and factor observations line up and stops if required estimation data are missing or non-finite. It writes the sample summary to `T01_data_quality.csv`.
#
# These checks help prevent misaligned data or accidental use of percentages as decimal returns. The files are already saved locally, so this cell runs offline. Price history does not establish whether a security was eligible on the case date.

# In[2]:


import zipfile

def load_px(t):
    d = pd.read_csv(RAW/"yahoo"/f"{t}.csv", index_col=0)
    d.index = pd.to_datetime(d.index, utc=True).tz_convert(None).normalize()
    if d.index.has_duplicates or not d.index.is_monotonic_increasing:
        raise ValueError(f"{t}: daily prices contain duplicate or unsorted dates")
    required = ["Adj Close", "Close"]
    if not set(required).issubset(d.columns) or d[required].isna().any().any():
        raise ValueError(f"{t}: missing required adjusted/close prices")
    return d

raw = {t: load_px(t) for t in ASSETS}
def month_end(px): return px.groupby(px.index.to_period("M")).last()
ret_tr = month_end(pd.DataFrame({t: raw[t]["Adj Close"] for t in ASSETS})).pct_change().iloc[1:]
ret_pr = month_end(pd.DataFrame({t: raw[t]["Close"] for t in ASSETS})).pct_change().iloc[1:]

if ret_tr.index.has_duplicates or not ret_tr.index.is_monotonic_increasing:
    raise ValueError("Monthly return index contains duplicate or unsorted months")
if not np.isfinite(ret_tr.to_numpy()).all() or (ret_tr.abs() >= 1).any().any():
    raise ValueError("Monthly total returns must be finite decimal returns, not percentages")

def read_french(zipname, names):
    with zipfile.ZipFile(RAW/"french"/zipname) as z:
        csv_names = [name for name in z.namelist() if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"{zipname}: expected one CSV member, found {csv_names}")
        lines = z.read(csv_names[0]).decode("latin-1").splitlines()
    rows, started = [], False
    for line in lines:
        p = [x.strip() for x in line.split(",")]
        if len(p[0]) == 6 and p[0].isdigit():
            started = True
            rows.append(p[:len(names)+1])
        elif started:
            break
    if not rows:
        raise ValueError(f"{zipname}: no monthly observations found")
    df = pd.DataFrame(rows, columns=["date"]+names)
    df.index = pd.PeriodIndex(pd.to_datetime(df.pop("date"), format="%Y%m"), freq="M")
    if df.index.has_duplicates or not df.index.is_monotonic_increasing:
        raise ValueError(f"{zipname}: duplicate or unsorted monthly factor dates")
    return df.astype(float).replace([-99.99, -999.0], np.nan) / 100

FF3 = ["Mkt-RF", "SMB", "HML"]
FF5 = FF3 + ["RMW", "CMA"]
FACTOR_COLUMNS = FF5 + ["RF"]
fac = read_french("F-F_Research_Data_5_Factors_2x3_CSV.zip", FACTOR_COLUMNS)
if not set(FACTOR_COLUMNS).issubset(fac.columns):
    raise ValueError(f"Required factor columns are missing: {set(FACTOR_COLUMNS) - set(fac.columns)}")
if fac.index.has_duplicates or not fac.index.is_monotonic_increasing:
    raise ValueError("Factor table contains duplicate or unsorted months")
if not np.isfinite(fac.to_numpy()).all():
    raise ValueError("Required monthly factor series contain missing/non-finite values")
if fac[FACTOR_COLUMNS].abs().to_numpy().max() >= 1 or fac["RF"].abs().max() >= 0.05:
    raise ValueError("Factor values are inconsistent with decimal monthly units")

W0, W1 = P["WIN"]
E0, E1 = P["EVAL"]
if (W0, W1) != ("2015-01", "2022-12"):
    raise ValueError("Estimation window violates the frozen assignment policy")
if (E0, E1) != ("2023-01", "2025-12"):
    raise ValueError("Evaluation window violates the frozen assignment policy")
policy_path = OUT/"frozen_policy.json"
if policy_path.exists():
    saved_policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if tuple(saved_policy.get("estimation_window", ())) != (W0, W1):
        raise ValueError("Configured estimation period differs from saved frozen policy")
    if tuple(saved_policy.get("evaluation_window", ())) != (E0, E1):
        raise ValueError("Configured evaluation period differs from saved frozen policy")

expected_train = pd.period_range(W0, W1, freq="M")
Rw = ret_tr.loc[W0:W1]
Fw = fac.loc[W0:W1]
if not Rw.index.equals(Fw.index):
    raise ValueError("Asset returns and factor months are not exactly aligned")
if not Rw.index.equals(expected_train) or not Fw.index.equals(expected_train):
    raise ValueError("Estimation observations do not exactly match frozen monthly dates")
if len(Rw) != 96 or len(Rw) < 60:
    raise ValueError(f"Frozen estimation sample must contain 96 monthly observations; found {len(Rw)}")
if not np.isfinite(Rw.to_numpy()).all() or not np.isfinite(Fw[FACTOR_COLUMNS].to_numpy()).all():
    raise ValueError("Missing/non-finite return or factor observations in estimation window")

ex = Rw.sub(Fw["RF"], axis=0)
ann_geo = lambda r: (1+r).prod()**(12/len(r)) - 1
dq = pd.DataFrame({"first_price_date": [raw[t].index[0].date() for t in ASSETS],
                   "months_in_window": Rw.count().values,
                   "ann_return_total": [ann_geo(Rw[t]) for t in ASSETS],
                   "ann_return_price_only": [ann_geo(ret_pr.loc[W0:W1, t]) for t in ASSETS]}, index=ASSETS)
save_table(dq, "T01_data_quality")
print("Window:", Rw.index[0], "to", Rw.index[-1], "| n =", len(Rw), "| factors through:", fac.index[-1])


# Check `T01_data_quality.csv` for coverage and compare the total-return and price-only columns. Missing or misaligned estimation data should be resolved before interpreting the results.

# ## Source-file integrity check
#
# This cell recalculates the SHA-256 hash for each file listed in `data/raw/source_record.json`, compares it with the saved hash, and stops if a file does not match. The results are recorded in `T00_source_record.csv`.
#
# A hash mismatch means the input may have changed or been corrupted; investigate it before relying on the analysis.

# In[3]:


import hashlib
rec = json.load(open(RAW/"source_record.json"))
chk = pd.DataFrame(rec["entries"])[["source","id","file","sha256"]]
chk["sha_ok"] = [hashlib.sha256((ROOT/f).read_bytes()).hexdigest() == h for f, h in zip(chk.file, chk.sha256)]
if not chk["sha_ok"].all():
    raise ValueError("Raw source hash verification failed; inspect T00_source_record before analysis")
print("Retrieved (UTC):", rec["retrieval_utc"], "| yfinance", rec["yfinance"], "| pandas", rec["pandas"], "| failed downloads:", rec["failures"] or "none")
save_table(chk.set_index("id"), "T00_source_record")


# In `T00_source_record.csv`, every `sha_ok` value should be true. The printed retrieval record should also show no download failures.

# ## Candidate investment universe
#
# The candidate list contains ten US common stocks across eight sectors, plus SPY (a broad US market ETF and our benchmark) and USMV (a minimum-volatility ETF). The eligibility register cites SEC filings identifying the stocks' common shares, ticker, exchange, and issuer business on filing dates in 2022, with a secondary S&P 500 constituent snapshot dated 28 December 2022. Those records do not establish continued case-date listing or index membership on 31 December. Yahoo price history confirms trading coverage only.
#
# There is also a selection-bias limitation: we chose companies with the benefit of knowing which names survived. We did not select stocks by obvious later-winner or later-loser rules, but that does not remove the bias.

# ## Security roles and eligibility evidence
#
# This cell joins the candidate roles to `data/security_eligibility_evidence.csv` and saves the evidence, source URL, document date, verification status, limitations, and trading coverage to `T02_universe.csv`. The dated SEC evidence documents the stock listings on their filing dates, SPY's ticker/listing/objective in its 28 January 2022 prospectus, and USMV's ticker/listing/inception/index mandate in its 25 May 2021 filing. The evidence register marks case-date eligibility partial because none of these records establishes continued status on 31 December 2022; the stock-list corroboration is secondary and dated 28 December.
#
# The configured universe meets the requested count and sector breadth. The evidence supports the listed facts as of each document date, but no ticker is marked fully verified for 31 December 2022. For the stocks, the business descriptions support sector/role context, not an investment mandate. Trading history is not eligibility evidence.

# In[4]:


roles = {"AAPL":("Info Tech","mega-cap growth"),"MSFT":("Info Tech","mega-cap growth/quality"),"JPM":("Financials","rate/credit-cycle cyclical"),
         "JNJ":("Health Care","defensive"),"UNH":("Health Care","defensive growth"),"XOM":("Energy","commodity/inflation hedge"),
         "PG":("Staples","defensive"),"HD":("Cons. Disc.","cyclical consumer"),"NEE":("Utilities","bond-like/rate sensitive"),
         "CAT":("Industrials","cyclical value"),"SPY":("Broad ETF","cap-weighted US market / benchmark"),"USMV":("Broad ETF","minimum-volatility mandate")}
uni = pd.DataFrame(roles, index=["sector","role"]).T
eligibility = pd.read_csv(ROOT / "data" / "security_eligibility_evidence.csv").set_index("ticker")
if eligibility.index.has_duplicates or set(eligibility.index) != set(ASSETS):
    raise ValueError("Eligibility register must contain exactly one evidence row for every configured ticker")
required_evidence = ["source_url", "document_date", "relevant_evidence", "verification_status", "limitation"]
if eligibility[required_evidence].isna().any().any() or eligibility[required_evidence].eq("").any().any():
    raise ValueError("Eligibility register contains missing source, date, evidence, status, or limitation")
if (pd.to_datetime(eligibility["document_date"]) > pd.Timestamp("2022-12-31")).any():
    raise ValueError("Eligibility evidence includes a document after the 2022-12-31 information cutoff")
uni["eligibility_evidence"] = eligibility["relevant_evidence"].reindex(ASSETS)
uni["eligibility_source"] = eligibility["source_url"].reindex(ASSETS)
uni["eligibility_source_date"] = eligibility["document_date"].reindex(ASSETS)
uni["eligibility_verification_status"] = eligibility["verification_status"].reindex(ASSETS)
uni["eligibility_limitation"] = eligibility["limitation"].reindex(ASSETS)
uni["corroborating_source_url"] = eligibility["corroborating_source_url"].reindex(ASSETS)
uni["corroborating_document_date"] = eligibility["corroborating_document_date"].reindex(ASSETS)
uni["trading_coverage"] = "Yahoo daily prices available over 2015-2022; see T01 and source record"
save_table(uni, "T02_universe")


# Review `T02_universe.csv` and its eligibility columns. Trading coverage should not be treated as proof of eligibility on the case date.

# ## 2. Bond valuation and payment funding
#
# The 1-year and 2-year zero-coupon bonds provide spot rates directly. We bootstrap the 3-, 5-, and 8-year spots from coupon-bond prices, then linearly interpolate rates at unquoted maturities (4, 6, and 7 years). This interpolation is an assumption and affects Delta and Epsilon.
#
# We test parallel shocks of +/-100 bp and +250 bp, as well as steepening and flattening scenarios that move from -50 bp at one year to +50 bp at eight years, or the reverse.

# ## Bond valuation, spot rates, duration, and convexity
#
# Using the five fictional bonds and prices in the case, this cell builds their annual cash flows, calculates yields to maturity, and bootstraps spot rates in maturity order. It marks observed curve points separately from interpolated rates in `T03_spot_curve.csv`. It also calculates duration and convexity, checks them numerically, and compares those estimates with exact repricing under the selected shocks in `T04_bond_analytics.csv` and `T05_duration_vs_exact.csv`.
#
# The case gives bond prices and contractual cash flows, but not a complete spot curve or resale history. We use the quoted prices and make the interpolation visible rather than inventing a historical bond-price series.

# In[5]:


bonds = pd.DataFrame({"mat":[1,2,3,5,8], "cpn":[0,0,4,3.5,4.5], "price":[958.77,922.78,1002.49,986.07,1040.71]},
                     index=["Alpha","Beta","Gamma","Delta","Epsilon"])
def cfs(b):
    t = np.arange(1, int(b["mat"])+1); c = np.full(len(t), b["cpn"]*10.0); c[-1] += 1000; return t, c
def price_ytm(b, y): t, c = cfs(b); return (c/(1+y)**t).sum()
def ytm(b): return brentq(lambda y: price_ytm(b, y)-b["price"], -0.05, 0.5)

# bootstrap spot curve with linear interpolation between knots
spots = {}
for n, b in bonds.iterrows():
    T = int(b["mat"]); t, c = cfs(b); known = sorted(spots)
    def f(s):
        curve_t = np.interp(t, known+[T], [spots[k] for k in known]+[s])
        return (c/(1+curve_t)**t).sum() - b["price"]
    spots[T] = brentq(f, -0.05, 0.5)
yrs = np.arange(1, 9); spot_v = np.interp(yrs, list(spots), list(spots.values()))
curve = lambda t: np.interp(t, yrs, spot_v)
fwd = [spot_v[0]] + [((1+spot_v[i])**(i+1)/(1+spot_v[i-1])**i - 1) for i in range(1, 8)]
save_table(pd.DataFrame({"spot":spot_v, "implied_forward":fwd, "observed": [y in spots for y in yrs]}, index=yrs), "T03_spot_curve")

rows = []
for n, b in bonds.iterrows():
    y = ytm(b); t, c = cfs(b); pv = c/(1+y)**t; p0 = b["price"]
    mac = (t*pv).sum()/p0; mod = mac/(1+y); cx = (t*(t+1)*c/(1+y)**(t+2)).sum()/p0
    d = 1e-4; up, dn = price_ytm(b, y+d), price_ytm(b, y-d)
    rows.append(dict(bond=n, maturity=b["mat"], coupon_pct=b["cpn"], price=p0, ytm=y, current_yield=b["cpn"]*10/p0,
                     spot_at_maturity=spots[int(b["mat"])], macaulay=mac, modified=mod, convexity=cx,
                     mod_dur_numeric=-(up-dn)/(2*p0*d), convexity_numeric=(up+dn-2*p0)/(p0*d*d)))
bt = save_table(pd.DataFrame(rows).set_index("bond"), "T04_bond_analytics")

# duration/convexity approximation vs exact repricing
rows = []
for n, b in bonds.iterrows():
    r = bt.loc[n]; t, c = cfs(b)
    for d in [0.01, -0.01, 0.025]:
        exact_y = price_ytm(b, r["ytm"]+d)/b["price"]-1
        exact_curve = (c/(1+curve(t)+d)**t).sum()/b["price"]-1
        dur = -r["modified"]*d; dc = dur + 0.5*r["convexity"]*d**2
        rows.append(dict(bond=n, shock_bp=d*1e4, duration_only=dur, duration_convexity=dc, exact_yield_reprice=exact_y,
                         exact_spot_curve_reprice=exact_curve, error_dur_conv=dc-exact_y))
save_table(pd.DataFrame(rows).set_index(["bond","shock_bp"]), "T05_duration_vs_exact")


# Review `T03_spot_curve.csv`, `T04_bond_analytics.csv`, and `T05_duration_vs_exact.csv`. The spot-curve file distinguishes quoted points from interpolated ones; the repricing file shows how duration and convexity estimates compare with exact prices.

# ## Funding the commitments with bonds
#
# This cell schedules bond cash flows through year five and maps the 2024 and 2027 payments to their due dates. A non-negative linear program finds the lowest-cost bond purchases that cover the cumulative payments. We round holdings up to whole units, check interim cash balances assuming zero cash carry, and save the funding schedule and holdings in `T06_funding_cashflows.csv` and `T07_bond_holdings.csv`.
#
# We then reprice the selected assets and payment liabilities under the base curve and the parallel and curve-shape scenarios. `T08_rate_scenarios_funding.csv` also reports present value and duration context.
#
# This approach matches contractual cash flows rather than relying on historical bond returns. It assumes default-free case bonds and zero cash carry. We exclude Epsilon because its later cash flows would require a resale-price assumption. The remaining cash balances are small, not a substantial liquidity cushion; scenario sizes and reinvestment assumptions are team choices.

# In[6]:


# ---- funding plan: cheapest set of bonds whose cash flows cover both payments, surplus cash earns 0% (conservative) ----
H = 5; names = ["Alpha","Beta","Gamma","Delta"]       # Epsilon excluded: only 5y of its cash flows usable without a resale-price assumption
cfm = np.zeros((len(names), H))
for i, n in enumerate(names): t, c = cfs(bonds.loc[n]); cfm[i, :len(t)] = c
pay = np.zeros(H)
for yr, a in P["PAY"].items(): pay[yr-1] = a
cum = np.tril(np.ones((H, H)))
res = linprog(c=bonds.loc[names, "price"].values, A_ub=-(cum@cfm.T), b_ub=-(cum@pay), bounds=[(0, None)]*len(names), method="highs")
if not res.success:
    raise RuntimeError(f"Bond cash-flow funding optimization failed: {res.message}")
units = np.ceil(res.x - 1e-9)                          # whole bonds, rounding up keeps feasibility
bond_cost = float((units*bonds.loc[names, "price"].values).sum())
inflow = cfm.T@units
bal = np.cumsum(inflow - pay); assert bal.min() > -1e-6
fund_tbl = pd.DataFrame({"bond_cash_in": inflow, "payment": pay, "closing_cash_0pct": bal}, index=range(2023, 2028))
save_table(fund_tbl, "T06_funding_cashflows")
hold = pd.DataFrame({"units": units, "price": bonds.loc[names, "price"].values}, index=names); hold["cost_usd"] = hold.units*hold.price
save_table(hold, "T07_bond_holdings")

shifts = {"base": lambda t: 0*t, "parallel +100bp": lambda t: 0.01+0*t, "parallel -100bp": lambda t: -0.01+0*t,
          "parallel +250bp": lambda t: 0.025+0*t,
          "steepener (-50bp 1y -> +50bp 8y)": lambda t: -0.005+0.01*(t-1)/7, "flattener (+50bp 1y -> -50bp 8y)": lambda t: 0.005-0.01*(t-1)/7}
def asset_pv(sh): return sum(units[i]*(lambda tc: (tc[1]/(1+curve(tc[0])+sh(tc[0]))**tc[0]).sum())(cfs(bonds.loc[n])) for i, n in enumerate(names))
def liab_pv(sh): return sum(pay[k]/(1+curve(k+1)+sh(k+1))**(k+1) for k in range(H) if pay[k] > 0)
rows = []
for k, sh in shifts.items():
    a, l = asset_pv(sh), liab_pv(sh); rows.append(dict(scenario=k, assets_pv=a, liabilities_pv=l, surplus=a-l))
sc = pd.DataFrame(rows).set_index("scenario"); sc["surplus_change"] = sc.surplus - sc.loc["base","surplus"]
save_table(sc, "T08_rate_scenarios_funding")
tt = np.array([k+1 for k in range(H) if pay[k] > 0]); w_l = np.array([pay[k-1]/(1+curve(k))**k for k in tt])
print("Liability PV (spot curve): %.0f | bond cost (0%% carry): %.0f | surplus cash end-2027: %.0f" % (liab_pv(shifts['base']), bond_cost, bal[-1]))
print("Liability Macaulay duration: %.2f yrs" % ((tt*w_l).sum()/w_l.sum()))
def mac_pv(n):
    t_, c_ = cfs(bonds.loc[n]); pv_ = c_/(1+curve(t_))**t_; return (t_*pv_).sum(), pv_.sum()
print("Matching-bond portfolio Macaulay duration: %.2f yrs" % (sum(units[i]*mac_pv(n)[0] for i, n in enumerate(names))/sum(units[i]*mac_pv(n)[1] for i, n in enumerate(names))))


# Review the payment-date balances in `T06_funding_cashflows.csv` and the holdings in `T07_bond_holdings.csv`. The scenario results are in `T08_rate_scenarios_funding.csv`; note the small cash residuals and the assumptions behind each rate shock.

# ## 3. Growth sleeve and real-value goal
#
# We hold the matching bonds to maturity, so the two payments do not depend on equity-market performance, assuming the case bonds are default-free. The real-value goal is at least USD 8 million at 31 December 2030, after eight years of inflation. Because the case does not give an inflation rate, we use 2.5% in the base case and show 2%-4% scenarios. This is a judgment: inflation at the end of 2022 was much higher.
#
# We interpret ?losses approaching 15%? as a one-year 95% loss of no more than 15% of the total fund. Under the hold-to-maturity assumption, this modeled loss comes from the growth sleeve. We also report the worst historical 12-month loss and maximum drawdown; these are different measures.

# ## Growth allocation and required return
#
# This cell uses the one-year spot rate as the risk-free rate and calculates how much remains for growth after the bond purchases and cash reserve. It estimates the initial trading costs and, for inflation assumptions of 2%, 2.5%, 3%, and 4%, calculates the 2030 nominal amount equivalent to the USD 8 million real goal and the annual return needed to reach it. Results are saved in `T09_goal_requirements.csv`.
#
# This translates the real goal into a nominal hurdle; it is not a return forecast. The inflation assumption and zero cash return are not specified in the case, so the base case needs to be justified.

# In[7]:


rf_ann = spots[1]                                       # 1y zero yield: observed risk-free rate at the decision date
G_total = P["FUND"] - bond_cost - P["CASH_BUFFER"]       # growth sleeve
tc_initial = P["TC"]*G_total
other = P["CASH_BUFFER"] - tc_initial + bal[-1]          # buffer net of costs + leftover bond cash, 0% to 2030
share = G_total/P["FUND"]
def need_growth(infl): return P["GOAL_REAL"]*(1+infl)**P["GOAL_YEARS"] - other
def req_ret(infl): return (need_growth(infl)/G_total)**(1/P["GOAL_YEARS"]) - 1
goal_tbl = pd.DataFrame({"inflation": [0.02,0.025,0.03,0.04]})
goal_tbl["nominal_goal_2030"] = P["GOAL_REAL"]*(1+goal_tbl.inflation)**P["GOAL_YEARS"]
goal_tbl["required_growth_return_pa"] = goal_tbl.inflation.map(req_ret)
save_table(goal_tbl.set_index("inflation"), "T09_goal_requirements")
print("Growth sleeve: %.0f (%.1f%% of fund) | risk-free (1y zero): %.2f%% | required growth return at base inflation: %.2f%%" %
      (G_total, share*100, rf_ann*100, req_ret(P["INFLATION"])*100))


# Use `T09_goal_requirements.csv` to compare the required return under each inflation assumption. These figures are hurdles, not predicted or guaranteed returns.

# ## 4. Growth-portfolio decision
#
# We estimate expected returns using CAPM: the one-year spot rate plus each security's beta multiplied by a 5% ERP. The ERP is our forward-looking assumption, not a return forecast supplied by the case. We show historical means only in the alternative allocation because they are noisy estimates.
#
# The optimizer maximizes mean-variance utility for a long-only, fully invested portfolio, with a cap on each security's weight. We compare sample-covariance risk estimates with a single-index model using the French Mkt-RF series. Risk aversion of 4, the 25% cap, and 10 bp one-way trading costs are team judgments. The frozen policy rebalances when any target weight drifts by more than 5 percentage points.

# ## Expected returns, risk models, and portfolio weights
#
# This cell estimates each security's beta and alpha from monthly excess returns against Mkt-RF, then builds annualized single-index and sample covariance matrices. Expected returns use the one-year spot rate plus beta times the assumed ERP. The optimizer checks that its long-only weights sum to one and respect the per-security cap.
#
# It saves risk-aversion sensitivity in `T10`, compares the two risk models in `T11` and `T12`, and records a historical-Sharpe alternative using the full and most recent 60-month samples in `T13`. `F01_weights.png` plots the allocations.
#
# The comparison shows how the estimates and assumptions affect the proposed weights. The historical-Sharpe portfolio is an alternative, not our frozen decision rule, and a solver's result is not by itself a recommendation.

# In[8]:


mkt = Fw["Mkt-RF"]
beta = ex.apply(lambda s: s.cov(mkt)/mkt.var())
alpha_i = ex.mean() - beta*mkt.mean()
resid = ex - pd.DataFrame(np.outer(mkt, beta), index=ex.index, columns=ex.columns) - alpha_i
S_si = pd.DataFrame(np.outer(beta, beta)*mkt.var() + np.diag(resid.var()), index=ASSETS, columns=ASSETS)*12
S_sa = ex.cov()*12
mu = rf_ann + beta*P["ERP"]

def mv_opt(mu, S, A, maxw):
    n = len(mu); m = mu.values; Sv = S.values
    if n * maxw < 1:
        raise ValueError(f"Infeasible per-security cap {maxw} for {n} assets")
    r = minimize(lambda w: -(w@m - 0.5*A*w@Sv@w), np.ones(n)/n, jac=lambda w: -(m - A*Sv@w), bounds=[(0, maxw)]*n,
                 constraints=[{"type":"eq","fun":lambda w: w.sum()-1,"jac":lambda w: np.ones(n)}], method="SLSQP")
    if not r.success:
        raise RuntimeError(f"Mean-variance optimization failed: {r.message}")
    if not np.isclose(r.x.sum(), 1.0) or np.any(r.x < -1e-8) or np.any(r.x > maxw + 1e-8):
        raise RuntimeError("Mean-variance optimizer returned weights outside the mandate constraints")
    return pd.Series(r.x, index=mu.index)
def stats_p(w, S, mu):
    m = float(w@mu); s = float(np.sqrt(w@S@w)); return dict(exp_return=m, vol=s, loss95_fund=-(m-1.645*s)*share)
effN = lambda w: 1/(w**2).sum()

# (a) effect of risk aversion
rows = []
for A in [1, 2, 4, 6, 8, 12]:
    w = mv_opt(mu, S_si, A, P["MAX_W"]); rows.append(dict(A=A, **stats_p(w, S_si, mu), eff_N=effN(w), **{f"w_{t}": w[t] for t in ASSETS}))
save_table(pd.DataFrame(rows).set_index("A"), "T10_risk_aversion")

# (b) recommended: single-index risk, chosen A; same universe under sample covariance for comparison
A = P["RISK_AVERSION"]
w_rec = mv_opt(mu, S_si, A, P["MAX_W"]); w_sa = mv_opt(mu, S_sa, A, P["MAX_W"])
cmp_ = pd.DataFrame({"single_index": w_rec, "sample_cov": w_sa}); cmp_["diff"] = cmp_.single_index - cmp_.sample_cov
save_table(cmp_, "T11_weights_si_vs_sample")
cross = pd.DataFrame({"w_single_index": stats_p(w_rec, S_si, mu) | {"vol_under_sample": float(np.sqrt(w_rec@S_sa@w_rec))},
                      "w_sample_cov": stats_p(w_sa, S_sa, mu) | {"vol_under_sample": float(np.sqrt(w_sa@S_sa@w_sa))}})
cross.loc["vol_under_single_index"] = [float(np.sqrt(w_rec@S_si@w_rec)), float(np.sqrt(w_sa@S_si@w_sa))]
cross.loc["turnover_si_vs_sample"] = [0.5*(w_rec-w_sa).abs().sum()]*2
save_table(cross, "T12_risk_estimate_comparison")
cmp_[["single_index","sample_cov"]].plot.bar(figsize=(9,3.5), title="Growth sleeve weights: single-index vs sample covariance"); save_fig("F01_weights")

# (c) rejected alternative: Eta - highest historical Sharpe, sample covariance, long-only
def max_sharpe(exm):
    mu_h = exm.mean().values*12; Sh = exm.cov().values*12; n = len(mu_h)
    r = minimize(lambda w: -(w@mu_h)/np.sqrt(w@Sh@w), np.ones(n)/n, bounds=[(0,1)]*n,
                 constraints=[{"type":"eq","fun":lambda w: w.sum()-1}], method="SLSQP")
    if not r.success:
        raise RuntimeError(f"Historical Sharpe optimization failed: {r.message}")
    return pd.Series(r.x, index=exm.columns)
w_alt = max_sharpe(ex); w_alt60 = max_sharpe(ex.iloc[-60:])
alt = pd.DataFrame({"eta_full_window": w_alt, "eta_last60m": w_alt60, "recommended": w_rec})
alt.loc["effective_N"] = [effN(w_alt), effN(w_alt60), effN(w_rec)]
alt.loc["instability (half-L1 full vs 60m)"] = [0.5*(w_alt-w_alt60).abs().sum(), np.nan, np.nan]
save_table(alt, "T13_rejected_alternative")
print("Rejected alt under common inputs:", stats_p(w_alt, S_si, mu), "| hist Sharpe:", float((w_alt@ex.mean()*12)/np.sqrt(w_alt@S_sa@w_alt)))


# Review `T10_risk_aversion.csv` through `T13_rejected_alternative.csv` and `F01_weights.png`. Compare the weights, concentration, risk estimates, and how the historical-Sharpe allocation changes across samples; do not rely on the optimizer output alone.

# ## Risk checks, sensitivity, and dollar allocation
#
# This cell reports the worst rolling 12-month sleeve return, historical drawdown, the sleeve's share of total-fund loss, and a model-based one-year 95% loss estimate in `T14`. It calculates component risk contributions and betas (`T15`), tests alternative ERP and security-cap assumptions (`T16`), and lays out the bond, growth, cash, and cost amounts (`T17`). A final check confirms that the dollar amounts add up to USD 12 million.
#
# The 15% loss figure is a diagnostic comparison, not an optimizer constraint. The modeled 95% loss assumes normally distributed returns; historical losses and drawdowns are different measures. Being below the selected threshold does not prove that the portfolio is safe or that trustees approved it. Sensitivity analysis shows the effects of changing assumptions, not that our chosen values are objectively correct.

# In[9]:


# risk contributions, historical sleeve risk, trade-off checks
rp = Rw@w_rec; wealth = (1+rp).cumprod()
hist = pd.Series({"worst_12m_sleeve": ((1+rp).rolling(12).apply(np.prod, raw=True)-1).min(),
                  "max_drawdown_sleeve": (wealth/wealth.cummax()-1).min(),
                  "worst_12m_on_total_fund": ((1+rp).rolling(12).apply(np.prod, raw=True)-1).min()*share,
                  "model_loss95_on_total_fund": stats_p(w_rec, S_si, mu)["loss95_fund"],
                  "expected_return_sleeve": stats_p(w_rec, S_si, mu)["exp_return"],
                  "required_return_base_inflation": req_ret(P["INFLATION"])})
save_table(hist.to_frame("value"), "T14_recommended_checks")
print("Loss diagnostic below threshold:", hist["model_loss95_on_total_fund"] <= P["LOSS_LIMIT"], "| expected return >= required:", hist["expected_return_sleeve"] >= hist["required_return_base_inflation"])
rc = w_rec*(S_si@w_rec)/(w_rec@S_si@w_rec)
save_table(pd.DataFrame({"weight": w_rec, "risk_contribution": rc, "beta": beta}), "T15_risk_contributions")

# sensitivity: ERP and cap
rows = {}
for e in [0.03, 0.04, 0.05, 0.06, 0.07]: rows[f"ERP={e:.0%}"] = mv_opt(rf_ann+beta*e, S_si, A, P["MAX_W"])
for cap in [0.15, 0.35, 1.0]: rows[f"cap={cap:.0%}"] = mv_opt(mu, S_si, A, cap)
save_table(pd.DataFrame(rows), "T16_sensitivity")

# initial dollar allocation (full USD 12m)
alloc = pd.concat([hold["cost_usd"].rename("usd"), (w_rec*G_total).rename("usd")])
alloc.loc["Cash buffer"] = P["CASH_BUFFER"] - tc_initial; alloc.loc["Trading costs (growth buy)"] = tc_initial
alloc = alloc.to_frame(); alloc["pct_of_fund"] = alloc.usd/P["FUND"]
assert abs(alloc.usd.sum() - P["FUND"]) < 1, alloc.usd.sum()
save_table(alloc, "T17_initial_allocation")


# Check `T14_recommended_checks.csv` through `T17_initial_allocation.csv`. Confirm that the allocation totals USD 12 million, and distinguish the loss diagnostic from a binding limit.

# ## 5. Market and factor exposures
#
# We compare CAPM (Mkt-RF), FF3 (Mkt-RF, SMB, HML), and FF5 (Mkt-RF, SMB, HML, RMW, CMA) for the growth portfolio and selected securities. HAC standard errors use three lags. Alpha is the monthly intercept multiplied by 12; its t-statistic is based on the unannualized monthly estimate.
#
# For our growth portfolio, the FF3 market beta is 0.715 (t=17.45), SMB beta is -0.335 (t=-6.50), and HML beta is 0.012 (t=0.29). Under FF5, RMW is 0.272 (t=3.58) and CMA is 0.296 (t=4.06). Annualized alpha falls from 5.02% under CAPM to 4.18% under FF3 and 2.34% under FF5; the FF5 t-statistic is 1.58. The estimate is uncertain, so we do not use it as evidence of persistent skill. AAPL has positive market exposure and negative HML exposure; XOM has positive HML exposure. These are historical associations, not causal effects. Expected returns remain CAPM-based; the factor regressions describe exposures rather than forecast persistent alpha.

# ## CAPM, FF3, and FF5 regressions
#
# This cell checks the factor specifications, then fits each model to the growth portfolio and two selected stocks over the same 96-month estimation window. It uses OLS with three-lag HAC standard errors, subtracts RF once from total returns, and saves coefficients, alphas, t-statistics, fit statistics, and model details in `T18_factor_regressions.csv`. It also reports estimation-window factor premia (`T19`), compares model-based expected returns (`T20`), and tests FF5 residual alpha over the separate 2023-2025 period (`T21`).
#
# The results show whether the return explanation changes across models and make uncertainty around alpha visible. The sample is only 96 months, and the chosen factor-file vintage and factor premia matter. An estimated alpha is not proof of persistent skill.

# In[10]:


models = {"CAPM": ["Mkt-RF"], "FF3": FF3, "FF5": FF5}
expected_models = {
    "CAPM": ("Mkt-RF",),
    "FF3": ("Mkt-RF", "SMB", "HML"),
    "FF5": ("Mkt-RF", "SMB", "HML", "RMW", "CMA"),
}
if {name: tuple(cols) for name, cols in models.items()} != expected_models:
    raise ValueError("Factor regression specifications do not match CAPM, FF3, and FF5")
expected_regression_index = pd.period_range(W0, W1, freq="M")
def run_reg(y, cols):
    if not Fw.index.equals(expected_regression_index) or not y.index.equals(expected_regression_index):
        raise ValueError("Regression dates must exactly match the frozen 96-month 2015-01 to 2022-12 estimation window")
    if len(y) != 96:
        raise ValueError(f"Frozen factor regression requires 96 monthly observations; found {len(y)}")
    if not set(cols).issubset(Fw.columns):
        raise ValueError(f"Regression is missing required factors: {set(cols) - set(Fw.columns)}")
    if not np.isfinite(y.to_numpy()).all() or not np.isfinite(Fw[cols].to_numpy()).all():
        raise ValueError("Regression contains missing or non-finite return/factor observations")
    r = sm.OLS(y, sm.add_constant(Fw[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    row = {"alpha_ann": r.params["const"]*12, "alpha_t": r.tvalues["const"],
           "R2": r.rsquared, "adjR2": r.rsquared_adj, "nobs": int(r.nobs),
           "sample_start": str(y.index.min()), "sample_end": str(y.index.max()),
           "frequency": "monthly", "factor_columns": ", ".join(cols)}
    for c in cols:
        row[f"b_{c}"] = r.params[c]
        row[f"t_{c}"] = r.tvalues[c]
    return row, r
if not np.isclose(w_rec.sum(), 1.0, atol=1e-10):
    raise ValueError("Frozen growth sleeve must be fully invested before subtracting RF once")
ex_g = (Rw@w_rec) - Fw["RF"]
items = {"Growth portfolio": ex_g, **{s: ex[s] for s in P["FACTOR_STOCKS"]}}
rows, fits = [], {}
for nm, y in items.items():
    for mn, cols in models.items():
        row, r = run_reg(y, cols)
        fits[(nm, mn)] = r
        rows.append(dict(asset=nm, model=mn, **row))
save_table(pd.DataFrame(rows).set_index(["asset", "model"]), "T18_factor_regressions")

prem = pd.DataFrame({"premium_ann": Fw[FF5].mean()*12, "t_stat": Fw[FF5].mean()/(Fw[FF5].std()/np.sqrt(len(Fw)))})
save_table(prem, "T19_factor_premia_window")
rows = []
for nm in items:
    r3 = fits[(nm, "FF3")]
    r5 = fits[(nm, "FF5")]
    capm = fits[(nm, "CAPM")]
    rows.append(dict(asset=nm, capm_exp_ret=rf_ann+capm.params["Mkt-RF"]*P["ERP"],
                     ff3_exp_ret_hist_premia=rf_ann+sum(r3.params[c]*prem.loc[c, "premium_ann"] for c in FF3),
                     ff5_exp_ret_hist_premia=rf_ann+sum(r5.params[c]*prem.loc[c, "premium_ann"] for c in FF5),
                     ff3_exp_ret_mkt_at_ERP=rf_ann+r3.params["Mkt-RF"]*P["ERP"],
                     ff5_exp_ret_mkt_at_ERP=rf_ann+r5.params["Mkt-RF"]*P["ERP"]))
save_table(pd.DataFrame(rows).set_index("asset"), "T20_expected_returns_by_model")

# Evaluation observations are reserved for this post-estimation check, not model or strategy selection.
ev = ret_tr.loc[E0:E1]
Fe = fac.loc[E0:E1]
idx = ev.index.intersection(Fe.index)
expected_eval = pd.period_range(E0, E1, freq="M")
if not idx.equals(expected_eval) or not ev.index.equals(expected_eval) or not Fe.index.equals(expected_eval):
    raise ValueError("Evaluation returns and factors must exactly match the frozen 2023-01 to 2025-12 window")
rows = []
for nm in items:
    y = ((ev.loc[idx]@w_rec) if nm == "Growth portfolio" else ev.loc[idx, nm]) - Fe.loc[idx, "RF"]
    r = fits[(nm, "FF5")]
    fitted = sum(r.params[c]*Fe.loc[idx, c] for c in FF5)
    e = y - fitted
    if not np.isfinite(e.to_numpy()).all():
        raise ValueError(f"Non-finite out-of-sample regression residuals for {nm}")
    oos_fit = sm.OLS(e, np.ones((len(e), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    rows.append(dict(asset=nm, months=len(idx), oos_alpha_ann=e.mean()*12,
                     t_stat_hac=float(np.asarray(oos_fit.tvalues).reshape(-1)[0]), t_stat_method="HAC, 3 lags",
                     in_sample_alpha_ann=r.params["const"]*12))
save_table(pd.DataFrame(rows).set_index("asset"), "T21_oos_alpha_check")


# Review `T18_factor_regressions.csv` through `T21_oos_alpha_check.csv`. Interpret the factor loadings alongside their HAC uncertainty; do not treat estimated alpha as persistent skill.

# ## 6. Out-of-sample comparison: 2023-2025
#
# The growth-portfolio weights are frozen at 31 December 2022. At each December month-end, the portfolio rebalances only if any weight has drifted by more than 5 percentage points. We charge 10 bp on one-way turnover, including the initial purchase, and apply the same costs to SPY. None of the later-period data are used in the initial decision. `T22` records the number of rebalances.

# ## Frozen portfolio and benchmark evaluation
#
# This cell checks the 36 monthly observations from 2023-2025 and applies the frozen strategy, including initial and rebalance costs. It evaluates our proposed portfolio, SPY, the historical-Sharpe alternative, and the sample-covariance portfolio. The comparison reports cumulative and annualized return, volatility, Sharpe ratio, drawdown, and worst 12-month return. Results and monthly returns are saved in `T22` and `T25`, with a value chart in `F02_evaluation.png`.
#
# Using a period separate from the initial estimation helps us test the frozen policy without changing it based on later returns. This is a retrospective three-year comparison, not evidence that the eight-year goal will be met. The rebalance trigger and cost rate are assumptions and should agree with the dated decision record.

# In[11]:


Re = ret_tr.loc[E0:E1, ASSETS]
if Re.isna().any().any() or not np.isfinite(Re.to_numpy()).all():
    raise ValueError("Evaluation return panel contains missing or non-finite observations")
REBALANCE_DRIFT = 0.05
def run_strategy(w, R, tc, drift_limit=REBALANCE_DRIFT):
    w = w.reindex(R.columns).fillna(0).to_numpy(dtype=float)
    if not np.isclose(w.sum(), 1.0, atol=1e-10) or np.any(w < -1e-10):
        raise ValueError("Backtest strategy weights must be nonnegative and sum to one")
    if not 0 <= tc < 1 or not 0 <= drift_limit < 1:
        raise ValueError("Transaction cost or rebalance drift threshold is outside its valid range")
    pos = w*(1-tc); prev = 1.0; out = []; rebalance_count = 0
    for d, row in zip(R.index, R.to_numpy()):
        pos = pos*(1+row); v = pos.sum()
        if v <= 0 or not np.isfinite(v):
            raise ValueError(f"Invalid portfolio value during evaluation at {d}")
        drift = np.max(np.abs(pos/v-w))
        if d.month == 12 and drift > drift_limit:
            cost = tc*np.abs(w*v-pos).sum()
            v -= cost
            pos = w*v
            rebalance_count += 1
        out.append(v/prev-1); prev = v
    return pd.Series(out, index=R.index), rebalance_count
def perf(r, rf):
    n = len(r); cum = (1+r).prod()-1; vol = r.std()*np.sqrt(12); e = (r-rf.reindex(r.index)).dropna(); wl = (1+r).cumprod()
    return dict(cumulative=cum, ann_return=(1+cum)**(12/n)-1, ann_vol=vol, sharpe=e.mean()*12/vol,
                max_drawdown=(wl/wl.cummax()-1).min(), worst_12m=((1+r).rolling(12).apply(np.prod, raw=True)-1).min())
bench_w = pd.Series({P["BENCH"]: 1.0})
strats = {"Recommended (frozen)": w_rec, "Benchmark SPY": bench_w, "Rejected: Eta max-Sharpe": w_alt, "Sample-cov MV": w_sa}
strategy_results = {k: run_strategy(w, Re, P["TC"]) for k, w in strats.items()}
rets = {k: result[0] for k, result in strategy_results.items()}
tab = pd.DataFrame({k: perf(r, fac["RF"]) for k, r in rets.items()}).T
act = rets["Recommended (frozen)"] - rets["Benchmark SPY"]
tab["tracking_error_vs_bench"] = [np.nan if k == "Benchmark SPY" else (rets[k]-rets["Benchmark SPY"]).std()*np.sqrt(12) for k in tab.index]
tab["active_return_ann_vs_bench"] = [np.nan if k == "Benchmark SPY" else (rets[k]-rets["Benchmark SPY"]).mean()*12 for k in tab.index]
tab["rebalance_count"] = [strategy_results[k][1] for k in tab.index]
save_table(tab, "T22_evaluation_2023_2025")
evaluation_returns = pd.DataFrame(rets, index=Re.index)
evaluation_returns.index.name = "date"
if not evaluation_returns.index.equals(pd.period_range(E0, E1, freq="M")):
    raise ValueError("Monthly evaluation outputs do not match the frozen 2023-01 to 2025-12 window")
save_table(evaluation_returns, "T25_evaluation_monthly_returns")
pd.DataFrame({k: (1+r).cumprod() for k, r in rets.items()}).set_index(Re.index.to_timestamp()).plot(figsize=(9,4), title="Growth value of $1, 2023-2025 (frozen strategies)")
save_fig("F02_evaluation")
print("Worst 12m of recommended sleeve x share of fund:", tab.loc["Recommended (frozen)","worst_12m"]*share)
print("Rebalance rule:", f"December only when max absolute weight drift > {REBALANCE_DRIFT:.0%}")
print("NOTE: 3 years of results do not show that the 8-year goal is achieved.")


# Review `T22_evaluation_2023_2025.csv`, `T25_evaluation_monthly_returns.csv`, and `F02_evaluation.png`. Discuss the portfolio's performance relative to SPY alongside its risk statistics.

# ## 7. Conditions that could change the conclusion
#
# We test two thresholds: the ERP below which expected growth return falls short of the required return, and the inflation rate above which the goal is out of reach in expectation. Goal probabilities use a lognormal approximation for the growth sleeve with constant weights; they ignore costs and rebalancing, so they are planning scenarios rather than guarantees or a full transaction-cost simulation.
#
# Under the base assumptions, the probability in `T23` is below 75%, and the 25th-percentile real value in `T24` is below the USD 8 million goal. These thresholds affect the growth-goal conclusion, not the bond-funded payment plan.

# ## Reversal thresholds and goal scenarios
#
# This cell solves for the ERP and inflation assumptions at which expected growth return crosses the required return, saving the thresholds in `T26_reversal_thresholds.csv`. It also uses a lognormal approximation to estimate goal probabilities across ERP and inflation scenarios (`T23_goal_probability.csv`) and percentiles of real fund value (`T24_real_value_distribution.csv`).
#
# The thresholds show where the model's conclusion changes; they do not predict what will happen. The probabilities depend on the return and inflation assumptions and the lognormal approximation, so they should be read as scenarios, not precise forecasts.

# In[12]:


beta_p = float(w_rec@beta); sig_p = float(np.sqrt(w_rec@S_si@w_rec)); T = P["GOAL_YEARS"]
erp_star = (req_ret(P["INFLATION"]) - rf_ann)/beta_p
infl_star = brentq(lambda i: req_ret(i) - (rf_ann + beta_p*P["ERP"]), 0.0, 0.25)
print("Threshold ERP (at base inflation): %.2f%% | threshold inflation (at base ERP): %.2f%%" % (erp_star*100, infl_star*100))
thresholds = pd.DataFrame([{"base_inflation": P["INFLATION"], "erp_threshold": erp_star, "base_erp": P["ERP"], "inflation_threshold": infl_star, "required_growth_return": req_ret(P["INFLATION"]), "expected_growth_return": rf_ann + beta_p*P["ERP"]}], index=["expected-growth-goal crossover"])
save_table(thresholds, "T26_reversal_thresholds")
def logn(mu_p):
    s2 = np.log(1+sig_p**2/(1+mu_p)**2); return np.log(1+mu_p) - s2/2, s2
def p_goal(erp, infl):
    mL, s2 = logn(rf_ann + beta_p*erp)
    return 1 - norm.cdf((np.log(need_growth(infl)/G_total) - mL*T)/np.sqrt(s2*T))
grid = pd.DataFrame({f"infl={i:.1%}": [p_goal(e, i) for e in [0.03,0.04,0.05,0.06]] for i in [0.02,0.025,0.03,0.04]},
                    index=[f"ERP={e:.0%}" for e in [0.03,0.04,0.05,0.06]])
save_table(grid, "T23_goal_probability")
mL, s2 = logn(rf_ann + beta_p*P["ERP"]); q = lambda z: G_total*np.exp(mL*T + z*np.sqrt(s2*T))
real = lambda g: (g + other)/(1+P["INFLATION"])**T
pct = pd.DataFrame({"real_fund_value_dec2022_usd": [real(q(norm.ppf(p))) for p in [0.10, 0.25, 0.50]]}, index=["P10","P25","P50"])
save_table(pct, "T24_real_value_distribution")
print("Real goal supported with ~75%% probability: USD %.2fm (vs 8.00m target)" % (real(q(norm.ppf(0.25)))/1e6))


# Use `T23_goal_probability.csv`, `T24_real_value_distribution.csv`, and `T26_reversal_thresholds.csv` to review the goal scenarios. Interpret probabilities and thresholds only in light of their assumptions.

# ## 8. Policy record and monitoring
#
# The dated decision record should track payment funding, interest-rate and curve changes against the scenarios, growth-sleeve drawdowns, inflation against the 2.5% base case, ERP and valuations, factor exposures, and the December rebalancing trigger (a drift of more than 5 percentage points).
#
# The 2.5% inflation assumption, 5% ERP, risk aversion of 4, 15% loss interpretation, 25% security cap, and 10 bp trading cost are team judgments. The case does not prescribe them.

# ## Save the policy snapshot and run final checks
#
# This cell saves the selected assumptions, bond holdings, growth weights, dollar allocation, benchmark, estimation and evaluation windows, and rebalance rule to `frozen_policy.json`. It will not replace an existing snapshot with different values; use a new output tag for a revised policy.
#
# The final checks review the data hashes, regression coverage and specifications, HAC reporting, rebalance counts, and portfolio weights. They help catch inconsistencies but do not replace the separate decision log. Other tables and figures are written before this final check, so preserve the original output folder when testing a revision.

# In[13]:


frozen = {"params": {k: (v if not isinstance(v, dict) else {str(a): b for a, b in v.items()}) for k, v in P.items()},
          "bond_units": hold["units"].to_dict(), "growth_weights": w_rec.round(6).to_dict(), "growth_usd": float(G_total),
          "cash_buffer_net": float(P["CASH_BUFFER"]-tc_initial), "rebalance_rule": "each December to frozen weights; trade if drift > 5pp",
          "benchmark": P["BENCH"], "estimation_window": list(P["WIN"]), "evaluation_window": list(P["EVAL"])}
policy_path = OUT/"frozen_policy.json"
frozen = json.loads(json.dumps(frozen, default=float))
if policy_path.exists():
    saved_policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if saved_policy != frozen:
        raise ValueError(f"Refusing to overwrite frozen policy at {policy_path}; set TAG to a new revision and compare against outputs/original")
else:
    policy_path.write_text(json.dumps(frozen, indent=2), encoding="utf-8")
print(sorted(p.name for p in OUT.iterdir()))
source = json.loads((RAW/"source_record.json").read_text(encoding="utf-8"))
if source["failures"]:
    raise ValueError(f"Raw source retrieval failures remain: {source['failures']}")
if not chk["sha_ok"].all():
    raise ValueError("Raw source hashes do not all match the recorded source manifest")
reg = pd.read_csv(OUT/"T18_factor_regressions.csv")
expected_factor_sets = {"CAPM": "Mkt-RF", "FF3": "Mkt-RF, SMB, HML", "FF5": "Mkt-RF, SMB, HML, RMW, CMA"}
if set(reg["model"]) != set(expected_factor_sets) or len(reg) != 9:
    raise ValueError("Regression output must contain CAPM, FF3, and FF5 for all three assets")
for model, factors in expected_factor_sets.items():
    subset = reg.loc[reg["model"] == model]
    if len(subset) != 3 or not subset["factor_columns"].eq(factors).all():
        raise ValueError(f"Incorrect {model} regression rows or factor columns")
if not reg["nobs"].eq(96).all() or not reg["sample_start"].eq("2015-01").all() or not reg["sample_end"].eq("2022-12").all() or not reg["frequency"].eq("monthly").all():
    raise ValueError("Regression output violates the frozen monthly estimation window")
oos = pd.read_csv(OUT/"T21_oos_alpha_check.csv")
if not {"t_stat_hac", "t_stat_method"}.issubset(oos.columns) or not oos["t_stat_method"].eq("HAC, 3 lags").all():
    raise ValueError("Out-of-sample alpha inference must report unannualized HAC t-statistics")
backtest = pd.read_csv(OUT/"T22_evaluation_2023_2025.csv", index_col=0)
if "rebalance_count" not in backtest.columns or backtest.loc["Recommended (frozen)", "rebalance_count"] != 1 or backtest.loc["Benchmark SPY", "rebalance_count"] != 0:
    raise ValueError("Evaluation output does not reflect the December-only 5pp drift-trigger rule")
if not np.isclose(sum(frozen["growth_weights"].values()), 1.0, atol=1e-5):
    raise ValueError("Frozen initial growth allocation does not sum to one")
print("Final audit validations passed: provenance, frozen monthly window, CAPM/FF3/FF5, HAC evaluation, rebalance trigger, and unchanged allocation.")


# The final message and `frozen_policy.json` show which internal checks passed. Passing does not establish full assignment compliance or mean the team has approved the policy.
