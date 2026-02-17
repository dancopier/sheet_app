from flask import Flask, render_template, request, redirect, session
import csv
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Files
SHEET_FILE = "sheet.csv"
USERS_FILE = "users.csv"

# Fixed columns
COLS = 3

# ---- Helper functions ----
def load_sheet():
    """Load the sheet from CSV or create default with 3 columns and clean empty rows."""
    if not os.path.exists(SHEET_FILE):
        # Start with 3 rows (header + 2 rows), 3 columns
        return [["Header 1", "Header 2", "Header 3"]] + [["" for _ in range(COLS)] for _ in range(2)]
    
    with open(SHEET_FILE, newline="") as f:
        sheet = list(csv.reader(f))
    
    # Remove completely empty rows at the bottom, except header
    sheet = [sheet[0]] + [row for row in sheet[1:] if any(cell.strip() != "" for cell in row)]
    
    # If sheet is empty after cleaning, create header + 2 empty rows
    if len(sheet) == 0:
        sheet = [["Header 1", "Header 2", "Header 3"]] + [["" for _ in range(COLS)] for _ in range(2)]
    
    return ensure_fixed_columns(sheet)


def save_sheet(sheet):
    with open(SHEET_FILE, "w", newline="") as f:
        csv.writer(f).writerows(sheet)


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, newline="") as f:
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
            return u[2]
    return None


def ensure_fixed_columns(sheet):
    """Ensure each row has exactly 3 columns."""
    for r in range(len(sheet)):
        while len(sheet[r]) < COLS:
            sheet[r].append("")
        if len(sheet[r]) > COLS:
            sheet[r] = sheet[r][:COLS]
    return sheet


# ---- Routes ----
@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = check_user(username, password)
        if role:
            session["user"] = username
            session["role"] = role
            if role == "admin":
                return redirect("/admin_dashboard")
            else:
                return redirect("/employee_dashboard")
        return "Invalid username or password!"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/login")
    return redirect("/sheet")


@app.route("/employee_dashboard")
def employee_dashboard():
    if session.get("role") != "employee":
        return redirect("/login")
    return redirect("/sheet")


@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():
    if session.get("role") != "admin":
        return "Only admin can register a new admin"
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if add_user(username, password, "admin"):
            return redirect("/sheet")
        else:
            return "Username already exists"
    return render_template("admin_register.html")


@app.route("/employee_register", methods=["GET", "POST"])
def employee_register():
    if session.get("role") != "admin":
        return "Only admin can register a new employee"
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if add_user(username, password, "employee"):
            return redirect("/sheet")
        else:
            return "Username already exists"
    return render_template("employee_register.html")


# --- Sheet Page ---
@app.route("/sheet")
def sheet():
    if "user" not in session:
        return redirect("/login")
    sheet = load_sheet()
    return render_template("sheet.html", sheet=sheet, role=session["role"])


# --- Update Cell (Admin Only) ---
# --- Update Cell (Admin Only) ---
@app.route("/update_cell", methods=["POST"])
def update_cell():
    if session.get("role") != "admin":
        return "", 403

    sheet = load_sheet()
    r = int(request.form["row"])
    c = int(request.form["col"])
    val = request.form["value"]

    while len(sheet) <= r:
        sheet.append(["" for _ in range(COLS)])

    sheet[r][c] = val

    # Auto-add new row if last row fully filled
    if r == len(sheet) - 1 and all(sheet[r][i].strip() != "" for i in range(COLS)):
        sheet.append(["" for _ in range(COLS)])

    save_sheet(sheet)
    return "", 200



# ---- Main ----
if __name__ == "__main__":
    # Add default admin if file not exists
    # Ensure default admin exists when app starts
    if not os.path.exists(USERS_FILE):
        add_user("admin", "admin123", "admin")

