from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "Dataset" / "startup_funding.csv"
CLEAN_PATH = ROOT / "Dataset" / "startup_funding_cleaned.csv"


CITY_MAP = {
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "delhi": "New Delhi",
    "new delhi": "New Delhi",
    "gurugram": "Gurgaon",
    "gurgaon": "Gurgaon",
    "pune": "Pune",
    "chennai": "Chennai",
    "hyderabad": "Hyderabad",
    "noida": "Noida",
    "faridabad": "Faridabad",
    "ahmedabad": "Ahmedabad",
    "kolkata": "Kolkata",
    "san francisco": "San Francisco",
}

SECTOR_KEYWORDS = {
    "fintech": "FinTech",
    "financial": "FinTech",
    "payment": "FinTech",
    "bank": "FinTech",
    "e-tech": "EdTech",
    "edtech": "EdTech",
    "e-learning": "EdTech",
    "education": "EdTech",
    "ecommerce": "E-Commerce",
    "e-commerce": "E-Commerce",
    "retail": "E-Commerce",
    "logistics": "Logistics",
    "transport": "Logistics",
    "mobility": "Logistics",
    "health": "HealthTech",
    "med": "HealthTech",
    "pharma": "HealthTech",
    "food": "FoodTech",
    "agri": "AgriTech",
    "agritech": "AgriTech",
    "software": "SaaS",
    "saas": "SaaS",
    "ai": "AI",
    "artificial intelligence": "AI",
    "gaming": "Gaming",
    "video": "Media",
    "media": "Media",
    "fashion": "Fashion",
    "travel": "Travel",
    "hospitality": "Travel",
    "real estate": "Real Estate",
    "aerospace": "Aerospace",
    "technology": "Technology",
    "tech": "Technology",
}

STAGE_RULES = [
    (r"seed|pre-seed|angel", "Seed"),
    (r"pre-series\s*a", "Pre-Series A"),
    (r"series\s*a", "Series A"),
    (r"series\s*b", "Series B"),
    (r"series\s*c|series\s*d|series\s*e|series\s*f|series\s*g|series\s*h|series\s*i", "Series B+"),
    (r"debt", "Debt"),
    (r"private equity", "Private Equity"),
]


def normalize_text(value: str) -> str:
    if pd.isna(value):
        return ""

    text = str(value)
    text = text.replace("\xa0", " ")
    text = re.sub(r"(?:\\+[xX][0-9a-fA-F]{2})+", " ", text)
    text = text.replace("\\", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_amount_to_usd(value: str) -> float:
    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()
    if text in {"", "undisclosed", "unknown", "n/a", "na", "-"}:
        return np.nan

    multiplier = 1.0
    if "cr" in text or "crore" in text:
        multiplier = 10_000_000
    elif "mn" in text or "million" in text:
        multiplier = 1_000_000
    elif "bn" in text or "billion" in text:
        multiplier = 1_000_000_000

    numeric = re.sub(r"[^0-9.]", "", text)
    if not numeric:
        return np.nan

    return float(numeric) * multiplier


def standardize_city(city: str) -> str:
    if pd.isna(city):
        return "Unknown"

    clean_city = normalize_text(city)
    base = re.sub(r"[^a-zA-Z\s]", "", clean_city).strip().lower()
    if not base:
        return "Unknown"
    return CITY_MAP.get(base, clean_city.title())


def standardize_sector(sector: str) -> str:
    if pd.isna(sector):
        return "Other"

    clean_sector = normalize_text(sector)
    if not clean_sector:
        return "Other"

    text = clean_sector.lower()
    compact = text.replace(" ", "")
    for keyword, canonical in SECTOR_KEYWORDS.items():
        if keyword in text or keyword.replace(" ", "") in compact:
            return canonical

    return clean_sector.title()


def standardize_stage(stage: str) -> str:
    if pd.isna(stage):
        return "Other"

    clean_stage = normalize_text(stage)
    if not clean_stage:
        return "Other"

    text = clean_stage.lower()
    for pattern, canonical in STAGE_RULES:
        if re.search(pattern, text):
            return canonical

    if "series" in text:
        return "Series B+"

    return clean_stage.title()


def build_clean_dataset() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    df.columns = [c.strip() for c in df.columns]

    rename_map = {
        "Date dd/mm/yyyy": "date",
        "Startup Name": "startup_name",
        "Industry Vertical": "industry_vertical",
        "SubVertical": "sub_vertical",
        "City  Location": "city",
        "Investors Name": "investors",
        "InvestmentnType": "investment_type",
        "Amount in USD": "amount_in_usd_raw",
        "Remarks": "remarks",
    }
    df = df.rename(columns=rename_map)

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["year"] = df["date"].dt.year.astype("Int64")

    df["city_clean"] = df["city"].apply(standardize_city)
    df["sector_clean"] = df["industry_vertical"].apply(standardize_sector)
    df["stage_clean"] = df["investment_type"].apply(standardize_stage)

    df["amount_usd"] = df["amount_in_usd_raw"].apply(parse_amount_to_usd)
    median_by_sector = df.groupby("sector_clean")["amount_usd"].transform("median")
    df["amount_usd"] = df["amount_usd"].fillna(median_by_sector)
    df["amount_usd"] = df["amount_usd"].fillna(df["amount_usd"].median())

    df["amount_usd_mn"] = (df["amount_usd"] / 1_000_000).round(3)

    df["investor_count"] = (
        df["investors"]
        .fillna("")
        .apply(lambda x: len([i for i in re.split(r",|;|/", str(x)) if i.strip()]))
    )

    output_cols = [
        "Sr No",
        "date",
        "year",
        "startup_name",
        "industry_vertical",
        "sector_clean",
        "sub_vertical",
        "city",
        "city_clean",
        "investors",
        "investor_count",
        "investment_type",
        "stage_clean",
        "amount_in_usd_raw",
        "amount_usd",
        "amount_usd_mn",
        "remarks",
    ]

    return df[output_cols]


if __name__ == "__main__":
    clean_df = build_clean_dataset()
    clean_df.to_csv(CLEAN_PATH, index=False)

    print(f"Rows cleaned: {len(clean_df):,}")
    print(f"Saved cleaned dataset to: {CLEAN_PATH}")
    print(f"Date range: {int(clean_df['year'].min())} to {int(clean_df['year'].max())}")
