# transaction.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime, timedelta
import pyodbc

transactions_bp = Blueprint('transactions', __name__)

'''# Mock book data
books_data = [
    {"id": 0, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Fiction", "available": True},
    {"id": 1, "title": "1984", "author": "George Orwell", "category": "Science Fiction", "available": True},
    {"id": 2, "title": "The Hobbit", "author": "J.R.R. Tolkien", "category": "Fantasy", "available": True},
    {"id": 3, "title": "Python Programming", "author": "MMU Press", "category": "Technology", "available": True}
]

# Track borrowed books per user
borrowed_books = {}
# Track borrow/return history per user
borrow_history = {}'''

MAX_BORROW_LIMIT = 3


# Connection helper function
def get_db_connection():
    # Using your specific setup: localhost, Windows Auth, and Encryption trust
    # Original connection string (Adibah's setup)
    # conn_str = (
    #     "Driver={ODBC Driver 18 for SQL Server};"
    #     "Server=localhost;"
    #     "Database=MMU_Library;"
    #     "Trusted_Connection=yes;"
    #     "TrustServerCertificate=yes;"
    # )

    # Updated connection string for SQLEXPRESS (Tiffany's setup)
    conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=MMU_Library;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
    )
    return pyodbc.connect(conn_str)

def log_action(username, book_id, action):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SQL Insert statement
        query = "INSERT INTO BorrowHistory (Username, BookID, Action) VALUES (?, ?, ?)"
        cursor.execute(query, (username, book_id, action))
        
        conn.commit() # Important: This saves the changes!
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

# The rest of your borrow/return routes remain mostly the same, 
# but they will now call this SQL-powered log_action.

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

        # --- IMPROVED LIMIT CHECK ---
        # Count how many books are CURRENTLY unavailable and were last borrowed by this user
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Books b
            JOIN BorrowHistory h ON b.BookID = h.BookID
            WHERE h.Username = ? 
            AND b.Available = 0 
            AND h.Action = 'borrow'
            AND h.Timestamp = (SELECT MAX(Timestamp) FROM BorrowHistory WHERE BookID = b.BookID)
        """, (username,))

        net_borrowed = cursor.fetchone()[0]

        if net_borrowed >= MAX_BORROW_LIMIT:
            flash(f"Limit reached! You currently have {net_borrowed} books out.", "danger")
            conn.close()
            return redirect(url_for('transactions.show_books', username=username))
        # --- END CHECK ---

        # 2. CHECK AVAILABILITY FIRST (Before updating anything)
        cursor.execute("SELECT Available FROM Books WHERE BookID = ?", (book_id,))
        row = cursor.fetchone()
        
        if not row:
            flash("Book does not exist in database.", "danger")
        elif row[0] == 0: 
            flash("This book is already borrowed by someone else.", "danger")
        else:
            # 3. CALCULATE DUE DATE
            due_date = datetime.now() + timedelta(days=14)

            # 4. PERFORM UPDATES (Now that we know it's safe)
            # Update Books table: Mark as unavailable AND set the DueDate
            cursor.execute("""
                UPDATE Books 
                SET Available = 0, DueDate = ? 
                WHERE BookID = ?
            """, (due_date, book_id))
            
            # Log the action in History
            cursor.execute(
                "INSERT INTO BorrowHistory (Username, BookID, Action) VALUES (?, ?, ?)",
                (username, book_id, "borrow")
            )
            
            conn.commit() # Save all changes
            flash(f"Successfully borrowed book ID: {book_id}", "success")
            
        conn.close()
    except Exception as e:
        flash(f"Database Error: {str(e)}", "danger")

    return redirect(url_for('transactions.show_books', username=username))

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

        # 1. Update the Books table to mark it as Available (1)
        cursor.execute("UPDATE Books SET Available = 1, DueDate = NULL WHERE BookID = ?", (book_id,))
        
        # 2. Add a 'return' entry to your BorrowHistory table
        cursor.execute(
            "INSERT INTO BorrowHistory (Username, BookID, Action) VALUES (?, ?, ?)",
            (username, book_id, "return")
        )
        
        conn.commit()
        conn.close()
        flash("Book successfully returned! Thank you", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        
    return redirect(url_for('transactions.show_books', username=username))

# In transaction.py
@transactions_bp.route('/books/<username>')
def show_books(username):
    # Security check
    if 'username' not in session or session.get('role') != 'Reader':
        flash("Please login as Reader.", "danger")
        return redirect(url_for('reader.home'))
    
    if session['role'] != 'Reader':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    if session['username'] != username:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('reader.home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all books for the catalog
    cursor.execute("SELECT BookID as id, Title as title, Author as author, Category as category, Available as available FROM Books")
    all_books = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    
    # Fetch books specifically borrowed by this user
    cursor.execute("""
        SELECT b.BookID as id, b.Title as title, b.Author as author, b.DueDate as due_date
        FROM Books b
        JOIN BorrowHistory h ON b.BookID = h.BookID
        WHERE h.Username = ? AND b.Available = 0 AND h.Action = 'borrow'
        AND h.Timestamp = (SELECT MAX(Timestamp) FROM BorrowHistory WHERE BookID = b.BookID)
    """, (username,))
    my_books = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    
    conn.close()
    return render_template('transactions.html', books=all_books, my_borrowed=my_books, username=username, now=datetime.now())

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
    
    # 1. Fetch filtered catalog books
    sql_query = "SELECT BookID as id, Title as title, Author as author, Category as category, Available as available FROM Books WHERE 1=1"
    params = []
    if query:
        sql_query += " AND (Title LIKE ? OR Author LIKE ?)"
        params.extend([f'%{query}%', f'%{query}%'])
    if cat_filter != 'All':
        sql_query += " AND Category = ?"
        params.append(cat_filter)

    cursor.execute(sql_query, params)
    filtered_books = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

    # 2. FETCH user's borrowed books so the bottom section stays
    cursor.execute("""
        SELECT b.BookID as id, b.Title as title, b.Author as author, b.DueDate as due_date
        FROM Books b
        JOIN BorrowHistory h ON b.BookID = h.BookID
        WHERE h.Username = ? AND b.Available = 0 AND h.Action = 'borrow'
        AND h.Timestamp = (SELECT MAX(Timestamp) FROM BorrowHistory WHERE BookID = b.BookID)
    """, (username,))
    my_books = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('transactions.html', 
                           books=filtered_books, 
                           my_borrowed=my_books, 
                           username=username, 
                           now=datetime.now())
'''# Mock book data
books_data = [
    {"id": 0, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Fiction", "available": True},
    {"id": 1, "title": "1984", "author": "George Orwell", "category": "Science Fiction", "available": True},
    {"id": 2, "title": "The Hobbit", "author": "J.R.R. Tolkien", "category": "Fantasy", "available": True},
    {"id": 3, "title": "Python Programming", "author": "MMU Press", "category": "Technology", "available": True}
]

# Track borrowed books per user
borrowed_books = {}
# Track borrow/return history per user
borrow_history = {}
MAX_BORROW_LIMIT = 3'''
