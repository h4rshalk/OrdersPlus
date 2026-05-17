import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import warnings
warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title    = "OrdersPlus Analytics",
    page_icon     = "📦",
    layout        = "wide",
    initial_sidebar_state = "expanded"
)

# ── DB Connection ─────────────────────────────────────────────
@st.cache_resource
def get_engine():
    load_dotenv()
    return create_engine(
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

engine = get_engine()

# ── Sidebar navigation ────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/box.png", width=60)
st.sidebar.title("OrdersPlus")
st.sidebar.markdown("*E-commerce Analytics Platform*")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "🚚 Delivery", "👥 Customers", "📈 Forecast"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Dataset**
- 96,477 delivered orders
- Sep 2016 — Aug 2018
- Brazilian E-commerce (Olist)
""")

# ── Page router ───────────────────────────────────────────────
if page == "📊 Overview":
    st.title("📊 Business Overview")
    st.markdown("High-level health metrics across the entire platform.")

    # ── KPI Query ─────────────────────────────────────────────
    @st.cache_data
    def load_overview():
        query = """
        SELECT
            COUNT(DISTINCT o.order_id)                        AS total_orders,
            COUNT(DISTINCT o.customer_id)                     AS total_customers,
            ROUND(SUM(p.payment_value), 2)                    AS total_revenue,
            ROUND(AVG(p.payment_value), 2)                    AS avg_order_value,
            SUM(o.is_late_delivery)                           AS late_orders,
            ROUND(SUM(o.is_late_delivery) * 100.0
                  / COUNT(o.order_id), 2)                     AS late_pct
        FROM orders o
        JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        """
        return pd.read_sql(query, engine)

    @st.cache_data
    def load_monthly():
        query = """
        SELECT
            DATE_FORMAT(o.order_purchase_timestamp, '%%Y-%%m') AS month,
            COUNT(DISTINCT o.order_id)                          AS total_orders,
            ROUND(SUM(p.payment_value), 2)                      AS monthly_revenue
        FROM orders o
        JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY month
        ORDER BY month
        """
        df = pd.read_sql(query, engine)
        return df[df["month"] < "2018-09"]

    @st.cache_data
    def load_categories():
        query = """
        SELECT
            COALESCE(ct.product_category_name_english,
                     pr.product_category_name)      AS category,
            COUNT(DISTINCT oi.order_id)              AS total_orders,
            ROUND(SUM(oi.price), 2)                  AS total_revenue
        FROM order_items oi
        JOIN products pr ON oi.product_id = pr.product_id
        JOIN orders o    ON oi.order_id   = o.order_id
        LEFT JOIN category_translation ct
               ON pr.product_category_name = ct.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY category
        ORDER BY total_revenue DESC
        LIMIT 10
        """
        return pd.read_sql(query, engine)

    @st.cache_data
    def load_payments():
        query = """
        SELECT
            payment_type,
            COUNT(DISTINCT order_id)                  AS total_orders,
            ROUND(SUM(payment_value), 2)              AS total_revenue,
            ROUND(SUM(payment_value) * 100.0 /
                  SUM(SUM(payment_value)) OVER (), 2) AS revenue_share_pct
        FROM payments
        WHERE payment_type != 'not_defined'
        GROUP BY payment_type
        ORDER BY total_revenue DESC
        """
        return pd.read_sql(query, engine)

    health   = load_overview()
    monthly  = load_monthly()
    cats     = load_categories()
    payments = load_payments()

    # ── KPI Cards ─────────────────────────────────────────────
    st.markdown("### Key Metrics")
    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Total Revenue",
              f"R$ {health['total_revenue'][0]/1_000_000:.2f}M")
    k2.metric("Total Orders",
              f"{health['total_orders'][0]:,}")
    k3.metric("Total Customers",
              f"{health['total_customers'][0]:,}")
    k4.metric("Avg Order Value",
              f"R$ {health['avg_order_value'][0]:,.2f}")
    k5.metric("Late Delivery Rate",
              f"{health['late_pct'][0]}%",
              delta=f"{health['late_orders'][0]:,.0f} orders",
              delta_color="inverse")

    st.markdown("---")

    # ── Monthly Revenue Chart ──────────────────────────────────
    st.markdown("### Monthly Revenue Trend")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["monthly_revenue"],
        fill="tozeroy", fillcolor="rgba(52,168,83,0.15)",
        line=dict(color="#2D6A4F", width=2.5),
        mode="lines+markers", marker=dict(size=5),
        name="Monthly Revenue"
    ))
    fig.add_trace(go.Bar(
        x=monthly["month"], y=monthly["total_orders"],
        yaxis="y2", name="Orders",
        marker_color="rgba(74,198,137,0.3)",
        showlegend=True
    ))
    fig.update_layout(
        yaxis =dict(title="Revenue (R$)", tickprefix="R$ "),
        yaxis2=dict(title="Total Orders", overlaying="y",
                    side="right", showgrid=False),
        hovermode="x unified",
        height=400,
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Categories + Payments side by side ────────────────────
    st.markdown("### Revenue Breakdown")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 10 Categories by Revenue**")
        fig_cat = px.bar(
            cats, x="total_revenue", y="category",
            orientation="h",
            color="total_revenue",
            color_continuous_scale=["#95D5B2", "#2D6A4F"],
            text=cats["total_revenue"].apply(
                lambda x: f"R$ {x/1_000_000:.2f}M"),
            height=400
        )
        fig_cat.update_traces(textposition="outside")
        fig_cat.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Revenue (R$)",
            yaxis_title="",
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(categoryorder="total ascending")
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        st.markdown("**Payment Method Distribution**")
        fig_pay = px.pie(
            payments,
            values="revenue_share_pct",
            names="payment_type",
            color_discrete_sequence=["#2D6A4F","#40916C",
                                     "#74C69D","#95D5B2"],
            hole=0.4,
            height=400
        )
        fig_pay.update_traces(
            textposition="outside",
            textinfo="percent+label"
        )
        fig_pay.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_pay, use_container_width=True)

    # ── Insight callout ───────────────────────────────────────
    st.markdown("---")
    st.info("""
    💡 **Key Insight:** Health & Beauty leads revenue at R$ 1.23M.
    Credit card dominates payments at 78.3% with avg 3.51 installments
    — reflecting typical Brazilian e-commerce buying behaviour.
    """)
elif page == "🚚 Delivery":
    st.title("🚚 Delivery Performance")
    st.markdown("Late delivery analysis by state and its impact on customer experience.")

    @st.cache_data
    def load_delivery():
        query = """
        SELECT
            c.customer_state                       AS state,
            COUNT(o.order_id)                       AS total_orders,
            SUM(o.is_late_delivery)                 AS late_orders,
            ROUND(SUM(o.is_late_delivery) * 100.0
                  / COUNT(o.order_id), 2)           AS late_pct,
            ROUND(AVG(o.delivery_days), 1)          AS avg_delivery_days
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
        HAVING COUNT(o.order_id) > 100
        ORDER BY late_pct DESC
        """
        return pd.read_sql(query, engine)

    @st.cache_data
    def load_review_impact():
        query = """
        SELECT
            CASE WHEN o.is_late_delivery = 1
                 THEN 'Late' ELSE 'On Time' END     AS delivery_status,
            COUNT(o.order_id)                        AS total_orders,
            ROUND(AVG(r.review_score), 3)            AS avg_review_score,
            SUM(CASE WHEN r.review_score = 1
                     THEN 1 ELSE 0 END)              AS score_1,
            SUM(CASE WHEN r.review_score = 2
                     THEN 1 ELSE 0 END)              AS score_2,
            SUM(CASE WHEN r.review_score = 3
                     THEN 1 ELSE 0 END)              AS score_3,
            SUM(CASE WHEN r.review_score = 4
                     THEN 1 ELSE 0 END)              AS score_4,
            SUM(CASE WHEN r.review_score = 5
                     THEN 1 ELSE 0 END)              AS score_5
        FROM orders o
        JOIN reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY o.is_late_delivery
        ORDER BY o.is_late_delivery
        """
        return pd.read_sql(query, engine)

    delivery = load_delivery()
    reviews  = load_review_impact()

    # ── KPI Cards ─────────────────────────────────────────────
    st.markdown("### Delivery KPIs")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Avg Late Rate",
              f"{delivery['late_pct'].mean():.1f}%")
    d2.metric("Worst State",
              f"{delivery.iloc[0]['state']}",
              f"{delivery.iloc[0]['late_pct']}% late",
              delta_color="inverse")
    d3.metric("Best State",
              f"{delivery.iloc[-1]['state']}",
              f"{delivery.iloc[-1]['late_pct']}% late",
              delta_color="normal")
    d4.metric("Avg Delivery Days",
              f"{delivery['avg_delivery_days'].mean():.1f} days")

    st.markdown("---")

    # ── Late % by state ───────────────────────────────────────
    st.markdown("### Late Delivery Rate by State")
    avg_late = delivery["late_pct"].mean()
    colors   = ["#B7192C" if x > 15 else
                "#E07B54" if x > 10 else
                "#52B788" for x in delivery["late_pct"]]

    fig_state = go.Figure()
    fig_state.add_trace(go.Bar(
        x=delivery["state"],
        y=delivery["late_pct"],
        marker_color=colors,
        text=delivery["late_pct"].apply(lambda x: f"{x}%"),
        textposition="outside",
        name="Late %"
    ))
    fig_state.add_hline(
        y=avg_late,
        line_dash="dash",
        line_color="white",
        annotation_text=f"Avg: {avg_late:.1f}%",
        annotation_position="top right"
    )
    fig_state.update_layout(
        height=400,
        xaxis_title="State",
        yaxis_title="Late Delivery %",
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_state, use_container_width=True)

    st.markdown("---")

    # ── Review impact ─────────────────────────────────────────
    st.markdown("### Impact on Customer Reviews")
    col1, col2 = st.columns(2)

    with col1:
        fig_score = go.Figure()
        fig_score.add_trace(go.Bar(
            x=reviews["delivery_status"],
            y=reviews["avg_review_score"],
            marker_color=["#52B788", "#B7192C"],
            text=reviews["avg_review_score"].apply(
                lambda x: f"{x:.2f} ⭐"),
            textposition="outside",
            width=0.4
        ))
        fig_score.update_layout(
            title="Avg Review Score",
            yaxis=dict(range=[0, 5], title="Score"),
            height=350,
            showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_score, use_container_width=True)

    with col2:
        score_cols = ["score_1","score_2","score_3","score_4","score_5"]
        score_colors = ["#B7192C","#E07B54","#F6C243","#74C69D","#2D6A4F"]
        fig_dist = go.Figure()
        for col, color in zip(score_cols, score_colors):
            pct = reviews[col] / reviews["total_orders"] * 100
            fig_dist.add_trace(go.Bar(
                name=f"{col[-1]} ⭐",
                x=reviews["delivery_status"],
                y=pct,
                marker_color=color,
                text=pct.apply(lambda x: f"{x:.1f}%"),
                textposition="inside"
            ))
        fig_dist.update_layout(
            barmode="stack",
            title="Review Score Distribution",
            yaxis_title="% of Orders",
            height=350,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    # ── Scatter: delivery days vs late pct ────────────────────
    st.markdown("---")
    st.markdown("### Delivery Days vs Late Rate by State")
    fig_scatter = px.scatter(
        delivery,
        x="avg_delivery_days",
        y="late_pct",
        text="state",
        size="total_orders",
        color="late_pct",
        color_continuous_scale=["#2D6A4F", "#F6C243", "#B7192C"],
        labels={
            "avg_delivery_days" : "Avg Delivery Days",
            "late_pct"          : "Late Delivery %",
            "total_orders"      : "Order Volume"
        },
        height=450
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")
    st.error("""
    🚨 **Critical Finding:** Late deliveries score 2.57★ vs 4.29★ for on-time orders.
    46.2% of late orders receive a 1★ review — 7x higher than on-time orders (6.6%).
    States AL, MA, and PI require urgent logistics intervention.
    """)

elif page == "👥 Customers":
    st.title("👥 Customer Intelligence")
    st.markdown("RFM segmentation and cohort retention analysis.")

    @st.cache_data
    def load_rfm():
        query = """
        WITH rfm_base AS (
            SELECT
                c.customer_unique_id,
                MAX(DATE(o.order_purchase_timestamp))  AS last_purchase_date,
                COUNT(DISTINCT o.order_id)             AS frequency,
                ROUND(SUM(p.payment_value), 2)         AS monetary
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN payments p  ON o.order_id    = p.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        ),
        rfm_scores AS (
            SELECT *,
                DATEDIFF('2018-10-01', last_purchase_date) AS recency_days,
                NTILE(5) OVER (ORDER BY DATEDIFF('2018-10-01',
                               last_purchase_date) ASC)    AS r_score,
                NTILE(5) OVER (ORDER BY frequency ASC)     AS f_score,
                NTILE(5) OVER (ORDER BY monetary ASC)      AS m_score
            FROM rfm_base
        )
        SELECT *,
            (r_score + f_score + m_score) AS rfm_total,
            CASE
                WHEN (r_score + f_score + m_score) >= 13 THEN 'Champions'
                WHEN (r_score + f_score + m_score) >= 10 THEN 'Loyal Customers'
                WHEN r_score >= 4 AND (f_score + m_score) < 6 THEN 'Promising'
                WHEN r_score <= 2 AND (f_score + m_score) >= 8 THEN 'At Risk'
                WHEN r_score <= 2 THEN 'Lost'
                ELSE 'Needs Attention'
            END AS customer_segment
        FROM rfm_scores
        """
        return pd.read_sql(query, engine)

    @st.cache_data
    def load_cohort():
        query = """
        WITH first_orders AS (
            SELECT
                c.customer_unique_id,
                MIN(DATE_FORMAT(o.order_purchase_timestamp,
                    '%%Y-%%m'))                         AS cohort_month
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        ),
        order_months AS (
            SELECT
                c.customer_unique_id,
                DATE_FORMAT(o.order_purchase_timestamp,
                    '%%Y-%%m')                          AS order_month
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id,
                     DATE_FORMAT(o.order_purchase_timestamp, '%%Y-%%m')
        )
        SELECT
            f.cohort_month,
            COUNT(DISTINCT f.customer_unique_id)             AS cohort_size,
            COUNT(DISTINCT CASE WHEN om.order_month >
                  f.cohort_month THEN f.customer_unique_id
                  END)                                       AS returned_customers,
            ROUND(COUNT(DISTINCT CASE WHEN om.order_month >
                  f.cohort_month THEN f.customer_unique_id
                  END) * 100.0 /
                  COUNT(DISTINCT f.customer_unique_id), 2)  AS retention_pct
        FROM first_orders f
        LEFT JOIN order_months om
               ON f.customer_unique_id = om.customer_unique_id
        GROUP BY f.cohort_month
        ORDER BY f.cohort_month
        """
        df = pd.read_sql(query, engine)
        return df[df["cohort_month"] < "2018-08"]

    rfm    = load_rfm()
    cohort = load_cohort()

    seg_summary = rfm.groupby("customer_segment").agg(
        customer_count = ("customer_unique_id", "count"),
        avg_monetary   = ("monetary", "mean"),
        total_revenue  = ("monetary", "sum"),
        avg_recency    = ("recency_days", "mean"),
        avg_frequency  = ("frequency", "mean")
    ).round(2).reset_index()

    seg_order  = ["Champions","Loyal Customers","Promising",
                  "Needs Attention","At Risk","Lost"]
    seg_colors = {
        "Champions"       : "#2D6A4F",
        "Loyal Customers" : "#40916C",
        "Promising"       : "#74C69D",
        "Needs Attention" : "#F6C243",
        "At Risk"         : "#E07B54",
        "Lost"            : "#B7192C",
    }
    seg_summary["sort_order"] = seg_summary["customer_segment"].map(
        {s: i for i, s in enumerate(seg_order)}
    )
    seg_summary = seg_summary.sort_values("sort_order")

    # ── KPI Cards ─────────────────────────────────────────────
    st.markdown("### Customer Segment KPIs")
    c1, c2, c3, c4 = st.columns(4)

    champions = seg_summary[seg_summary["customer_segment"] == "Champions"]
    at_risk   = seg_summary[seg_summary["customer_segment"] == "At Risk"]
    lost      = seg_summary[seg_summary["customer_segment"] == "Lost"]

    c1.metric("Total Customers",   f"{rfm.shape[0]:,}")
    c2.metric("Champions",
              f"{champions['customer_count'].values[0]:,}",
              f"R$ {champions['avg_monetary'].values[0]:.0f} avg spend")
    c3.metric("At Risk",
              f"{at_risk['customer_count'].values[0]:,}",
              f"R$ {at_risk['avg_monetary'].values[0]:.0f} avg — save them",
              delta_color="inverse")
    c4.metric("Lost Customers",
              f"{lost['customer_count'].values[0]:,}",
              f"R$ {lost['total_revenue'].values[0]/1_000_000:.2f}M lost revenue",
              delta_color="inverse")

    st.markdown("---")

    # ── Segment charts ────────────────────────────────────────
    st.markdown("### RFM Customer Segments")
    col1, col2, col3 = st.columns(3)

    colors_list = [seg_colors[s] for s in seg_summary["customer_segment"]]

    with col1:
        fig1 = go.Figure(go.Bar(
            x=seg_summary["customer_segment"],
            y=seg_summary["customer_count"],
            marker_color=colors_list,
            text=seg_summary["customer_count"].apply(lambda x: f"{x:,}"),
            textposition="outside"
        ))
        fig1.update_layout(
            title="Customers per Segment",
            height=350,
            showlegend=False,
            xaxis_tickangle=-20,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure(go.Bar(
            x=seg_summary["customer_segment"],
            y=seg_summary["total_revenue"],
            marker_color=colors_list,
            text=seg_summary["total_revenue"].apply(
                lambda x: f"R${x/1_000_000:.2f}M"),
            textposition="outside"
        ))
        fig2.update_layout(
            title="Total Revenue per Segment",
            yaxis_tickprefix="R$ ",
            height=350,
            showlegend=False,
            xaxis_tickangle=-20,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        fig3 = go.Figure(go.Bar(
            x=seg_summary["customer_segment"],
            y=seg_summary["avg_monetary"],
            marker_color=colors_list,
            text=seg_summary["avg_monetary"].apply(lambda x: f"R${x:.0f}"),
            textposition="outside"
        ))
        fig3.update_layout(
            title="Avg Order Value per Segment",
            yaxis_tickprefix="R$ ",
            height=350,
            showlegend=False,
            xaxis_tickangle=-20,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # ── Cohort retention ──────────────────────────────────────
    st.markdown("### Cohort Retention Analysis")
    col1, col2 = st.columns(2)

    with col1:
        fig_coh = go.Figure()
        fig_coh.add_trace(go.Bar(
            x=cohort["cohort_month"],
            y=cohort["cohort_size"],
            name="Cohort Size",
            marker_color="#52B788"
        ))
        fig_coh.update_layout(
            title="New Customers per Month",
            xaxis_tickangle=-45,
            height=380,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_coh, use_container_width=True)

    with col2:
        cohort_stable = cohort[cohort["cohort_month"] < "2018-04"]
        fig_ret = go.Figure()
        fig_ret.add_trace(go.Scatter(
            x=cohort_stable["cohort_month"],
            y=cohort_stable["retention_pct"],
            fill="tozeroy",
            fillcolor="rgba(183,25,44,0.15)",
            line=dict(color="#B7192C", width=2.5),
            mode="lines+markers",
            marker=dict(size=6),
            name="Retention %"
        ))
        fig_ret.add_hline(
            y=cohort_stable["retention_pct"].mean(),
            line_dash="dash", line_color="white",
            annotation_text=f"Avg: {cohort_stable['retention_pct'].mean():.1f}%",
            annotation_position="top right"
        )
        fig_ret.update_layout(
            title="Repeat Purchase Rate by Cohort",
            yaxis_title="Retention %",
            xaxis_tickangle=-45,
            height=380,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_ret, use_container_width=True)

    st.markdown("---")
    st.warning("""
    ⚠️ **Retention Crisis:** 92% of customers never make a second purchase.
    The At Risk segment (3,009 customers) has the highest avg spend of R$ 439
    — a targeted retention campaign here would have the highest ROI.
    """)

elif page == "📈 Forecast":
    st.title("📈 Revenue Forecast")
    st.markdown("90-day Prophet time-series revenue forecast.")

    @st.cache_data
    def load_forecast():
        query = """
        SELECT
            DATE(o.order_purchase_timestamp)    AS ds,
            ROUND(SUM(p.payment_value), 2)      AS y
        FROM orders o
        JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        AND o.order_purchase_timestamp < '2018-09-01'
        GROUP BY DATE(o.order_purchase_timestamp)
        ORDER BY ds
        """
        df = pd.read_sql(query, engine)
        df["ds"] = pd.to_datetime(df["ds"])
        return df

    from prophet import Prophet

    daily = load_forecast()

    with st.spinner("Training Prophet model — please wait..."):
        model = Prophet(
            changepoint_prior_scale = 0.05,
            seasonality_prior_scale = 10,
            yearly_seasonality      = True,
            weekly_seasonality      = True,
            daily_seasonality       = False,
            interval_width          = 0.95
        )
        model.fit(daily)
        future   = model.make_future_dataframe(periods=90)
        forecast = model.predict(future)

    forecast_tail = forecast[forecast["ds"] > daily["ds"].max()].copy()

    # ── KPI Cards ─────────────────────────────────────────────
    st.markdown("### Forecast Summary")
    f1, f2, f3, f4 = st.columns(4)

    f1.metric("Avg Daily Revenue (actual)",
              f"R$ {daily['y'].mean():,.0f}")
    f2.metric("Projected 90-day Revenue",
              f"R$ {forecast_tail['yhat'].sum()/1_000_000:.2f}M")
    f3.metric("Lower Bound (95%)",
              f"R$ {forecast_tail['yhat_lower'].sum()/1_000_000:.2f}M")
    f4.metric("Upper Bound (95%)",
              f"R$ {forecast_tail['yhat_upper'].sum()/1_000_000:.2f}M")

    st.markdown("---")

    # ── Full forecast chart ───────────────────────────────────
    st.markdown("### Full Timeline — Actuals + Forecast")
    fig_full = go.Figure()

    fig_full.add_trace(go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_upper"],
        fill=None, mode="lines",
        line=dict(color="rgba(82,183,136,0)"),
        showlegend=False, name="Upper"
    ))
    fig_full.add_trace(go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_lower"],
        fill="tonexty",
        fillcolor="rgba(82,183,136,0.15)",
        mode="lines",
        line=dict(color="rgba(82,183,136,0)"),
        name="95% Confidence"
    ))
    fig_full.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat"],
        mode="lines",
        line=dict(color="#2D6A4F", width=2),
        name="Forecast"
    ))
    fig_full.add_trace(go.Scatter(
        x=daily["ds"], y=daily["y"],
        mode="markers",
        marker=dict(color="#95D5B2", size=3, opacity=0.6),
        name="Actual daily revenue"
    ))
    fig_full.add_vline(
        x=daily["ds"].max().timestamp() * 1000,
        line_dash="dash", line_color="#E07B54",
        annotation_text="Forecast start",
        annotation_position="top right"
    )
    fig_full.update_layout(
        height=420,
        hovermode="x unified",
        yaxis=dict(title="Daily Revenue (R$)",
                   tickprefix="R$ "),
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_full, use_container_width=True)

    st.markdown("---")

    # ── 90 day forecast only ──────────────────────────────────
    st.markdown("### Next 90 Days — Daily Forecast")
    fig_90 = go.Figure()

    fig_90.add_trace(go.Scatter(
        x=forecast_tail["ds"],
        y=forecast_tail["yhat_upper"],
        fill=None, mode="lines",
        line=dict(color="rgba(82,183,136,0)"),
        showlegend=False
    ))
    fig_90.add_trace(go.Scatter(
        x=forecast_tail["ds"],
        y=forecast_tail["yhat_lower"],
        fill="tonexty",
        fillcolor="rgba(82,183,136,0.2)",
        mode="lines",
        line=dict(color="rgba(82,183,136,0)"),
        name="95% Confidence interval"
    ))
    fig_90.add_trace(go.Scatter(
        x=forecast_tail["ds"],
        y=forecast_tail["yhat"],
        mode="lines+markers",
        line=dict(color="#2D6A4F", width=2.5),
        marker=dict(size=4),
        name="Forecast"
    ))
    fig_90.update_layout(
        height=400,
        hovermode="x unified",
        yaxis=dict(title="Forecasted Revenue (R$)",
                   tickprefix="R$ "),
        xaxis_title="Date",
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_90, use_container_width=True)

    st.markdown("---")

    # ── Seasonality components ────────────────────────────────
    st.markdown("### Weekly Seasonality Pattern")
    weekly = forecast[["ds","weekly"]].copy()
    weekly["day"] = weekly["ds"].dt.day_name()
    weekly_avg = weekly.groupby("day")["weekly"].mean().reindex([
        "Monday","Tuesday","Wednesday",
        "Thursday","Friday","Saturday","Sunday"
    ])

    fig_week = go.Figure(go.Bar(
        x=weekly_avg.index,
        y=weekly_avg.values,
        marker_color=["#2D6A4F" if v > 0 else "#B7192C"
                      for v in weekly_avg.values],
        text=[f"R$ {v:,.0f}" for v in weekly_avg.values],
        textposition="outside"
    ))
    fig_week.update_layout(
        height=350,
        yaxis_title="Revenue Effect (R$)",
        xaxis_title="Day of Week",
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_week, use_container_width=True)

    st.markdown("---")
    st.success("""
    📈 **Forecast Insight:** Revenue is projected to reach R$ 3.19M over
    the next 90 days — a 40% increase from current daily average driven
    by Black Friday seasonality detected in the 2017 data.
    Monday is the strongest sales day — ideal for launching promotions.
    Saturday is the weakest — avoid ad spend.
    """)

st.sidebar.markdown("---")
st.sidebar.markdown("Built by Harshal Kawane")