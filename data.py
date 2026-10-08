import sqlite3
import random

conn = sqlite3.connect('expenses.db')

user_id = 4  # bahaji

# Category IDs from your schema
# 1=Salary, 2=Freelance, 3=Rent, 4=Food, 5=Utilities, 6=Transport, 7=Other

months = ['2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']

for month in months:
    # Monthly salary on the 1st
    conn.execute(
        "INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?,?,?,?,?,?)",
        (user_id, 1, 3500.00, 'income', f'{month}-01', 'Monthly salary')
    )

    # Freelance income (some months)
    if random.random() > 0.4:
        conn.execute(
            "INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?,?,?,?,?,?)",
            (user_id, 2, random.randint(200, 800), 'income', f'{month}-15', 'Freelance project')
        )

    # Rent on the 5th
    conn.execute(
        "INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?,?,?,?,?,?)",
        (user_id, 3, 1200.00, 'expense', f'{month}-05', 'Monthly rent')
    )

    # Food expenses (5-8 per month)
    for _ in range(random.randint(5, 8)):
        day = str(random.randint(1, 28)).zfill(2)
        amount = round(random.uniform(8, 45), 2)
        notes = random.choice(['Grocery store', 'Restaurant', 'Coffee shop', 'Takeout', 'Lunch'])
        conn.execute(
            "INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?,?,?,?,?,?)",
            (user_id, 4, amount, 'expense', f'{month}-{day}', notes)
        )

    # Utilities
    conn.execute(
        "INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?,?,?,?,?,?)",
        (user_id, 5, round(random.uniform(50, 120), 2), 'expense', f'{month}-10', 'Electric and water')
    )

    # Transport (3-5 per month)
    for _ in range(random.randint(3, 5)):
        day = str(random.randint(1, 28)).zfill(2)
        amount = round(random.uniform(5, 30), 2)
        notes = random.choice(['Bus', 'Taxi', 'Metro', 'Gas'])
        conn.execute(
            "INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?,?,?,?,?,?)",
            (user_id, 6, amount, 'expense', f'{month}-{day}', notes)
        )

    # Other expenses (1-3 per month)
    for _ in range(random.randint(1, 3)):
        day = str(random.randint(1, 28)).zfill(2)
        amount = round(random.uniform(10, 100), 2)
        notes = random.choice(['Clothes', 'Phone bill', 'Haircut', 'Gift', 'Books'])
        conn.execute(
            "INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?,?,?,?,?,?)",
            (user_id, 7, amount, 'expense', f'{month}-{day}', notes)
        )

conn.commit()
conn.close()
print("Sample data added! 6 months of entries created.")