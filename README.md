# 📦 OrdersPlus — E-Commerce Analytics Platform

> An end-to-end data analytics platform built on 100,000+ real Brazilian e-commerce transactions —
> covering the full pipeline from raw data ingestion to interactive business intelligence dashboard
> and 90-day revenue forecasting.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat&logo=mysql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Prophet](https://img.shields.io/badge/Prophet-Forecasting-0066CC?style=flat)
![Power BI](https://img.shields.io/badge/PowerBI-DAX-F2C811?style=flat&logo=powerbi&logoColor=black)
![Status](https://img.shields.io/badge/Status-Complete-2D6A4F?style=flat)

---

## 🎯 Business Problem

E-commerce companies lose revenue through three silent killers:
late deliveries that destroy customer trust, high-value customers
silently churning before anyone notices, and no visibility into
future revenue to plan inventory and marketing spend.

**OrdersPlus answers three questions a real e-commerce business
pays analysts to answer every week:**

1. Which customer segments are at risk of churning — and what is their revenue value?
2. Which states have critical delivery failures — and how does that impact review scores?
3. What will revenue look like over the next 90 days?

---

## 📊 Key Findings

| Finding | Metric | Business Impact |
|---|---|---|
| Late delivery destroys reviews | 2.57★ vs 4.29★ | 46.2% of late orders get 1★ — 7x higher than on-time |
| Retention crisis | 92% never return | 23,047 customers already lost — R$ 2.19M gone |
| High-value churn risk | 3,009 At Risk customers | Avg spend R$ 439 — highest of all segments |
| Delivery hotspot | AL state — 23.93% late | vs RO state — 2.88% late |
| Revenue forecast | R$ 3.19M next 90 days | +40% driven by Black Friday seasonality |
| Credit card dominance | 78.3% of revenue | Avg 3.51 installments — typical Brazilian behaviour |

---

## 🏗️ Architecture
![Overview](docs/pipeline.png)

## 📈 Dashboard Preview

### 📊 Business Overview
![Overview](docs/dashboard_overview.png)

### 🚚 Delivery Performance
![Delivery](docs/dashboard_delivery.png)

### 👥 Customer Intelligence
![Customers](docs/dashboard_customers.png)

### 📈 Revenue Forecast
![Forecast](docs/dashboard_forecast.png)

---

## 🔍 Analysis Highlights

### Late Delivery Impact
Late deliveries score **2.57★** vs **4.29★** for on-time orders.
**46.2%** of late orders receive a 1★ review — 7x higher than
on-time orders (6.6%). States AL (23.93%), MA (19.67%), and PI
(15.97%) require urgent logistics intervention.

### RFM Customer Segmentation
93,357 customers segmented using Recency, Frequency, and Monetary
scoring via SQL NTILE window functions:

| Segment | Customers | Avg Spend | Total Revenue |
|---|---|---|---|
| Champions | 1,159 | R$ 364 | R$ 421,936 |
| Loyal Customers | 36,312 | R$ 260 | R$ 9,456,285 |
| Promising | 22,168 | R$ 73 | R$ 1,607,263 |
| Needs Attention | 7,662 | R$ 55 | R$ 424,847 |
| At Risk | 3,009 | R$ 439 | R$ 1,321,913 |
| Lost | 23,047 | R$ 95 | R$ 2,190,217 |

### Cohort Retention
Average repeat purchase rate of **8.02%** across all cohorts —
meaning **92% of customers never make a second purchase**.
The business is entirely dependent on new customer acquisition.
A retention campaign targeting the At Risk segment (R$ 439 avg spend)
would yield the highest ROI.

### Prophet Forecasting
Trained on **611 days** of daily revenue data. Model detected:
- **Weekly seasonality** — Monday peak, Saturday/Sunday trough
- **Yearly seasonality** — Black Friday 2017 spike learned and
  projected into November 2018
- **90-day projection** — R$ 3.19M (95% CI: R$ 1.75M — R$ 4.62M)

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.11 |
| Data Cleaning | Pandas, NumPy |
| Database | MySQL 8.0, SQLAlchemy, PyMySQL |
| SQL | CTEs, Window Functions, LAG, RANK, NTILE |
| Analysis | Jupyter Notebook |
| Forecasting | Facebook Prophet |
| Visualisation | Matplotlib, Seaborn, Plotly |
| Dashboard | Streamlit |
| Version Control | Git, GitHub |

---

## 📁 Project Structure

![Overview](docs/structure.png)

## 🚀 How to Run Locally

**1. Clone the repository**
```bash
git clone https://github.com/YourUsername/OrdersPlus.git
cd OrdersPlus
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**3. Download the dataset**

Download from Kaggle:
👉 https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Place all 9 CSV files in `data/raw/`

**4. Configure database**

Create a `.env` file in the root folder:

**5. Run the pipeline**
```bash
python scripts/01_data_profiler.py
python scripts/02_data_cleaner.py
python scripts/03_db_setup.py
```

**6. Launch the dashboard**
```bash
streamlit run dashboard/app.py
```

---

## 📸 EDA Charts

| Chart | Insight |
|---|---|
| Monthly Revenue Trend | Consistent growth Oct 2016 → Aug 2018 |
| Top 10 Categories | Health & Beauty leads at R$ 1.23M |
| Late Delivery by State | AL worst (23.93%), RO best (2.88%) |
| Review vs Delivery | Late = 2.57★, On-time = 4.29★ |
| RFM Segments | 6 customer tiers by value and recency |
| Payment Analysis | Credit card 78.3%, avg 3.51 installments |
| Cohort Retention | 92% of customers never return |
| Prophet Forecast | R$ 3.19M projected next 90 days |
| Forecast Components | Monday peak, Black Friday seasonality |

---

## 👤 Author

**Harshal Kawane**
Data Analyst | Python • SQL • Power BI • Prophet

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/harshal-kawane/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/h4rshalk)
[![Kaggle](https://img.shields.io/badge/Kaggle-Profile-20BEFF?style=flat&logo=kaggle)](https://www.kaggle.com/h4rshal3)

---

*Built as an industry-grade portfolio project demonstrating
end-to-end data analytics — from raw data to business insights.*