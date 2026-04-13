from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "Dataset" / "startup_funding_cleaned.csv"
OUT_DIR = ROOT / "outputs" / "sql_duckdb"
OUT_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute(
    """
    CREATE OR REPLACE TABLE startup_funding_cleaned AS
    SELECT * FROM read_csv_auto(?, header=true);
    """,
    [str(CSV_PATH)],
)

queries = {
    "01_top10_sector_funding": """
        SELECT
            sector_clean,
            ROUND(SUM(amount_usd), 2) AS total_funding_usd,
            COUNT(*) AS total_deals
        FROM startup_funding_cleaned
        GROUP BY sector_clean
        ORDER BY total_funding_usd DESC
        LIMIT 10
    """,
    "02_top10_city_funding": """
        SELECT
            city_clean,
            ROUND(SUM(amount_usd), 2) AS total_funding_usd,
            COUNT(*) AS total_deals
        FROM startup_funding_cleaned
        GROUP BY city_clean
        ORDER BY total_funding_usd DESC
        LIMIT 10
    """,
    "03_yoy_sector_growth": """
        WITH sector_year AS (
            SELECT
                sector_clean,
                year AS deal_year,
                SUM(amount_usd) AS total_funding_usd
            FROM startup_funding_cleaned
            GROUP BY sector_clean, year
        ),
        sector_growth AS (
            SELECT
                sector_clean,
                deal_year,
                total_funding_usd,
                LAG(total_funding_usd) OVER (
                    PARTITION BY sector_clean ORDER BY deal_year
                ) AS prev_year_funding
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
        ORDER BY sector_clean, deal_year
    """,
    "04_avg_deal_size_by_stage": """
        SELECT
            stage_clean,
            ROUND(AVG(amount_usd), 2) AS avg_deal_size_usd,
            COUNT(*) AS total_deals
        FROM startup_funding_cleaned
        GROUP BY stage_clean
        ORDER BY avg_deal_size_usd DESC
    """,
    "05_top10_investors_by_deals": """
        WITH investor_split AS (
            SELECT
                "Sr No" AS sr_no,
                TRIM(UNNEST(STRING_SPLIT(COALESCE(investors, ''), ','))) AS investor
            FROM startup_funding_cleaned
        )
        SELECT
            investor,
            COUNT(DISTINCT sr_no) AS deals_count
        FROM investor_split
        WHERE investor <> ''
        GROUP BY investor
        ORDER BY deals_count DESC
        LIMIT 10
    """,
    "06_sector_largest_avg_deal": """
        SELECT
            sector_clean,
            ROUND(AVG(amount_usd), 2) AS avg_deal_size_usd,
            COUNT(*) AS total_deals
        FROM startup_funding_cleaned
        GROUP BY sector_clean
        HAVING COUNT(*) >= 5
        ORDER BY avg_deal_size_usd DESC
        LIMIT 1
    """,
}

for name, sql in queries.items():
    df = con.execute(sql).fetchdf()
    out_path = OUT_DIR / f"{name}.csv"
    df.to_csv(out_path, index=False)
    print(f"{name}: {len(df)} rows -> {out_path}")

print("All SQL analyses executed successfully in DuckDB.")
