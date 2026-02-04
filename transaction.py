# transaction.py (MySQL / RDS version)

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime, timedelta
import pymysql

transactions_bp = Blueprint('transactions', __name__)

MAX_BORROW_LIMIT = 3

# =========================
# DATABASE CONNECTION (MYSQL)
# =========================
def get_db_connection():
    return pymysql.connect(
        host="RDS-ENDPOINT-HERE",
        user="admin",
        password="password",
        database="mmu_library",
        cursorclass=pymysql.cursors.DictCursor
    )

def get_account_id(cursor, username):
    cursor.execute(
        "SELECT AccountID FROM Accounts WHERE Username = %s",
        (username,)
    )
    row = cursor.fetchone()
    return row["AccountID"] if row else None

# =========================
# BORROW BOOK
# =========================
@transactions_bp.route('/borrow/<username>/<int:book_id>')
def borrow(username, book_id):
    if 'username' not in session or session.get('role') != 'Reader':
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
            FROM BorrowHistory
            WHERE AccountID = %s
              AND Status = 'borrow'
              AND ReturnDate IS NULL
        """, (account_id,))
        borrowed_count = cursor.fetchone()["total"]

        if borrowed_count >= MAX_BORROW_LIMIT:
            conn.close()
            flash("Borrow limit reached.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # Check availability
        cursor.execute(
            "SELECT Available FROM Books WHERE BookID = %s",
            (book_id,)
        )
        book = cursor.fetchone()

        if not book or book["Available"] == 0:
            conn.close()
            flash("Book is not available.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # Set due date
        due_date = datetime.now() + timedelta(days=14)

        cursor.execute("""
            UPDATE Books
            SET Available = 0,
                DueDate = %s
            WHERE BookID = %s
        """, (due_date, book_id))

        cursor.execute("""
            INSERT INTO BorrowHistory (AccountID, BookID, BorrowDate, Status)
            VALUES (%s, %s, NOW(), 'borrow')
        """, (account_id, book_id))

        conn.commit()
        conn.close()

        flash("Book borrowed successfully.", "success")

    except Exception as e:
        flash(f"Database error: {str(e)}", "danger")

    return redirect(url_for('transactions.show_books', username=username))

# =========================
# RETURN BOOK
# =========================
@transactions_bp.route('/return/<username>/<int:book_id>')
def return_book(username, book_id):
    if 'username' not in session or session.get('role') != 'Reader':
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
            UPDATE BorrowHistory
            SET ReturnDate = NOW(),
                Status = 'return'
            WHERE AccountID = %s
              AND BookID = %s
              AND ReturnDate IS NULL
        """, (account_id, book_id))

        cursor.execute("""
            UPDATE Books
            SET Available = 1,
                DueDate = NULL
            WHERE BookID = %s
        """, (book_id,))

        conn.commit()
        conn.close()

        flash("Book returned successfully.", "success")

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('transactions.show_books', username=username))

# =========================
# SHOW BOOKS
# =========================
@transactions_bp.route('/books/<username>')
def show_books(username):
    if 'username' not in session or session.get('role') != 'Reader':
        flash("Please login as Reader.", "danger")
        return redirect(url_for('reader.home'))

    if session['username'] != username:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('reader.home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT BookID AS id,
               Title AS title,
               Author AS author,
               Category AS category,
               Available AS available
        FROM Books
        ORDER BY Title
    """)
    books = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT Category
        FROM Books
        WHERE Category IS NOT NULL
        ORDER BY Category
    """)
    categories = [row["Category"] for row in cursor.fetchall()]

    account_id = get_account_id(cursor, username)

    cursor.execute("""
        SELECT b.BookID AS id,
               b.Title AS title,
               bh.BorrowDate + INTERVAL 14 DAY AS due_date
        FROM BorrowHistory bh
        JOIN Books b ON bh.BookID = b.BookID
        WHERE bh.AccountID = %s
          AND bh.Status = 'borrow'
          AND bh.ReturnDate IS NULL
        ORDER BY bh.BorrowDate
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
    if 'username' not in session or session.get('role') != 'Reader':
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
        SELECT BookID AS id,
               Title AS title,
               Author AS author,
               Category AS category,
               Available AS available
        FROM Books
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (Title LIKE %s OR Author LIKE %s)"
        params.extend([f"%{query}%", f"%{query}%"])

    if category_filter != 'All':
        sql += " AND Category = %s"
        params.append(category_filter)

    sql += " ORDER BY Title"

    cursor.execute(sql, params)
    books = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT Category
        FROM Books
        WHERE Category IS NOT NULL
        ORDER BY Category
    """)
    categories = [row["Category"] for row in cursor.fetchall()]

    account_id = get_account_id(cursor, username)

    cursor.execute("""
        SELECT b.BookID AS id,
               b.Title AS title,
               bh.BorrowDate + INTERVAL 14 DAY AS due_date
        FROM BorrowHistory bh
        JOIN Books b ON bh.BookID = b.BookID
        WHERE bh.AccountID = %s
          AND bh.Status = 'borrow'
          AND bh.ReturnDate IS NULL
        ORDER BY bh.BorrowDate
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
