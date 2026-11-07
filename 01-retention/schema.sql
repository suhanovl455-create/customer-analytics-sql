CREATE TABLE users(user_id INTEGER PRIMARY KEY, signup_date TEXT NOT NULL);
CREATE TABLE activity(event_id INTEGER PRIMARY KEY,
 user_id INTEGER NOT NULL REFERENCES users(user_id), event_date TEXT NOT NULL);
