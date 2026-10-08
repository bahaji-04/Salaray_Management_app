from flask import Flask, g, request, render_template, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from flask_login import LoginManager, UserMixin, login_user, logout_user,login_required,current_user
from collections import OrderedDict
 
app = Flask('__name__')
DB_PATH = 'expenses.db'

app.secret_key = "your-secret-key-change-this-later"
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
    return render_template("index.html")
        
@app.route('/signup',methods=["GET","POST"])
def signup():
    db = get_db()
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hash_password = generate_password_hash(password)
        db.execute("INSERT INTO user (username,user_password) VALUES (?,?)",(username,hash_password))
        
        db.commit()
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login",methods=["GET","POST"])
def login():
    db = get_db()
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
                        
                          
    return render_template("spending.html", months = months)

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
    
    return render_template("month_detail.html", categories = categories, entries = entries, month = month, total = total)
 
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
            "UPDATE entries SET amount=?, categories_id=?, type=?, entry_date=?, note=? WHERE id=?",
            (amount, category_id, entry_type, entry_date, note, entry_id)
        )
        db.commit()
        return redirect("/spending")
 
    entry = db.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template("edit_entry.html", entry=entry, categories=categories)
 
@app.route("/delete-entry/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    db.commit()
    return redirect("/spending")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")
 
if __name__ == "__main__":
    app.run(debug=True)