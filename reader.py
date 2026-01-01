from flask import Flask, render_template, request, redirect, url_for, flash, session
from transaction import transactions_bp
import pyodbc
from flask import Blueprint

# Ensure this variable name is exactly 'reader_bp'
reader_bp = Blueprint('reader', __name__)

'''app = Flask(__name__)
app.secret_key = 'mmu_library_secret' 

# REGISTER the blueprint so reader.py knows about the SQL routes
app.register_blueprint(transactions_bp)'''

# Temporary User DB (We can move this to SQL next)
users_db = {} 
current_user = None
# Update books list here
'''books_data = [
    {"id": 0, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Fiction", "available": True},
    {"id": 1, "title": "1984", "author": "George Orwell", "category": "Science Fiction", "available": True},
    {"id": 2, "title": "The Hobbit", "author": "J.R.R. Tolkien", "category": "Fantasy", "available": True},
    {"id": 3, "title": "Python Programming", "author": "MMU Press", "category": "Technology", "available": True}
]'''

'''@reader_bp.route('/search')
def search():
    query = request.args.get('query', '').lower()
    cat_filter = request.args.get('category', 'All') 
    
    filtered_books = []
    for b in books_data:
        text_match = query in b['title'].lower() or query in b['author'].lower()
        cat_match = (cat_filter == 'All' or b['category'] == cat_filter)
        
        if text_match and cat_match:
            filtered_books.append(b)
            
    return render_template('user_interface.html', books=filtered_books, user=current_user)
current_user = None'''

def get_db_connection():
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

# In reader.py or your main app file
@reader_bp.route('/')
def home():
    return render_template('user_interface.html', user=None)



'''@reader_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert the new user into the Accounts table
        cursor.execute("INSERT INTO Accounts (Username, Password, Role) VALUES (?, ?, ?)", (username, password, 'Reader'))
        conn.commit()
        conn.close()
        flash("Registration successful! You can now login.", "success")
    except pyodbc.IntegrityError:
        flash("Username already exists. Please choose another.", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('reader.home'))'''


@reader_bp.route('/dashboard')
def dashboard_redirect():
    if 'username' not in session:
        return redirect(url_for('reader.home'))

    if session['role'] == 'Librarian':
        return redirect(url_for('librarian.dashboard'))

    return redirect(url_for('transactions.show_books', username=session['username']))


@reader_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    selected_role = request.form.get('role')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the password and role for the user
    cursor.execute("SELECT Password, Role FROM Accounts WHERE Username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        flash("Invalid username or password.", "danger")
        return redirect(url_for('reader.home'))


    db_password, db_role = user_data

    if db_password == password and db_role == selected_role:
        session['username'] = username
        session['role'] = db_role

        if db_role == 'Librarian':
            return redirect('/librarian/dashboard')
        else:
            return redirect(url_for('transactions.show_books', username=username))

    
    flash("Invalid username or password", "danger")
    return redirect(url_for('reader.home'))
    
@reader_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('reader.home'))


'''@reader_bp.route('/borrow/<int:book_id>')
def borrow(book_id):
    borrowed_count = len([b for b in books_data if not b['available']])
    if borrowed_count >= 3:
        flash("Limit reached! You can only borrow up to 3 books.", "danger")
    else:
        books_data[book_id]['available'] = False
    return redirect(url_for('home'))

@reader_bp.route('/return/<int:book_id>')
def return_book(book_id):
    books_data[book_id]['available'] = True
    return redirect(url_for('home'))'''

'''if __name__ == '__main__':
    app.run(debug=True)'''