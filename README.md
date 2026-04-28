# 🔍 Dark Pattern Detector
### Quantifying Manipulative UX on Indian E-commerce | 2021–2025

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.24+-013243?style=for-the-badge&logo=numpy&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Status](https://img.shields.io/badge/Status-Complete-27AE60?style=for-the-badge)
![Listings](https://img.shields.io/badge/Listings_Analysed-10%2C717-E74C3C?style=for-the-badge)

</div>

---

## 📌 Project Summary

This end-to-end data analytics project systematically identifies, quantifies, and visualises **dark patterns** — deceptive UX and pricing tactics used to manipulate consumers — across three major Indian e-commerce platforms: **Flipkart**, **Meesho**, and **Nykaa**.

Covering **10,717 product listings from 2021–2025**, the project builds a fully reproducible pipeline from raw data validation through to an executive-grade 4-page Power BI dashboard, with a custom **Consumer Harm Score** model that ranks platforms and product categories by deceptive risk.

> **Why it matters:** India's CCPA issued its first dark pattern guidelines in 2023. This project quantifies the scale of non-compliance across platforms — and whether the regulation had any measurable effect. The answer is stark: **it didn't.**

---

## 🎯 Key Findings

| Metric | Finding |
|---|---|
| **Overall CCPA violation rate** | **73.21%** of all listings violate CCPA guidelines |
| **Total violations detected** | **7,846** out of 10,717 listings |
| **Highest-risk platform** | **Meesho** — avg 77.8% violation rate across 5 years |
| **Most dangerous pattern** | **Hidden Convenience Fee** — Harm Score 70.35/100, Severity 5/5 |
| **Fastest-growing pattern** | **Misleading Discount Badge** — grew from 182 (2021) to 217 (2025) |
| **Most manipulated category** | **Toys** — 1,044 dark pattern instances |
| **Highest consumer loss category** | **Mobile Phones** — ₹43.2L total (avg ₹4,425 per listing) |
| **Avg price inflation** | **84.54%** — consumers pay nearly double the real price |
| **Max price inflation seen** | **236.3%** on a single listing |
| **Total consumer financial loss** | **₹1.00 Crore** across all violation listings |
| **CCPA 2023 impact** | **Zero** — violations *increased* from 72.92% → 73.75% in 2023 |

> 💡 **The headline finding:** CCPA guidelines were issued in 2023. Violation rates went **up** that year on every platform. No platform has shown measurable improvement. Regulatory announcements without enforcement have no effect.

---

## 📊 Dashboard Preview

> *Power BI dashboard — 4 pages covering Executive Overview, Platform Deep Dive, Pattern Analysis, and Category Heatmap*

![Dashboard Preview](docs/dashboard_preview.png)

🔗 **[Live Dashboard →](https://app.powerbi.com/YOUR_LINK_HERE)** *(publish after building in Power BI Desktop)*

---

## 🗂️ Project Structure

```
dark-pattern-detector/
│
├── 📁 data/
│   ├── raw/                          # Original source CSVs (unmodified)
│   │   ├── listings_raw.csv          # 10,717 listings — master fact table
│   │   ├── dark_patterns_classified.csv  # 7,846 violation rows (pre-filtered)
│   │   ├── platform_summary.csv      # Yearly KPIs per platform (15 rows)
│   │   ├── pattern_type_trend.csv    # Pattern counts by year (45 rows)
│   │   └── category_heatmap.csv      # Category × pattern pivot (64 rows)
│   └── processed/                    # Outputs from scoring model
│
├── 📁 scripts/
│   ├── step1_validate.py             # Data validation — shape, nulls, domain checks
│   ├── step2_eda.py                  # EDA — 8 charts + 3 summary CSVs
│   └── step3_scoring.py             # Consumer Harm Score model — 4 charts + 4 CSVs
│
├── 📁 sql/
│   ├── 01_platform_dark_rate.sql     # Highest violation rate by platform & year
│   ├── 02_top_harmful_categories.sql # Top 3 categories by consumer loss
│   ├── 03_avg_inflation_by_pattern.sql  # Avg price inflation per pattern type
│   └── 04_yoy_ccpa_violation_change.sql # YoY CCPA violation trend
│
├── 📁 dashboard/
│   ├── dark_pattern_dashboard.pbix   # Power BI Desktop file
│   ├── dax_measures.txt              # All 44 DAX measures with expected values
│   └── powerbi_build_guide.md        # Step-by-step build instructions
│
├── 📁 outputs/
│   ├── validation_report.txt         # Step 1 output
│   ├── harm_scores_listings.csv      # 7,846 scored rows with harm score
│   ├── harm_scores_platform.csv      # Platform ranking table
│   ├── harm_scores_category.csv      # Category ranking table
│   ├── harm_scores_pattern.csv       # Pattern type ranking table
│   └── charts/                       # All 12 EDA + scoring charts (PNG)
│
├── 📁 docs/
│   ├── data_dictionary.md            # Column definitions + dark pattern reference
│   └── dashboard_preview.png         # Dashboard screenshot for README
│
├── requirements.txt
└── README.md
```

---

## 📂 Dataset Overview

| File | Rows | Cols | Description |
|---|---|---|---|
| `listings_raw.csv` | 10,717 | 17 | Master dataset — all listings with prices, severity, flags, fees |
| `dark_patterns_classified.csv` | 7,846 | 13 | Violation-only rows (ccpa_violation = "Yes") |
| `platform_summary.csv` | 15 | 9 | 3 platforms × 5 years — pre-aggregated KPIs |
| `pattern_type_trend.csv` | 45 | 5 | 8 pattern types × 5 years — count and severity |
| `category_heatmap.csv` | 64 | 3 | 8 categories × 8 patterns — pivot-ready |

### Key Columns

| Column | Type | Description |
|---|---|---|
| `platform` | string | Flipkart / Meesho / Nykaa |
| `actual_price_inr` | int | True market price (₹) |
| `displayed_original_price_inr` | int | Inflated price shown to consumer (₹) |
| `price_inflation_inr` | int | Difference — direct financial loss per listing |
| `dark_pattern_type` | string | One of 8 pattern types |
| `severity_score` | int | 2–5 scale (2=Low, 5=Critical) |
| `ccpa_violation` | string | "Yes" / "No" — CCPA 2023 compliance flag |
| `hidden_fee_inr` | int | Hidden fee charged at checkout (₹0 if none) |

---

## 🧰 Tech Stack

| Layer | Tools |
|---|---|
| **Language** | Python 3.10+ |
| **Data Wrangling** | pandas 2.x, NumPy |
| **Visualisation** | matplotlib, seaborn, plotly |
| **Scoring Model** | NumPy (Min-Max normalisation) |
| **SQL Analysis** | SQLite (dev) / PostgreSQL (prod) |
| **Dashboard** | Power BI Desktop (DAX, window functions) |
| **Version Control** | Git + GitHub |

---

## ⚙️ How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/dark-pattern-detector.git
cd dark-pattern-detector
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Add Raw Data Files
Place all 5 CSV files into `data/raw/`:
```
data/raw/listings_raw.csv
data/raw/dark_patterns_classified.csv
data/raw/platform_summary.csv
data/raw/pattern_type_trend.csv
data/raw/category_heatmap.csv
```

### 4. Run Step 1 — Data Validation
```bash
python scripts/step1_validate.py
# → outputs/validation_report.txt
```
Expected: **zero blocking errors** | 2 warnings (expected nulls in non-violation rows)

### 5. Run Step 2 — EDA
```bash
python scripts/step2_eda.py
# → outputs/charts/01_yoy_violation_trend.png  (+ 7 more charts)
# → outputs/eda_platform_summary.csv
# → outputs/eda_pattern_summary.csv
# → outputs/eda_category_summary.csv
```

### 6. Run Step 3 — Consumer Harm Score Model
```bash
python scripts/step3_scoring.py
# → outputs/harm_scores_listings.csv   (7,846 scored rows)
# → outputs/harm_scores_platform.csv
# → outputs/harm_scores_category.csv
# → outputs/harm_scores_pattern.csv
# → outputs/charts/09_harm_score_overview.png  (+ 3 more charts)
```

### 7. Run SQL Queries
Load `data/raw/listings_raw.csv` and `data/raw/platform_summary.csv` into your SQL client (SQLite, DBeaver, pgAdmin), then execute files from `sql/` in order.

```bash
# Quick validation using SQLite in Python:
python - << 'EOF'
import pandas as pd, sqlite3
conn = sqlite3.connect(":memory:")
pd.read_csv("data/raw/listings_raw.csv").to_sql("listings_raw", conn, index=False)
pd.read_csv("data/raw/platform_summary.csv").to_sql("platform_summary", conn, index=False)
# Then run any query from sql/ folder
EOF
```

### 8. Open Power BI Dashboard
1. Open `dashboard/dark_pattern_dashboard.pbix` in Power BI Desktop
2. Update data source paths: **Home → Transform Data → Data Source Settings**
3. Refer to `dashboard/powerbi_build_guide.md` for full build instructions
4. All 44 DAX measures are in `dashboard/dax_measures.txt`

---

## 📐 Consumer Harm Score Model

A composite score (0–100) per listing quantifying financial and regulatory harm:

```
Harm Score = (0.45 × severity_norm
            + 0.35 × price_inflation_norm
            + 0.20 × hidden_fee_norm) × 90
            + 10 (CCPA violation penalty)
```

All three inputs are **Min-Max normalised** to [0, 1] before weighting.

| Weight | Input | Rationale |
|---|---|---|
| **45%** | Severity score (2–5) | Primary regulatory harm signal |
| **35%** | Price inflation % | Direct financial loss to consumer |
| **20%** | Hidden fee ₹ | Sparse (9% of listings) but severe when present |
| **+10 pts** | CCPA violation | Flat regulatory penalty — creates minimum floor of 10.3 |

### Risk Tiers

| Tier | Score Range | Listings | % |
|---|---|---|---|
| 🔴 Critical | ≥ 80 | 57 | 0.7% |
| 🟠 High | 65–79 | 936 | 11.9% |
| 🟡 Medium | 50–64 | 1,903 | 24.3% |
| 🟢 Low | < 50 | 4,950 | 63.1% |

### Platform Rankings (by Harm Score)

| Rank | Platform | Mean Harm Score | Critical % | Total Consumer Loss |
|---|---|---|---|---|
| 🥇 1 | **Flipkart** | 46.34 | 1.5% | ₹34.1L |
| 🥈 2 | Nykaa | 45.69 | 0.5% | ₹30.6L |
| 🥉 3 | Meesho | 45.29 | 0.1% | ₹34.9L |

### Pattern Type Rankings (by Harm Score)

| Rank | Pattern Type | Harm Score | Severity | Avg Inflation ₹ |
|---|---|---|---|---|
| 🔴 #1 | **Hidden Convenience Fee** | **70.35** | 5/5 | ₹1,223 |
| 🔴 #2 | **Inflated Original Price** | **61.37** | 5/5 | ₹1,267 |
| 🟡 #3 | Forced Continuity | 48.07 | 4/5 | ₹1,240 |
| 🟡 #4 | False Scarcity | 48.04 | 4/5 | ₹1,302 |
| 🟡 #5 | Misleading Discount Badge | 47.76 | 4/5 | ₹1,327 |
| 🟢 #6 | Fake Countdown Timer | 34.48 | 3/5 | ₹1,207 |
| 🟢 #7 | Confirm Shaming | 34.46 | 3/5 | ₹1,259 |
| 🟢 #8 | Social Proof Manipulation | 20.70 | 2/5 | ₹1,333 |

> ⚠️ **Model insight:** Social Proof Manipulation ranks #8 by harm score (severity 2/5) but has the **highest average ₹ inflation (₹1,333)**. Low-severity patterns can still cause large financial harm when deployed on high-price products. This reveals a gap in purely severity-based regulatory frameworks.

---

## 🗄️ SQL Highlights

Four production queries with CTEs, window functions, and LAG-based YoY analysis:

### Q1 — Highest Dark Pattern Rate by Platform & Year
```sql
SELECT platform, year,
    ROUND(dark_pattern_rate_pct, 2) AS violation_rate_pct,
    RANK() OVER (ORDER BY dark_pattern_rate_pct DESC) AS overall_rank,
    CASE WHEN year >= 2023 THEN 'Post-CCPA' ELSE 'Pre-CCPA' END AS ccpa_era
FROM platform_summary
ORDER BY dark_pattern_rate_pct DESC;
-- Result: Meesho 2025 leads at 79.6% | Meesho holds all top-5 slots
```

### Q4 — YoY CCPA Violation Change (key finding)
```sql
WITH yearly AS (
    SELECT year,
        SUM(CASE WHEN ccpa_violation='Yes' THEN 1 ELSE 0 END) AS violations,
        ROUND(100.0 * SUM(CASE WHEN ccpa_violation='Yes' THEN 1 ELSE 0 END)
              / COUNT(*), 2) AS violation_rate_pct
    FROM listings_raw GROUP BY year
)
SELECT year,
    violations,
    violation_rate_pct,
    violations - LAG(violations) OVER (ORDER BY year) AS yoy_delta,
    CASE WHEN year >= 2023 THEN 'Post-CCPA' ELSE 'Pre-CCPA' END AS era
FROM yearly ORDER BY year;
-- Result: Rate went UP in 2023 (73.75%) — CCPA had zero measurable effect
```

*See `sql/` folder for all 4 full queries with CTEs, RANK(), LAG(), PARTITION BY, and bonus sub-queries.*

---

## 📈 Power BI Dashboard — 4 Pages

| Page | Key Visuals | Primary Insight |
|---|---|---|
| **Executive Overview** | 6 KPI cards, YoY bar+line chart, violation donut, platform scorecard | 73.21% violation rate — consistent across all 5 years |
| **Platform Deep Dive** | Rate by year grid, 100% stacked severity bar, overcharge bars | Meesho worst; all platforms near-identical severity mix |
| **Pattern Type Analysis** | Harm score bars, severity vs inflation scatter, ranking table | Hidden Fee + Inflated Price are the critical-risk patterns |
| **Category Heatmap** | 8×8 matrix (conditional format), category loss bars | Mobile Phones = highest ₹ loss; Toys = highest instance count |

**DAX measures include:** `[Violation Rate %]`, `[YoY Rate Change pp]`, `[Platform Violation Rank]`, `[CCPA Impact pp]`, `[Avg Harm Score]`, `[% Critical Risk]`, `[Dynamic Title Platform]`, and 37 more.

---

## 🔬 Analytical Approach

```
Raw Data (5 CSVs)
      │
      ▼
Step 1: Validation     → schema checks, null analysis, domain rules,
                          cross-file consistency (7,846 rows match exactly)
      │
      ▼
Step 2: Python EDA     → 8 charts covering YoY trends, platform comparison,
                          category heatmap, severity distribution, price inflation
      │
      ▼
Step 3: Scoring Model  → Min-Max normalisation, weighted composite score,
                          CCPA penalty, risk tier classification, 4 ranking tables
      │
      ▼
Step 4: SQL Analysis   → 4 production queries with CTEs, window functions,
                          LAG-based YoY analysis, pre/post-CCPA comparison
      │
      ▼
Step 5: Power BI       → 4-page dashboard, 44 DAX measures, cross-filtering,
                          bookmarks, conditional formatting, dynamic titles
```

---

## 📚 References & Context

- [CCPA Dark Patterns Guidelines, 2023](https://consumeraffairs.nic.in/sites/default/files/file-uploads/latestnews/Guidelines%20for%20Prevention%20and%20Regulation%20of%20Dark%20Patterns%2C%202023.pdf) — Government of India
- [EU Dark Patterns Guidelines — Digital Services Act, 2022](https://ec.europa.eu/commission/presscorner/detail/en/ip_22_2545)
- Gray, C. M., et al. (2018). *The Dark (Patterns) Side of UX Design.* CHI Conference on Human Factors in Computing Systems.
- Mathur, A., et al. (2019). *Dark Patterns at Scale: Findings from a Crawl of 11K Shopping Websites.* ACM CSCW.

---

## 🧠 What I Learned

- **Data modelling at scale:** Managing 5 interrelated tables, derived columns, and cross-file consistency checks in a production-style workflow
- **Weighted scoring model design:** Balancing sparse features (hidden fees, 9% coverage) with dense features — and documenting the design rationale
- **SQL window functions in practice:** Using `LAG()`, `RANK()`, `PARTITION BY` to answer real analytical questions, not just syntax exercises
- **Power BI DAX patterns:** Time intelligence without a date table, dynamic titles with `SELECTEDVALUE`, conditional colour coding with `RANKX`
- **Communicating null data:** The 2,871 nulls in `dark_pattern_type` *are* the story (non-violation rows) — learning to explain data absence as a feature, not a bug

---

## 👤 About

**Ajay Patel**
Data Analyst | 2.5 years experience in Python · SQL · Power BI · Excel

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/ajay-patel-006may)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/Ajaypatel06)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-27AE60?style=flat)](https://YOUR_PORTFOLIO_URL)

---

## 📄 License

This project is released under the [MIT License](LICENSE).
Data is synthetic/anonymised and generated for portfolio demonstration purposes.

---

<div align="center">
  <sub>Built with Python · SQL · Power BI | Dark Pattern Detector © 2025</sub>
</div>
