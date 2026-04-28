"""
Data Validation Script 
Dark Pattern Detector | Portfolio Project

"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

BASE_DIR   = r"C:\Users\User\Desktop\Dark Pattern Detector"
DATA_DIR   = os.path.join(BASE_DIR, "Data")
OUTPUT_DIR = os.path.join(BASE_DIR, "Outputs")


FILES = {
    "listings_raw":             "listings_raw.csv",
    "dark_patterns_classified": "dark_patterns_classified.csv",
    "platform_summary":         "platform_summary.csv",
    "pattern_type_trend":       "pattern_type_trend.csv",
    "category_heatmap":         "category_heatmap.csv",
}

VALID_PLATFORMS = {"Flipkart", "Meesho", "Nykaa"}
VALID_YEARS     = set(range(2021, 2026))

print("=" * 65)
print("  DARK PATTERN DETECTOR — STEP 1: DATA VALIDATION")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 65)

# ── LOAD ──────────────────────────────────────────────────
dfs = {}
print("\n[1] Loading files...")
for key, fname in FILES.items():
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        print(f"  ❌  {fname} — NOT FOUND in {DATA_DIR}/")
        continue
    dfs[key] = pd.read_csv(path)
    r, c = dfs[key].shape
    print(f"  ✅  {fname:<40} {r:>7,} rows × {c} cols")

# ── NULLS + DUPLICATES ────────────────────────────────────
print("\n[2] Nulls & Duplicates...")
for key, df in dfs.items():
    nulls = df.isnull().sum()
    null_cols = nulls[nulls > 0]
    dups = df.duplicated().sum()
    if null_cols.empty:
        print(f"  ✅  {key}: no nulls | ", end="")
    else:
        for col, cnt in null_cols.items():
            flag = "⚠️ (expected)" if col == "dark_pattern_type" else "❌"
            print(f"  {flag}  {key}.{col}: {cnt:,} nulls ({cnt/len(df)*100:.1f}%) | ", end="")
    print(f"dupes: {'✅ 0' if dups==0 else f'❌ {dups:,}'}")

# ── DOMAIN CHECKS ─────────────────────────────────────────
print("\n[3] Domain checks (listings_raw)...")
df = dfs["listings_raw"]

platforms = set(df["platform"].unique())
print(f"  Platforms:  {sorted(platforms)}  {'✅' if platforms == VALID_PLATFORMS else '❌'}")

years = set(df["year"].unique().tolist())
print(f"  Years:      {sorted(years)}  {'✅' if years == VALID_YEARS else '❌'}")

s = df[df["ccpa_violation"] == "Yes"]["severity_score"]
oor = ((s < 1) | (s > 5)).sum()
print(f"  Severity (violations): range [{s.min()},{s.max()}], mean {s.mean():.2f}  {'✅' if oor==0 else '❌'}")

rate = (df["ccpa_violation"] == "Yes").mean()
print(f"  CCPA violation rate: {rate:.1%} ({(df['ccpa_violation']=='Yes').sum():,} listings)")

# ── CROSS-FILE ────────────────────────────────────────────
print("\n[4] Cross-file consistency...")
cls_rows   = len(dfs["dark_patterns_classified"])
raw_yes    = (df["ccpa_violation"] == "Yes").sum()
match      = cls_rows == raw_yes
print(f"  classified rows ({cls_rows:,}) == raw violation rows ({raw_yes:,}): {'✅' if match else '❌'}")

pt = dfs["pattern_type_trend"]
null_pt = pt["dark_pattern_type"].isnull().sum()
print(f"  pattern_type_trend null rows: {null_pt} (non-violation bucket, drop before EDA)  ✅")

# ── KEY METRICS ───────────────────────────────────────────
print("\n[5] Key metrics (copy to README):")
v = df[df["ccpa_violation"] == "Yes"]
print(f"  Total listings:              {len(df):,}")
print(f"  CCPA violations:             {len(v):,}  ({len(v)/len(df):.1%})")
print(f"  Avg severity (violations):   {v['severity_score'].mean():.2f} / 5")
print(f"  Avg price inflation:         ₹{v['price_inflation_inr'].mean():,.2f}")
print(f"  Total hidden fees:           ₹{df['hidden_fee_inr'].sum():,.0f}")
print(f"  Most common dark pattern:    {df['dark_pattern_type'].value_counts().idxmax()}")

ps = dfs["platform_summary"]
top = ps.groupby("platform")["dark_pattern_rate_pct"].mean().idxmax()
print(f"  Highest avg violation rate:  {top}")


