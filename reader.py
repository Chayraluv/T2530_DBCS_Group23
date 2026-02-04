# reader.py (Cloud / EC2 version)

from flask import Blueprint, render_template, redirect, url_for, flash, session

reader_bp = Blueprint('reader', __name__)

# =========================
# HOME (PUBLIC LANDING PAGE)
# =========================
@reader_bp.route('/')
def home():
    # Cloud demo homepage
    return """
    <h1>MMU Library System (Cloud Demo)</h1>
    <p>This application is running on Amazon EC2.</p>
    <p>Database features are disabled in this deployment.</p>
    """

# =========================
# LOGIN (DISABLED)
# =========================
@reader_bp.route('/login', methods=['POST'])
def login():
    flash("Login is disabled in cloud demo.", "warning")
    return redirect(url_for('reader.home'))

# =========================
# CHANGE PASSWORD (DISABLED)
# =========================
@reader_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    flash("Password change is disabled in cloud demo.", "warning")
    return redirect(url_for('reader.home'))

# =========================
# LOGOUT
# =========================
@reader_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('reader.home'))
