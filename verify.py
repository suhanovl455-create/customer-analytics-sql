"""Check exported SQL results independently and exercise boundary cases."""
import csv
import sqlite3
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def csv_rows(case, name):
    with (ROOT / case / 'results' / name).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def memory(case):
    con = sqlite3.connect(':memory:')
    con.executescript((ROOT / case / 'schema.sql').read_text())
    return con


db = sqlite3.connect(ROOT / '01-retention' / 'project.sqlite')
cohorts, members = {}, defaultdict(set)
for uid, stamp in db.execute('SELECT * FROM users'):
    signup = date.fromisoformat(stamp)
    monday = signup - timedelta(days=signup.weekday())
    cohorts[uid] = (signup, monday)
    members[monday].add(uid)
active = defaultdict(set)
for uid, stamp in db.execute('SELECT user_id,event_date FROM activity'):
    signup, monday = cohorts[uid]
    day = date.fromisoformat(stamp)
    if signup <= day <= date(2026, 8, 31):
        active[monday, (day - monday).days // 7].add(uid)
expected = {}
for monday, users in members.items():
    for week in range(5):
        if monday + timedelta(days=7 * (week + 1)) <= date(2026, 9, 1):
            expected[monday.isoformat(), week] = (len(users), len(active[monday, week]))
rows = csv_rows('01-retention', 'retention.csv')
assert len(rows) == len(expected)
for r in rows:
    size, count = expected[r['cohort_week'], int(r['week_number'])]
    assert int(r['cohort_size']) == size and int(r['active_users']) == count
    assert abs(float(r['retention_pct']) - 100 * count / size) <= .0051
db.close()

db = sqlite3.connect(ROOT / '02-rfm' / 'project.sqlite')
purchases = defaultdict(list)
for uid, stamp, status, amount in db.execute('SELECT customer_id,order_date,status,amount_kopecks FROM orders'):
    if status == 'paid' and '2026-03-04' <= stamp <= '2026-08-31':
        purchases[uid].append((date.fromisoformat(stamp), amount))
rows = csv_rows('02-rfm', 'customers.csv')
assert len(rows) == 150 and len({r['customer_id'] for r in rows}) == 150
for r in rows:
    orders = purchases[int(r['customer_id'])]
    assert int(r['frequency']) == len(orders)
    assert round(float(r['monetary_rub']) * 100) == sum(p[1] for p in orders)
    if orders:
        assert int(r['recency_days']) == (date(2026,8,31)-max(p[0] for p in orders)).days
        assert all(1 <= int(r[k]) <= 3 for k in ('r_score','f_score','m_score'))
    else:
        assert r['recency_days'] == '' and r['segment'] == 'no_purchases'
        assert all(r[k] == '' for k in ('r_score','f_score','m_score'))
db.close()

# Cohort boundaries: duplicate activity, W0/W1 boundary, zero activity, incomplete W3.
db = memory('01-retention')
db.executemany('INSERT INTO users VALUES (?,?)', [(1,'2026-08-10'),(2,'2026-08-10')])
db.executemany('INSERT INTO activity VALUES (?,?,?)', [
    (1,1,'2026-08-09'), (2,1,'2026-08-16'), (3,1,'2026-08-16'),
    (4,1,'2026-08-17'), (5,1,'2026-08-31')])
rows=db.execute((ROOT/'01-retention'/'01_retention.sql').read_text()).fetchall()
assert [(r[1],r[3],r[4]) for r in rows] == [(0,1,50.0),(1,1,50.0),(2,0,0.0)]
db.close()

# RFM boundaries: exact 30/90-day cutoffs, exact price thresholds, cancellation,
# old/future orders excluded; customer without paid orders survives LEFT JOIN.
db = memory('02-rfm')
db.executemany('INSERT INTO customers VALUES (?)',[(1,),(2,),(3,),(4,)])
orders=[]
for uid,days,n,amount in [(1,30,6,500000),(2,90,3,400000),(3,91,1,99000)]:
    for _ in range(n):
        orders.append((len(orders)+1,uid,(date(2026,8,31)-timedelta(days=days)).isoformat(),'paid',amount))
for stamp,status in [('2026-08-31','cancelled'),('2026-03-03','paid'),('2026-09-01','paid')]:
    orders.append((len(orders)+1,4,stamp,status,5000000))
db.executemany('INSERT INTO orders VALUES (?,?,?,?,?)',orders)
rows=db.execute((ROOT/'02-rfm'/'01_customers.sql').read_text()).fetchall()
assert [r[4:7] for r in rows] == [(3,3,3),(2,2,2),(1,1,1),(None,None,None)]
assert [r[-1] for r in rows] == ['loyal_high_value','other_buyers','inactive','no_purchases']
assert rows[3][1:4] == (None,0,0.0)
db.close()
print('PASS: cohort counts, observation windows, duplicates, zero activity, RFM metrics, thresholds and clients without purchases.')
