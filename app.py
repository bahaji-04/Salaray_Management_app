from flask import Flask, g, request, render_template, redirect, abort
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg
from psycopg.rows import dict_row
import math
from datetime import datetime

from flask_login import LoginManager, UserMixin, login_user, logout_user,login_required,current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from collections import OrderedDict
 
import pandas as pd
import plotly
import plotly.graph_objects as go

import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Add it to your .env file.")

# Forest design colors (same as static/style.css)
DARK_GREEN = "#0b4a37"
MID_GREEN = "#3e9c76"
LIGHT_GREEN = "#a9d3bf"
TEXT_GREEN = "#587066"
LINE_GREEN = "#d7e4dd"

def style_chart(fig, height=320):
    # make plotly charts match the Forest design
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, system-ui, sans-serif", color=TEXT_GREEN, size=13),
        legend=dict(orientation="h", y=1.1, x=0),
        bargap=0.35,
    )
    # type="category" keeps "2026-10" as a label instead of turning it into a date like "00:00:00 Oct 1, 2026"
    fig.update_xaxes(showgrid=False, linecolor=LINE_GREEN, type="category")
    fig.update_yaxes(gridcolor=LINE_GREEN, zeroline=False, tickprefix="$")
    return plotly.io.to_html(fig, full_html=False, config={"displayModeBar": False, "responsive": True})

app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing. Add it to your .env file.")

# don't send the login cookie when another website posts a form to this app
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# every POST form must send the hidden csrf_token field
csrf = CSRFProtect(app)
# counts login attempts per IP address (kept in memory, so it resets when the app restarts)
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self,id,username):
        self.id = id 
        self.username = username
        
@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = %s",(user_id,)).fetchone()
    if user:
        return User(user["id"],user["username"])
    return None


def get_db():
    if 'db' not in g:
        g.db = psycopg.connect(DATABASE_URL)
        g.db.row_factory = dict_row
        
    return g.db
 
@app.teardown_appcontext
def db_close(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# stops huge numbers like 1e39 from overflowing the database column
MAX_AMOUNT = 1_000_000_000

def parse_amount(text):
    # a money amount bigger than 0 like "12.50", or None if the text isn't one
    try:
        amount = round(float(text), 2)
    except ValueError:
        return None
    if not math.isfinite(amount) or amount <= 0 or amount > MAX_AMOUNT:
        return None
    return amount

def parse_date(text):
    # a date written as YYYY-MM-DD, or None if the text isn't one
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None

def read_entry_form(categories):

    entry_type = request.form.get("type", "")
    amount = parse_amount(request.form.get("amount", ""))
    category_id = request.form.get("category_id", "")
    entry_date = parse_date(request.form.get("entry_date", ""))
    note = request.form.get("note", "").strip()

    if entry_type not in ("income", "expense"):
        return None, "Choose income or expense."
    if amount is None:
        return None, "Amount must be a number bigger than 0, like 12.50."
    if category_id not in [str(category["id"]) for category in categories]:
        return None, "Choose a category from the list."
    if entry_date is None:
        return None, "Enter a valid date."
    return (int(category_id), amount, entry_type, entry_date, note), None

@app.before_request
def reject_nul_characters():
    # Postgres text can't hold a NUL character, so these requests could only crash
    if "\x00" in request.path or any("\x00" in value for value in request.form.values()):
        abort(400)

@app.errorhandler(429)
def too_many_attempts(e):
    return render_template("login.html", error="Too many login attempts. Wait a minute and try again."), 429
        
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect("/spending")
    return render_template("index.html")
        
@app.route('/signup',methods=["GET","POST"])
def signup():
    db = get_db()
    if current_user.is_authenticated:
        return redirect("/spending")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password.strip():
            return render_template("signup.html", error = "Please enter a username and a password.")
        if len(username) > 50:
            return render_template("signup.html", error = "Username must be 50 characters or less.")
        check_username = db.execute("SELECT username FROM users WHERE username = %s",(username,)).fetchone()
        if check_username : 
            return render_template("signup.html",error = "this username already exits, please choose another one.")
        hash_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username,user_password) VALUES (%s,%s)",(username,hash_password))
        
        db.commit()
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login",methods=["GET","POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    db = get_db()
    if current_user.is_authenticated:
        return redirect("/spending")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("login.html",error="Please enter your username and password.")
        
        user = db.execute("""SELECT * FROM users
                   WHERE username = %s """,(username,)).fetchone()
        
        if user and check_password_hash(user["user_password"],password):
            user_things = User(user["id"],user["username"])
            login_user(user_things)
            return redirect("/spending")
        else:
            return render_template("login.html",error="Invalid password or username")
        
        
    return render_template("login.html")
        

@app.route('/spending')
@login_required
def spending():
    db = get_db()
    months = db.execute(""" SELECT substr(entry_date,1,7) AS month, 
                        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS total_income,
                        SUM (CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS total_expense
                        FROM entries 
                        WHERE user_id = %s
                        GROUP BY substr(entry_date,1,7)
                        ORDER BY month """,(current_user.id,)).fetchall()
    
    if months:
        df = pd.DataFrame(months,columns=[key for key in months[0].keys()])
        
        df["total_income"] = df["total_income"].astype(float)
        df["total_expense"] = df["total_expense"].astype(float)

        total_saving = df["total_income"] - df["total_expense"]
        
        saving_fig = go.Figure(data=[
            go.Bar(name="Income", x=df["month"].tolist(), y=df["total_income"].tolist(), marker_color=LIGHT_GREEN),
            go.Bar(name="Saving", x=df["month"].tolist(), y=total_saving.tolist(), marker_color=DARK_GREEN)
        ])
        saving_chart = style_chart(saving_fig)
        
    else:
        total_saving = []
        saving_chart = ""
                           
    return render_template("spending.html", months = months, total_saving = total_saving, saving_chart = saving_chart)

@app.route("/spending/<month>")
@login_required
def month_detail(month):
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()
    entries = db.execute("""SELECT entries.*, categories.name AS category_name 
                         FROM entries JOIN categories ON entries.categories_id = categories.id 
                         WHERE user_id = %s AND substr(entry_date,1,7) = %s
                         ORDER BY entry_date DESC, entries.id DESC """,(current_user.id, month )).fetchall()
    
    total = db.execute(""" SELECT SUM(CASE WHEN type = 'income' THEN amount else 0 END) AS total_income,
                       SUM(CASE WHEN type = 'expense' THEN amount else 0 END ) AS total_expense
                       FROM entries
                       WHERE substr(entry_date,1,7) = %s AND user_id = %s """,(month,current_user.id)).fetchone()
    
    # making the dataframe from the database 
    if entries:
        df = pd.DataFrame(entries,columns=[key for key in entries[0].keys()])
        expenses_only = df["amount"] = df["amount"].astype(float)
        
        expenses_only = df[df["type"] == "expense"]
        # how much I spent in every category
        total_category = expenses_only.groupby("category_name")["amount"].sum()
        
        #top 3 expenses 
        top_3 = expenses_only.nlargest(3, "amount")
        
        #avg daily spent
        total_expense = expenses_only["amount"].sum()
        uniq_days = expenses_only["entry_date"].nunique() # returns a number not like unique() returns a list
        
        if uniq_days > 0:
            daily_avg_expense = total_expense / uniq_days
        else: 
            daily_avg_expense = 0
            
        # bar chart of catefories
        fig = go.Bar(x=total_category.index.tolist(),y=total_category.values.tolist(),
                     marker_color=DARK_GREEN, text=total_category.values.round(0).tolist(),
                     texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
        chart = style_chart(go.Figure(data=[fig]))

        fig2 = go.Pie(labels=top_3["category_name"].tolist(),values=top_3["amount"].tolist(),
                      marker=dict(colors=[DARK_GREEN, MID_GREEN, LIGHT_GREEN], line=dict(color="#ffffff", width=2)),
                      sort=False)
        chart2 = style_chart(go.Figure(data=[fig2]), height=260)
        
         
    else:
        total_category = {}
        top_3 = []
        daily_avg_expense = 0
        chart = ""
        chart2 = ""

    
        
    return render_template("month_detail.html", categories = categories, entries = entries,
                           month = month,total = total, total_category = total_category,
                           top_3 = top_3, daily_avg_expense = daily_avg_expense,
                           chart = chart, chart2 = chart2 )
 
@app.route("/add-entry", methods=["GET", "POST"])
@login_required
def add_entry():
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()
    if request.method == "POST":
        values, error = read_entry_form(categories)
        if error:
            return render_template("add_entry.html", categories=categories, error=error)
        
        category_id, amount, entry_type, entry_date, note = values
        db.execute("INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (%s, %s, %s, %s, %s, %s)",
            (current_user.id , category_id, amount, entry_type, entry_date, note))
        db.commit()
        return redirect("/spending")
 
    return render_template("add_entry.html", categories=categories)
 
@app.route("/edit-entry/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    db = get_db()
    entry = db.execute("SELECT * FROM entries WHERE user_id = %s and id = %s", (current_user.id, entry_id)).fetchone()
    if not entry:
        abort(404)
    categories = db.execute("SELECT * FROM categories").fetchall()
    if request.method == "POST":
        values, error = read_entry_form(categories)
        if error:
            return render_template("edit_entry.html", entry=entry, categories=categories, error=error)
        category_id, amount, entry_type, entry_date, note = values
        db.execute(
            "UPDATE entries SET amount=%s, categories_id=%s, type=%s, entry_date=%s, note=%s WHERE id=%s and user_id=%s",
            (amount, category_id, entry_type, entry_date, note, entry_id, current_user.id)
        )
        db.commit()
        return redirect("/spending")
    
    return render_template("edit_entry.html", entry=entry, categories=categories)

def render_goals(error=None):
    goals = get_db().execute(""" SELECT * FROM targets 
                       WHERE user_id = %s ORDER BY id """,(current_user.id,)).fetchall()
    return render_template("goal.html", goals = goals, error = error)

@app.route("/goal",methods=["GET","POST"])
@login_required
def goal():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        target_amount = parse_amount(request.form.get("target_amount", ""))
        if not name or len(name) > 100:
            return render_goals("Goal name must be between 1 and 100 characters.")
        if target_amount is None:
            return render_goals("Target amount must be a number bigger than 0, like 2000.")
        db.execute("""INSERT INTO targets (user_id, name, target_amount)
                   VALUES (%s,%s,%s)""",(current_user.id,name,target_amount))
        
        db.commit()
        return redirect("/goal")

    return render_goals()

@app.route("/goal/<int:goal_id>/contribution", methods=["POST"])
@login_required
def contribution(goal_id):
    db = get_db()
    target = db.execute("SELECT * FROM targets WHERE id = %s AND user_id = %s",(goal_id,current_user.id)).fetchone()
    if not target:
        abort(404)
    amount = parse_amount(request.form.get("amount", ""))
    contribution_date = parse_date(request.form.get("contribution_date", ""))
    if amount is None:
        return render_goals("Amount saved must be a number bigger than 0, like 50.")
    if contribution_date is None:
        return render_goals("Enter a valid date for the contribution.")
        
    db.execute(""" INSERT INTO contribution (goal_id,amount,contribution_date) 
               VALUES (%s,%s,%s) """,(goal_id,amount,contribution_date))
    db.execute(""" UPDATE targets SET 
               current_amount = current_amount + %s
               WHERE id = %s AND user_id = %s """,(amount,goal_id,current_user.id))
    db.commit()
    
    return redirect("/goal")

@app.route("/goal/<int:goal_id>",methods=["GET"])
@login_required
def contribution_detail(goal_id):
    db = get_db()
    target = db.execute("SELECT * FROM targets WHERE id = %s AND user_id = %s",(goal_id,current_user.id)).fetchone()
    if not target:
        abort(404)
    contribution = db.execute("SELECT * FROM contribution WHERE goal_id = %s ORDER BY time_created DESC",(goal_id,)).fetchall()
    
    return render_template("contribution_detail.html",target = target, contribution=contribution )
          
    
 
@app.route("/delete-entry/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    db = get_db()
    
    db.execute("DELETE FROM entries WHERE id=%s AND user_id=%s", (entry_id, current_user.id))
    db.commit()
    return redirect("/spending")


@app.route("/account",methods=["GET","POST"])
@login_required
def account():
    db = get_db()
    
    user = db.execute("SELECT * FROM users WHERE id = %s",(current_user.id,)).fetchone()
    
    return render_template("account.html",user = user)

@app.route("/account/user-password", methods=["GET","POST"])
@login_required
def change_password():
    db = get_db()
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        if not new_password.strip():
            return render_template("change_password.html", error="New password can't be empty.")
        
        user = db.execute("SELECT * FROM users WHERE id = %s",(current_user.id,)).fetchone()
        
        if check_password_hash(user["user_password"],old_password):
            new = generate_password_hash(new_password)
            db.execute("UPDATE users SET user_password=%s WHERE id = %s",(new,current_user.id))
            db.commit()
            return redirect("/account")
        else:
            return render_template("change_password.html", error="Old password is incorrect")
        
        
    return render_template("change_password.html")

@app.route("/account/delete",methods=["POST"])
@login_required
def delete_account():
    db = get_db()
    db.execute("DELETE FROM entries WHERE user_id = %s",(current_user.id,))
    db.execute(""" DELETE FROM contribution WHERE goal_id IN 
               (SELECT id FROM targets WHERE user_id = %s )""",(current_user.id,))
    db.execute("DELETE FROM targets WHERE user_id = %s ",(current_user.id,))
    db.execute("DELETE FROM users WHERE id = %s ",(current_user.id,))
    
    db.commit()
    logout_user()
    
    return redirect("/")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect("/")
 
if __name__ == "__main__":
    # FLASK_DEBUG=1 in .env turns on the debugger; keep it off anywhere other people can reach the app
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5001)