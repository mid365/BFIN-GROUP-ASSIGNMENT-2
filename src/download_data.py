"""Retrieval code. Run ONCE with internet:  python src/download_data.py
Saves untransformed responses to data/raw/ and a source record (data/raw/source_record.json).
Failures are logged, never filled with invented data."""
import json, hashlib, time, platform, datetime as dt, urllib.request
from pathlib import Path
import pandas as pd, yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
cfg = json.load(open(ROOT / "config.json"))
tickers = cfg["stocks"] + cfg["etfs"]
START, END = cfg["download_start"], cfg["download_end"]   # yfinance end date is exclusive
FRENCH_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FRENCH_FILES = [
    "F-F_Research_Data_5_Factors_2x3_CSV.zip",
]

RAW_TARGETS = [RAW / "yahoo" / f"{ticker}.csv" for ticker in tickers]
RAW_TARGETS += [RAW / "french" / name for name in FRENCH_FILES]
RAW_TARGETS += [RAW / "source_record.json"]
if any(path.exists() for path in RAW_TARGETS):
    raise FileExistsError(
        "Refusing to overwrite saved raw data or its source record. "
        "Archive the existing raw snapshot before starting a new retrieval."
    )

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

record = {"retrieval_utc": dt.datetime.utcnow().isoformat() + "Z",
          "python": platform.python_version(), "yfinance": yf.__version__, "pandas": pd.__version__,
          "tickers": tickers, "entries": [], "failures": []}

for t in tickers:                       # --- Yahoo Finance: daily, dividends/splits kept, NOT auto-adjusted
    for attempt in range(3):
        try:
            df = yf.Ticker(t).history(start=START, end=END, interval="1d", auto_adjust=False, actions=True)
            if df.empty: raise ValueError("empty response")
            f = RAW / "yahoo" / f"{t}.csv"; df.to_csv(f)
            record["entries"].append({"source": "Yahoo Finance via yfinance", "id": t, "start": START, "end": END,
                "interval": "1d", "auto_adjust": False, "actions": True, "file": str(f.relative_to(ROOT)),
                "rows": len(df), "first": str(df.index[0]), "last": str(df.index[-1]), "sha256": sha(f)})
            print("OK", t, len(df)); break
        except Exception as e:
            if attempt == 2: record["failures"].append({"id": t, "error": repr(e)}); print("FAILED", t, e)
            time.sleep(2)

for name in FRENCH_FILES:               # --- Kenneth French Data Library (raw zip saved as-is)
    url = FRENCH_BASE + name
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        f = RAW / "french" / name; f.write_bytes(data)
        record["entries"].append({"source": "Kenneth French Data Library", "id": name, "url": url,
                                  "file": str(f.relative_to(ROOT)), "bytes": len(data), "sha256": sha(f)})
        print("OK", name)
    except Exception as e:
        record["failures"].append({"id": name, "url": url, "error": repr(e)}); print("FAILED", name, e)

json.dump(record, open(RAW / "source_record.json", "w"), indent=2)
print("Failures:", record["failures"] or "none")
