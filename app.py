# app.py
from flask import Flask, redirect, url_for
from transaction import transactions_bp
from librarian import librarian_bp
from reader import reader_bp # Ensure this is imported
from datetime import timedelta
import pyodbc

app = Flask(__name__)
# app.secret_key = "test_secret"
app.secret_key = 'mmu_library_secret'

# Delete the session when browser is closed
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Register ALL blueprints so url_for can find them
# app.register_blueprint(transactions_bp, url_prefix='/reader')
# app.register_blueprint(librarian_bp, url_prefix='/admin')
# app.register_blueprint(reader_bp) # THIS WAS MISSING
app.register_blueprint(reader_bp)
app.register_blueprint(librarian_bp)
app.register_blueprint(transactions_bp)

def get_db_connection():
        # Update these values to match your local setup
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=localhost;" #\\SQLEXPRESS;
        "Database=MMU_Library;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

# This route is good for testing the connection initially
@app.route('/test_db')
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@version;")
        row = cursor.fetchone()
        conn.close()
        return f"Connected! MS SQL Version: {row[0]}"
    except Exception as e:
        return f"Error: {str(e)}"
    
'''@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@version;") # Simple query to test connection
        row = cursor.fetchone()
        conn.close()
        return f"Connected! MS SQL Version: {row[0]}"
    except Exception as e:
        return f"Error: {str(e)}"'''

@app.route("/")
def index():
    # Now that reader_bp is registered, this will work
    return redirect(url_for('reader.home'))

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host="0.0.0.0", port=5000, debug=True)


'''# Default route to show the library page for a test user
@app.route("/")
def index():
    test_username = "testuser"  # Change this if you want another username
    return redirect(url_for('transactions.show_books', username=test_username))

if __name__ == "__main__":
    app.run(debug=True)'''
