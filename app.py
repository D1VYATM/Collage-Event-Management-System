from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret"  # change for production

DB_PATH = Path(__file__).parent / "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # users: students who registered in system
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    # events
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date TEXT
    )
    """)
    # participants: who registered for which event
    cur.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        name TEXT,
        email TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id)
    )
    """)
    # feedback
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

# initialize DB
init_db()

# Simple default admin credentials (for demo). Change in real use.
ADMIN_PASSWORD = "admin123"




# splash route (opening page)
@app.route("/")
def splash():
    return render_template("splash.html")

# home route (previously index) — keep same functionality, just new route name /home
@app.route("/home")
def home():
    conn = get_db()
    events = conn.execute("SELECT * FROM events ORDER BY date").fetchall()
    conn.close()
    return render_template("index.html", events=events)




# ------------ Register & Login for users ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        if not name or not email or not password:
            flash("Please fill all fields", "danger")
            return redirect(url_for("register"))
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name,email,password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            flash("Registered successfully. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("events"))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

# ------------ Events & participant registration ----------------
@app.route("/events")
def events():
    conn = get_db()
    events = conn.execute("SELECT * FROM events ORDER BY date").fetchall()
    conn.close()
    return render_template("events.html", events=events)

@app.route("/register_event/<int:event_id>", methods=["POST"])
def register_event(event_id):
    name = request.form.get("name") or session.get("user_name") or request.form.get("guest_name")
    email = request.form.get("email") or request.form.get("guest_email")
    if not name or not email:
        flash("Please provide name and email to register.", "danger")
        return redirect(url_for("events"))
    conn = get_db()
    conn.execute("INSERT INTO participants (event_id,name,email) VALUES (?, ?, ?)", (event_id, name, email))
    conn.commit()
    conn.close()
    flash("Registered for event successfully!", "success")
    return redirect(url_for("events"))

# ------------ Feedback ----------------
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        if not message:
            flash("Please enter feedback message.", "danger")
            return redirect(url_for("feedback"))
        conn = get_db()
        conn.execute("INSERT INTO feedback (name,email,message) VALUES (?,?,?)", (name, email, message))
        conn.commit()
        conn.close()
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("index"))
    return render_template("feedback.html")

# ------------ Simple rule-based Chatbot ----------------
def bot_reply(message):
    msg = message.lower()
    if any(x in msg for x in ["hello", "hi", "hey"]):
        return "Hi! I'm the event assistant. Ask me about events, registration or feedback."
    if "events" in msg or "event" in msg:
        return "You can view events on the Events page. Which event are you interested in?"
    if "register" in msg or "signup" in msg:
        return "To register, go to the Events page and click Register on the event you want."
    if "admin" in msg:
        return "Admin can login at /admin-login. Only admins can add events or view participants."
    if "thanks" in msg or "thank" in msg:
        return "You're welcome! 😊"
    return "Sorry, I didn't understand. Try asking 'What events are there?' or 'How to register?'"

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json() or {}
    msg = data.get("message", "")
    reply = bot_reply(msg)
    return jsonify({"reply": reply})

# ------------ Admin ----------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if pwd == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Admin logged in", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Wrong admin password", "danger")
            return redirect(url_for("admin_login"))
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        flash("Admin access required", "danger")
        return redirect(url_for("admin_login"))
    conn = get_db()
    events = conn.execute("SELECT * FROM events ORDER BY date").fetchall()
    feedbacks = conn.execute("SELECT * FROM feedback ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", events=events, feedbacks=feedbacks)

@app.route("/admin/create_event", methods=["POST"])
def admin_create_event():
    if not session.get("is_admin"):
        flash("Admin access required", "danger")
        return redirect(url_for("admin_login"))
    title = request.form.get("title")
    description = request.form.get("description")
    date = request.form.get("date")
    conn = get_db()
    conn.execute("INSERT INTO events (title,description,date) VALUES (?, ?, ?)", (title, description, date))
    conn.commit()
    conn.close()
    flash("Event created", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/participants/<int:event_id>")
def admin_participants(event_id):
    if not session.get("is_admin"):
        flash("Admin access required", "danger")
        return redirect(url_for("admin_login"))
    conn = get_db()
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    participants = conn.execute("SELECT * FROM participants WHERE event_id = ? ORDER BY timestamp DESC", (event_id,)).fetchall()
    conn.close()
    return render_template("participants.html", event=event, participants=participants)

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Admin logged out", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
