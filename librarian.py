from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime
import pymysql
import bcrypt
import os

librarian_bp = Blueprint('librarian', __name__)

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )

def hash_pwd(password: str, rounds=12) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds)
    ).decode("utf-8")

# =========================
# DASHBOARD
# =========================
@librarian_bp.route('/librarian/dashboard')
def dashboard():
    if session.get('role') != 'librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT book_id, title, author, category, available, due_date
        FROM books
        ORDER BY title
    """)
    inventory = cursor.fetchall()

    cursor.execute("""
        SELECT username, role
        FROM accounts
        ORDER BY username
    """)
    members = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT category
        FROM books
        WHERE category IS NOT NULL
        ORDER BY category
    """)
    categories = [row["category"] for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "librarian_dashboard.html",
        inventory=inventory,
        members=members,
        categories=categories,
        now=datetime.now()
    )

# =========================
# CREATE READER
# =========================
@librarian_bp.route('/librarian/create_member', methods=['POST'])
def create_member():
    if session.get('role') != 'librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    username = request.form.get('username')
    password = request.form.get('password')

    hashed = hash_pwd(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO accounts (username, password, role)
            VALUES (%s, %s, 'Reader')
        """, (username, hashed))
        conn.commit()
        flash("Reader created successfully.", "success")
    except Exception as e:
        flash("Failed to create user.", "danger")
        print(e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# LOGOUT
# =========================
@librarian_bp.route('/librarian/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('reader.home'))
