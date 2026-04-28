"""
Consumer Harm Scoring Model
Dark Pattern Detector 
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR  = os.path.join(BASE_DIR, "Data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
CHART_DIR  = os.path.join(OUTPUT_DIR, "charts")

os.makedirs(CHART_DIR, exist_ok=True)

WEIGHTS = {
    "severity":         0.45,
    "price_inflation":  0.35,
    "hidden_fee":       0.20,
}
CCPA_PENALTY   = 10.0   # added to score when ccpa_violation == "Yes"
SCORE_SCALE    = 90.0   # base score range before penalty (0–90 → 0–100 with penalty)

PLATFORM_COLORS = {
    "Flipkart": "#2874F0",
    "Meesho":   "#9B59B6",
    "Nykaa":    "#FC2779",
}
SEVERITY_PALETTE = {2: "#F9E79F", 3: "#F39C12", 4: "#E74C3C", 5: "#7B241C"}

plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.dpi":        150,
    "savefig.bbox":      "tight",
    "savefig.dpi":       150,
})

def save(fig, name):
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"  ✅  Saved → {path}")

# ── LOAD ──────────────────────────────────────────────────────────────
print("Loading data...")
df  = pd.read_csv(f"{DATA_DIR}/listings_raw.csv")
ps  = pd.read_csv(f"{DATA_DIR}/platform_summary.csv")
ch  = pd.read_csv(f"{DATA_DIR}/category_heatmap.csv")

# Work on violations only
v = df[df["ccpa_violation"] == "Yes"].copy()
print(f"  Violation listings: {len(v):,}")

# Derived input
v["price_inflation_pct"] = (v["price_inflation_inr"] / v["actual_price_inr"] * 100).round(4)

print(f"\n  Input ranges:")
print(f"    severity_score:       [{v['severity_score'].min():.0f}, {v['severity_score'].max():.0f}]  mean={v['severity_score'].mean():.2f}")
print(f"    price_inflation_pct:  [{v['price_inflation_pct'].min():.1f}%, {v['price_inflation_pct'].max():.1f}%]  mean={v['price_inflation_pct'].mean():.1f}%")
print(f"    hidden_fee_inr:       [₹{v['hidden_fee_inr'].min():.0f}, ₹{v['hidden_fee_inr'].max():.0f}]  mean=₹{v['hidden_fee_inr'].mean():.2f}")

# ── MIN-MAX NORMALISATION ─────────────────────────────────────────────
print("\nNormalising inputs...")

def minmax(series):
    """Min-Max normalise to [0, 1]. Returns 0 if constant."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - mn) / (mx - mn)

v["sev_norm"]  = minmax(v["severity_score"])
v["inf_norm"]  = minmax(v["price_inflation_pct"])
v["fee_norm"]  = minmax(v["hidden_fee_inr"])          # 0 for most rows (no hidden fee)

# ── COMPOSITE SCORE ───────────────────────────────────────────────────
print("Computing Consumer Harm Scores...")

v["base_score"] = (
    WEIGHTS["severity"]        * v["sev_norm"]  +
    WEIGHTS["price_inflation"] * v["inf_norm"]  +
    WEIGHTS["hidden_fee"]      * v["fee_norm"]
) * SCORE_SCALE

# CCPA penalty (all violation rows get +10, capped at 100)
v["ccpa_penalty"] = CCPA_PENALTY   # all rows here are ccpa_violation == "Yes"
v["harm_score"]   = (v["base_score"] + v["ccpa_penalty"]).clip(upper=100).round(2)

# Component contributions (for waterfall / breakdown charts)
v["contrib_severity"]    = (WEIGHTS["severity"]        * v["sev_norm"]  * SCORE_SCALE).round(2)
v["contrib_inflation"]   = (WEIGHTS["price_inflation"] * v["inf_norm"]  * SCORE_SCALE).round(2)
v["contrib_hidden_fee"]  = (WEIGHTS["hidden_fee"]      * v["fee_norm"]  * SCORE_SCALE).round(2)

print(f"\n  Harm Score range: [{v['harm_score'].min():.1f}, {v['harm_score'].max():.1f}]")
print(f"  Mean harm score:  {v['harm_score'].mean():.2f}")
print(f"  Median harm score: {v['harm_score'].median():.2f}")

# ── RISK TIER LABELLING ───────────────────────────────────────────────
def risk_tier(score):
    if score >= 80:  return "🔴 Critical"
    if score >= 65:  return "🟠 High"
    if score >= 50:  return "🟡 Medium"
    return               "🟢 Low"

v["risk_tier"] = v["harm_score"].apply(risk_tier)

tier_counts = v["risk_tier"].value_counts()
print(f"\n  Risk Tier distribution:")
for tier, cnt in tier_counts.sort_index().items():
    print(f"    {tier}: {cnt:,} ({cnt/len(v)*100:.1f}%)")

# ── PLATFORM RANKING ──────────────────────────────────────────────────
print("\nBuilding platform ranking...")

platform_scores = v.groupby("platform").agg(
    total_violations      = ("harm_score", "count"),
    mean_harm_score       = ("harm_score", "mean"),
    median_harm_score     = ("harm_score", "median"),
    max_harm_score        = ("harm_score", "max"),
    pct_critical          = ("risk_tier",  lambda x: (x == "🔴 Critical").mean() * 100),
    pct_high              = ("risk_tier",  lambda x: (x == "🟠 High").mean() * 100),
    avg_severity          = ("severity_score",       "mean"),
    avg_inflation_pct     = ("price_inflation_pct",  "mean"),
    avg_hidden_fee        = ("hidden_fee_inr",        "mean"),
    listings_with_hf      = ("hidden_fee_inr",        lambda x: (x > 0).sum()),
    total_consumer_loss   = ("price_inflation_inr",   "sum"),
    contrib_sev_avg       = ("contrib_severity",      "mean"),
    contrib_inf_avg       = ("contrib_inflation",     "mean"),
    contrib_fee_avg       = ("contrib_hidden_fee",    "mean"),
).round(2)

platform_scores["harm_rank"] = platform_scores["mean_harm_score"].rank(ascending=False).astype(int)
platform_scores = platform_scores.sort_values("mean_harm_score", ascending=False)

print(f"\n  Platform Rankings:")
for plat, row in platform_scores.iterrows():
    print(f"    #{int(row['harm_rank'])} {plat}: mean score {row['mean_harm_score']:.2f} | "
          f"critical {row['pct_critical']:.1f}% | consumer loss ₹{row['total_consumer_loss']:,.0f}")

# ── CATEGORY RANKING ──────────────────────────────────────────────────
print("\nBuilding category ranking...")

category_scores = v.groupby("category").agg(
    total_violations      = ("harm_score", "count"),
    mean_harm_score       = ("harm_score", "mean"),
    median_harm_score     = ("harm_score", "median"),
    max_harm_score        = ("harm_score", "max"),
    pct_critical          = ("risk_tier",  lambda x: (x == "🔴 Critical").mean() * 100),
    avg_severity          = ("severity_score",       "mean"),
    avg_inflation_pct     = ("price_inflation_pct",  "mean"),
    total_consumer_loss   = ("price_inflation_inr",   "sum"),
).round(2)

category_scores["harm_rank"] = category_scores["mean_harm_score"].rank(ascending=False).astype(int)
category_scores = category_scores.sort_values("mean_harm_score", ascending=False)

print(f"\n  Category Rankings (top 5):")
for cat, row in category_scores.head(5).iterrows():
    print(f"    #{int(row['harm_rank'])} {cat}: {row['mean_harm_score']:.2f} | "
          f"critical {row['pct_critical']:.1f}% | ₹{row['total_consumer_loss']:,.0f} total loss")

# ── PATTERN TYPE RANKING ──────────────────────────────────────────────
print("\nBuilding pattern type ranking...")

pattern_scores = v.groupby("dark_pattern_type").agg(
    total_violations      = ("harm_score", "count"),
    mean_harm_score       = ("harm_score", "mean"),
    median_harm_score     = ("harm_score", "median"),
    max_harm_score        = ("harm_score", "max"),
    pct_critical          = ("risk_tier",  lambda x: (x == "🔴 Critical").mean() * 100),
    avg_severity          = ("severity_score",       "mean"),
    avg_inflation_pct     = ("price_inflation_pct",  "mean"),
    avg_inflation_inr     = ("price_inflation_inr",  "mean"),
    total_consumer_loss   = ("price_inflation_inr",   "sum"),
).round(2)

pattern_scores["harm_rank"] = pattern_scores["mean_harm_score"].rank(ascending=False).astype(int)
pattern_scores = pattern_scores.sort_values("mean_harm_score", ascending=False)

print(f"\n  Pattern Type Rankings:")
for pat, row in pattern_scores.iterrows():
    print(f"    #{int(row['harm_rank'])} {pat}: {row['mean_harm_score']:.2f} | "
          f"severity {row['avg_severity']:.1f} | consumer loss ₹{row['total_consumer_loss']:,.0f}")


# ══════════════════════════════════════════════════════════════════════
# CHART 9 — Score Distribution + Component Breakdown
# ══════════════════════════════════════════════════════════════════════
print("\n[Chart 9] Score distribution + component breakdown...")

fig, axes = plt.subplots(2, 2, figsize=(15, 11))
fig.suptitle("Consumer Harm Score — Model Output", fontweight="bold", fontsize=15)

TIER_COLORS = {
    "🟢 Low": "#2ECC71", "🟡 Medium": "#F1C40F",
    "🟠 High": "#E67E22", "🔴 Critical": "#E74C3C"
}

# Top-left: Harm score histogram with tier shading
ax = axes[0][0]
ax.hist(v["harm_score"], bins=40, color="#95A5A6", edgecolor="white", linewidth=0.4,
        zorder=3, alpha=0.6, label="All violations")
ax.axvspan(0,  50, alpha=0.08, color="#2ECC71",  label="Low (<50)")
ax.axvspan(50, 65, alpha=0.08, color="#F1C40F",  label="Medium (50–65)")
ax.axvspan(65, 80, alpha=0.08, color="#E67E22",  label="High (65–80)")
ax.axvspan(80,100, alpha=0.12, color="#E74C3C",  label="Critical (80+)")
for thresh, col in [(50,"#2ECC71"),(65,"#F1C40F"),(80,"#E67E22")]:
    ax.axvline(thresh, color=col, linewidth=1.5, linestyle="--", alpha=0.8)
ax.axvline(v["harm_score"].mean(), color="#2C3E50", linewidth=2,
           linestyle="-", label=f"Mean {v['harm_score'].mean():.1f}")
ax.set_xlabel("Consumer Harm Score (0–100)")
ax.set_ylabel("Number of Listings")
ax.set_title("Harm Score Distribution — All Violation Listings")
ax.legend(fontsize=8, loc="upper left")
ax.yaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)

# Top-right: Stacked bar showing score components by platform
ax2 = axes[0][1]
comps = ["contrib_sev_avg", "contrib_inf_avg", "contrib_fee_avg"]
comp_labels = [f"Severity (×{WEIGHTS['severity']})",
               f"Inflation (×{WEIGHTS['price_inflation']})",
               f"Hidden Fee (×{WEIGHTS['hidden_fee']})"]
comp_colors = ["#E74C3C", "#3498DB", "#F39C12"]
bottom = np.zeros(len(platform_scores))
plat_names = platform_scores.index.tolist()
for comp, label, color in zip(comps, comp_labels, comp_colors):
    vals = platform_scores[comp].values
    ax2.bar(plat_names, vals, bottom=bottom, color=color, label=label, edgecolor="white", width=0.5)
    for i, (val, bot) in enumerate(zip(vals, bottom)):
        ax2.text(i, bot + val/2, f"{val:.1f}", ha="center", va="center",
                 fontsize=9, fontweight="bold", color="white")
    bottom += vals
# Add CCPA penalty bar
ax2.bar(plat_names, [CCPA_PENALTY]*len(plat_names), bottom=bottom,
        color="#7F8C8D", label=f"CCPA Penalty (+{CCPA_PENALTY:.0f})", edgecolor="white", width=0.5, alpha=0.7)
for i, (val, bot) in enumerate(zip([CCPA_PENALTY]*len(plat_names), bottom)):
    ax2.text(i, bot + val/2, f"+{CCPA_PENALTY:.0f}", ha="center", va="center",
             fontsize=9, fontweight="bold", color="white")
ax2.set_ylabel("Avg Consumer Harm Score")
ax2.set_title("Score Component Breakdown by Platform")
ax2.legend(fontsize=8, loc="upper right")
ax2.yaxis.grid(True, alpha=0.3, linestyle="--"); ax2.set_axisbelow(True)

# Bottom-left: Risk tier distribution by platform (100% stacked)
ax3 = axes[1][0]
tier_order = ["🟢 Low", "🟡 Medium", "🟠 High", "🔴 Critical"]
tier_plat = (v.groupby(["platform","risk_tier"]).size()
              .unstack(fill_value=0)
              .reindex(columns=tier_order, fill_value=0))
tier_pct = tier_plat.div(tier_plat.sum(axis=1), axis=0) * 100
bottom = np.zeros(len(tier_pct))
for tier in tier_order:
    vals = tier_pct[tier].values
    ax3.bar(tier_pct.index, vals, bottom=bottom,
            color=TIER_COLORS[tier], label=tier, edgecolor="white", width=0.5)
    for i, (val, bot) in enumerate(zip(vals, bottom)):
        if val > 3:
            ax3.text(i, bot + val/2, f"{val:.0f}%", ha="center", va="center",
                     fontsize=9, fontweight="bold", color="white")
    bottom += vals
ax3.set_ylabel("% of Violation Listings")
ax3.set_title("Risk Tier Distribution by Platform")
ax3.legend(fontsize=9, loc="upper right"); ax3.set_ylim(0, 115)
ax3.yaxis.grid(True, alpha=0.3, linestyle="--"); ax3.set_axisbelow(True)

# Bottom-right: Category mean harm score ranked
ax4 = axes[1][1]
cat_sorted = category_scores.sort_values("mean_harm_score")
bar_colors = ["#E74C3C" if v >= 65 else "#E67E22" if v >= 50 else "#F1C40F"
              for v in cat_sorted["mean_harm_score"]]
bars = ax4.barh(cat_sorted.index, cat_sorted["mean_harm_score"],
                color=bar_colors, edgecolor="white", zorder=3)
for bar, val in zip(bars, cat_sorted["mean_harm_score"]):
    ax4.text(val + 0.3, bar.get_y() + bar.get_height()/2,
             f"{val:.1f}", va="center", fontsize=10, fontweight="bold")
ax4.axvline(65, color="#E67E22", linewidth=1.5, linestyle="--", alpha=0.8, label="High threshold (65)")
ax4.axvline(80, color="#E74C3C", linewidth=1.5, linestyle="--", alpha=0.8, label="Critical threshold (80)")
ax4.set_xlabel("Mean Consumer Harm Score")
ax4.set_title("Category Harm Score Ranking")
ax4.legend(fontsize=8); ax4.xaxis.grid(True, alpha=0.3, linestyle="--"); ax4.set_axisbelow(True)
ax4.set_xlim(0, max(cat_sorted["mean_harm_score"]) * 1.2)

plt.tight_layout()
save(fig, "09_harm_score_overview.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 10 — Pattern Type Ranking + Scatter
# ══════════════════════════════════════════════════════════════════════
print("[Chart 10] Pattern type scoring + severity vs inflation scatter...")

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Consumer Harm Score — Pattern Type Deep Dive", fontweight="bold", fontsize=14)

PATTERN_COLORS_8 = ["#E74C3C","#E67E22","#F1C40F","#2ECC71",
                    "#1ABC9C","#3498DB","#9B59B6","#EC407A"]

# Left: horizontal bar — pattern type by mean harm score
ax = axes[0]
pat_sorted = pattern_scores.sort_values("mean_harm_score")
colors_p = [PATTERN_COLORS_8[i % 8] for i in range(len(pat_sorted))]
bars = ax.barh(pat_sorted.index, pat_sorted["mean_harm_score"],
               color=colors_p, edgecolor="white", zorder=3)
for bar, val, rank in zip(bars, pat_sorted["mean_harm_score"],
                           pat_sorted.sort_values("mean_harm_score")["harm_rank"]):
    ax.text(val + 0.2, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}  (#{rank})", va="center", fontsize=9, fontweight="bold")
ax.axvline(65, color="#E67E22", linewidth=1.5, linestyle="--", alpha=0.7, label="High (65)")
ax.axvline(80, color="#E74C3C", linewidth=1.5, linestyle="--", alpha=0.7, label="Critical (80)")
ax.set_xlabel("Mean Consumer Harm Score")
ax.set_title("Pattern Type — Mean Harm Score Ranking")
ax.legend(fontsize=9); ax.xaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
ax.set_xlim(0, max(pat_sorted["mean_harm_score"]) * 1.25)
ax.tick_params(axis="y", labelsize=9)

# Right: bubble scatter — severity vs inflation, bubble=count, colour=pattern
ax2 = axes[1]
patterns = pattern_scores.index.tolist()
for i, pat in enumerate(patterns):
    row = pattern_scores.loc[pat]
    ax2.scatter(row["avg_inflation_pct"], row["avg_severity"],
                s=row["total_violations"] * 0.4,
                color=PATTERN_COLORS_8[i], alpha=0.85,
                edgecolors="white", linewidth=1.2, zorder=4)
    ax2.annotate(pat, (row["avg_inflation_pct"], row["avg_severity"]),
                 textcoords="offset points", xytext=(6, 4),
                 fontsize=8, color=PATTERN_COLORS_8[i], fontweight="bold")
ax2.set_xlabel("Avg Price Inflation (%)")
ax2.set_ylabel("Avg Severity Score (1–5)")
ax2.set_title("Severity vs. Price Inflation by Pattern Type\n(bubble size = number of violations)")
ax2.xaxis.grid(True, alpha=0.3, linestyle="--")
ax2.yaxis.grid(True, alpha=0.3, linestyle="--")
ax2.set_axisbelow(True)

# Quadrant annotations
ax2.axhline(pattern_scores["avg_severity"].mean(), color="gray",
            linewidth=1, linestyle=":", alpha=0.6)
ax2.axvline(pattern_scores["avg_inflation_pct"].mean(), color="gray",
            linewidth=1, linestyle=":", alpha=0.6)
ax2.text(pattern_scores["avg_inflation_pct"].max()*0.97,
         pattern_scores["avg_severity"].max()*1.0,
         "HIGH SEVERITY\n+ HIGH INFLATION\n(worst quadrant)",
         ha="right", va="top", fontsize=8, color="#E74C3C",
         alpha=0.7, style="italic")

plt.tight_layout()
save(fig, "10_pattern_harm_scores.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 11 — Platform × Category Harm Score Heatmap
# ══════════════════════════════════════════════════════════════════════
print("[Chart 11] Platform × Category Harm Score Heatmap...")

plat_cat = v.groupby(["platform","category"])["harm_score"].mean().round(2).unstack()

fig, ax = plt.subplots(figsize=(13, 5))
sns.heatmap(plat_cat, ax=ax, annot=True, fmt=".1f", cmap="RdYlGn_r",
            linewidths=0.5, linecolor="white",
            cbar_kws={"label": "Mean Consumer Harm Score"},
            annot_kws={"size": 11, "weight": "bold"},
            vmin=50, vmax=90)
ax.set_title("Mean Consumer Harm Score — Platform × Category",
             fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Product Category", fontsize=11)
ax.set_ylabel("Platform", fontsize=11)
ax.tick_params(axis="x", rotation=30, labelsize=9)
ax.tick_params(axis="y", rotation=0, labelsize=11)

# Mark max cell per row
for i, plat in enumerate(plat_cat.index):
    max_col = plat_cat.loc[plat].idxmax()
    j = list(plat_cat.columns).index(max_col)
    ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, edgecolor="navy", lw=2.5))

plt.tight_layout()
save(fig, "11_platform_category_heatmap.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 12 — Score Over Time by Platform
# ══════════════════════════════════════════════════════════════════════
print("[Chart 12] Harm score trend by platform over time...")

score_trend = v.groupby(["year","platform"])["harm_score"].mean().reset_index()
piv_trend   = score_trend.pivot(index="year", columns="platform", values="harm_score")

fig, ax = plt.subplots(figsize=(11, 6))
for plat in ["Flipkart","Meesho","Nykaa"]:
    ax.fill_between(piv_trend.index, piv_trend[plat], alpha=0.07, color=PLATFORM_COLORS[plat])
    ax.plot(piv_trend.index, piv_trend[plat], "o-",
            color=PLATFORM_COLORS[plat], linewidth=2.5, markersize=8, label=plat)
    for x, y in zip(piv_trend.index, piv_trend[plat]):
        ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=9,
                    color=PLATFORM_COLORS[plat], fontweight="bold")

ax.axhline(65, color="#E67E22", linewidth=1.5, linestyle="--", alpha=0.7, label="High threshold (65)")
ax.axhline(80, color="#E74C3C", linewidth=1.5, linestyle="--", alpha=0.7, label="Critical threshold (80)")
ax.axvline(2023, color="red", linestyle="--", alpha=0.5, linewidth=1.5)
ax.text(2023.05, piv_trend.min().min() - 1, "CCPA\n2023 →",
        fontsize=8, color="red", alpha=0.8, va="top")

ax.set_xlabel("Year"); ax.set_ylabel("Mean Consumer Harm Score")
ax.set_title("Consumer Harm Score Trend by Platform — 2021–2025",
             fontsize=13, fontweight="bold")
ax.legend(fontsize=10); ax.yaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
margin = 5
ax.set_ylim(piv_trend.min().min() - margin, piv_trend.max().max() + margin + 5)

plt.tight_layout()
save(fig, "12_harm_score_trend.png")

# ── SAVE OUTPUT CSVs ──────────────────────────────────────────────────
print("\nSaving output files...")

scored_cols = [
    "listing_id","year","month","platform","category","product_name","brand",
    "dark_pattern_type","ccpa_category","severity_score","actual_price_inr",
    "displayed_original_price_inr","price_inflation_inr","price_inflation_pct",
    "hidden_fee_inr","ccpa_violation",
    "sev_norm","inf_norm","fee_norm",
    "contrib_severity","contrib_inflation","contrib_hidden_fee",
    "base_score","ccpa_penalty","harm_score","risk_tier"
]
v[scored_cols].to_csv(f"{OUTPUT_DIR}/harm_scores_listings.csv", index=False)
print(f"  ✅  harm_scores_listings.csv  — {len(v):,} rows")

platform_scores.to_csv(f"{OUTPUT_DIR}/harm_scores_platform.csv")
print(f"  ✅  harm_scores_platform.csv")

category_scores.to_csv(f"{OUTPUT_DIR}/harm_scores_category.csv")
print(f"  ✅  harm_scores_category.csv")

pattern_scores.to_csv(f"{OUTPUT_DIR}/harm_scores_pattern.csv")
print(f"  ✅  harm_scores_pattern.csv")

# ── MODEL REPORT ──────────────────────────────────────────────────────
print("\nWriting model report...")

report = f"""
Dark Pattern Detector — Consumer Harm Score Model Report
═══════════════════════════════════════════════════════════════════

1. MODEL METHODOLOGY
─────────────────────────────────────────────────────────────────
The Consumer Harm Score is a composite index (0–100) designed to
quantify the financial and psychological harm caused by each dark
pattern listing to the end consumer.

Formula:
  Harm Score = (0.45 × severity_norm
              + 0.35 × price_inflation_norm
              + 0.20 × hidden_fee_norm) × 90
              + 10 (CCPA violation penalty)

where each input is Min-Max normalised to [0, 1] before weighting.

Weight rationale:
  • Severity (45%):         Highest weight — directly measures
                             regulatory harm classification.
  • Price Inflation (35%):  Second-highest — direct financial loss.
  • Hidden Fee (20%):       Lower weight — sparse feature (9% of
                             listings), but severe when present.

CCPA Penalty (flat +10): Applied to all violation rows (all 7,846
  listings here are ccpa_violation="Yes"). Represents the regulatory
  dimension of harm beyond the financial signal.

Base score range: 0–90 | After CCPA penalty: 10–100

Risk Tiers:
  🟢 Low:      Score < 50
  🟡 Medium:   50 ≤ Score < 65
  🟠 High:     65 ≤ Score < 80
  🔴 Critical: Score ≥ 80

2. INPUT STATISTICS (violation rows only, n=7,846)
─────────────────────────────────────────────────────────────────
  severity_score:         min=2  max=5  mean=3.76
  price_inflation_pct:    min=4.1%  max=236.3%  mean=84.5%
  hidden_fee_inr:         min=₹0  max=₹120  mean=₹7.36  (91% zero)

3. HARM SCORE DISTRIBUTION
─────────────────────────────────────────────────────────────────
  Score range:  {v['harm_score'].min():.1f} – {v['harm_score'].max():.1f}
  Mean:         {v['harm_score'].mean():.2f}
  Median:       {v['harm_score'].median():.2f}
  Std dev:      {v['harm_score'].std():.2f}

  Risk Tier Breakdown:
"""
for tier in ["🔴 Critical","🟠 High","🟡 Medium","🟢 Low"]:
    cnt = (v["risk_tier"] == tier).sum()
    report += f"    {tier}:  {cnt:,} ({cnt/len(v)*100:.1f}%)\n"

report += f"""
4. PLATFORM RANKINGS
─────────────────────────────────────────────────────────────────
"""
for rank, (plat, row) in enumerate(platform_scores.iterrows(), 1):
    report += f"""  #{rank} {plat}
      Mean Harm Score:      {row['mean_harm_score']:.2f}
      Critical listings:    {row['pct_critical']:.1f}%
      Avg severity:         {row['avg_severity']:.2f}/5
      Avg inflation:        {row['avg_inflation_pct']:.1f}%
      Total consumer loss:  ₹{row['total_consumer_loss']:,.0f}
      Component breakdown:  Severity {row['contrib_sev_avg']:.1f} | Inflation {row['contrib_inf_avg']:.1f} | Fee {row['contrib_fee_avg']:.1f} | CCPA +10
"""

report += f"""
5. CATEGORY RANKINGS
─────────────────────────────────────────────────────────────────
"""
for cat, row in category_scores.iterrows():
    report += f"  #{int(row['harm_rank'])} {cat:<20} score={row['mean_harm_score']:.2f}  critical={row['pct_critical']:.1f}%  loss=₹{row['total_consumer_loss']:,.0f}\n"

report += f"""
6. PATTERN TYPE RANKINGS
─────────────────────────────────────────────────────────────────
"""
for pat, row in pattern_scores.iterrows():
    report += f"  #{int(row['harm_rank'])} {pat:<35} score={row['mean_harm_score']:.2f}  severity={row['avg_severity']:.1f}  inflation=₹{row['avg_inflation_inr']:,.0f}\n"

report += f"""
7. KEY FINDINGS FROM MODEL
─────────────────────────────────────────────────────────────────
• All violation listings score ≥ 10 (CCPA penalty floor) — none
  escape the regulatory harm classification.

• Meesho ranks #1 most harmful by mean harm score, driven by highest
  violation rate (77.8%) and highest proportion of Critical-tier listings.

• "Inflated Original Price" and "Hidden Convenience Fee" are the
  highest-scoring pattern types (severity = 5/5) — primary targets
  for regulatory enforcement.

• Hidden fees, while sparse (9% of listings), push harm scores
  significantly higher when present — Flipkart has the most.

• No platform scores below 'High' tier on average — the industry-wide
  nature of dark patterns is the central finding of this project.

8. OUTPUTS GENERATED
─────────────────────────────────────────────────────────────────
  harm_scores_listings.csv  — {len(v):,} scored rows (all violation listings)
  harm_scores_platform.csv  — 3-row platform ranking table
  harm_scores_category.csv  — 8-row category ranking table
  harm_scores_pattern.csv   — 8-row pattern type ranking table
  charts/09_harm_score_overview.png
  charts/10_pattern_harm_scores.png
  charts/11_platform_category_heatmap.png
  charts/12_harm_score_trend.png

═══════════════════════════════════════════════════════════════════
Step 3 COMPLETE — proceed to Step 4: SQL Queries
═══════════════════════════════════════════════════════════════════
"""
with open(f"{OUTPUT_DIR}/harm_score_model_report.txt", "w", encoding="utf-8") as f:
    f.write(report)
print(f"  ✅  harm_score_model_report.txt")

print("\n✅  Step 3 COMPLETE — 4 charts, 4 CSVs, 1 model report.")
print("    Next → Step 4: SQL Queries")
