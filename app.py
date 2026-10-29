
from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("employees.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            designation TEXT NOT NULL,
            joining_date TEXT NOT NULL,
            basic_salary REAL NOT NULL,
            hra REAL NOT NULL,
            da REAL NOT NULL,
            allowances REAL NOT NULL,
            pf REAL NOT NULL,
            esi REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db_connection()
    employees = conn.execute(
        "SELECT * FROM employees ORDER BY employee_id"
    ).fetchall()
    conn.close()
    return render_template("index.html", employees=employees)


@app.route("/add_employee", methods=["POST"])
def add_employee():
    employee = (
        request.form["employee_id"].strip(),
        request.form["name"].strip(),
        request.form["designation"].strip(),
        request.form["joining_date"],
        float(request.form["basic_salary"]),
        float(request.form["hra"]),
        float(request.form["da"]),
        float(request.form["allowances"]),
        float(request.form["pf"]),
        float(request.form["esi"])
    )

    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO employees
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, employee)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Employee ID already exists. Please use a unique ID.", 400

    conn.close()
    return redirect("/")


@app.route("/generate_payslip", methods=["POST"])
def generate_payslip():
    employee_id = request.form["employee_id"]
    leave_days = int(request.form["leave_days"])
    month = request.form["month"]

    if leave_days < 0 or leave_days > 30:
        return "Leave days must be between 0 and 30.", 400

    conn = get_db_connection()
    employee = conn.execute(
        "SELECT * FROM employees WHERE employee_id = ?",
        (employee_id,)
    ).fetchone()
    conn.close()

    if employee is None:
        return "Employee not found.", 404

    basic = employee["basic_salary"]
    hra = basic * employee["hra"] / 100
    da = basic * employee["da"] / 100
    allowances = basic * employee["allowances"] / 100

    gross = basic + hra + da + allowances
    pf = basic * employee["pf"] / 100
    esi = basic * employee["esi"] / 100

    leave_deduction = (gross / 30) * leave_days
    net_salary = gross - pf - esi - leave_deduction

    return render_template(
        "payslip.html",
        employee=employee,
        month=month,
        leave_days=leave_days,
        basic=basic,
        hra=hra,
        da=da,
        allowances=allowances,
        gross=gross,
        pf=pf,
        esi=esi,
        leave_deduction=leave_deduction,
        net_salary=net_salary
    )


@app.route("/edit_employee/<employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):
    conn = get_db_connection()

    if request.method == "POST":
        conn.execute("""
            UPDATE employees
            SET name = ?, designation = ?, joining_date = ?,
                basic_salary = ?, hra = ?, da = ?,
                allowances = ?, pf = ?, esi = ?
            WHERE employee_id = ?
        """, (
            request.form["name"].strip(),
            request.form["designation"].strip(),
            request.form["joining_date"],
            float(request.form["basic_salary"]),
            float(request.form["hra"]),
            float(request.form["da"]),
            float(request.form["allowances"]),
            float(request.form["pf"]),
            float(request.form["esi"]),
            employee_id
        ))
        conn.commit()
        conn.close()
        return redirect("/")

    employee = conn.execute(
        "SELECT * FROM employees WHERE employee_id = ?",
        (employee_id,)
    ).fetchone()
    conn.close()

    if employee is None:
        return "Employee not found", 404

    return render_template("edit_employee.html", employee=employee)


@app.route("/delete_employee/<employee_id>", methods=["POST"])
def delete_employee(employee_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM employees WHERE employee_id = ?",
        (employee_id,)
    )
    conn.commit()
    conn.close()
    return redirect("/")


create_table()

if __name__ == "__main__":
    app.run(debug=True)
