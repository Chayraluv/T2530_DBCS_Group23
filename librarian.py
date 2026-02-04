# librarian.py (MySQL / RDS version)

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime
import pymysql
import bcrypt
import os

librarian_bp = Blueprint('librarian', __name__)

# =========================
# DATABASE CONNECTION (MYSQL)
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
        password.encode(),
        bcrypt.gensalt(rounds)
    ).decode()

# =========================
# CREATE READER ACCOUNT
# =========================
@librarian_bp.route('/librarian/create_member', methods=['POST'])
def create_member():
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("All fields are required.", "danger")
        return redirect(url_for('librarian.dashboard'))

    hashed = hash_pwd(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Accounts (Username, Password, Role, CreatedDate)
            VALUES (%s, %s, 'Reader', NOW())
            """,
            (username, hashed)
        )
        conn.commit()
        flash("Reader account created successfully.", "success")
    except Exception as e:
        flash("Failed to create account.", "danger")
        print("CreateReader error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# ADD BOOK
# =========================
@librarian_bp.route('/librarian/add_book', methods=['POST'])
def add_book():
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    title = request.form.get('title')
    author = request.form.get('author')
    category = request.form.get('category')

    if not title or not author or not category:
        flash("All book fields are required.", "danger")
        return redirect(url_for('librarian.dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Books (Title, Author, Category, Available)
            VALUES (%s, %s, %s, 1)
            """,
            (title, author, category)
        )
        conn.commit()
        flash("Book added successfully.", "success")
    except Exception as e:
        flash("Failed to add book.", "danger")
        print("AddBook error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# DASHBOARD
# =========================
@librarian_bp.route('/librarian/dashboard')
def dashboard():
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Books ORDER BY BookID")
    inventory = cursor.fetchall()

    cursor.execute("SELECT Username, Role FROM Accounts ORDER BY Username")
    members = cursor.fetchall()

    cursor.execute("SELECT DISTINCT Category FROM Books ORDER BY Category")
    categories = [row["Category"] for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "librarian_dashboard.html",
        inventory=inventory,
        members=members,
        categories=categories,
        now=datetime.now()
    )

# =========================
# LOGOUT
# =========================
@librarian_bp.route('/librarian/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('reader.home'))
