CREATE DATABASE IF NOT EXISTS fundmap;
USE fundmap;

DROP TABLE IF EXISTS startup_funding_cleaned;

CREATE TABLE startup_funding_cleaned (
    sr_no INT,
    deal_date DATE,
    deal_year INT,
    startup_name VARCHAR(255),
    industry_vertical VARCHAR(255),
    sector_clean VARCHAR(100),
    sub_vertical VARCHAR(255),
    city_raw VARCHAR(255),
    city_clean VARCHAR(100),
    investors TEXT,
    investor_count INT,
    investment_type VARCHAR(100),
    stage_clean VARCHAR(50),
    amount_in_usd_raw VARCHAR(100),
    amount_usd DECIMAL(18, 2),
    amount_usd_mn DECIMAL(18, 3),
    remarks TEXT
);

-- Update path if needed. Use forward slashes on Windows for MySQL importer.
LOAD DATA LOCAL INFILE 'D:/PROJECTS/FundMap/Dataset/startup_funding_cleaned.csv'
INTO TABLE startup_funding_cleaned
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    sr_no,
    @deal_date,
    deal_year,
    startup_name,
    industry_vertical,
    sector_clean,
    sub_vertical,
    city_raw,
    city_clean,
    investors,
    investor_count,
    investment_type,
    stage_clean,
    amount_in_usd_raw,
    amount_usd,
    amount_usd_mn,
    remarks
)
SET deal_date = STR_TO_DATE(@deal_date, '%Y-%m-%d');
