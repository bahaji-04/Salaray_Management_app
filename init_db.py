import sqlite3

DB_PATH = 'expenses.db'

connection = sqlite3.connect(DB_PATH)

with open('schema.sql', 'r') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print('Database initialized successfully.')
