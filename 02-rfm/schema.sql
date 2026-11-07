CREATE TABLE customers(customer_id INTEGER PRIMARY KEY);
CREATE TABLE orders(order_id INTEGER PRIMARY KEY,
 customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
 order_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('paid','cancelled')),
 amount_kopecks INTEGER NOT NULL CHECK(amount_kopecks>=0));
