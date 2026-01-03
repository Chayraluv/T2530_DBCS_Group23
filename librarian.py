from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime
import pyodbc
import bcrypt

librarian_bp = Blueprint('librarian', __name__)

# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=localhost;"
        "Database=MMU_Library;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

# =========================
# PASSWORD HASHING
# =========================
def hash_pwd(password: str, rounds=12) -> str:
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt(rounds)
    ).decode()

# =========================
# CREATE READER ACCOUNT (SP)
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
            "EXEC LibraryData.CreateReaderAccount ?, ?",
            (username, hashed)
        )
        conn.commit()
        flash("Reader account created successfully.", "success")
    except Exception as e:
        flash("Failed to create account.", "danger")
        print("CreateReaderAccount error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# ADD BOOK (SP) + CATEGORY
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
            "EXEC LibraryData.AddBook ?, ?, ?",
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
# EDIT BOOK (SP) + CATEGORY
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
        cursor.execute(
            "EXEC LibraryData.EditBook ?, ?, ?, ?",
            (book_id, title, author, category)
        )
        conn.commit()
        flash("Book updated successfully.", "success")
    except Exception as e:
        flash("Failed to update book.", "danger")
        print("EditBook error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# DELETE BOOK (SP)
# =========================
@librarian_bp.route('/librarian/delete_book/<int:book_id>')
def delete_book(book_id):
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC LibraryData.DeleteBook ?", (book_id,))
        conn.commit()
        flash("Book deleted.", "success")
    except Exception as e:
        flash("Cannot delete book.", "danger")
        print("DeleteBook error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# TOGGLE BOOK STATUS (SP)
# =========================
@librarian_bp.route('/librarian/toggle_status/<int:book_id>')
def toggle_status(book_id):
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC LibraryData.ToggleBookStatus ?", (book_id,))
        conn.commit()
        flash("Book status updated.", "success")
    except Exception as e:
        flash("Failed to toggle status.", "danger")
        print("ToggleBookStatus error:", e)
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

    if username == session.get('username'):
        flash("Use Change Password flow.", "danger")
        return redirect(url_for('librarian.dashboard'))

    hashed = hash_pwd(new_password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "EXEC LibraryData.ResetUserPassword ?, ?",
            (username, hashed)
        )
        conn.commit()
        flash("Password reset successfully.", "success")
    except Exception as e:
        flash("Password reset failed.", "danger")
        print("ResetUserPassword error:", e)
    finally:
        conn.close()

    return redirect(url_for('librarian.dashboard'))

# =========================
# DELETE USER (SP)
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
        cursor.execute("EXEC LibraryData.DeleteUser ?", (username,))
        conn.commit()
        flash(f"User {username} deleted.", "success")
    except Exception as e:
        flash("Failed to delete user.", "danger")
        print("DeleteUser error:", e)
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

    cursor.execute("""
        SELECT BookID, Title, Author, Category, Available
        FROM LibraryData.Books
    """)
    inventory = cursor.fetchall()

    cursor.execute("""
        SELECT Username, Role
        FROM LibraryData.Accounts
    """)
    members = cursor.fetchall()

    conn.close()

    return render_template(
        "librarian_dashboard.html",
        inventory=inventory,
        members=members,
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
