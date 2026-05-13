import pandas as pd
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
RAW_PATH = "data/raw"
DOCS_PATH = "docs"
LOG_FILE  = os.path.join(DOCS_PATH, "profiling_report.txt")

FILES = {
    "customers"   : "olist_customers_dataset.csv",
    "geolocation" : "olist_geolocation_dataset.csv",
    "order_items" : "olist_order_items_dataset.csv",
    "payments"    : "olist_order_payments_dataset.csv",
    "reviews"     : "olist_order_reviews_dataset.csv",
    "orders"      : "olist_orders_dataset.csv",
    "products"    : "olist_products_dataset.csv",
    "sellers"     : "olist_sellers_dataset.csv",
    "category_translation" : "product_category_name_translation.csv",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def separator(title=""):
    line = "=" * 60
    return f"\n{line}\n  {title}\n{line}" if title else f"\n{line}"

def profile_dataframe(name, df):
    lines = []
    lines.append(separator(f"TABLE: {name.upper()}"))
    lines.append(f"  Rows        : {df.shape[0]:,}")
    lines.append(f"  Columns     : {df.shape[1]}")
    lines.append(f"  Duplicates  : {df.duplicated().sum():,}")
    lines.append("\n  --- Column Detail ---")

    for col in df.columns:
        null_count  = df[col].isna().sum()
        null_pct    = (null_count / len(df)) * 100
        unique_vals = df[col].nunique()
        dtype       = str(df[col].dtype)

        flag = ""
        if null_pct > 20:
            flag = "  ⚠ HIGH NULLS"
        elif null_pct > 0:
            flag = "  ← has nulls"

        lines.append(
            f"  {col:<45} dtype: {dtype:<10} "
            f"nulls: {null_count:>6,} ({null_pct:>5.1f}%)  "
            f"unique: {unique_vals:>7,}{flag}"
        )

    return "\n".join(lines)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(DOCS_PATH, exist_ok=True)
    report_lines = []

    header = (
        f"OrdersPlus — Data Profiling Report\n"
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Raw path  : {os.path.abspath(RAW_PATH)}"
    )
    report_lines.append(separator())
    report_lines.append(header)
    report_lines.append(separator())

    summary_rows = []

    for name, filename in FILES.items():
        filepath = os.path.join(RAW_PATH, filename)

        if not os.path.exists(filepath):
            msg = f"  [MISSING] {filename}"
            print(msg)
            report_lines.append(msg)
            continue

        df = pd.read_csv(filepath)
        profile = profile_dataframe(name, df)
        report_lines.append(profile)

        total_nulls = df.isna().sum().sum()
        summary_rows.append({
            "table"      : name,
            "rows"       : df.shape[0],
            "columns"    : df.shape[1],
            "duplicates" : df.duplicated().sum(),
            "total_nulls": total_nulls,
        })

        print(f"  ✓ Profiled  →  {name:<25} {df.shape[0]:>7,} rows  |  {df.shape[1]} cols  |  nulls: {total_nulls:,}")

    # Summary table
    report_lines.append(separator("SUMMARY"))
    summary_df = pd.DataFrame(summary_rows)
    report_lines.append(summary_df.to_string(index=False))

    report_lines.append(separator("END OF REPORT"))

    # Write report
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n  Report saved → {LOG_FILE}\n")

if __name__ == "__main__":
    main()