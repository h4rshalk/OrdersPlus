-- ============================================================
-- OrdersPlus — Business Analysis Queries
-- Database : ordersplus
-- ============================================================

USE ordersplus;


-- ── Query 1: Overall Business Health ─────────────────────────
-- What is the overall revenue, order volume, and average order value?

SELECT
    COUNT(DISTINCT o.order_id)                        AS total_orders,
    COUNT(DISTINCT o.customer_id)                     AS total_customers,
    ROUND(SUM(p.payment_value), 2)                    AS total_revenue,
    ROUND(AVG(p.payment_value), 2)                    AS avg_order_value,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT
          o.order_id), 2)                             AS revenue_per_order,
    MIN(DATE(o.order_purchase_timestamp))             AS first_order_date,
    MAX(DATE(o.order_purchase_timestamp))             AS last_order_date
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered';


-- ── Query 2: Monthly Revenue Trend ───────────────────────────
-- How has revenue trended month over month?

SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
    COUNT(DISTINCT o.order_id)                        AS total_orders,
    ROUND(SUM(p.payment_value), 2)                    AS monthly_revenue,
    ROUND(AVG(p.payment_value), 2)                    AS avg_order_value,
    LAG(ROUND(SUM(p.payment_value), 2))
        OVER (ORDER BY DATE_FORMAT(
              o.order_purchase_timestamp, '%Y-%m'))   AS prev_month_revenue,
    ROUND(
        (SUM(p.payment_value) - LAG(SUM(p.payment_value))
            OVER (ORDER BY DATE_FORMAT(
                  o.order_purchase_timestamp, '%Y-%m')))
        / NULLIF(LAG(SUM(p.payment_value))
            OVER (ORDER BY DATE_FORMAT(
                  o.order_purchase_timestamp, '%Y-%m')), 0) * 100
    , 2)                                              AS mom_growth_pct
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY month
ORDER BY month;


-- ── Query 3: Revenue by Product Category ─────────────────────
-- Which product categories drive the most revenue?

SELECT
    COALESCE(ct.product_category_name_english,
             pr.product_category_name)               AS category,
    COUNT(DISTINCT oi.order_id)                       AS total_orders,
    SUM(oi.quantity)                                  AS total_units,
    ROUND(SUM(oi.revenue), 2)                         AS total_revenue,
    ROUND(AVG(oi.avg_price), 2)                       AS avg_item_price,
    RANK() OVER (ORDER BY SUM(oi.revenue) DESC)       AS revenue_rank
FROM (
    SELECT
        order_id,
        product_id,
        seller_id,
        COUNT(*)            AS quantity,
        SUM(price)          AS revenue,
        AVG(price)          AS avg_price
    FROM order_items
    GROUP BY order_id, product_id, seller_id
) oi
JOIN products pr        ON oi.product_id = pr.product_id
JOIN orders o           ON oi.order_id   = o.order_id
LEFT JOIN category_translation ct
                        ON pr.product_category_name = ct.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY total_revenue DESC
LIMIT 15;


-- ── Query 4: Late Delivery Analysis by State ─────────────────
-- Which customer states suffer the most late deliveries?

SELECT
    c.customer_state                                  AS state,
    COUNT(o.order_id)                                 AS total_orders,
    SUM(o.is_late_delivery)                           AS late_orders,
    ROUND(SUM(o.is_late_delivery) * 100.0
          / COUNT(o.order_id), 2)                     AS late_pct,
    ROUND(AVG(o.delivery_days), 1)                    AS avg_delivery_days,
    RANK() OVER (ORDER BY
        SUM(o.is_late_delivery) * 100.0
        / COUNT(o.order_id) DESC)                     AS late_rank
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
HAVING COUNT(o.order_id) > 100
ORDER BY late_pct DESC;


-- ── Query 5: Customer Review Score vs Delivery Performance ───
-- Do late deliveries actually cause lower review scores?

SELECT
    o.is_late_delivery,
    CASE WHEN o.is_late_delivery = 1
         THEN 'Late' ELSE 'On Time' END               AS delivery_status,
    COUNT(o.order_id)                                 AS total_orders,
    ROUND(AVG(r.review_score), 3)                     AS avg_review_score,
    SUM(CASE WHEN r.review_score <= 2
             THEN 1 ELSE 0 END)                       AS poor_reviews,
    ROUND(SUM(CASE WHEN r.review_score <= 2
             THEN 1 ELSE 0 END) * 100.0
          / COUNT(o.order_id), 2)                     AS poor_review_pct
FROM orders o
JOIN reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY o.is_late_delivery
ORDER BY o.is_late_delivery;


-- ── Query 6: RFM Segmentation ─────────────────────────────────
-- Segment customers by Recency, Frequency, Monetary value

WITH rfm_base AS (
    SELECT
        c.customer_unique_id,
        MAX(DATE(o.order_purchase_timestamp))         AS last_purchase_date,
        COUNT(DISTINCT o.order_id)                    AS frequency,
        ROUND(SUM(p.payment_value), 2)                AS monetary
    FROM orders o
    JOIN customers c  ON o.customer_id  = c.customer_id
    JOIN payments p   ON o.order_id     = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scores AS (
    SELECT
        customer_unique_id,
        last_purchase_date,
        frequency,
        monetary,
        DATEDIFF('2018-10-01', last_purchase_date)    AS recency_days,
        NTILE(5) OVER (ORDER BY
            DATEDIFF('2018-10-01', last_purchase_date) ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)        AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)         AS m_score
    FROM rfm_base
)
SELECT
    customer_unique_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score)                     AS rfm_total,
    CASE
        WHEN (r_score + f_score + m_score) >= 13
             THEN 'Champions'
        WHEN (r_score + f_score + m_score) >= 10
             THEN 'Loyal Customers'
        WHEN r_score >= 4 AND (f_score + m_score) < 6
             THEN 'Promising'
        WHEN r_score <= 2 AND (f_score + m_score) >= 8
             THEN 'At Risk'
        WHEN r_score <= 2
             THEN 'Lost'
        ELSE 'Needs Attention'
    END                                               AS customer_segment
FROM rfm_scores
ORDER BY rfm_total DESC;


-- ── Query 7: Seller Performance Leaderboard ───────────────────
-- Who are the top and bottom performing sellers?

SELECT
    s.seller_id,
    s.seller_state,
    COUNT(DISTINCT oi.order_id)                       AS total_orders,
    ROUND(SUM(oi.price), 2)                           AS total_revenue,
    ROUND(AVG(r.review_score), 2)                     AS avg_review_score,
    SUM(o.is_late_delivery)                           AS late_deliveries,
    ROUND(SUM(o.is_late_delivery) * 100.0
          / COUNT(DISTINCT oi.order_id), 2)           AS late_pct,
    RANK() OVER (ORDER BY SUM(oi.price) DESC)         AS revenue_rank
FROM order_items oi
JOIN sellers s  ON oi.seller_id  = s.seller_id
JOIN orders o   ON oi.order_id   = o.order_id
JOIN reviews r  ON oi.order_id   = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY s.seller_id, s.seller_state
HAVING COUNT(DISTINCT oi.order_id) > 10
ORDER BY total_revenue DESC
LIMIT 20;


-- ── Query 8: Payment Method Analysis ─────────────────────────
-- How do customers pay and does it affect order value?

SELECT
    payment_type,
    COUNT(DISTINCT order_id)                          AS total_orders,
    ROUND(SUM(payment_value), 2)                      AS total_revenue,
    ROUND(AVG(payment_value), 2)                      AS avg_payment,
    ROUND(AVG(payment_installments), 2)               AS avg_installments,
    ROUND(SUM(payment_value) * 100.0 /
          SUM(SUM(payment_value)) OVER (), 2)         AS revenue_share_pct
FROM payments
GROUP BY payment_type
ORDER BY total_revenue DESC;


-- ── Query 9: Cohort Retention Analysis ───────────────────────
-- Of customers who ordered in month X, how many returned?

WITH first_orders AS (
    SELECT
        c.customer_unique_id,
        MIN(DATE_FORMAT(o.order_purchase_timestamp,
            '%Y-%m'))                                 AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
order_months AS (
    SELECT
        c.customer_unique_id,
        DATE_FORMAT(o.order_purchase_timestamp,
            '%Y-%m')                                  AS order_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id,
             DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
)
SELECT
    f.cohort_month,
    COUNT(DISTINCT f.customer_unique_id)              AS cohort_size,
    COUNT(DISTINCT CASE WHEN om.order_month >
          f.cohort_month THEN f.customer_unique_id
          END)                                        AS returned_customers,
    ROUND(COUNT(DISTINCT CASE WHEN om.order_month >
          f.cohort_month THEN f.customer_unique_id
          END) * 100.0 /
          COUNT(DISTINCT f.customer_unique_id), 2)   AS retention_pct
FROM first_orders f
LEFT JOIN order_months om
       ON f.customer_unique_id = om.customer_unique_id
GROUP BY f.cohort_month
ORDER BY f.cohort_month;


-- ── Query 10: Peak Order Hours and Days ──────────────────────
-- When do customers place orders most?

SELECT
    DAYNAME(order_purchase_timestamp)                 AS day_of_week,
    HOUR(order_purchase_timestamp)                    AS hour_of_day,
    COUNT(o.order_id)                                 AS total_orders,
    ROUND(AVG(p.payment_value), 2)                    AS avg_order_value
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY day_of_week, hour_of_day
ORDER BY total_orders DESC
LIMIT 20;