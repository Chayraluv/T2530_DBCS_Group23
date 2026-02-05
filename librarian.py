# librarian.py (MySQL / Amazon RDS version - FULL)

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime
import pymysql
import bcrypt
import os

librarian_bp = Blueprint('librarian', __name__)

# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
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

    hashed = hash_pwd(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (username, password, role)
            VALUES (%s, %s, 'Reader')
        """, (username, hashed))
        conn.commit()
        flash("Reader account created successfully.", "success")
    except Exception as e:
        flash("Failed to create account.", "danger")
        print("Create member error:", e)
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

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, category, available)
            VALUES (%s, %s, %s, 1)
        """, (title, author, category))
        conn.commit()
        flash("Book added successfully.", "success")
    except Exception as e:
        flash("Failed to add book.", "danger")
        print("Add book error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# EDIT BOOK
# =========================
@librarian_bp.route('/librarian/edit_book/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    title = request.form.get('title')
    author = request.form.get('author')
    category = request.form.get('category')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE books
            SET title=%s, author=%s, category=%s
            WHERE book_id=%s
        """, (title, author, category, book_id))
        conn.commit()
        flash("Book updated successfully.", "success")
    except Exception as e:
        flash("Failed to update book.", "danger")
        print("Edit book error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# DELETE BOOK
# =========================
@librarian_bp.route('/librarian/delete_book/<int:book_id>')
def delete_book(book_id):
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE book_id=%s", (book_id,))
        conn.commit()
        flash("Book deleted.", "success")
    except Exception as e:
        flash("Failed to delete book.", "danger")
        print("Delete book error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# TOGGLE BOOK STATUS
# =========================
@librarian_bp.route('/librarian/toggle_status/<int:book_id>')
def toggle_status(book_id):
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE books
            SET available = IF(available=1, 0, 1)
            WHERE book_id=%s
        """, (book_id,))
        conn.commit()
        flash("Book status updated.", "success")
    except Exception as e:
        flash("Failed to toggle status.", "danger")
        print("Toggle status error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# RESET USER PASSWORD (SP)
# =========================
@librarian_bp.route('/librarian/reset_password', methods=['POST'])
def reset_password():
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    username = request.form.get('username')
    new_password = request.form.get('new_password')

    hashed = hash_pwd(new_password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accounts
            SET password = %s,
                failed_attempts = 0,
                lockout_until = NULL,
                created_date = NOW()
            WHERE username = %s
        """, (hashed, username))
        conn.commit()
        flash("Password reset successfully.", "success")
    except Exception as e:
        flash("Password reset failed.", "danger")
        print(e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# DELETE USER
# =========================
@librarian_bp.route('/librarian/delete_user/<username>')
def delete_user(username):
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    if username == session.get('username'):
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('librarian.dashboard'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE username=%s", (username,))
        conn.commit()
        flash(f"User {username} deleted.", "success")
    except Exception as e:
        flash("Failed to delete user.", "danger")
        print("Delete user error:", e)
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

    cursor.execute("SELECT * FROM books ORDER BY book_id")
    inventory = cursor.fetchall()

    cursor.execute("SELECT username AS Username, role AS Role FROM accounts ORDER BY username")
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
        overdue_list=[], 
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
