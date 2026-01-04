from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime, timedelta
import pyodbc

transactions_bp = Blueprint('transactions', __name__)

MAX_BORROW_LIMIT = 3

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

def get_account_id(cursor, username):
    cursor.execute(
        "SELECT AccountID FROM LibraryData.Accounts WHERE Username = ?",
        (username,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


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
            SELECT COUNT(*)
            FROM LibraryData.BorrowHistory
            WHERE AccountID = ?
              AND Status = 'borrow'
              AND ReturnDate IS NULL
        """, (account_id,))
        borrowed_count = cursor.fetchone()[0]

        if borrowed_count >= MAX_BORROW_LIMIT:
            conn.close()
            flash("Borrow limit reached.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # Check availability
        cursor.execute(
            "SELECT Available FROM LibraryData.Books WHERE BookID = ?",
            (book_id,)
        )
        row = cursor.fetchone()

        if not row or row[0] == 0:
            conn.close()
            flash("Book is not available.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # ✅ SET DUE DATE
        due_date = datetime.now() + timedelta(days=14)

        cursor.execute("""
            UPDATE LibraryData.Books
            SET Available = 0,
                DueDate = ?
            WHERE BookID = ?
        """, (due_date, book_id))

        cursor.execute("""
            INSERT INTO LibraryData.BorrowHistory
                (AccountID, BookID, BorrowDate, Status)
            VALUES (?, ?, GETDATE(), 'borrow')
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
            UPDATE LibraryData.BorrowHistory
            SET ReturnDate = GETDATE(),
                Status = 'return'
            WHERE AccountID = ?
              AND BookID = ?
              AND ReturnDate IS NULL
        """, (account_id, book_id))

        # ✅ CLEAR DUE DATE
        cursor.execute("""
            UPDATE LibraryData.Books
            SET Available = 1,
                DueDate = NULL
            WHERE BookID = ?
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

    account_id = get_account_id(cursor, username)
    if not account_id:
        conn.close()
        flash("User not found.", "danger")
        return redirect(url_for('reader.home'))

    # All books
    cursor.execute("""
        SELECT 
            BookID AS id,
            Title AS title,
            Author AS author,
            Category AS category,
            Available AS available
        FROM LibraryData.Books
    """)
    all_books = [
        dict(zip([col[0] for col in cursor.description], row))
        for row in cursor.fetchall()
    ]

    # My borrowed books with REAL due date
    cursor.execute("""
        SELECT 
            b.BookID AS id,
            b.Title AS title,
            b.Author AS author,
            b.DueDate AS due_date
        FROM LibraryData.Books b
        JOIN LibraryData.BorrowHistory bh ON b.BookID = bh.BookID
        WHERE bh.AccountID = ?
          AND bh.Status = 'borrow'
          AND bh.ReturnDate IS NULL
    """, (account_id,))

    my_books = [
        dict(zip([col[0] for col in cursor.description], row))
        for row in cursor.fetchall()
    ]

    conn.close()

    return render_template(
        'transactions.html',
        books=all_books,
        my_borrowed=my_books,
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
    cat_filter = request.args.get('category', 'All')

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT 
            BookID AS id,
            Title AS title,
            Author AS author,
            Category AS category,
            Available AS available
        FROM LibraryData.Books
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (Title LIKE ? OR Author LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])

    if cat_filter != 'All':
        sql += " AND Category = ?"
        params.append(cat_filter)

    cursor.execute(sql, params)
    filtered_books = [
        dict(zip([col[0] for col in cursor.description], row))
        for row in cursor.fetchall()
    ]

    account_id = get_account_id(cursor, username)

    cursor.execute("""
        SELECT 
            b.BookID AS id,
            b.Title AS title,
            b.Author AS author,
            b.DueDate AS due_date
        FROM LibraryData.Books b
        JOIN LibraryData.BorrowHistory bh ON b.BookID = bh.BookID
        WHERE bh.AccountID = ?
          AND bh.Status = 'borrow'
          AND bh.ReturnDate IS NULL
    """, (account_id,))

    my_books = [
        dict(zip([col[0] for col in cursor.description], row))
        for row in cursor.fetchall()
    ]

    conn.close()

    return render_template(
        'transactions.html',
        books=filtered_books,
        my_borrowed=my_books,
        username=username,
        now=datetime.now()
    )
