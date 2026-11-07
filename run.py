"""Create deterministic synthetic data, execute SQL, export CSV results."""
import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
END = date(2026, 8, 31)


def export(cursor, path):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([column[0] for column in cursor.description])
        writer.writerows(cursor)


def cohort_data():
    rng = random.Random(2718)
    users, events = [], []
    for uid in range(1, 271):
        week = (uid - 1) // 45
        monday = date(2026, 7, 6) + timedelta(weeks=week)
        signup = monday + timedelta(days=rng.randrange(7))
        users.append((uid, signup.isoformat()))
        for age in range(7):
            if rng.random() > max(.16, .92 - .13 * age):
                continue
            day = monday + timedelta(days=7 * age + rng.randrange(7))
            if signup <= day <= END:
                events.append((len(events) + 1, uid, day.isoformat()))
                if uid % 11 == 0:
                    events.append((len(events) + 1, uid, day.isoformat()))
    return [('users', ('user_id', 'signup_date'), users),
            ('activity', ('event_id', 'user_id', 'event_date'), events)]


def rfm_data():
    rng = random.Random(31415)
    customers = [(i,) for i in range(1, 151)]
    orders = []
    for uid in range(1, 151):
        n = 0 if uid % 13 == 0 else rng.randint(1, 12)
        for _ in range(n):
            day = END - timedelta(days=rng.randrange(181))
            status = 'cancelled' if rng.random() < .14 else 'paid'
            orders.append((len(orders) + 1, uid, day.isoformat(), status,
                           rng.choice([99000, 199000, 499000, 999000, 1499000])))
    return [('customers', ('customer_id',), customers),
            ('orders', ('order_id', 'customer_id', 'order_date', 'status', 'amount_kopecks'), orders)]


def run(name, make_data):
    project = ROOT / name
    for folder in ('data', 'results'):
        (project / folder).mkdir(exist_ok=True)
    con = sqlite3.connect(':memory:')
    con.execute('PRAGMA foreign_keys=ON')
    con.executescript((project / 'schema.sql').read_text())
    for table, columns, rows in make_data():
        con.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in columns)})', rows)
        export(con.execute(f'SELECT * FROM {table}'), project / 'data' / f'{table}.csv')
    con.commit()
    assert not con.execute('PRAGMA foreign_key_check').fetchall()
    for query in sorted(project.glob('[0-9][0-9]_*.sql')):
        output = project / 'results' / (query.stem[3:] + '.csv')
        export(con.execute(query.read_text()), output)
        print(name, '->', output.name)
    with sqlite3.connect(project / 'project.sqlite') as db:
        con.backup(db)
    con.close()


if __name__ == '__main__':
    run('01-retention', cohort_data)
    run('02-rfm', rfm_data)
