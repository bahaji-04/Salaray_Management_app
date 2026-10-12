
CREATE TABLE IF NOT EXISTS user(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    user_password TEXT NOT NULL,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE TABLE IF NOT EXISTS categories(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income','expense'))
);
 
CREATE TABLE IF NOT EXISTS entries(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    categories_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income','expense')),
    entry_date TEXT NOT NULL,
    note TEXT,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (categories_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS contribution(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    contribution_date TEXT NOT NULL,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(goal_id) REFERENCES targets(id)
);

CREATE TABLE IF NOT EXISTS targets(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user(id)
);

 
INSERT INTO categories (name, type) VALUES
    ('Salary', 'income'),
    ('Freelance', 'income'),
    ('Rent', 'expense'),
    ('Food', 'expense'),
    ('Utilities', 'expense'),
    ('Transport', 'expense'),
    ('Other', 'expense');