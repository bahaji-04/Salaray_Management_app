# Salary Management App

A Flask-based personal finance tracker for managing income, expenses, spending trends, and savings goals. The app is built to help users stay on top of their finances with a clean dashboard, category-based tracking, and simple monthly insights.

## Overview

This project is a personal budgeting application that lets users:

- create an account and log in securely
- record income and expense entries with a date and note
- organize transactions by category
- view monthly spending summaries
- analyze expenses by category and top spending areas
- set savings goals and record contributions toward them
- manage account details and update passwords

## Features

- User authentication with secure password hashing
- Login rate limiting to reduce repeated failed attempts
- Add, edit, and delete financial entries
- Track both income and expense records
- Categorized transaction system
- Monthly overview dashboard
- Visual spending charts using Plotly
- Savings goal tracker with contribution history
- SQLite database for lightweight local storage
- Clean HTML/CSS interface with a modern green theme

## Tech Stack

- Python
- Flask
- SQLite
- Jinja2 Templates
- Pandas
- Plotly
- Flask-Login
- Flask-WTF
- Flask-Limiter
- Werkzeug

## Project Structure

```text
Salaray_Management_app/
├── app.py                  # Main Flask application
├── data.py                 # Data-related logic/helpers
├── init_db.py             # Creates the SQLite database and schema
├── schema.sql             # Database tables and default category data
├── .env                   # Environment variables (SECRET_KEY)
├── .gitignore
├── expenses.db            # SQLite database generated at runtime
├── static/
│   └── style.css          # App styling and layout
├── templates/
│   ├── account.html
│   ├── add_entry.html
│   ├── base.html
│   ├── change_password.html
│   ├── contribution_detail.html
│   ├── edit_entry.html
│   ├── goal.html
│   ├── index.html
│   ├── login.html
│   ├── month_detail.html
│   ├── signup.html
│   └── spending.html
├── README.md
└── requirements.txt       # Optional if added later for dependency installation
```

## Database Design

The project uses SQLite with the following core tables:

- `user` — stores account information
- `categories` — stores predefined spending/income categories
- `entries` — stores financial transactions
- `targets` — stores savings goals
- `contribution` — stores progress contributions to goals

Default categories included:

- Salary (income)
- Freelance (income)
- Rent (expense)
- Food (expense)
- Utilities (expense)
- Transport (expense)
- Other (expense)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/bahaji-04/Salaray_Management_app.git
cd Salaray_Management_app
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask flask-login flask-wtf flask-limiter pandas plotly python-dotenv
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_secret_key_here
FLASK_DEBUG=1
```

### 5. Initialize the database

```bash
python init_db.py
```

### 6. Run the application

```bash
python app.py
```

Then open:

```text
http://localhost:5001
```

## Usage

1. Sign up for a new account.
2. Log in with your credentials.
3. Add your income and expense records.
4. View monthly totals and category spending trends.
5. Open detailed monthly reports to inspect transaction history.
6. Create and track savings goals.
7. Update your account and password settings whenever needed.

## Screens and Functionality

The app includes pages for:

- landing page and login/signup
- spending dashboard
- monthly expense details
- add/edit entries
- goal management and contributions
- account settings and profile management

## Notes

- The app expects a valid `SECRET_KEY` to run properly.
- `expenses.db` is created locally and stores all user data.
- This project is suitable for personal budgeting and learning full-stack Flask app development.

## Future Enhancements

Possible next improvements include:

- CSV import/export support
- recurring transactions
- report export to PDF/CSV
- mobile-responsive improvements
- user dashboards with advanced analytics
- dark mode and theme customization

## License

This project does not currently include a formal license file. Please check with the repository owner before using it for commercial or public distribution.
