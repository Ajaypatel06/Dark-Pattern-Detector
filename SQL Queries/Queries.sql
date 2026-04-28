
CREATE DATABASE dark_pattern_analysis;
USE dark_pattern_analysis;


-- ============================================================
-- QUERY 1: Dark Pattern Rate by Platform & Year
-- ============================================================

SELECT
    ps.platform,
    ps.year,
    ps.total_listings,
    ps.listings_with_dark_pattern,
    
    ROUND(COALESCE(ps.dark_pattern_rate_pct, 0), 2) AS violation_rate_pct,
    ps.avg_severity,
    ROUND(COALESCE(ps.avg_price_inflation_inr, 0), 0) AS avg_inflation_inr,
    COALESCE(ps.total_consumer_overcharge_inr, 0) AS total_consumer_overcharge_inr,

    DENSE_RANK() OVER (ORDER BY ps.dark_pattern_rate_pct DESC) AS overall_rank,

    DENSE_RANK() OVER (
        PARTITION BY ps.platform
        ORDER BY ps.dark_pattern_rate_pct DESC
    ) AS platform_rank,

    CASE
        WHEN ps.dark_pattern_rate_pct >
             AVG(ps.dark_pattern_rate_pct) OVER (PARTITION BY ps.platform)
        THEN 'Above Avg'
        WHEN ps.dark_pattern_rate_pct =
             AVG(ps.dark_pattern_rate_pct) OVER (PARTITION BY ps.platform)
        THEN 'At Avg'
        ELSE 'Below Avg'
    END AS vs_platform_avg,

    CASE
        WHEN ps.year >= 2023 THEN 'Post-CCPA'
        ELSE 'Pre-CCPA'
    END AS ccpa_phase

FROM platform_summary ps
ORDER BY violation_rate_pct DESC;


-- ============================================================
-- QUERY 2: Top 3 Most Harmful Categories (Consumer Loss)
-- ============================================================

WITH violation_listings AS (
    SELECT *
    FROM listings_raw
    WHERE ccpa_violation = 'Yes'
),

category_metrics AS (
    SELECT
        vl.category,
        COUNT(*) AS total_violations,

        ROUND(AVG(vl.severity_score), 2) AS avg_severity,

        SUM(COALESCE(vl.price_inflation_inr, 0)) AS total_inflation_loss_inr,
        ROUND(AVG(vl.price_inflation_inr), 2) AS avg_inflation_inr,

        ROUND(
            AVG(
                CASE 
                    WHEN vl.actual_price_inr > 0 
                    THEN (vl.price_inflation_inr / vl.actual_price_inr) * 100
                    ELSE 0
                END
            ), 2
        ) AS avg_inflation_pct,

        MAX(vl.price_inflation_inr) AS max_inflation_inr,

        SUM(CASE WHEN vl.hidden_fee_inr > 0 THEN 1 ELSE 0 END) AS listings_with_hidden_fees,
        SUM(COALESCE(vl.hidden_fee_inr, 0)) AS total_hidden_fees_inr,

        SUM(COALESCE(vl.price_inflation_inr, 0)) 
        + SUM(COALESCE(vl.hidden_fee_inr, 0)) AS total_consumer_loss_inr,

        ROUND(
            100 * SUM(CASE WHEN vl.severity_score = 5 THEN 1 ELSE 0 END) 
            / NULLIF(COUNT(*), 0),
            1
        ) AS pct_critical_severity

    FROM violation_listings vl
    GROUP BY vl.category
),

ranked AS (
    SELECT
        cm.*,

        DENSE_RANK() OVER (
            ORDER BY cm.total_consumer_loss_inr DESC
        ) AS harm_rank,

        ROUND(
            100 * cm.total_consumer_loss_inr
            / SUM(cm.total_consumer_loss_inr) OVER (),
            1
        ) AS pct_of_total_loss

    FROM category_metrics cm
)

SELECT *
FROM ranked
ORDER BY harm_rank
LIMIT 3;


-- ============================================================
-- QUERY 3: All Categories Ranking
-- ============================================================

WITH violation_listings AS (
    SELECT *
    FROM listings_raw
    WHERE ccpa_violation = 'Yes'
),

category_metrics AS (
    SELECT
        vl.category,
        COUNT(*) AS total_violations,

        SUM(COALESCE(vl.price_inflation_inr, 0)) 
        + SUM(COALESCE(vl.hidden_fee_inr, 0)) AS total_consumer_loss_inr,

        ROUND(AVG(vl.severity_score), 2) AS avg_severity,

        ROUND(
            100 * SUM(CASE WHEN vl.severity_score = 5 THEN 1 ELSE 0 END) 
            / NULLIF(COUNT(*), 0),
            1
        ) AS pct_critical_severity

    FROM violation_listings vl
    GROUP BY vl.category
),

ranked AS (
    SELECT
        cm.*,
        DENSE_RANK() OVER (ORDER BY cm.total_consumer_loss_inr DESC) AS harm_rank
    FROM category_metrics cm
)

SELECT *
FROM ranked
ORDER BY harm_rank;


-- ============================================================
-- QUERY 4: Price Inflation by Dark Pattern Type
-- ============================================================

WITH violation_listings AS (
    SELECT
        lr.*,
        ROUND(
            CASE 
                WHEN lr.actual_price_inr > 0
                THEN (lr.price_inflation_inr / lr.actual_price_inr) * 100
                ELSE 0
            END,
            2
        ) AS price_inflation_pct
    FROM listings_raw lr
    WHERE lr.ccpa_violation = 'Yes'
      AND lr.dark_pattern_type IS NOT NULL
),

pattern_inflation AS (
    SELECT
        dark_pattern_type,
        COUNT(*) AS listing_count,

        ROUND(AVG(COALESCE(price_inflation_inr, 0)), 2) AS avg_inflation_inr,
        MIN(price_inflation_inr) AS min_inflation_inr,
        MAX(price_inflation_inr) AS max_inflation_inr,
        SUM(price_inflation_inr) AS total_inflation_inr,

        ROUND(AVG(price_inflation_pct), 2) AS avg_inflation_pct,
        ROUND(AVG(severity_score), 2) AS avg_severity,

        SUM(CASE WHEN hidden_fee_inr > 0 THEN 1 ELSE 0 END) AS hidden_fee_listing_count

    FROM violation_listings
    GROUP BY dark_pattern_type
)

SELECT
    *,
    DENSE_RANK() OVER (ORDER BY avg_inflation_inr DESC) AS rank_by_avg_inr,
    DENSE_RANK() OVER (ORDER BY avg_inflation_pct DESC) AS rank_by_avg_pct,

    ROUND(
        100 * total_inflation_inr / SUM(total_inflation_inr) OVER (),
        1
    ) AS pct_of_total_inflation

FROM pattern_inflation
ORDER BY avg_inflation_inr DESC;


-- ============================================================
-- QUERY 5: Inflation % Buckets per Pattern
-- ============================================================

WITH violation_listings AS (
    SELECT
        lr.*,
        ROUND(
            CASE 
                WHEN lr.actual_price_inr > 0
                THEN (lr.price_inflation_inr / lr.actual_price_inr) * 100
                ELSE 0
            END,
            2
        ) AS price_inflation_pct
    FROM listings_raw lr
    WHERE lr.ccpa_violation = 'Yes'
      AND lr.dark_pattern_type IS NOT NULL
)

SELECT
    dark_pattern_type,

    SUM(CASE WHEN price_inflation_pct < 50 THEN 1 ELSE 0 END) AS under_50pct,
    SUM(CASE WHEN price_inflation_pct BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS btw_50_100pct,
    SUM(CASE WHEN price_inflation_pct BETWEEN 100 AND 149 THEN 1 ELSE 0 END) AS btw_100_150pct,
    SUM(CASE WHEN price_inflation_pct >= 150 THEN 1 ELSE 0 END) AS over_150pct,

    COUNT(*) AS total

FROM violation_listings
GROUP BY dark_pattern_type
ORDER BY dark_pattern_type;


-- ============================================================
-- QUERY 6: Year-on-Year Violation Trend (Overall)
-- ============================================================

WITH yearly_counts AS (
    SELECT
        year,
        COUNT(*) AS total_listings,
        SUM(CASE WHEN ccpa_violation = 'Yes' THEN 1 ELSE 0 END) AS violations
    FROM listings_raw
    GROUP BY year
),

yoy_overall AS (
    SELECT
        year,
        total_listings,
        violations,

        ROUND(100 * violations / total_listings, 2) AS violation_rate_pct,

        violations - LAG(violations) OVER (ORDER BY year) AS yoy_violation_delta,

        ROUND(
            (100 * violations / total_listings)
            - LAG(100 * violations / total_listings) OVER (ORDER BY year),
            2
        ) AS yoy_rate_delta_pts

    FROM yearly_counts
)

SELECT *
FROM yoy_overall
ORDER BY year;


-- ============================================================
-- QUERY 7: Platform-wise YoY Trend
-- ============================================================

WITH platform_yearly AS (
    SELECT
        platform,
        year,
        COUNT(*) AS total_listings,
        SUM(CASE WHEN ccpa_violation = 'Yes' THEN 1 ELSE 0 END) AS violations,

        ROUND(
            100 * SUM(CASE WHEN ccpa_violation = 'Yes' THEN 1 ELSE 0 END) / COUNT(*),
            2
        ) AS violation_rate_pct

    FROM listings_raw
    GROUP BY platform, year
)

SELECT
    platform,
    year,
    total_listings,
    violations,
    violation_rate_pct,

    violations - LAG(violations)
        OVER (PARTITION BY platform ORDER BY year) AS yoy_violation_delta,

    ROUND(
        violation_rate_pct
        - LAG(violation_rate_pct)
          OVER (PARTITION BY platform ORDER BY year),
        2
    ) AS yoy_rate_delta_pts

FROM platform_yearly
ORDER BY platform, year;


-- ============================================================
-- QUERY 8: Pre vs Post CCPA Comparison
-- ============================================================

SELECT
    platform,

    CASE 
        WHEN year >= 2023 THEN 'Post-CCPA (2023–2025)'
        ELSE 'Pre-CCPA (2021–2022)'
    END AS era,

    SUM(total_listings) AS total_listings,
    SUM(violations) AS total_violations,

    ROUND(
        100 * SUM(violations) / SUM(total_listings),
        2
    ) AS avg_violation_rate_pct

FROM (
    SELECT
        platform,
        year,
        COUNT(*) AS total_listings,
        SUM(CASE WHEN ccpa_violation = 'Yes' THEN 1 ELSE 0 END) AS violations
    FROM listings_raw
    GROUP BY platform, year
) sub

GROUP BY platform,
         CASE 
             WHEN year >= 2023 THEN 'Post-CCPA (2023–2025)'
             ELSE 'Pre-CCPA (2021–2022)'
         END

ORDER BY platform, era DESC;