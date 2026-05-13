import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME     = os.getenv("DB_NAME")

PROCESSED_PATH = "data/processed"
LOG_FILE       = "docs/db_setup_log.txt"

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
log = logging.getLogger("OrdersPlus.DBSetup")

# ── Create database if not exists ─────────────────────────────────────────────
def create_database():
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}",
        echo=False
    )
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
        conn.execute(text(f"USE {DB_NAME}"))
    log.info(f"Database '{DB_NAME}' ready")
    engine.dispose()

# ── Table DDL ─────────────────────────────────────────────────────────────────
DDL_STATEMENTS = """
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS geolocation;
DROP TABLE IF EXISTS category_translation;

CREATE TABLE customers (
    customer_id              VARCHAR(50)  PRIMARY KEY,
    customer_unique_id       VARCHAR(50)  NOT NULL,
    customer_zip_code_prefix INT,
    customer_city            VARCHAR(100),
    customer_state           CHAR(2)
);

CREATE TABLE geolocation (
    geolocation_zip_code_prefix INT,
    geolocation_lat             DECIMAL(10,6),
    geolocation_lng             DECIMAL(10,6),
    geolocation_city            VARCHAR(100),
    geolocation_state           CHAR(2)
);

CREATE TABLE sellers (
    seller_id              VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix INT,
    seller_city            VARCHAR(100),
    seller_state           CHAR(2)
);

CREATE TABLE category_translation (
    product_category_name         VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100)
);

CREATE TABLE products (
    product_id                   VARCHAR(50) PRIMARY KEY,
    product_category_name        VARCHAR(100),
    product_name_lenght          FLOAT,
    product_description_lenght   FLOAT,
    product_photos_qty           FLOAT,
    product_weight_g             FLOAT,
    product_length_cm            FLOAT,
    product_height_cm            FLOAT,
    product_width_cm             FLOAT
);

CREATE TABLE orders (
    order_id                        VARCHAR(50) PRIMARY KEY,
    customer_id                     VARCHAR(50),
    order_status                    VARCHAR(30),
    order_purchase_timestamp        DATETIME,
    order_approved_at               DATETIME,
    order_delivered_carrier_date    DATETIME,
    order_delivered_customer_date   DATETIME,
    order_estimated_delivery_date   DATETIME,
    is_late_delivery                TINYINT DEFAULT 0,
    delivery_days                   FLOAT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_id             VARCHAR(50),
    order_item_id        INT,
    product_id           VARCHAR(50),
    seller_id            VARCHAR(50),
    shipping_limit_date  DATETIME,
    price                DECIMAL(10,2),
    freight_value        DECIMAL(10,2),
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id)  REFERENCES sellers(seller_id)
);

CREATE TABLE payments (
    order_id             VARCHAR(50),
    payment_sequential   INT,
    payment_type         VARCHAR(30),
    payment_installments INT,
    payment_value        DECIMAL(10,2),
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE reviews (
    review_id               VARCHAR(50),
    order_id                VARCHAR(50),
    review_score            INT,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    DATETIME,
    review_answer_timestamp DATETIME,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
"""

def create_tables(engine):
    with engine.connect() as conn:
        for statement in DDL_STATEMENTS.strip().split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()
    log.info("All tables created successfully")

# ── Load CSVs into MySQL ───────────────────────────────────────────────────────
LOAD_ORDER = [
    ("customers",            "customers.csv"),
    ("geolocation",          "geolocation.csv"),
    ("sellers",              "sellers.csv"),
    ("category_translation", "category_translation.csv"),
    ("products",             "products.csv"),
    ("orders",               "orders.csv"),
    ("order_items",          "order_items.csv"),
    ("payments",             "payments.csv"),
    ("reviews",              "reviews.csv"),
]

def load_tables(engine):
    for table_name, filename in LOAD_ORDER:
        filepath = os.path.join(PROCESSED_PATH, filename)
        df = pd.read_csv(filepath)

        # Let pandas handle datetime parsing naturally
        df.to_sql(
            name        = table_name,
            con         = engine,
            if_exists   = "append",
            index       = False,
            chunksize   = 1000,
        )
        log.info(f"  Loaded {len(df):>7,} rows → {table_name}")

# ── Verify row counts ─────────────────────────────────────────────────────────
def verify_counts(engine):
    tables = [t for t, _ in LOAD_ORDER]
    log.info("── Verification ──────────────────────────────────────")
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count  = result.scalar()
            log.info(f"  {table:<25} {count:>8,} rows in MySQL")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("OrdersPlus — Database Setup")
    log.info(f"Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    create_database()

    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        echo=False
    )

    log.info("Creating tables...")
    create_tables(engine)

    log.info("Loading data...")
    load_tables(engine)

    verify_counts(engine)

    engine.dispose()
    log.info("=" * 60)
    log.info("Database setup complete")
    log.info("=" * 60)

if __name__ == "__main__":
    main()