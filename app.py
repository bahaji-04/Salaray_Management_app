
from flask import Flask, g, request, render_template, redirect
import sqlite3
 
app = Flask('__name__')
DB_PATH = 'expenses.db'
 
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
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()
    entries = db.execute("SELECT entries.*, categories.name AS category_name FROM entries JOIN categories ON entries.categories_id = categories.id").fetchall()
    return render_template("index.html", categories=categories, entries=entries)
 
@app.route("/add-entry", methods=["GET", "POST"])
def add_entry():
    db = get_db()
    if request.method == "POST":
        amount = request.form["amount"]
        category_id = request.form["category_id"]
        entry_type = request.form["type"]
        entry_date = request.form["entry_date"]
        note = request.form.get("note", "")
        db.execute("INSERT INTO entries (user_id, categories_id, amount, type, entry_date, note) VALUES (?, ?, ?, ?, ?, ?)",
            (1, category_id, amount, entry_type, entry_date, note)
        )
        db.commit()
        return redirect("/")
 
    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template("add_entry.html", categories=categories)
 
@app.route("/edit-entry/<int:entry_id>", methods=["GET", "POST"])
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
        return redirect("/")
 
    entry = db.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template("edit_entry.html", entry=entry, categories=categories)
 
@app.route("/delete-entry/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    db.commit()
    return redirect("/")
 
if __name__ == "__main__":
    app.run(debug=True)