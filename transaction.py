# transaction.py (Cloud / EC2 version)

from flask import Blueprint, redirect, url_for, flash, session

transactions_bp = Blueprint('transactions', __name__)

# =========================
# TRANSACTIONS HOME (DISABLED)
# =========================
@transactions_bp.route('/transactions')
def transactions_home():
    return """
    <h1>Transactions Module (Cloud Demo)</h1>
    <p>Borrow / return features are disabled.</p>
    <p>Database will be connected using Amazon RDS in the next phase.</p>
    """

# =========================
# SHOW BOOKS (DISABLED)
# =========================
@transactions_bp.route('/books/<username>')
def show_books(username):
    flash("Book listing is disabled in cloud demo.", "warning")
    return redirect(url_for('reader.home'))

# =========================
# BORROW BOOK (DISABLED)
# =========================
@transactions_bp.route('/borrow/<username>/<int:book_id>')
def borrow(username, book_id):
    flash("Borrowing is disabled in cloud demo.", "warning")
    return redirect(url_for('reader.home'))

# =========================
# RETURN BOOK (DISABLED)
# =========================
@transactions_bp.route('/return/<username>/<int:book_id>')
def return_book(username, book_id):
    flash("Return is disabled in cloud demo.", "warning")
    return redirect(url_for('reader.home'))

# =========================
# SEARCH BOOKS (DISABLED)
# =========================
@transactions_bp.route('/search/<username>')
def search(username):
    flash("Search is disabled in cloud demo.", "warning")
    return redirect(url_for('reader.home'))
