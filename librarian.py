# librarian.py (Cloud / EC2 version)

from flask import Blueprint, redirect, url_for, flash, session

librarian_bp = Blueprint('librarian', __name__)

# =========================
# DASHBOARD (DB DISABLED)
# =========================
@librarian_bp.route('/librarian/dashboard')
def dashboard():
    # In cloud demo, DB is disabled
    if session.get('role') != 'Librarian':
        flash("Access denied.", "danger")
        return redirect(url_for('reader.home'))

    return """
    <h1>Librarian Dashboard (Cloud Demo)</h1>
    <p>Database functionality is disabled in EC2 deployment.</p>
    """

# =========================
# LOGOUT
# =========================
@librarian_bp.route('/librarian/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('reader.home'))
