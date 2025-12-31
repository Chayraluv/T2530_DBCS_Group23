from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime, timedelta
import pyodbc

librarian_bp = Blueprint('librarian', __name__)

# Connection helper (matches your transaction.py setup)
def get_db_connection():
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=localhost;"
        "Database=MMU_Library;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

# librarian.py

@librarian_bp.route('/librarian/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    category = request.form.get('category')
    
    if title and author:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # We only send 3 parameters: Title, Author, Category
        # SQL Server automatically adds the next BookID
        cursor.execute(
            "INSERT INTO Books (Title, Author, Category, Available) VALUES (?, ?, ?, 1)", 
            (title, author, category)
        )
        
        conn.commit()
        conn.close()
        flash("New book added successfully!", "success")
    return redirect(url_for('librarian.dashboard'))

@librarian_bp.route('/librarian/delete_book/<int:book_id>')
def delete_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure book is not currently borrowed before deleting
    cursor.execute("DELETE FROM Books WHERE BookID = ? AND Available = 1", (book_id,))
    if cursor.rowcount > 0:
        flash("Book removed from inventory.", "success")
    else:
        flash("Cannot delete: Book is currently borrowed.", "danger")
    conn.commit()
    conn.close()
    return redirect(url_for('librarian.dashboard'))

# librarian.py

@librarian_bp.route('/librarian/delete_user/<username>')
def delete_user(username):
    # SECURITY NODE: Prevent deletion of the main admin (root)
    if username.lower() == 'root':
        flash("Access Denied: The Main Admin account cannot be deleted.", "danger")
        return redirect(url_for('librarian.dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Securely delete only if it's not the protected account
    cursor.execute("DELETE FROM Accounts WHERE Username = ?", (username,))
    
    conn.commit()
    conn.close()
    flash(f"Account for {username} has been removed.", "success")
    return redirect(url_for('librarian.dashboard'))

@librarian_bp.route('/librarian/create_member', methods=['POST'])
def create_member():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if username and password and role:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Use parameterized SQL to securely insert the new member and their role
            cursor.execute("INSERT INTO Accounts (Username, Password, Role) VALUES (?, ?, ?)", 
                           (username, password, role))
            conn.commit()
            conn.close()
            flash(f"New {role} account created for {username}!", "success")
        except Exception as e:
            flash(f"Error creating account: {str(e)}", "danger")
            
    return redirect(url_for('librarian.dashboard'))

# librarian.py

# librarian.py

@librarian_bp.route('/librarian/reset_password', methods=['POST'])
def reset_password():
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    
    # SECURITY NODE: Explicitly block any web-based reset for 'root'
    if username.lower() == 'root':
        flash("Unauthorized: The main admin account is protected and cannot be modified here.", "danger")
        return redirect(url_for('librarian.dashboard'))

    if username and new_password:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Parameterized query to securely update non-root users
            cursor.execute("UPDATE Accounts SET Password = ? WHERE Username = ?", (new_password, username))
            conn.commit()
            conn.close()
            flash(f"Password for {username} reset successfully!", "success")
        except Exception as e:
            flash(f"Error updating password: {str(e)}", "danger")
            
    return redirect(url_for('librarian.dashboard'))

@librarian_bp.route('/librarian/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch Inventory Status
    cursor.execute("SELECT BookID, Title, Author, Category, Available, DueDate FROM Books")
    inventory = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    # 2. Fetch Overdue Report
    # Identify books where the DueDate has passed the current time
    cursor.execute("""
        SELECT h.Username, b.Title, b.DueDate 
        FROM Books b
        JOIN BorrowHistory h ON b.BookID = h.BookID
        WHERE b.Available = 0 
        AND b.DueDate < GETDATE()
        AND h.Action = 'borrow'
        AND h.Timestamp = (SELECT MAX(Timestamp) FROM BorrowHistory WHERE BookID = b.BookID)
    """, )
    overdue_list = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    # 3. Fetch Member List
    # Update this part in librarian.py
    cursor.execute("SELECT Username, Role FROM Accounts")
    members = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    conn.close()
    return render_template('librarian_dashboard.html', 
                           inventory=inventory, 
                           overdue_list=overdue_list, 
                           members=members,
                           now=datetime.now())

# librarian.py additions

# 1. LOGOUT ROUTE
@librarian_bp.route('/librarian/logout')
def logout():
    # In a real app, you'd clear the session here
    flash("You have been logged out.", "success")
    return redirect(url_for('reader.home')) # Redirect to the main login page

# 2. EDIT BOOK ROUTE
@librarian_bp.route('/librarian/edit_book/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    new_title = request.form.get('title')
    new_author = request.form.get('author')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Update title and author for a specific book
    cursor.execute("UPDATE Books SET Title = ?, Author = ? WHERE BookID = ?", 
                   (new_title, new_author, book_id))
    conn.commit()
    conn.close()
    flash("Book updated successfully!", "success")
    return redirect(url_for('librarian.dashboard'))

# 3. TOGGLE AVAILABILITY (Alter Borrow/Available status manually)
@librarian_bp.route('/librarian/toggle_status/<int:book_id>')
def toggle_status(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Flip the Available status (0 to 1 or 1 to 0)
    cursor.execute("UPDATE Books SET Available = 1 - Available, DueDate = NULL WHERE BookID = ?", (book_id,))
    conn.commit()
    conn.close()
    flash("Book status updated.", "success")
    return redirect(url_for('librarian.dashboard'))