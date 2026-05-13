import pandas as pd
import os
import logging
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
RAW_PATH       = "data/raw"
PROCESSED_PATH = "data/processed"
LOG_FILE       = "docs/cleaning_log.txt"

os.makedirs(PROCESSED_PATH, exist_ok=True)
os.makedirs("docs", exist_ok=True)

# ── Logger ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s  %(levelname)s  %(message)s",
    handlers = [
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("OrdersPlus.Cleaner")

def log_shape(name, before, after):
    dropped = before - after
    log.info(f"{name:<25} {before:>7,} → {after:>7,} rows  (dropped {dropped:,})")

# ── Cleaners ──────────────────────────────────────────────────────────────────

def clean_customers():
    name = "customers"
    df = pd.read_csv(f"{RAW_PATH}/olist_customers_dataset.csv")
    before = len(df)
    df.drop_duplicates(inplace=True)
    log_shape(name, before, len(df))
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_geolocation():
    name = "geolocation"
    df = pd.read_csv(f"{RAW_PATH}/olist_geolocation_dataset.csv")
    before = len(df)

    # Keep one row per zip code — average lat/lng
    df = (
        df.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg({
            "geolocation_lat"   : "mean",
            "geolocation_lng"   : "mean",
            "geolocation_city"  : "first",
            "geolocation_state" : "first",
        })
    )
    log_shape(name, before, len(df))
    log.info(f"  Decision: kept 1 row per zip code (avg lat/lng) — removed {before - len(df):,} duplicates")
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_order_items():
    name = "order_items"
    df = pd.read_csv(f"{RAW_PATH}/olist_order_items_dataset.csv")
    before = len(df)

    # Parse date column
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"])

    # Sanity check: no negative prices
    invalid_price = df[df["price"] <= 0]
    if len(invalid_price) > 0:
        log.warning(f"  {len(invalid_price)} rows with price <= 0 found — dropping")
        df = df[df["price"] > 0]

    log_shape(name, before, len(df))
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_payments():
    name = "payments"
    df = pd.read_csv(f"{RAW_PATH}/olist_order_payments_dataset.csv")
    before = len(df)
    df.drop_duplicates(inplace=True)
    log_shape(name, before, len(df))
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_reviews():
    name = "reviews"
    df = pd.read_csv(f"{RAW_PATH}/olist_order_reviews_dataset.csv")
    before = len(df)

    # Fill text nulls with empty string — nulls just mean no comment written
    df["review_comment_title"]   = df["review_comment_title"].fillna("")
    df["review_comment_message"] = df["review_comment_message"].fillna("")

    # Parse dates
    df["review_creation_date"]    = pd.to_datetime(df["review_creation_date"])
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"])

    log_shape(name, before, len(df))
    log.info(f"  Decision: filled comment nulls with empty string — not dropped (no comment ≠ bad data)")
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_orders():
    name = "orders"
    df = pd.read_csv(f"{RAW_PATH}/olist_orders_dataset.csv")
    before = len(df)

    # Parse all date columns
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col])

    # Add derived column: was order delivered late?
    delivered = df["order_delivered_customer_date"].notna()
    df["is_late_delivery"] = (
        delivered &
        (df["order_delivered_customer_date"] > df["order_estimated_delivery_date"])
    ).astype(int)

    late_count = df["is_late_delivery"].sum()
    log.info(f"  Derived column added: is_late_delivery — {late_count:,} late orders ({late_count/len(df)*100:.1f}%)")

    # Add delivery days column
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days

    log_shape(name, before, len(df))
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_products():
    name = "products"
    df = pd.read_csv(f"{RAW_PATH}/olist_products_dataset.csv")
    before = len(df)

    # Fill category nulls with 'unknown'
    df["product_category_name"] = df["product_category_name"].fillna("unknown")
    log.info(f"  Decision: filled 610 category nulls with 'unknown'")

    # Fill physical dimension nulls with median
    dim_cols = [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    for col in dim_cols:
        median_val = df[col].median()
        null_count = df[col].isna().sum()
        if null_count > 0:
            df[col] = df[col].fillna(median_val)
            log.info(f"  Filled {null_count} nulls in {col} with median ({median_val})")

    log_shape(name, before, len(df))
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_sellers():
    name = "sellers"
    df = pd.read_csv(f"{RAW_PATH}/olist_sellers_dataset.csv")
    before = len(df)
    df.drop_duplicates(inplace=True)
    log_shape(name, before, len(df))
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


def clean_category_translation():
    name = "category_translation"
    df = pd.read_csv(f"{RAW_PATH}/product_category_name_translation.csv")
    before = len(df)
    df.drop_duplicates(inplace=True)
    log_shape(name, before, len(df))
    df.to_csv(f"{PROCESSED_PATH}/{name}.csv", index=False)
    log.info(f"  Saved → {name}.csv")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("OrdersPlus — Data Cleaning Pipeline")
    log.info(f"Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    clean_customers()
    clean_geolocation()
    clean_order_items()
    clean_payments()
    clean_reviews()
    clean_orders()
    clean_products()
    clean_sellers()
    clean_category_translation()

    log.info("=" * 60)
    log.info("All tables cleaned and saved to data/processed/")
    log.info("=" * 60)

if __name__ == "__main__":
    main()