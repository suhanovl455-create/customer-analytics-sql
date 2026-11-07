-- R: дни с последнего оплаченного заказа, F: число заказов, M: сумма покупок.
-- Дата отчёта: 2026-08-31; окно: 2026-03-04 .. 2026-08-31 включительно (181 день).
WITH metrics AS (
 SELECT c.customer_id,
 CAST(julianday('2026-08-31')-julianday(MAX(o.order_date)) AS INTEGER) AS recency_days,
 COUNT(o.order_id) AS frequency,
 COALESCE(SUM(o.amount_kopecks),0) AS monetary_kopecks
 FROM customers c LEFT JOIN orders o ON o.customer_id=c.customer_id
 AND o.status='paid' AND o.order_date BETWEEN '2026-03-04' AND '2026-08-31'
 GROUP BY c.customer_id
), scored AS (
 SELECT *,
 CASE WHEN frequency=0 THEN NULL WHEN recency_days<=30 THEN 3 WHEN recency_days<=90 THEN 2 ELSE 1 END AS r_score,
 CASE WHEN frequency=0 THEN NULL WHEN frequency>=6 THEN 3 WHEN frequency>=3 THEN 2 ELSE 1 END AS f_score,
 CASE WHEN frequency=0 THEN NULL WHEN monetary_kopecks>=3000000 THEN 3 WHEN monetary_kopecks>=1000000 THEN 2 ELSE 1 END AS m_score
 FROM metrics
)
SELECT customer_id,recency_days,frequency,ROUND(monetary_kopecks/100.0,2) AS monetary_rub,
 r_score,f_score,m_score,
 CASE WHEN frequency=0 THEN 'no_purchases'
 WHEN r_score=3 AND f_score=3 AND m_score=3 THEN 'loyal_high_value'
 WHEN r_score=1 THEN 'inactive'
 WHEN r_score=3 AND f_score=1 THEN 'recent_low_frequency'
 ELSE 'other_buyers' END AS segment
FROM scored ORDER BY customer_id;
