
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    user_password TEXT NOT NULL,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE TABLE IF NOT EXISTS categories(
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income','expense'))
);
 
CREATE TABLE IF NOT EXISTS entries(
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    categories_id INTEGER NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income','expense')),
    entry_date TEXT NOT NULL,
    note TEXT,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (categories_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS targets(
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    target_amount DOUBLE PRECISION NOT NULL,
    current_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS contribution(
    id SERIAL PRIMARY KEY,
    goal_id INTEGER NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    contribution_date TEXT NOT NULL,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(goal_id) REFERENCES targets(id)
);

 
INSERT INTO categories (name, type) VALUES
    ('Salary', 'income'),
    ('Freelance', 'income'),
    ('Rent', 'expense'),
    ('Food', 'expense'),
    ('Utilities', 'expense'),
    ('Transport', 'expense'),
    ('Other', 'expense')
ON CONFLICT DO NOTHING;