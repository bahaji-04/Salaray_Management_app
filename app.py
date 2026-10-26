from flask import Flask, g, request, render_template, redirect, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from flask_login import LoginManager, UserMixin, login_user, logout_user,login_required,current_user
from collections import OrderedDict
 
import pandas as pd
import plotly
import plotly.graph_objects as go

import os
from dotenv import load_dotenv

load_dotenv()


app = Flask('__name__')
DB_PATH = 'expenses.db'

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
    user = db.execute("SELECT * FROM user WHERE id = ?",(user_id,)).fetchone()
    if user:
        return User(user["id"],user["username"])
    return None


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db
 
@app.teardown_appcontext
def db_close(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        
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
        username = request.form["username"]
        password = request.form["password"]
        check_username = db.execute("SELECT username FROM user WHERE username = ?",(username,)).fetchone()
        if check_username : 
            return render_template("signup.html",error = "this username already exits, please choose another one.")
        hash_password = generate_password_hash(password)
        db.execute("INSERT INTO user (username,user_password) VALUES (?,?)",(username,hash_password))
        
        db.commit()
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login",methods=["GET","POST"])
def login():
    db = get_db()
    if current_user.is_authenticated:
        return redirect("/spending")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = db.execute("""SELECT * FROM user
                   WHERE username = ? """,(username,)).fetchone()
        
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
    months = db.execute(""" SELECT substr(entry_date,1,7) AS Month, 
                        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS Total_Income,
                        SUM (CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS Total_Expense
                        FROM entries 
                        WHERE user_id = ?
                        GROUP BY substr(entry_date,1,7) """,(current_user.id,)).fetchall()
    
    if months:
        df = pd.DataFrame(months,columns=[key for key in months[0].keys()])
        
        total_saving = df["Total_Income"] - df["Total_Expense"]
        
        saving_fig = go.Figure(data=[
            go.Bar(name="Income", x=df["Month"].tolist(), y=df["Total_Income"].tolist(), marker_color=LIGHT_GREEN),
            go.Bar(name="Saving", x=df["Month"].tolist(), y=total_saving.tolist(), marker_color=DARK_GREEN)
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
                         WHERE user_id = ? AND substr(entry_date,1,7) = ?
                         ORDER BY entry_date DESC """,(current_user.id, month )).fetchall()
    
    total = db.execute(""" SELECT SUM(CASE WHEN type = 'income' THEN amount else 0 END) AS Total_Income,
                       SUM(CASE WHEN type = 'expense' THEN amount else 0 END ) AS Total_Expense
                       FROM entries
                       WHERE substr(entry_date,1,7) = ? AND user_id = ? 
                       ORDER BY entry_date ASC""",(month,current_user.id)).fetchone()
    
    # making the dataframe from the database 
    if entries:
        df = pd.DataFrame(entries,columns=[key for key in entries[0].keys()])
        
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
    if request.method == "POST":
        amount = request.form["amount"]
        category_id = request.form["category_id"]
        entry_type = request.form["type"]
        entry_date = request.form["entry_date"]
        note = request.form.get("note", "")
        db.execute("INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?, ?, ?, ?, ?, ?)",
            (current_user.id , category_id, amount, entry_type, entry_date, note)
        )
        db.commit()
        return redirect("/spending")
 
    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template("add_entry.html", categories=categories)
 
@app.route("/edit-entry/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    db = get_db()
    if request.method == "POST":
        amount = request.form["amount"]
        category_id = request.form["category_id"]
        entry_type = request.form["type"]
        entry_date = request.form["entry_date"]
        note = request.form.get("note", "")
        db.execute(
            "UPDATE entries SET amount=?, categories_id=?, type=?, entry_date=?, note=? WHERE id=? and user_id=?",
            (amount, category_id, entry_type, entry_date, note, entry_id, current_user.id)
        )
        db.commit()
        return redirect("/spending")
 
    entry = db.execute("SELECT * FROM entries WHERE user_id = ? and id = ?", (current_user.id, entry_id)).fetchone()
    if not entry:
        abort(404)
    categories = db.execute("SELECT * FROM categories").fetchall()
    
    return render_template("edit_entry.html", entry=entry, categories=categories)

@app.route("/goal",methods=["GET","POST"])
@login_required
def goal():
    db = get_db()
    if request.method == "POST":
        name = request.form["name"]
        target_amount = request.form["target_amount"]
        db.execute("""INSERT INTO targets (user_id, name, target_amount)
                   VALUES (?,?,?)""",(current_user.id,name,target_amount))
        
        db.commit()
        return redirect("/goal")

    goals = db.execute(""" SELECT * FROM targets 
                       WHERE user_id = ? """,(current_user.id,)).fetchall()
    return render_template("goal.html", goals = goals)

@app.route("/goal/<int:goal_id>/contribution", methods=["POST"])
@login_required
def contribution(goal_id):
    db = get_db()
    amount = request.form["amount"]
    contribution_date = request.form["contribution_date"]
    target = db.execute("SELECT * FROM targets WHERE id = ? AND user_id = ?",(goal_id,current_user.id)).fetchone()
    if not target:
        abort(404)
        
    db.execute(""" INSERT INTO contribution (goal_id,amount,contribution_date) 
               VALUES (?,?,?) """,(goal_id,amount,contribution_date))
    db.execute(""" UPDATE targets SET 
               current_amount = current_amount + ?
               WHERE id = ? AND user_id = ? """,(amount,goal_id,current_user.id))
    db.commit()
    
    return redirect("/goal")

@app.route("/goal/<int:goal_id>",methods=["GET"])
@login_required
def contribution_detail(goal_id):
    db = get_db()
    target = db.execute("SELECT * FROM targets WHERE id = ? AND user_id = ?",(goal_id,current_user.id)).fetchone()
    if not target:
        abort(404)
    contribution = db.execute("SELECT * FROM contribution WHERE goal_id = ? ORDER BY time_created DESC",(goal_id,)).fetchall()
    
    return render_template("contribution_detail.html",target = target, contribution=contribution )
          
    
 
@app.route("/delete-entry/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    db = get_db()
    
    db.execute("DELETE FROM entries WHERE id=? AND user_id=?", (entry_id, current_user.id))
    db.commit()
    return redirect("/spending")


@app.route("/account",methods=["GET","POST"])
@login_required
def account():
    db = get_db()
    
    user = db.execute("SELECT * FROM user WHERE id = ?",(current_user.id,)).fetchone()
    
    return render_template("account.html",user = user)

@app.route("/account/user-password", methods=["GET","POST"])
@login_required
def change_password():
    db = get_db()
    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        
        user = db.execute("SELECT * FROM user WHERE id = ?",(current_user.id,)).fetchone()
        
        if check_password_hash(user["user_password"],old_password):
            new = generate_password_hash(new_password)
            db.execute("UPDATE user SET user_password=? WHERE id = ?",(new,current_user.id))
            db.commit()
            return redirect("/account")
        else:
            return render_template("change_password.html", error="Old password is incorrect")
        
        
    return render_template("change_password.html")

@app.route("/account/delete",methods=["POST"])
@login_required
def delete_account():
    db = get_db()
    db.execute("DELETE FROM entries WHERE user_id = ?",(current_user.id,))
    db.execute("DELETE FROM targets WHERE user_id = ? ",(current_user.id,))
    db.execute("DELETE FROM user WHERE id = ? ",(current_user.id,))
    
    db.commit()
    logout_user()
    
    return redirect("/")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")
 
if __name__ == "__main__":
    app.run(debug=True)