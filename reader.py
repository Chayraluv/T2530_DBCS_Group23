# reader.py (MySQL / RDS - FIXED VERSION)

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import pymysql
import bcrypt
import os

# =========================
# SECURITY CONSTANTS
# =========================
MAX_ATTEMPTS = 3
LOCKOUT_MINUTES = 3
PASSWORD_EXPIRY_DAYS = 180  # 6 months

reader_bp = Blueprint('reader', __name__)

# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )

# =========================
# PASSWORD HASHING
# =========================
def hash_pwd(password: str, rounds=12) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds)
    ).decode("utf-8")

def check_pwd(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )

# =========================
# HOME
# =========================
@reader_bp.route('/')
def home():
    return render_template('user_interface.html', user=None)

# =========================
# LOGIN
# =========================
@reader_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('user_interface.html')

@reader_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    selected_role = request.form.get('role')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password, role, failed_attempts, lockout_until, created_date
        FROM accounts
        WHERE username = %s
    """, (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        flash("Invalid username or password.", "danger")
        return redirect(url_for('reader.home'))

    db_password = user["password"]
    db_role = user["role"].lower()
    selected_role = selected_role.lower()
    session["role"] = db_role
    failed = user["failed_attempts"]
    lockout_until = user["lockout_until"]
    pwd_created = user["created_date"]

    # =========================
    # LOCKOUT CHECK
    # =========================
    if lockout_until and lockout_until > datetime.now():
        remaining = int((lockout_until - datetime.now()).total_seconds() / 60) + 1
        conn.close()
        flash(f"Account locked. Try again in {remaining} minute(s).", "danger")
        return redirect(url_for('reader.home'))

    # =========================
    # INVALID PASSWORD OR ROLE
    # =========================
    if not check_pwd(password, db_password) or db_role != selected_role:
        failed += 1

        if failed >= MAX_ATTEMPTS:
            if db_role == "librarian":
                # Permanent lock
                cursor.execute("""
                    UPDATE accounts
                    SET failed_attempts = %s,
                        lockout_until = '9999-12-31'
                    WHERE username = %s
                """, (failed, username))
            else:
                # Temporary lock
                cursor.execute("""
                    UPDATE accounts
                    SET failed_attempts = %s,
                        lockout_until = NOW() + INTERVAL %s MINUTE
                    WHERE username = %s
                """, (failed, LOCKOUT_MINUTES, username))
        else:
            cursor.execute("""
                UPDATE accounts
                SET failed_attempts = %s
                WHERE username = %s
            """, (failed, username))

        conn.commit()
        conn.close()
        flash("Invalid login credentials.", "danger")
        return redirect(url_for('reader.home'))

    # =========================
    # SUCCESSFUL LOGIN
    # =========================
    cursor.execute("""
        UPDATE accounts
        SET failed_attempts = 0,
            lockout_until = NULL
        WHERE username = %s
    """, (username,))
    conn.commit()
    conn.close()

    session["username"] = username
    session["role"] = db_role

    # =========================
    # PASSWORD EXPIRY (LIBRARIAN)
    # =========================
    if db_role == "librarian":
        if not pwd_created or pwd_created < datetime.now() - timedelta(days=PASSWORD_EXPIRY_DAYS):
            session["force_pwd_change"] = True
            return redirect(url_for("reader.change_password"))
        return redirect(url_for("librarian.dashboard"))

    return redirect(url_for("transactions.show_books", username=username))

# =========================
# CHANGE PASSWORD
# =========================
@reader_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if "username" not in session:
        return redirect(url_for("reader.home"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        hashed = hash_pwd(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accounts
            SET password = %s,
                created_date = NOW(),
                failed_attempts = 0,
                lockout_until = NULL
            WHERE username = %s
        """, (hashed, session["username"]))
        conn.commit()
        conn.close()

        session.pop("force_pwd_change", None)
        flash("Password updated successfully.", "success")

        if session["role"] == "librarian":
            return redirect(url_for("librarian.dashboard"))

        return redirect(url_for("transactions.show_books", username=session["username"]))

    return render_template("change_password.html")


# =========================
# LOGOUT
# =========================
@reader_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('reader.home'))
