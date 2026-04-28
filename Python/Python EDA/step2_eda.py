"""
 Python EDA
Dark Pattern Detector | Portfolio Project

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "Data")   # ← FIXED (capital D, no /raw)
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "charts")

os.makedirs(OUTPUT_DIR, exist_ok=True)

PLATFORM_COLORS = {
    "Flipkart": "#2874F0",   # Flipkart blue
    "Meesho":   "#9B59B6",   # Meesho violet
    "Nykaa":    "#FC2779",   # Nykaa pink
}

PATTERN_COLORS = [
    "#E74C3C", "#E67E22", "#F1C40F", "#2ECC71",
    "#1ABC9C", "#3498DB", "#9B59B6", "#EC407A",
]

SEVERITY_COLORS = {2: "#F9E79F", 3: "#F39C12", 4: "#E74C3C", 5: "#7B241C"}

# Global style
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
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"  ✅  Saved → {path}")

# ── LOAD DATA ─────────────────────────────────────────────────────────
print("Loading data...")
FILES = {
    "listings_raw":             "listings_raw.csv",
    "dark_patterns_classified": "dark_patterns_classified.csv",
    "platform_summary":         "platform_summary.csv",
    "pattern_type_trend":       "pattern_type_trend.csv",
    "category_heatmap":         "category_heatmap.csv",
}
dfs = {}
for k, file in FILES.items():
    path = os.path.join(DATA_DIR, file)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    
    dfs[k] = pd.read_csv(path)
    
df  = dfs["listings_raw"].copy()
v   = df[df["ccpa_violation"] == "Yes"].copy()
ps  = dfs["platform_summary"].copy()
pt  = dfs["pattern_type_trend"].dropna(subset=["dark_pattern_type"]).copy()
ch  = dfs["category_heatmap"].copy()
cls = dfs["dark_patterns_classified"].copy()

# Derived columns
df["price_inflation_pct"] = (df["price_inflation_inr"] / df["actual_price_inr"] * 100).round(2)
v["price_inflation_pct"]  = (v["price_inflation_inr"]  / v["actual_price_inr"]  * 100).round(2)

YEARS     = sorted(df["year"].unique())
PLATFORMS = sorted(df["platform"].unique())
PATTERNS  = sorted(pt["dark_pattern_type"].unique())
CATEGORIES= sorted(ch["category"].unique())

print(f"  listings_raw: {len(df):,} rows | violations: {len(v):,} ({len(v)/len(df):.1%})\n")

# ══════════════════════════════════════════════════════════════════════
# CHART 1 — Year-on-Year Violation Count & Rate
# ══════════════════════════════════════════════════════════════════════
print("[Chart 1] YoY Violation Trend...")

yoy_count = v.groupby("year").size().reset_index(name="violations")
yoy_total = df.groupby("year").size().reset_index(name="total")
yoy = yoy_count.merge(yoy_total, on="year")
yoy["rate_pct"] = (yoy["violations"] / yoy["total"] * 100).round(2)
yoy["yoy_delta"] = yoy["violations"].diff()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Year-on-Year Dark Pattern Violations (2021–2025)", fontweight="bold", fontsize=14)

# Left: bar chart of violation count
ax = axes[0]
bars = ax.bar(yoy["year"], yoy["violations"], color="#3498DB", edgecolor="white", linewidth=0.8, zorder=3)
ax.plot(yoy["year"], yoy["violations"], "o-", color="#E74C3C", linewidth=2, markersize=6, zorder=4, label="Trend")
for bar, val in zip(bars, yoy["violations"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 8,
            f"{val:,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_xlabel("Year"); ax.set_ylabel("Number of Violations")
ax.set_title("Total Violations Per Year")
ax.set_ylim(0, yoy["violations"].max() * 1.18)
ax.yaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)

# Right: violation rate % line
ax2 = axes[1]
ax2.fill_between(yoy["year"], yoy["rate_pct"], alpha=0.15, color="#9B59B6")
ax2.plot(yoy["year"], yoy["rate_pct"], "o-", color="#9B59B6", linewidth=2.5, markersize=8, zorder=4)
for x, y in zip(yoy["year"], yoy["rate_pct"]):
    ax2.annotate(f"{y:.1f}%", (x, y), textcoords="offset points",
                 xytext=(0, 10), ha="center", fontsize=10, fontweight="bold", color="#9B59B6")
ax2.set_xlabel("Year"); ax2.set_ylabel("Violation Rate (%)")
ax2.set_title("CCPA Violation Rate Per Year")
ax2.set_ylim(yoy["rate_pct"].min() - 2, yoy["rate_pct"].max() + 4)
ax2.yaxis.grid(True, alpha=0.3, linestyle="--"); ax2.set_axisbelow(True)
ax2.axhline(yoy["rate_pct"].mean(), color="gray", linestyle="--", linewidth=1, alpha=0.7,
            label=f"Avg {yoy['rate_pct'].mean():.1f}%")
ax2.legend(fontsize=9)

plt.tight_layout()
save(fig, "01_yoy_violation_trend.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 2 — Platform Comparison (violation rate per year)
# ══════════════════════════════════════════════════════════════════════
print("[Chart 2] Platform Comparison...")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Platform Deep Dive — Flipkart vs Meesho vs Nykaa (2021–2025)",
             fontweight="bold", fontsize=14)

# Left: Violation rate % per platform per year — grouped bar
ax = axes[0]
piv_rate = ps.pivot(index="year", columns="platform", values="dark_pattern_rate_pct")
x = np.arange(len(YEARS)); width = 0.27
for i, plat in enumerate(PLATFORMS):
    offset = (i - 1) * width
    bars = ax.bar(x + offset, piv_rate[plat], width=width,
                  color=PLATFORM_COLORS[plat], label=plat, edgecolor="white")
ax.set_xticks(x); ax.set_xticklabels(YEARS)
ax.set_xlabel("Year"); ax.set_ylabel("Dark Pattern Rate (%)")
ax.set_title("Violation Rate by Platform")
ax.legend(fontsize=9); ax.yaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
ax.set_ylim(0, 100)

# Middle: Total consumer overcharge ₹ per platform
ax2 = axes[1]
overcharge = ps.groupby("platform")["total_consumer_overcharge_inr"].sum().reindex(PLATFORMS)
colors = [PLATFORM_COLORS[p] for p in PLATFORMS]
bars = ax2.bar(PLATFORMS, overcharge / 1e6, color=colors, edgecolor="white", zorder=3)
for bar, val in zip(bars, overcharge / 1e6):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
             f"₹{val:.2f}M", ha="center", fontsize=10, fontweight="bold")
ax2.set_ylabel("Total Consumer Overcharge (₹ Million)")
ax2.set_title("Total Consumer Overcharge\n(2021–2025 Cumulative)")
ax2.yaxis.grid(True, alpha=0.3, linestyle="--"); ax2.set_axisbelow(True)

# Right: Avg severity per platform — dot plot
ax3 = axes[2]
sev_plat = v.groupby("platform")["severity_score"].mean().reindex(PLATFORMS)
for i, (plat, val) in enumerate(sev_plat.items()):
    ax3.barh(i, val, color=PLATFORM_COLORS[plat], height=0.5, zorder=3)
    ax3.text(val + 0.02, i, f"{val:.2f}", va="center", fontsize=11, fontweight="bold")
ax3.set_yticks(range(len(PLATFORMS))); ax3.set_yticklabels(PLATFORMS)
ax3.set_xlabel("Avg Severity Score (1–5)")
ax3.set_title("Avg Severity by Platform")
ax3.xaxis.grid(True, alpha=0.3, linestyle="--"); ax3.set_axisbelow(True)
ax3.set_xlim(0, 5.5)

plt.tight_layout()
save(fig, "02_platform_comparison.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 3 — Pattern Type Trend (Stacked Area 2021–2025)
# ══════════════════════════════════════════════════════════════════════
print("[Chart 3] Pattern Type Trend...")

piv_pt = pt.pivot(index="year", columns="dark_pattern_type", values="count").fillna(0)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("Dark Pattern Type Trends — 2021–2025", fontweight="bold", fontsize=14)

# Stacked area
ax = axes[0]
ax.stackplot(piv_pt.index, [piv_pt[col] for col in piv_pt.columns],
             labels=piv_pt.columns, colors=PATTERN_COLORS, alpha=0.85)
ax.set_xlabel("Year"); ax.set_ylabel("Number of Listings")
ax.set_title("Stacked Area — All Pattern Types")
ax.legend(loc="upper left", fontsize=8, framealpha=0.8)
ax.yaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)

# Line chart per pattern
ax2 = axes[1]
for i, col in enumerate(piv_pt.columns):
    ax2.plot(piv_pt.index, piv_pt[col], "o-", color=PATTERN_COLORS[i],
             linewidth=2, markersize=5, label=col)
ax2.set_xlabel("Year"); ax2.set_ylabel("Count")
ax2.set_title("Individual Pattern Trends")
ax2.legend(fontsize=8, framealpha=0.8)
ax2.yaxis.grid(True, alpha=0.3, linestyle="--"); ax2.set_axisbelow(True)

plt.tight_layout()
save(fig, "03_pattern_type_trend.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 4 — Category Heatmap
# ══════════════════════════════════════════════════════════════════════
print("[Chart 4] Category Heatmap...")

pivot_heat = ch.pivot(index="category", columns="dark_pattern_type", values="count")

fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(
    pivot_heat, ax=ax,
    annot=True, fmt="d", cmap="YlOrRd",
    linewidths=0.5, linecolor="white",
    cbar_kws={"label": "Number of Dark Pattern Instances"},
    annot_kws={"size": 10, "weight": "bold"},
)
ax.set_title("Category × Dark Pattern Type Heatmap", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Dark Pattern Type", fontsize=11)
ax.set_ylabel("Product Category", fontsize=11)
ax.tick_params(axis="x", rotation=30, labelsize=9)
ax.tick_params(axis="y", rotation=0, labelsize=10)

# Annotate top cell per column
for j, col in enumerate(pivot_heat.columns):
    max_row = pivot_heat[col].idxmax()
    max_i   = list(pivot_heat.index).index(max_row)
    ax.add_patch(plt.Rectangle((j, max_i), 1, 1, fill=False,
                                edgecolor="navy", lw=2.5))

plt.tight_layout()
save(fig, "04_category_heatmap.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 5 — Severity Score Distribution
# ══════════════════════════════════════════════════════════════════════
print("[Chart 5] Severity Distribution...")

sev_counts = v["severity_score"].value_counts().sort_index()
sev_labels = {2: "Low\n(2)", 3: "Medium\n(3)", 4: "High\n(4)", 5: "Critical\n(5)"}

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Severity Score Analysis", fontweight="bold", fontsize=14)

# Overall distribution — donut
ax = axes[0]
colors_sev = [SEVERITY_COLORS[s] for s in sev_counts.index]
wedges, texts, autotexts = ax.pie(
    sev_counts, labels=[sev_labels[s] for s in sev_counts.index],
    colors=colors_sev, autopct="%1.1f%%", startangle=140,
    pctdistance=0.75, wedgeprops=dict(width=0.55),
    textprops={"fontsize": 10},
)
for at in autotexts:
    at.set_fontweight("bold")
ax.set_title("Severity Distribution (All Violations)")
centre = plt.Circle((0, 0), 0.45, fc="white")
ax.add_artist(centre)
ax.text(0, 0, f"{len(v):,}\nlistings", ha="center", va="center",
        fontsize=11, fontweight="bold", color="#2C3E50")

# Severity by platform — grouped bar
ax2 = axes[1]
sev_plat = v.groupby(["platform", "severity_score"]).size().unstack(fill_value=0)
sev_plat_pct = sev_plat.div(sev_plat.sum(axis=1), axis=0) * 100
bottom = np.zeros(len(PLATFORMS))
sev_levels = sorted(v["severity_score"].unique())
for sev in sev_levels:
    vals = [sev_plat_pct.loc[p, sev] if sev in sev_plat_pct.columns else 0 for p in PLATFORMS]
    ax2.bar(PLATFORMS, vals, bottom=bottom, color=SEVERITY_COLORS[sev],
            label=sev_labels[sev], edgecolor="white")
    bottom += np.array(vals)
ax2.set_ylabel("% of Violations"); ax2.set_title("Severity Mix by Platform")
ax2.legend(title="Severity", fontsize=8, loc="upper right")
ax2.yaxis.grid(True, alpha=0.3, linestyle="--"); ax2.set_axisbelow(True)

# Severity by pattern type — horizontal bar (avg)
ax3 = axes[2]
sev_pat = v.groupby("dark_pattern_type")["severity_score"].mean().sort_values()
colors_pat = ["#E74C3C" if x >= 4.5 else "#E67E22" if x >= 3.5 else "#F9E79F" for x in sev_pat]
bars = ax3.barh(sev_pat.index, sev_pat.values, color=colors_pat, edgecolor="white", zorder=3)
for bar, val in zip(bars, sev_pat.values):
    ax3.text(val + 0.03, bar.get_y() + bar.get_height()/2,
             f"{val:.2f}", va="center", fontsize=9, fontweight="bold")
ax3.set_xlabel("Avg Severity Score"); ax3.set_title("Avg Severity by Pattern Type")
ax3.xaxis.grid(True, alpha=0.3, linestyle="--"); ax3.set_axisbelow(True)
ax3.set_xlim(0, 6)
ax3.tick_params(axis="y", labelsize=9)

plt.tight_layout()
save(fig, "05_severity_distribution.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 6 — Price Inflation Analysis
# ══════════════════════════════════════════════════════════════════════
print("[Chart 6] Price Inflation Analysis...")

fig, axes = plt.subplots(2, 2, figsize=(15, 11))
fig.suptitle("Price Inflation Analysis — Violation Listings", fontweight="bold", fontsize=14)

# Top-left: Distribution of price inflation %
ax = axes[0][0]
ax.hist(v["price_inflation_pct"], bins=40, color="#3498DB",
        edgecolor="white", linewidth=0.5, zorder=3, alpha=0.85)
ax.axvline(v["price_inflation_pct"].mean(),   color="#E74C3C", linewidth=2,
           linestyle="--", label=f"Mean {v['price_inflation_pct'].mean():.1f}%")
ax.axvline(v["price_inflation_pct"].median(), color="#2ECC71", linewidth=2,
           linestyle="--", label=f"Median {v['price_inflation_pct'].median():.1f}%")
ax.set_xlabel("Price Inflation (%)"); ax.set_ylabel("Number of Listings")
ax.set_title("Distribution of Price Inflation %")
ax.legend(fontsize=9); ax.yaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)

# Top-right: Avg price inflation % by platform (violin/box)
ax2 = axes[0][1]
data_by_plat = [v[v["platform"] == p]["price_inflation_pct"].values for p in PLATFORMS]
bp = ax2.boxplot(data_by_plat, labels=PLATFORMS, patch_artist=True,
                 medianprops={"color": "white", "linewidth": 2},
                 whiskerprops={"linewidth": 1.5},
                 capprops={"linewidth": 1.5})
for patch, plat in zip(bp["boxes"], PLATFORMS):
    patch.set_facecolor(PLATFORM_COLORS[plat])
    patch.set_alpha(0.8)
ax2.set_ylabel("Price Inflation (%)"); ax2.set_title("Price Inflation % by Platform")
ax2.yaxis.grid(True, alpha=0.3, linestyle="--"); ax2.set_axisbelow(True)

# Bottom-left: Avg price inflation INR by pattern type
ax3 = axes[1][0]
inf_pat = v.groupby("dark_pattern_type")["price_inflation_inr"].mean().sort_values(ascending=False)
colors_inf = PATTERN_COLORS[:len(inf_pat)]
bars = ax3.bar(range(len(inf_pat)), inf_pat.values, color=colors_inf, edgecolor="white", zorder=3)
for bar, val in zip(bars, inf_pat.values):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
             f"₹{val:,.0f}", ha="center", fontsize=9, fontweight="bold")
ax3.set_xticks(range(len(inf_pat)))
ax3.set_xticklabels(inf_pat.index, rotation=30, ha="right", fontsize=9)
ax3.set_ylabel("Avg Price Inflation (₹)")
ax3.set_title("Avg Price Inflation (₹) by Pattern Type")
ax3.yaxis.grid(True, alpha=0.3, linestyle="--"); ax3.set_axisbelow(True)

# Bottom-right: Year-on-year avg inflation ₹ per platform
ax4 = axes[1][1]
inf_plat_yr = ps.pivot(index="year", columns="platform", values="avg_price_inflation_inr")
for plat in PLATFORMS:
    ax4.plot(inf_plat_yr.index, inf_plat_yr[plat], "o-",
             color=PLATFORM_COLORS[plat], linewidth=2, markersize=6, label=plat)
ax4.set_xlabel("Year"); ax4.set_ylabel("Avg Price Inflation (₹)")
ax4.set_title("Avg Price Inflation (₹) per Platform — YoY")
ax4.legend(fontsize=9); ax4.yaxis.grid(True, alpha=0.3, linestyle="--"); ax4.set_axisbelow(True)

plt.tight_layout()
save(fig, "06_price_inflation_analysis.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 7 — Top Brands by Violation + Hidden Fees
# ══════════════════════════════════════════════════════════════════════
print("[Chart 7] Brand & Hidden Fees...")

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Brand-level Violations & Hidden Fees", fontweight="bold", fontsize=14)

# Top 12 brands by violations
ax = axes[0]
top_brands = v["brand"].value_counts().head(12)
colors_brand = ["#E74C3C" if i < 3 else "#E67E22" if i < 6 else "#3498DB"
                for i in range(len(top_brands))]
bars = ax.barh(top_brands.index[::-1], top_brands.values[::-1],
               color=colors_brand[::-1], edgecolor="white", zorder=3)
for bar, val in zip(bars, top_brands.values[::-1]):
    ax.text(val + 1, bar.get_y() + bar.get_height()/2,
            str(val), va="center", fontsize=10, fontweight="bold")
ax.set_xlabel("Number of Violations"); ax.set_title("Top 12 Brands by Violation Count")
ax.xaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)

# Hidden fee distribution by platform (non-zero only)
ax2 = axes[1]
hf = v[v["hidden_fee_inr"] > 0]
hf_plat = [hf[hf["platform"] == p]["hidden_fee_inr"].values for p in PLATFORMS]
bp2 = ax2.boxplot(hf_plat, labels=PLATFORMS, patch_artist=True,
                  medianprops={"color": "white", "linewidth": 2},
                  whiskerprops={"linewidth": 1.5})
for patch, plat in zip(bp2["boxes"], PLATFORMS):
    patch.set_facecolor(PLATFORM_COLORS[plat])
    patch.set_alpha(0.8)
ax2_t = ax2.twinx()
hf_counts = {p: (df[df["platform"] == p]["hidden_fee_inr"] > 0).sum() for p in PLATFORMS}
ax2_t.bar(range(1, len(PLATFORMS) + 1), [hf_counts[p] for p in PLATFORMS],
          alpha=0.2, color="gray", width=0.4, label="Count (listings)")
ax2_t.set_ylabel("Listings with Hidden Fees", color="gray")
ax2.set_ylabel("Hidden Fee Amount (₹)")
ax2.set_title("Hidden Fee Distribution by Platform\n(non-zero listings only)")
ax2.yaxis.grid(True, alpha=0.3, linestyle="--"); ax2.set_axisbelow(True)

plt.tight_layout()
save(fig, "07_brands_and_hidden_fees.png")

# ══════════════════════════════════════════════════════════════════════
# CHART 8 — Platform Trend Lines (violation rate 2021–2025)
# ══════════════════════════════════════════════════════════════════════
print("[Chart 8] Platform violation rate trend...")

fig, ax = plt.subplots(figsize=(11, 6))
piv_rate = ps.pivot(index="year", columns="platform", values="dark_pattern_rate_pct")
for plat in PLATFORMS:
    ax.fill_between(piv_rate.index, piv_rate[plat], alpha=0.08, color=PLATFORM_COLORS[plat])
    ax.plot(piv_rate.index, piv_rate[plat], "o-",
            color=PLATFORM_COLORS[plat], linewidth=2.5, markersize=8, label=plat)
    for x, y in zip(piv_rate.index, piv_rate[plat]):
        ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=9,
                    color=PLATFORM_COLORS[plat], fontweight="bold")
ax.set_xlabel("Year"); ax.set_ylabel("Dark Pattern Violation Rate (%)")
ax.set_title("CCPA Violation Rate per Platform — 2021–2025",
             fontsize=13, fontweight="bold")
ax.legend(fontsize=10, loc="upper right")
ax.yaxis.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
ax.set_ylim(55, 90)

# Annotate CCPA guideline year
ax.axvline(2023, color="red", linestyle="--", alpha=0.5, linewidth=1.5)
ax.text(2023.05, 57, "CCPA Guidelines\nIssued →", fontsize=8.5,
        color="red", alpha=0.8, va="bottom")

plt.tight_layout()
save(fig, "08_platform_violation_rate_trend.png")

# ══════════════════════════════════════════════════════════════════════
# EDA SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
print("\nGenerating EDA summary table...")

platform_stats = v.groupby("platform").agg(
    total_violations=("listing_id", "count"),
    avg_severity=("severity_score", "mean"),
    avg_inflation_pct=("price_inflation_pct", "mean"),
    avg_inflation_inr=("price_inflation_inr", "mean"),
    median_inflation_inr=("price_inflation_inr", "median"),
    listings_with_hidden_fees=("hidden_fee_inr", lambda x: (x > 0).sum()),
).round(2)
platform_stats["violation_rate_pct"] = ps.groupby("platform")["dark_pattern_rate_pct"].mean().round(2)
platform_stats.to_csv("outputs/eda_platform_summary.csv")
print("  ✅  Saved → outputs/eda_platform_summary.csv")

pattern_stats = v.groupby("dark_pattern_type").agg(
    total_count=("listing_id", "count"),
    avg_severity=("severity_score", "mean"),
    avg_inflation_pct=("price_inflation_pct", "mean"),
    avg_inflation_inr=("price_inflation_inr", "mean"),
).round(2).sort_values("avg_severity", ascending=False)
pattern_stats.to_csv("outputs/eda_pattern_summary.csv")
print("  ✅  Saved → outputs/eda_pattern_summary.csv")

category_stats = ch.groupby("category")["count"].sum().sort_values(ascending=False).reset_index()
category_stats.columns = ["category", "total_dark_patterns"]
category_stats.to_csv("outputs/eda_category_summary.csv", index=False)
print("  ✅  Saved → outputs/eda_category_summary.csv")

# ── PRINT KEY INSIGHTS ────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  EDA KEY INSIGHTS — USE IN README & PRESENTATION")
print("=" * 65)

print(f"\n📌 Overall")
print(f"   • {len(df):,} listings analysed across 3 platforms, 2021–2025")
print(f"   • {len(v):,} violations detected ({len(v)/len(df):.1%} overall CCPA violation rate)")
print(f"   • Violations are remarkably stable YoY: {v.groupby('year').size().min()}–{v.groupby('year').size().max()} per year")

print(f"\n📌 Platform")
for p in PLATFORMS:
    avg_r = ps[ps["platform"]==p]["dark_pattern_rate_pct"].mean()
    avg_s = v[v["platform"]==p]["severity_score"].mean()
    print(f"   • {p}: avg {avg_r:.1f}% violation rate | avg severity {avg_s:.2f}/5")

print(f"\n📌 Pattern Types")
for pat, row in pattern_stats.iterrows():
    print(f"   • {pat}: {int(row['total_count']):,} violations | "
          f"avg severity {row['avg_severity']:.2f} | "
          f"avg inflation ₹{row['avg_inflation_inr']:,.0f}")

print(f"\n📌 Price Inflation")
print(f"   • Avg inflation across violations: {v['price_inflation_pct'].mean():.1f}%")
print(f"   • Median inflation: {v['price_inflation_pct'].median():.1f}%")
print(f"   • Max inflation seen: {v['price_inflation_pct'].max():.1f}%")
print(f"   • Most inflationary pattern: {v.groupby('dark_pattern_type')['price_inflation_inr'].mean().idxmax()}")

print(f"\n📌 Categories")
cat_totals = ch.groupby("category")["count"].sum().sort_values(ascending=False)
for cat, cnt in cat_totals.items():
    print(f"   • {cat}: {cnt:,} dark pattern instances")

print(f"\n📌 Hidden Fees")
hf_nonzero = df[df["hidden_fee_inr"] > 0]
print(f"   • {len(hf_nonzero):,} listings ({len(hf_nonzero)/len(df):.1%}) include hidden fees")
print(f"   • Avg hidden fee: ₹{hf_nonzero['hidden_fee_inr'].mean():.2f}")
print(f"   • Total hidden fees in dataset: ₹{df['hidden_fee_inr'].sum():,.0f}")

