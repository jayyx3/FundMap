USE fundmap;

-- 1) Total funding by sector - top 10
SELECT
    sector_clean,
    ROUND(SUM(amount_usd), 2) AS total_funding_usd,
    COUNT(*) AS total_deals
FROM startup_funding_cleaned
GROUP BY sector_clean
ORDER BY total_funding_usd DESC
LIMIT 10;

-- 2) Total funding by city - top 10
SELECT
    city_clean,
    ROUND(SUM(amount_usd), 2) AS total_funding_usd,
    COUNT(*) AS total_deals
FROM startup_funding_cleaned
GROUP BY city_clean
ORDER BY total_funding_usd DESC
LIMIT 10;

-- 3) Year-over-year funding growth by sector
WITH sector_year AS (
    SELECT
        sector_clean,
        deal_year,
        SUM(amount_usd) AS total_funding_usd
    FROM startup_funding_cleaned
    GROUP BY sector_clean, deal_year
),
sector_growth AS (
    SELECT
        sector_clean,
        deal_year,
        total_funding_usd,
        LAG(total_funding_usd) OVER (PARTITION BY sector_clean ORDER BY deal_year) AS prev_year_funding
    FROM sector_year
)
SELECT
    sector_clean,
    deal_year,
    ROUND(total_funding_usd, 2) AS total_funding_usd,
    ROUND(prev_year_funding, 2) AS prev_year_funding,
    ROUND(
        CASE
            WHEN prev_year_funding IS NULL OR prev_year_funding = 0 THEN NULL
            ELSE (total_funding_usd - prev_year_funding) * 100.0 / prev_year_funding
        END,
        2
    ) AS yoy_growth_pct
FROM sector_growth
ORDER BY sector_clean, deal_year;

-- 4) Average deal size by funding stage
SELECT
    stage_clean,
    ROUND(AVG(amount_usd), 2) AS avg_deal_size_usd,
    COUNT(*) AS total_deals
FROM startup_funding_cleaned
GROUP BY stage_clean
ORDER BY avg_deal_size_usd DESC;

-- 5) Top 10 most active investors by number of deals
-- Uses recursive split approach in MySQL 8+
WITH RECURSIVE investor_split AS (
    SELECT
        sr_no,
        TRIM(SUBSTRING_INDEX(investors, ',', 1)) AS investor,
        TRIM(SUBSTRING(investors, LENGTH(SUBSTRING_INDEX(investors, ',', 1)) + 2)) AS rest
    FROM startup_funding_cleaned
    WHERE investors IS NOT NULL AND investors <> ''

    UNION ALL

    SELECT
        sr_no,
        TRIM(SUBSTRING_INDEX(rest, ',', 1)) AS investor,
        TRIM(SUBSTRING(rest, LENGTH(SUBSTRING_INDEX(rest, ',', 1)) + 2)) AS rest
    FROM investor_split
    WHERE rest IS NOT NULL AND rest <> ''
)
SELECT
    investor,
    COUNT(DISTINCT sr_no) AS deals_count
FROM investor_split
WHERE investor <> ''
GROUP BY investor
ORDER BY deals_count DESC
LIMIT 10;

-- 6) Sector with largest average deal size
SELECT
    sector_clean,
    ROUND(AVG(amount_usd), 2) AS avg_deal_size_usd,
    COUNT(*) AS total_deals
FROM startup_funding_cleaned
GROUP BY sector_clean
HAVING COUNT(*) >= 5
ORDER BY avg_deal_size_usd DESC
LIMIT 1;
