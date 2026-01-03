from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from transaction import transactions_bp
import pyodbc
import bcrypt
from datetime import datetime, timedelta

MAX_ATTEMPTS = 3
LOCKOUT_MINUTES = 3
PASSWORD_EXPIRY_DAYS = 180  # 6 months

# Ensure this variable name is exactly 'reader_bp'
reader_bp = Blueprint('reader', __name__)

# Temporary User DB (We can move this to SQL next)
users_db = {} 
current_user = None

def get_db_connection():
    conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;" #\\SQLEXPRESS;
    "DATABASE=MMU_Library;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
    )
    return pyodbc.connect(conn_str)

# In reader.py or your main app file
def hash_pwd(password: str, rounds=12) -> str:
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt(rounds)
    ).decode()

def check_pwd(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False

def check_pwd(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

@reader_bp.route('/')
def home():
    return render_template('user_interface.html', user=None)

@reader_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    selected_role = request.form.get('role')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Password, Role, FailedAttempts, LockoutUntil, CreatedDate
        FROM Accounts
        WHERE Username = ?
    """, (username,))
    user = cursor.fetchone()

    if not user:
        flash("Invalid username or password.", "danger")
        return redirect(url_for('reader.home'))

    db_password, db_role, failed, lockout_until, pwd_created = user

    # 🔒 CHECK LOCKOUT
    if lockout_until and lockout_until > datetime.now():
        remaining = int((lockout_until - datetime.now()).total_seconds() / 60) + 1
        conn.close()
        flash(f"Account locked. Try again in {remaining} minute(s).", "danger")
        return redirect(url_for('reader.home'))

    # ❌ WRONG PASSWORD OR ROLE
    if not check_pwd(password, db_password) or db_role != selected_role:
        failed += 1

        if failed >= MAX_ATTEMPTS:
            cursor.execute("""
                UPDATE dbo.Accounts
                SET FailedAttempts = ?, 
                    LockoutUntil = DATEADD(MINUTE, ?, GETDATE())
                WHERE Username = ?
            """, (failed, LOCKOUT_MINUTES, username))

            conn.commit()
            conn.close()

            flash("Account locked for 3 minutes due to multiple failed attempts.", "danger")
            return redirect(url_for('reader.home'))

        else:
            cursor.execute("""
                UPDATE Accounts
                SET FailedAttempts = ?
                WHERE Username = ?
            """, (failed, username))
            conn.commit()
            conn.close()

            flash(f"Invalid login. Attempt {failed}/{MAX_ATTEMPTS}.", "danger")
            return redirect(url_for('reader.home'))

    # ✅ SUCCESSFUL LOGIN → RESET SECURITY
    cursor.execute("""
        UPDATE Accounts
        SET FailedAttempts = 0, LockoutUntil = NULL
        WHERE Username = ?
    """, (username,))
    conn.commit()
    conn.close()

    session['username'] = username
    session['role'] = db_role

    # 🔐 PASSWORD POLICY
    if db_role == 'Librarian':
        if not pwd_created or pwd_created < datetime.now() - timedelta(days=PASSWORD_EXPIRY_DAYS):
            session['force_pwd_change'] = True
            return redirect(url_for('reader.change_password'))

        return redirect(url_for('librarian.dashboard'))

    return redirect(url_for('transactions.show_books', username=username))

@reader_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('reader.home'))
    
    if not session.get('force_pwd_change'):
        flash("Password can only be changed every 6 months.", "danger")
        return redirect(url_for('librarian.dashboard'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')

        hashed = hash_pwd(new_password)

    # Get last password change date
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT CreatedDate FROM Accounts WHERE Username = ?",
        (session['username'],)
    )
    pwd_created = cursor.fetchone()[0]
    conn.close()

    # 🚫 Block early change (within 6 months)
    if pwd_created and pwd_created > datetime.now() - timedelta(days=PASSWORD_EXPIRY_DAYS):
        flash("Password can only be changed every 6 months.", "danger")
        return redirect(url_for('librarian.dashboard'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')

        hashed = hash_pwd(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Accounts
            SET Password = ?, CreatedDate = GETDATE()
            WHERE Username = ?
        """, (hashed, session['username']))
        conn.commit()
        conn.close()

        session.pop('force_pwd_change', None)
        session.pop('pwd_reason', None)

        flash("Password updated successfully.", "success")

        if session['role'] == 'Librarian':
            return redirect(url_for('librarian.dashboard'))

        return redirect(url_for('transactions.show_books', username=session['username']))

    return render_template('change_password.html')
    
@reader_bp.route('/dashboard')
def dashboard_redirect():
    if 'username' not in session:
        return redirect(url_for('reader.home'))

    if session['role'] == 'Librarian':
        return redirect(url_for('librarian.dashboard'))

    return redirect(url_for('transactions.show_books', username=session['username']))

#def authenticate_windows(username, password):
#    try:
#        win32security.LogonUser(
#            username,
#            "",  # local machine or domain
#            password,
#            win32security.LOGON32_LOGON_INTERACTIVE,
#            win32security.LOGON32_PROVIDER_DEFAULT
#        )
#        return True
#    except Exception:
#        return False 

@reader_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('reader.home'))
