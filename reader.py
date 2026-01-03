from flask import Flask, render_template, request, redirect, url_for, flash, session
from transaction import transactions_bp
import pyodbc
from flask import Blueprint
import  win32security

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
@reader_bp.route('/')
def home():
    return render_template('user_interface.html', user=None)


@reader_bp.route('/dashboard')
def dashboard_redirect():
    if 'username' not in session:
        return redirect(url_for('reader.home'))

    if session['role'] == 'Librarian':
        return redirect(url_for('librarian.dashboard'))

    return redirect(url_for('transactions.show_books', username=session['username']))


@reader_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    selected_role = request.form.get('role')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the password and role for the user
    cursor.execute("SELECT Password, Role FROM Accounts WHERE Username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        flash("Invalid username or password.", "danger")
        return redirect(url_for('reader.home'))


    db_password, db_role = user_data

    if db_password == password and db_role == selected_role:
        session['username'] = username
        session['role'] = db_role

        if db_role == 'Librarian':
            return redirect('/librarian/dashboard')
        else:
            return redirect(url_for('transactions.show_books', username=username))

    
    flash("Invalid username or password", "danger")
    return redirect(url_for('reader.home'))
    
@reader_bp.route('/logout')

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

def logout():
    session.clear()
    return redirect(url_for('reader.home'))
