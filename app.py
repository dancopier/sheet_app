from flask import Flask, render_template, request, redirect, session
import csv
import os

app = Flask(__name__)
app.secret_key = "secret123"

SHEET_FILE = "sheet.csv"
USERS_FILE = "users.csv"

# Default sheet size
ROWS = 5
COLS = 5

# ---- Helper functions ----
def load_sheet():
    if not os.path.exists(SHEET_FILE):
        return [["" for _ in range(COLS)] for _ in range(ROWS)]
    with open(SHEET_FILE) as f:
        return list(csv.reader(f))

def save_sheet(sheet):
    with open(SHEET_FILE, "w", newline="") as f:
        csv.writer(f).writerows(sheet)

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return [row for row in csv.reader(f)]

def add_user(username, password, role):
    users = load_users()
    for u in users:
        if u[0] == username:
            return False
    with open(USERS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([username, password, role])
    return True

def check_user(username, password):
    users = load_users()
    for u in users:
        if u[0] == username and u[1] == password:
            return u[2]  # return role
    return None

def ensure_min_sheet(sheet):
    # Make sure at least 1 empty row at bottom
    if all(cell != "" for cell in sheet[-1]):
        sheet.append(["" for _ in range(len(sheet[0]))])
    return sheet

# ---- Routes ----

# Home redirects to login
@app.route("/")
def home():
    return redirect("/login")

# Unified login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role")  # admin or employee

        user_role = check_user(username, password)
        if user_role == role:
            session["user"] = username
            session["role"] = role
            return redirect("/sheet")
        else:
            return "Login failed: wrong username, password, or role"
    return render_template("login.html")

# Admin register (only admin can register new admin)
@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():
    if "role" not in session or session["role"] != "admin":
        return "Only logged-in admin can register a new admin"

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        success = add_user(username, password, "admin")
        if success:
            return redirect("/sheet")
        else:
            return "Username already exists"
    return render_template("admin_register.html")

# Employee register
@app.route("/employee_register", methods=["GET", "POST"])
def employee_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        success = add_user(username, password, "employee")
        if success:
            return redirect("/login")
        else:
            return "Username already exists"
    return render_template("employee_register.html")

# Sheet page
@app.route("/sheet", methods=["GET", "POST"])
def sheet():
    if "user" not in session:
        return redirect("/login")

    sheet = load_sheet()
    sheet = ensure_min_sheet(sheet)

    # Only admin can POST edits
    if request.method == "POST" and session["role"] == "admin":
        action = request.form.get("action")
        if action == "edit":
            r = int(request.form["row"])
            c = int(request.form["col"])
            val = request.form["value"]
            sheet[r][c] = val
        elif action == "add_row":
            sheet.append(["" for _ in range(len(sheet[0]))])
        elif action == "delete_row":
            idx = int(request.form["row"])
            if len(sheet) > 1:
                sheet.pop(idx)
        elif action == "add_col":
            for row in sheet:
                row.append("")
        elif action == "delete_col":
            idx = int(request.form["col"])
            if len(sheet[0]) > 1:
                for row in sheet:
                    row.pop(idx)

        save_sheet(sheet)

    return render_template("sheet.html", sheet=sheet, role=session["role"])

# Background auto-save route (admin only)
@app.route("/update_cell", methods=["POST"])
def update_cell():
    if "user" not in session or session["role"] != "admin":
        return "", 403
    sheet = load_sheet()
    r = int(request.form["row"])
    c = int(request.form["col"])
    val = request.form["value"]
    sheet[r][c] = val
    save_sheet(sheet)
    return "", 200

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---- Main ----
if __name__ == "__main__":
    app.run()
