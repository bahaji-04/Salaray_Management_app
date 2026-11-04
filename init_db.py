import psycopg
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Add it to your .env file.")

connection = psycopg.connect(DATABASE_URL)

with open('schema.sql', 'r') as f:
    connection.execute(f.read())

connection.commit()
connection.close()

print('Database initialized successfully.')
