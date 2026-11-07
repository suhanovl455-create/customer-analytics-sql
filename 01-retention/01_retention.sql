-- Когорта: календарная неделя регистрации (понедельник–воскресенье).
-- Неполные недели наблюдения исключены. Последний день данных: 2026-08-31.
WITH cohorts AS (
 SELECT user_id, signup_date,
 date(signup_date, '-' || ((CAST(strftime('%w', signup_date) AS INTEGER)+6)%7) || ' days') AS cohort_week
 FROM users
), sizes AS (
 SELECT cohort_week, COUNT(*) AS cohort_size FROM cohorts GROUP BY cohort_week
), periods(week_number) AS (VALUES (0),(1),(2),(3),(4)),
active AS (
 SELECT c.cohort_week, c.user_id,
 CAST((julianday(a.event_date)-julianday(c.cohort_week))/7 AS INTEGER) AS week_number
 FROM cohorts c JOIN activity a ON a.user_id=c.user_id
 WHERE a.event_date>=c.signup_date AND a.event_date<='2026-08-31'
 GROUP BY c.cohort_week,c.user_id,week_number
)
SELECT s.cohort_week,p.week_number,s.cohort_size,
 COUNT(a.user_id) AS active_users,
 ROUND(100.0*COUNT(a.user_id)/s.cohort_size,2) AS retention_pct
FROM sizes s CROSS JOIN periods p
LEFT JOIN active a ON a.cohort_week=s.cohort_week AND a.week_number=p.week_number
WHERE date(s.cohort_week,'+' || (7*(p.week_number+1)) || ' days')<='2026-09-01'
GROUP BY s.cohort_week,p.week_number,s.cohort_size
ORDER BY s.cohort_week,p.week_number;
