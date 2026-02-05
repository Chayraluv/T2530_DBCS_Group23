# transaction.py (MySQL / RDS - FIXED VERSION)

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime, timedelta
import pymysql
import os

transactions_bp = Blueprint('transactions', __name__)

MAX_BORROW_LIMIT = 3

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
# GET ACCOUNT ID
# =========================
def get_account_id(cursor, username):
    cursor.execute(
        "SELECT account_id FROM accounts WHERE username = %s",
        (username,)
    )
    row = cursor.fetchone()
    return row["account_id"] if row else None

# =========================
# BORROW BOOK
# =========================
@transactions_bp.route('/borrow/<username>/<int:book_id>')
def borrow(username, book_id):
    if 'username' not in session or session.get('role') != 'reader':
        flash("Unauthorized action.", "danger")
        return redirect(url_for('reader.home'))

    if session['username'] != username:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('reader.home'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        account_id = get_account_id(cursor, username)
        if not account_id:
            conn.close()
            flash("User not found.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # Borrow limit check
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM borrow_history
            WHERE account_id = %s
              AND status = 'borrow'
              AND return_date IS NULL
        """, (account_id,))
        borrowed_count = cursor.fetchone()["total"]

        if borrowed_count >= MAX_BORROW_LIMIT:
            conn.close()
            flash("Borrow limit reached.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # Check availability
        cursor.execute(
            "SELECT available FROM books WHERE book_id = %s",
            (book_id,)
        )
        book = cursor.fetchone()

        if not book or book["available"] == 0:
            conn.close()
            flash("Book is not available.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        due_date = datetime.now() + timedelta(days=14)

        cursor.execute("""
            UPDATE books
            SET available = 0,
                due_date = %s
            WHERE book_id = %s
        """, (due_date, book_id))

        cursor.execute("""
            INSERT INTO borrow_history (account_id, book_id, borrow_date, status)
            VALUES (%s, %s, NOW(), 'borrow')
        """, (account_id, book_id))

        conn.commit()
        conn.close()

        flash("Book borrowed successfully.", "success")

    except Exception as e:
        print("Borrow error:", e)
        flash("Database error occurred.", "danger")

    return redirect(url_for('transactions.show_books', username=username))

# =========================
# RETURN BOOK
# =========================
@transactions_bp.route('/return/<username>/<int:book_id>')
def return_book(username, book_id):
    if 'username' not in session or session.get('role') != 'reader':
        flash("Unauthorized action.", "danger")
        return redirect(url_for('reader.home'))

    if session['username'] != username:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('reader.home'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        account_id = get_account_id(cursor, username)

        cursor.execute("""
            UPDATE borrow_history
            SET return_date = NOW(),
                status = 'return'
            WHERE account_id = %s
              AND book_id = %s
              AND return_date IS NULL
        """, (account_id, book_id))

        cursor.execute("""
            UPDATE books
            SET available = 1,
                due_date = NULL
            WHERE book_id = %s
        """, (book_id,))

        conn.commit()
        conn.close()

        flash("Book returned successfully.", "success")

    except Exception as e:
        print("Return error:", e)
        flash("Error occurred while returning book.", "danger")

    return redirect(url_for('transactions.show_books', username=username))

# =========================
# SHOW BOOKS
# =========================
@transactions_bp.route('/books/<username>')
def show_books(username):
    if 'username' not in session or session.get('role') != 'reader':
        flash("Please login as Reader.", "danger")
        return redirect(url_for('reader.home'))

    if session['username'] != username:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('reader.home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT book_id AS id,
               title,
               author,
               category,
               available
        FROM books
        ORDER BY title
    """)
    books = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT category
        FROM books
        WHERE category IS NOT NULL
        ORDER BY category
    """)
    categories = [row["category"] for row in cursor.fetchall()]

    account_id = get_account_id(cursor, username)

    cursor.execute("""
        SELECT b.book_id AS id,
               b.title,
               bh.borrow_date + INTERVAL 14 DAY AS due_date
        FROM borrow_history bh
        JOIN books b ON bh.book_id = b.book_id
        WHERE bh.account_id = %s
          AND bh.status = 'borrow'
          AND bh.return_date IS NULL
        ORDER BY bh.borrow_date
    """, (account_id,))
    my_borrowed = cursor.fetchall()

    conn.close()

    return render_template(
        'transactions.html',
        books=books,
        my_borrowed=my_borrowed,
        categories=categories,
        username=username,
        now=datetime.now()
    )

# =========================
# SEARCH BOOKS
# =========================
@transactions_bp.route('/search/<username>')
def search(username):
    if 'username' not in session or session.get('role') != 'reader':
        flash("Please login as Reader.", "danger")
        return redirect(url_for('reader.home'))

    if session['username'] != username:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('reader.home'))

    query = request.args.get('query', '')
    category_filter = request.args.get('category', 'All')

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT book_id AS id,
               title,
               author,
               category,
               available
        FROM books
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (title LIKE %s OR author LIKE %s)"
        params.extend([f"%{query}%", f"%{query}%"])

    if category_filter != 'All':
        sql += " AND category = %s"
        params.append(category_filter)

    sql += " ORDER BY title"

    cursor.execute(sql, params)
    books = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT category
        FROM books
        WHERE category IS NOT NULL
        ORDER BY category
    """)
    categories = [row["category"] for row in cursor.fetchall()]

    account_id = get_account_id(cursor, username)

    cursor.execute("""
        SELECT b.book_id AS id,
               b.title,
               bh.borrow_date + INTERVAL 14 DAY AS due_date
        FROM borrow_history bh
        JOIN books b ON bh.book_id = b.book_id
        WHERE bh.account_id = %s
          AND bh.status = 'borrow'
          AND bh.return_date IS NULL
        ORDER BY bh.borrow_date
    """, (account_id,))
    my_borrowed = cursor.fetchall()

    conn.close()

    return render_template(
        'transactions.html',
        books=books,
        my_borrowed=my_borrowed,
        categories=categories,
        username=username,
        now=datetime.now()
    )
