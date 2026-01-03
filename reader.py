from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from transaction import transactions_bp
import pyodbc
import bcrypt
from datetime import datetime, timedelta

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
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=MMU_Library;"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
    )

# =========================
# PASSWORD HASHING
# =========================
def hash_pwd(password: str, rounds=12) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()

def check_pwd(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False

# =========================
# HOME
# =========================
@reader_bp.route('/')
def home():
    return render_template('user_interface.html', user=None)

# =========================
# LOGIN WITH AUTO-RESET LOCKOUT
# =========================
@reader_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    selected_role = request.form.get('role')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Password, Role, FailedAttempts, LockoutUntil, CreatedDate
        FROM LibraryData.Accounts
        WHERE Username = ?
    """, (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        flash("Invalid username or password.", "danger")
        return redirect(url_for('reader.home'))

    db_password, db_role, failed, lockout_until, pwd_created = user

    # =========================
    # LOCKOUT CHECK & AUTO-RESET
    # =========================
    if lockout_until:
        if lockout_until <= datetime.now():
            # 🔓 Lock expired → reset counters
            cursor.execute("""
                UPDATE LibraryData.Accounts
                SET FailedAttempts = 0,
                    LockoutUntil = NULL
                WHERE Username = ?
            """, (username,))
            conn.commit()
            failed = 0
        else:
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
            if db_role == 'Librarian':
                # 🔒 Permanent lock until password reset
                cursor.execute("""
                    UPDATE LibraryData.Accounts
                    SET FailedAttempts = ?, LockoutUntil = '9999-12-31'
                    WHERE Username = ?
                """, (failed, username))
            else:
                # ⏱ Temporary lock for Reader
                cursor.execute("""
                    UPDATE LibraryData.Accounts
                    SET FailedAttempts = ?,
                        LockoutUntil = DATEADD(MINUTE, ?, GETDATE())
                    WHERE Username = ?
                """, (failed, LOCKOUT_MINUTES, username))

            conn.commit()
            conn.close()
            flash("Account locked due to multiple failed attempts.", "danger")
            return redirect(url_for('reader.home'))

        cursor.execute("""
            UPDATE LibraryData.Accounts
            SET FailedAttempts = ?
            WHERE Username = ?
        """, (failed, username))
        conn.commit()
        conn.close()

        flash(f"Invalid login. Attempt {failed}/{MAX_ATTEMPTS}.", "danger")
        return redirect(url_for('reader.home'))

    # =========================
    # SUCCESSFUL LOGIN
    # =========================
    cursor.execute("""
        UPDATE LibraryData.Accounts
        SET FailedAttempts = 0, LockoutUntil = NULL
        WHERE Username = ?
    """, (username,))
    conn.commit()
    conn.close()

    session['username'] = username
    session['role'] = db_role

    # =========================
    # PASSWORD EXPIRY (LIBRARIAN)
    # =========================
    if db_role == 'Librarian':
        if not pwd_created or pwd_created < datetime.now() - timedelta(days=PASSWORD_EXPIRY_DAYS):
            session['force_pwd_change'] = True
            return redirect(url_for('reader.change_password'))

        return redirect(url_for('librarian.dashboard'))

    return redirect(url_for('transactions.show_books', username=username))

# =========================
# CHANGE PASSWORD (UNLOCKS ACCOUNT)
# =========================
@reader_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('reader.home'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        hashed = hash_pwd(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE LibraryData.Accounts
            SET Password = ?,
                CreatedDate = GETDATE(),
                FailedAttempts = 0,
                LockoutUntil = NULL
            WHERE Username = ?
        """, (hashed, session['username']))
        conn.commit()
        conn.close()

        session.pop('force_pwd_change', None)
        flash("Password updated successfully.", "success")

        if session['role'] == 'Librarian':
            return redirect(url_for('librarian.dashboard'))

        return redirect(url_for('transactions.show_books', username=session['username']))

    return render_template('change_password.html')

# =========================
# LOGOUT
# =========================
@reader_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('reader.home'))
