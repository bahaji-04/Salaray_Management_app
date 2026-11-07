# Salary App

A personal salary and expense manager built with Flask and PostgreSQL. Log your income and expenses, see each month broken down by category, and put savings toward goals you set.

**Live app:** https://salaray-management-app.onrender.com

## Features

- **Monthly summary**: total income, total spent, total saved and savings rate across all months, with an income-vs-savings chart and a table of every month.
- **Month detail**: spending by category, your top 3 expenses, average daily spend, and every entry for the month, which you can edit or delete.
- **Entries**: income or expense, with an amount, a category, a date and an optional note.
- **Savings goals**: set a target amount, add contributions as you save, and watch a progress bar fill. Each goal has a page listing its contributions.
- **Accounts**: sign up, log in, change your password, or delete your account along with all of its data.

Charts are drawn with Plotly and styled to match the app's green theme.

## Tech stack

| Layer | Tools |
| --- | --- |
| Web framework | Flask 3, Jinja templates |
| Auth and security | Flask-Login, Flask-WTF (CSRF), Flask-Limiter, Werkzeug password hashing |
| Database | PostgreSQL through psycopg 3 |
| Charts and analysis | pandas, Plotly |
| Production server | Gunicorn |

## Quick start

### 1. Prerequisites

- Python 3.10 or newer
- PostgreSQL running locally or reachable over the network

### 2. Clone and install

```bash
git clone https://github.com/bahaji-04/Salaray_Management_app.git
```

```bash
cd Salaray_Management_app
```

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 3. Create a database

```bash
createdb salary_app
```

### 4. Configure the environment

Create a `.env` file in the project root:

```env
SECRET_KEY=replace-with-a-long-random-string
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/salary_app
FLASK_DEBUG=1
```

| Variable | Required | What it does |
| --- | --- | --- |
| `SECRET_KEY` | Yes | Signs session cookies and CSRF tokens. The app won't start without it. |
| `DATABASE_URL` | Yes | PostgreSQL connection string. The app won't start without it. |
| `FLASK_DEBUG` | No | Set to `1` to turn on the Flask debugger when you run `python app.py`. Leave it off anywhere other people can reach the app. |

One way to make a secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

`.env` is in `.gitignore`, so your secrets stay out of git.

### 5. Create the tables

```bash
python init_db.py
```

This runs `schema.sql`, which creates the tables and adds the default categories. It's safe to run again.

### 6. Run the app

```bash
python app.py
```

Open http://127.0.0.1:5001, create an account and start adding entries.

## Sample data (optional)

`data.py` fills six months (April to September 2026) with random salary, freelance, rent, food, utilities, transport and other entries. It writes them to the user with id `1`, so sign up first and then run:

```bash
python data.py
```

Each run adds another set of entries, so run it once.

## Running in production

Use Gunicorn instead of the Flask development server:

```bash
gunicorn app:app --bind 0.0.0.0:8000
```

Set `SECRET_KEY` and `DATABASE_URL` in the server's environment (or a `.env` file) and leave `FLASK_DEBUG` unset.

The login rate limit is kept in memory, so it resets when the app restarts and each Gunicorn worker counts attempts separately.

### Deploying on Render

The live app runs on [Render](https://render.com). To deploy your own copy:

1. Create a **PostgreSQL** database on Render and copy its **Internal Database URL**.
2. Create a **Web Service** from this repository with:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
3. Under **Environment**, add `SECRET_KEY` (a long random string) and `DATABASE_URL` (the Internal Database URL from step 1).
4. Create the tables once. Run `python init_db.py` on your own machine with `DATABASE_URL` set to the database's **External Database URL**. Or add it to the build command: `pip install -r requirements.txt && python init_db.py`, which is safe because the script can run more than once.

You don't need to set a port. Gunicorn listens on the `PORT` that Render provides.

## Project structure

```
.
├── app.py             # Flask app: routes, auth, validation, charts
├── init_db.py         # Creates the tables from schema.sql
├── schema.sql         # Table definitions and default categories
├── data.py            # Optional sample data for user 1
├── requirements.txt   # Python dependencies
├── static/
│   └── style.css      # App styles
└── templates/         # Jinja templates, all extending base.html
```

## Pages

| Path | What it shows |
| --- | --- |
| `/` | Landing page (sends you to `/spending` if you're logged in) |
| `/signup`, `/login` | Create an account or log in |
| `/spending` | Monthly summary |
| `/spending/<YYYY-MM>` | One month in detail |
| `/add-entry` | Add an income or expense |
| `/edit-entry/<id>` | Edit an entry |
| `/goal` | Your goals, with forms to create a goal and add contributions |
| `/goal/<id>` | One goal and its contributions |
| `/account` | Account details and account deletion |
| `/account/user-password` | Change your password |

Every page except the landing, sign-up and login pages needs you to be logged in.

## Data model

| Table | Holds |
| --- | --- |
| `users` | Username, hashed password, sign-up time |
| `categories` | Shared categories, each marked `income` or `expense` |
| `entries` | A user's income and expense entries |
| `targets` | A user's savings goals: target amount and amount saved so far |
| `contribution` | Money added to a goal, with its date |

Money is stored as `NUMERIC(12,2)` so cents stay exact. Amounts must be above 0 and at most 1,000,000,000.

Default categories: Salary and Freelance (income); Rent, Food, Utilities, Transport and Other (expense). To add more, insert rows into `categories`. Every user shares the same list.

## Security

- Passwords are hashed with Werkzeug and never stored in plain text.
- Every form carries a CSRF token, and the session cookie uses `SameSite=Lax`.
- Login attempts are limited to 5 per minute per IP address.
- Every query is filtered by the logged-in user, so you can only see and change your own entries and goals.
- Requests containing NUL characters are rejected with a 400.

## Changing the schema

`schema.sql` uses `CREATE TABLE IF NOT EXISTS`, so running `init_db.py` again won't change tables that already exist. If you edit a column in `schema.sql`, apply the change to an existing database yourself with `ALTER TABLE`, or drop the database and run `init_db.py` again.
