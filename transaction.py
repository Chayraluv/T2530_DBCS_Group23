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

        # 🔢 Check borrow limit
        cursor.execute("""
            SELECT COUNT(*)
            FROM LibraryData.Books b
            JOIN LibraryData.BorrowHistory h ON b.BookID = h.BookID
            WHERE h.Username = ?
              AND b.Available = 0
              AND h.Action = 'borrow'
              AND h.Timestamp = (
                    SELECT MAX(Timestamp)
                    FROM LibraryData.BorrowHistory
                    WHERE BookID = b.BookID
              )
        """, (username,))

        net_borrowed = cursor.fetchone()[0]

        if net_borrowed >= MAX_BORROW_LIMIT:
            conn.close()
            flash(f"Limit reached! You currently have {net_borrowed} books.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # 🔍 Check availability
        cursor.execute("""
            SELECT Available
            FROM LibraryData.Books
            WHERE BookID = ?
        """, (book_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            flash("Book does not exist.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        if row[0] == 0:
            conn.close()
            flash("Book is already borrowed.", "danger")
            return redirect(url_for('transactions.show_books', username=username))

        # 📅 Borrow book
        due_date = datetime.now() + timedelta(days=14)

        cursor.execute("""
            UPDATE LibraryData.Books
            SET Available = 0, DueDate = ?
            WHERE BookID = ?
        """, (due_date, book_id))

        cursor.execute("""
            INSERT INTO LibraryData.BorrowHistory (Username, BookID, Action)
            VALUES (?, ?, 'borrow')
        """, (username, book_id))

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

        cursor.execute("""
            UPDATE LibraryData.Books
            SET Available = 1, DueDate = NULL
            WHERE BookID = ?
        """, (book_id,))

        cursor.execute("""
            INSERT INTO LibraryData.BorrowHistory (Username, BookID, Action)
            VALUES (?, ?, 'return')
        """, (username, book_id))

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

    cursor.execute("""
        SELECT 
            b.BookID AS id,
            b.Title AS title,
            b.Author AS author,
            b.DueDate AS due_date
        FROM LibraryData.Books b
        JOIN LibraryData.BorrowHistory h ON b.BookID = h.BookID
        WHERE h.Username = ?
          AND b.Available = 0
          AND h.Action = 'borrow'
          AND h.Timestamp = (
                SELECT MAX(Timestamp)
                FROM LibraryData.BorrowHistory
                WHERE BookID = b.BookID
          )
    """, (username,))
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

    cursor.execute("""
        SELECT 
            b.BookID AS id,
            b.Title AS title,
            b.Author AS author,
            b.DueDate AS due_date
        FROM LibraryData.Books b
        JOIN LibraryData.BorrowHistory h ON b.BookID = h.BookID
        WHERE h.Username = ?
          AND b.Available = 0
          AND h.Action = 'borrow'
          AND h.Timestamp = (
                SELECT MAX(Timestamp)
                FROM LibraryData.BorrowHistory
                WHERE BookID = b.BookID
          )
    """, (username,))
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
