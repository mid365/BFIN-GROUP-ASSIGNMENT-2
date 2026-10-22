"""Validate the offline analysis inputs and generated outputs.

Run from the ``kappa`` directory with ``python scripts/validate_analysis.py``.
The script reads saved raw data and generated tables only; it makes no network
requests and does not modify project files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_table(path: Path, *, index_col: int | None = None) -> pd.DataFrame:
    require(path.is_file(), f"Missing required output: {path}")
    return pd.read_csv(path, index_col=index_col)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="original", help="Output directory tag (default: original)")
    args = parser.parse_args()

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    stocks = config["stocks"]
    etfs = config["etfs"]
    tickers = stocks + etfs
    raw = ROOT / "data" / "raw"
    processed = ROOT / "data" / "processed"
    output = ROOT / "outputs" / args.tag

    require(8 <= len(stocks) <= 12, "Candidate universe must contain 8-12 stocks")
    require(len(etfs) == 2, "Candidate universe must contain exactly two ETF candidates")

    manifest_path = raw / "source_record.json"
    require(manifest_path.is_file(), f"Missing raw source record: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(bool(manifest.get("retrieval_utc")), "Source record lacks retrieval timestamp")
    require(bool(manifest.get("python")) and bool(manifest.get("yfinance")) and bool(manifest.get("pandas")),
            "Source record lacks Python/yfinance/pandas versions")
    require(not manifest.get("failures"), f"Raw retrieval failures remain: {manifest['failures']}")

    entries = {entry.get("id"): entry for entry in manifest.get("entries", [])}
    required_raw_ids = set(tickers) | {
        "F-F_Research_Data_5_Factors_2x3_CSV.zip",
    }
    require(required_raw_ids.issubset(entries), "Source record is missing one or more expected data entries")
    for entry_id in required_raw_ids:
        entry = entries[entry_id]
        relative_path = Path(entry["file"].replace("\\", "/"))
        source_path = ROOT / relative_path
        require(source_path.is_file(), f"Missing recorded raw data file: {source_path}")
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        require(digest == entry.get("sha256"), f"Raw source hash mismatch for {entry_id}")
        if entry_id in tickers:
            require(entry.get("start") == config["download_start"] and
                    entry.get("end") == config["download_end"],
                    f"Recorded requested date range is incorrect for {entry_id}")
            require(entry.get("interval") == "1d" and entry.get("auto_adjust") is False and
                    entry.get("actions") is True,
                    f"Recorded Yahoo download settings are incomplete for {entry_id}")
            daily = pd.read_csv(source_path, index_col=0)
            required_daily_columns = {
                "Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits",
            }
            require(required_daily_columns.issubset(daily.columns),
                    f"Raw Yahoo file lacks required price/action columns for {entry_id}")
            daily_dates = pd.DatetimeIndex(pd.to_datetime(daily.index, utc=True))
            require(not daily_dates.has_duplicates and daily_dates.is_monotonic_increasing,
                    f"Raw Yahoo dates are duplicated or unsorted for {entry_id}")
            require(daily_dates.min().date() <= pd.Timestamp(config["download_start"]).date() and
                    daily_dates.max().date() >= pd.Timestamp(config["download_end"]).date() - pd.Timedelta(days=1),
                    f"Raw Yahoo dates do not span the requested range for {entry_id}")
            require(pd.notna(daily[["Close", "Adj Close"]]).all().all() and
                    np.isfinite(daily[["Close", "Adj Close"]].to_numpy()).all(),
                    f"Raw Yahoo prices contain missing or non-finite values for {entry_id}")
            require((daily[["Close", "Adj Close"]].to_numpy() > 0).all(),
                    f"Raw Yahoo prices must be positive for {entry_id}")

    start = pd.Period("2015-01", freq="M")
    estimation_end = pd.Period("2022-12", freq="M")
    evaluation_start = pd.Period("2023-01", freq="M")
    evaluation_end = pd.Period("2025-12", freq="M")
    expected_estimation = pd.period_range(start, estimation_end, freq="M")
    expected_evaluation = pd.period_range(evaluation_start, evaluation_end, freq="M")
    expected_all = expected_estimation.append(expected_evaluation)

    returns = read_table(processed / "monthly_returns.csv")
    return_columns = {
        "ticker", "date", "monthly_return_total", "monthly_return_price_only",
    }
    require(return_columns.issubset(returns.columns), "Processed returns table lacks required columns")
    returns["period"] = pd.PeriodIndex(pd.to_datetime(returns["date"]), freq="M")
    require(not returns.duplicated(["ticker", "period"]).any(), "Processed returns contain duplicate ticker-month rows")
    require(set(returns["ticker"]) == set(tickers), "Processed returns do not match the configured candidate universe")
    require(np.isfinite(returns[["monthly_return_total", "monthly_return_price_only"]].to_numpy()).all(),
            "Processed returns contain missing or non-finite values")
    require((returns[["monthly_return_total", "monthly_return_price_only"]].abs() < 1).all().all(),
            "Processed return units are not decimal returns")

    return_panel = returns.pivot(index="period", columns="ticker", values="monthly_return_total")
    return_panel = return_panel.reindex(columns=tickers).sort_index()
    require(return_panel.columns.tolist() == tickers, "Processed return columns do not follow configured ticker order")
    require(return_panel.index.equals(expected_all), "Processed return dates do not exactly cover Jan 2015-Dec 2025")
    require(return_panel.notna().all().all(), "Processed returns have missing asset-month observations")
    require(len(return_panel.loc[start:estimation_end]) >= 60,
            "Fewer than 60 common monthly estimation observations")

    factors = read_table(processed / "french_factors.csv")
    factor_columns = {"date", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"}
    require(factor_columns.issubset(factors.columns), "Processed French factor table lacks required columns")
    factors["period"] = pd.PeriodIndex(pd.to_datetime(factors["date"]), freq="M")
    require(not factors["period"].duplicated().any(), "Processed factor table contains duplicate months")
    factor_panel = factors.set_index("period").sort_index()
    require(np.isfinite(factor_panel.loc[start:evaluation_end, list(factor_columns - {"date"})].to_numpy()).all(),
            "Estimation/evaluation factors contain missing or non-finite values")
    require((factor_panel.loc[start:evaluation_end, list(factor_columns - {"date"})].abs() < 1).all().all(),
            "Factor units are not decimal returns")
    require(factor_panel.loc[start:estimation_end].index.equals(expected_estimation),
            "Factor observations do not exactly cover the frozen estimation window")
    require(factor_panel.loc[evaluation_start:evaluation_end].index.equals(expected_evaluation),
            "Factor observations do not exactly cover the evaluation window")
    print("PASS: raw source manifest, hashes, required columns, monthly dates, units, and common observations")

    eligibility = read_table(ROOT / "data" / "security_eligibility_evidence.csv")
    evidence_columns = {
        "ticker", "source_url", "document_date", "relevant_evidence",
        "verification_status", "limitation",
    }
    require(evidence_columns.issubset(eligibility.columns), "Eligibility evidence register lacks required fields")
    require(not eligibility["ticker"].duplicated().any(), "Eligibility evidence register has duplicate ticker rows")
    require(set(eligibility["ticker"]) == set(tickers), "Eligibility register does not cover every candidate")
    require(eligibility[list(evidence_columns)].notna().all().all(),
            "Eligibility evidence register contains empty required fields")
    require(eligibility["source_url"].str.startswith("https://www.sec.gov/Archives/").all(),
            "Primary eligibility sources must be official SEC filing URLs")
    evidence_dates = pd.to_datetime(eligibility["document_date"], errors="coerce")
    require(evidence_dates.notna().all() and (evidence_dates <= pd.Timestamp("2022-12-31")).all(),
            "Eligibility evidence has a missing or post-cutoff document date")
    require(eligibility["verification_status"].eq("partial").all(),
            "Do not mark case-date eligibility verified without a source that establishes it")
    require(eligibility["limitation"].str.len().gt(0).all(),
            "Eligibility evidence must state its case-date limitation")
    print("PASS: official dated source and explicit case-date limitations for all candidates")

    universe = read_table(output / "T02_universe.csv", index_col=0)
    require(set(stocks).issubset(universe.index), "Universe output omits one or more stocks")
    require(universe.loc[stocks, "sector"].nunique() >= 4, "Stock candidates span fewer than four sectors")
    require(set(etfs).issubset(universe.index), "Universe output omits one or more ETF candidates")
    if args.tag != "original":
        expected_t02_columns = {
            "eligibility_evidence", "eligibility_source", "eligibility_source_date",
            "eligibility_verification_status", "eligibility_limitation",
            "corroborating_source_url", "corroborating_document_date",
        }
        require(expected_t02_columns.issubset(universe.columns),
                "Refreshed universe output lacks dated eligibility evidence fields")
        evidence_by_ticker = eligibility.set_index("ticker")
        for ticker in tickers:
            require(
                universe.loc[ticker, "eligibility_evidence"] == evidence_by_ticker.loc[ticker, "relevant_evidence"]
                and universe.loc[ticker, "eligibility_source"] == evidence_by_ticker.loc[ticker, "source_url"]
                and universe.loc[ticker, "eligibility_source_date"] == evidence_by_ticker.loc[ticker, "document_date"]
                and universe.loc[ticker, "eligibility_verification_status"]
                == evidence_by_ticker.loc[ticker, "verification_status"]
                and universe.loc[ticker, "eligibility_limitation"] == evidence_by_ticker.loc[ticker, "limitation"],
                f"T02 eligibility evidence does not match the register for {ticker}",
            )

    policy_path = output / "frozen_policy.json"
    require(policy_path.is_file(), f"Missing frozen policy snapshot: {policy_path}")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    params = policy["params"]
    require(params["WIN"] == ["2015-01", "2022-12"], "Frozen estimation window differs from the assignment window")
    require(params["EVAL"] == ["2023-01", "2025-12"], "Frozen evaluation window differs from the assignment window")
    require(params["FUND"] == 12_000_000, "Frozen fund value is not USD 12 million")
    weights = pd.Series(policy["growth_weights"], dtype=float)
    require(weights.index.tolist() == stocks + etfs, "Frozen growth weights do not match the candidate universe")
    require(np.isfinite(weights.to_numpy()).all(), "Frozen growth weights contain non-finite values")
    require(np.isclose(weights.sum(), 1.0, atol=1e-8), "Frozen growth weights do not sum to one")
    require((weights >= -1e-10).all() and (weights <= params["MAX_W"] + 1e-8).all(),
            "Frozen growth weights violate long-only or per-security cap")
    if args.tag != "original":
        baseline = json.loads((ROOT / "outputs" / "original" / "frozen_policy.json").read_text(encoding="utf-8"))
        baseline_params = {key: value for key, value in baseline["params"].items() if key != "TAG"}
        revised_params = {key: value for key, value in params.items() if key != "TAG"}
        require(revised_params == baseline_params, "Review run changed a frozen policy parameter")
        require(policy["bond_units"] == baseline["bond_units"], "Review run changed the bond allocation")
        require(policy["growth_weights"] == baseline["growth_weights"], "Review run changed portfolio weights")
        require(policy["growth_usd"] == baseline["growth_usd"], "Review run changed the growth allocation")
        require(policy["rebalance_rule"] == baseline["rebalance_rule"],
                "Review run changed the rebalancing rule")
        baseline_allocation = read_table(ROOT / "outputs" / "original" / "T17_initial_allocation.csv", index_col=0)
        refreshed_allocation = read_table(output / "T17_initial_allocation.csv", index_col=0)
        require(
            baseline_allocation.shape == refreshed_allocation.shape
            and np.allclose(baseline_allocation.to_numpy(dtype=float),
                            refreshed_allocation.to_numpy(dtype=float), rtol=0, atol=1e-8),
            "Review run changed the original initial-dollar allocation",
        )
    risk_estimate_weights = read_table(output / "T11_weights_si_vs_sample.csv", index_col=0)
    require({"single_index", "sample_cov"}.issubset(risk_estimate_weights.columns),
            "Risk-estimator comparison omits portfolio weights")
    for column in ["single_index", "sample_cov"]:
        candidate_weights = risk_estimate_weights[column]
        require(np.isfinite(candidate_weights.to_numpy()).all(),
                f"{column} portfolio weights contain non-finite values")
        require(np.isclose(candidate_weights.sum(), 1.0, atol=1e-6) and
                (candidate_weights >= -1e-8).all() and
                (candidate_weights <= params["MAX_W"] + 1e-6).all(),
                f"{column} portfolio weights violate fully-invested long-only constraints")

    allocation = read_table(output / "T17_initial_allocation.csv", index_col=0)
    require("usd" in allocation.columns, "Initial allocation output lacks USD amounts")
    require(np.isfinite(allocation["usd"].to_numpy()).all(), "Initial allocation contains non-finite amounts")
    require(abs(allocation["usd"].sum() - params["FUND"]) <= 1.0,
            f"Initial allocation does not reconcile to USD 12 million: {allocation['usd'].sum():.2f}")

    funding = read_table(output / "T06_funding_cashflows.csv", index_col=0)
    funding.index = pd.to_numeric(funding.index, errors="raise").astype(int)
    require({2024, 2027}.issubset(funding.index), "Funding table omits a mandatory payment date")
    require(np.isfinite(funding[["bond_cash_in", "payment", "closing_cash_0pct"]].to_numpy()).all(),
            "Funding cash flows contain non-finite values")
    require((funding["closing_cash_0pct"] >= -1.0).all(), "Funding plan has a negative closing cash balance")
    require(np.isclose(funding.loc[2024, "payment"], 2_400_000), "2024 payment amount is incorrect")
    require(np.isclose(funding.loc[2027, "payment"], 3_600_000), "2027 payment amount is incorrect")
    require(funding.loc[2024, "closing_cash_0pct"] >= -1.0 and
            funding.loc[2027, "closing_cash_0pct"] >= -1.0, "Mandatory payment is not fully funded")

    bond_values = {
        "Alpha": (1, 0.0, 958.77),
        "Beta": (2, 0.0, 922.78),
        "Gamma": (3, 4.0, 1002.49),
        "Delta": (5, 3.5, 986.07),
        "Epsilon": (8, 4.5, 1040.71),
    }
    bond_analytics = read_table(output / "T04_bond_analytics.csv", index_col=0)
    for bond, (maturity, coupon, price) in bond_values.items():
        require(bond in bond_analytics.index, f"Bond analytics omit {bond}")
        row = bond_analytics.loc[bond]
        require(row["maturity"] == maturity and row["coupon_pct"] == coupon,
                f"Contract terms do not match the assignment for {bond}")
        require(np.isclose(row["price"], price), f"Price does not match the assignment for {bond}")
        require(np.isfinite(row[["ytm", "modified", "convexity"]].to_numpy(dtype=float)).all(),
                f"Bond analytics contain non-finite values for {bond}")
        require(np.isclose(row["modified"], row["mod_dur_numeric"], atol=1e-5),
                f"Analytical and numerical modified duration do not reconcile for {bond}")
    repricing = read_table(output / "T05_duration_vs_exact.csv")
    require(np.isfinite(repricing.select_dtypes(include=[np.number]).to_numpy()).all(),
            "Bond repricing comparison contains non-finite values")
    print("PASS: full allocation, long-only constraints, payment funding, and bond analytics")

    regression = read_table(output / "T18_factor_regressions.csv")
    require(len(regression) == 9, "Factor regression output must contain nine required model/asset rows")
    require(set(regression["model"]) == {"CAPM", "FF3", "FF5"}, "Factor regression models are incomplete")
    require(regression["nobs"].eq(96).all(), "Factor regressions do not use 96 estimation observations")
    require(regression["sample_start"].eq("2015-01").all() and
            regression["sample_end"].eq("2022-12").all(),
            "Factor regressions extend outside the frozen estimation window")

    monthly_evaluation = read_table(output / "T25_evaluation_monthly_returns.csv", index_col=0)
    monthly_evaluation.index = pd.PeriodIndex(monthly_evaluation.index, freq="M")
    require(monthly_evaluation.index.equals(expected_evaluation),
            "Monthly strategy evaluation does not exactly cover Jan 2023-Dec 2025")
    require(monthly_evaluation.notna().all().all() and
            np.isfinite(monthly_evaluation.to_numpy()).all(),
            "Monthly strategy evaluation contains missing or non-finite returns")
    required_strategies = {"Recommended (frozen)", "Benchmark SPY"}
    require(required_strategies.issubset(monthly_evaluation.columns),
            "Monthly evaluation output omits the frozen strategy or benchmark")
    evaluation_summary = read_table(output / "T22_evaluation_2023_2025.csv", index_col=0)
    require(required_strategies.issubset(evaluation_summary.index),
            "Evaluation summary omits the frozen strategy or benchmark")
    notebook = json.loads((ROOT / "Bài nộp cho 2210" / "analysis.ipynb").read_text(encoding="utf-8"))
    strategy_cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code" and "def run_strategy(" in "".join(cell.get("source", []))
    ]
    require(len(strategy_cells) == 1, "Could not identify exactly one evaluation strategy implementation")
    strategy_source = strategy_cells[0]
    loop_position = strategy_source.find("for d, row in zip(R.index, R.to_numpy()):")
    current_return_position = strategy_source.find("pos = pos*(1+row)", loop_position)
    rebalance_position = strategy_source.find("if d.month == 12 and drift > drift_limit:", loop_position)
    cost_position = strategy_source.find("cost = tc*np.abs(w*v-pos).sum()", rebalance_position)
    output_position = strategy_source.find("out.append(v/prev-1)", rebalance_position)
    require(-1 not in (
        loop_position, current_return_position, rebalance_position, cost_position, output_position,
    ) and loop_position < current_return_position < rebalance_position < cost_position < output_position,
            "Evaluation rebalancing must use only current and prior returns, after current-month price movement")
    require("shift(-" not in strategy_source and "bfill" not in strategy_source,
            "Evaluation strategy contains a future-looking shift or backward fill")
    thresholds = read_table(output / "T26_reversal_thresholds.csv", index_col=0)
    required_threshold_columns = {
        "base_inflation", "erp_threshold", "base_erp", "inflation_threshold",
        "required_growth_return", "expected_growth_return",
    }
    require(required_threshold_columns.issubset(thresholds.columns),
            "Reversal-threshold output lacks required quantified assumptions")
    threshold = thresholds.iloc[0]
    require(np.isfinite(threshold[list(required_threshold_columns)].to_numpy(dtype=float)).all(),
            "Reversal thresholds contain non-finite values")
    require(threshold["erp_threshold"] < threshold["base_erp"] and
            threshold["inflation_threshold"] > threshold["base_inflation"],
            "Reported threshold directions do not reverse the expected-growth-goal conclusion")
    print("PASS: factor-regression window and matched monthly evaluation dates")

    required_outputs = [
        "T00_source_record.csv", "T01_data_quality.csv", "T02_universe.csv",
        "T03_spot_curve.csv", "T04_bond_analytics.csv", "T05_duration_vs_exact.csv",
        "T06_funding_cashflows.csv", "T07_bond_holdings.csv",
        "T08_rate_scenarios_funding.csv", "T09_goal_requirements.csv",
        "T10_risk_aversion.csv", "T11_weights_si_vs_sample.csv",
        "T12_risk_estimate_comparison.csv", "T13_rejected_alternative.csv",
        "T14_recommended_checks.csv", "T15_risk_contributions.csv",
        "T16_sensitivity.csv", "T17_initial_allocation.csv",
        "T18_factor_regressions.csv", "T19_factor_premia_window.csv",
        "T20_expected_returns_by_model.csv", "T21_oos_alpha_check.csv",
        "T22_evaluation_2023_2025.csv", "T23_goal_probability.csv",
        "T24_real_value_distribution.csv", "T25_evaluation_monthly_returns.csv",
        "T26_reversal_thresholds.csv",
        "F01_weights.png", "F02_evaluation.png",
    ]
    for filename in required_outputs:
        require((output / filename).is_file(), f"Missing required generated output: {output / filename}")
    print(f"PASS: required material outputs are present under outputs/{args.tag}/")
    print("All offline analysis validation checks passed.")


if __name__ == "__main__":
    main()
