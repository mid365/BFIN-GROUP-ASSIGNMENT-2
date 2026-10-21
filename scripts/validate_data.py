"""Validate the raw-data package and prepare analysis-ready processed tables.

This script intentionally works offline from saved raw files and fails loudly if the
assignment's data integrity rules are violated.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

with (ROOT / "config.json").open("r", encoding="utf-8") as f:
    cfg = json.load(f)

TICKERS = cfg["stocks"] + cfg["etfs"]
START = cfg["download_start"]
END = cfg["download_end"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


source_record = json.loads((RAW / "source_record.json").read_text(encoding="utf-8"))
assert source_record["failures"] == [], f"Raw download failures: {source_record['failures']}"

# Raw files should exist and match the recorded hashes.
for entry in source_record["entries"]:
    path = ROOT / entry["file"]
    if not path.exists():
        raise FileNotFoundError(f"Missing raw file for entry: {entry['id']} -> {path}")
    actual = sha256(path)
    if actual != entry["sha256"]:
        raise ValueError(f"Hash mismatch for {entry['id']}: expected {entry['sha256']}, got {actual}")

# Yahoo market data validation.
yahoo_dir = RAW / "yahoo"
for ticker in TICKERS:
    path = yahoo_dir / f"{ticker}.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    required = {"Adj Close", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Ticker {ticker} missing columns {sorted(missing)}")
    if df.empty:
        raise ValueError(f"Ticker {ticker} is empty")
    first = pd.Timestamp(df.index.min()).tz_localize(None).normalize()
    last = pd.Timestamp(df.index.max()).tz_localize(None).normalize()
    start_dt = pd.Timestamp(START).tz_localize(None)
    end_dt = pd.Timestamp(END).tz_localize(None)
    if first > start_dt:
        raise ValueError(f"Ticker {ticker} first date {first.date()} is after the requested start {START}")
    if last < end_dt - pd.Timedelta(days=1):
        raise ValueError(f"Ticker {ticker} last date {last.date()} is before the requested end {END}")

# Kenneth French factors validation.
for factor_zip in [
    RAW / "french" / "F-F_Research_Data_5_Factors_2x3_CSV.zip",
]:
    with zipfile.ZipFile(factor_zip) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise ValueError(f"Unexpected factor zip contents: {factor_zip}")
        text = zf.read(names[0]).decode("latin1", errors="replace")
        if "Mkt-RF" not in text:
            raise ValueError(f"Factor file appears malformed: {factor_zip}")

# Build a processed monthly return table from raw daily prices.
month_ret = []
for ticker in TICKERS:
    df = pd.read_csv(RAW / "yahoo" / f"{ticker}.csv", index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(None)
    # Use total return from adjusted close; keep price-only as a visible companion series.
    monthly = pd.DataFrame({"date": df.index.to_period("M").to_timestamp(how="end")})
    # We retain both variables for downstream analysis and traceability.
    series = df["Adj Close"].resample("ME").last()
    price_only = df["Close"].resample("ME").last()
    ret_total = series.pct_change().dropna()
    ret_price = price_only.pct_change().dropna()
    per = pd.DataFrame({
        "ticker": ticker,
        "date": ret_total.index,
        "monthly_return_total": ret_total.values,
        "monthly_return_price_only": ret_price.reindex(ret_total.index).values,
    })
    month_ret.append(per)

returns_df = pd.concat(month_ret, ignore_index=True)
returns_df.to_csv(PROCESSED / "monthly_returns.csv", index=False)

# Build a factor table with monthly frequency.
with zipfile.ZipFile(RAW / "french" / "F-F_Research_Data_5_Factors_2x3_CSV.zip") as zf:
    ff = pd.read_csv(zf.open("F-F_Research_Data_5_Factors_2x3.csv"), skiprows=4, header=0)
ff.columns = [c.strip().strip(",") for c in ff.columns]
ff = ff.rename(columns={ff.columns[0]: "year_month"})
ff = ff.loc[ff["year_month"].astype(str).str.fullmatch(r"\d{6}")].copy()
ff["date"] = pd.to_datetime(ff["year_month"].astype(str), format="%Y%m")
for col in ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]:
    ff[col] = pd.to_numeric(ff[col], errors="coerce") / 100.0
ff = ff[["date", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]]
ff.to_csv(PROCESSED / "french_factors.csv", index=False)

source_record_csv = pd.DataFrame(source_record["entries"])
source_record_csv["verification_status"] = "verified"
source_record_csv.to_csv(ROOT / "data" / "source_record.csv", index=False)

print("PASS: raw data persisted, hashes verified, monthly returns and factor files built.")
print(f"Processed files written to: {PROCESSED}")
