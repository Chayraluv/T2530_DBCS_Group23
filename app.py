# app.py (Cloud / EC2 version)

from flask import Flask, redirect, url_for
from datetime import timedelta

# Import blueprints (cloud-safe versions)
from reader import reader_bp
from librarian import librarian_bp
from transaction import transactions_bp

app = Flask(__name__)

# =========================
# BASIC APP CONFIG
# =========================
app.secret_key = "mmu_library_secret"

# Session config
app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# =========================
# REGISTER BLUEPRINTS
# =========================
app.register_blueprint(reader_bp)
app.register_blueprint(librarian_bp)
app.register_blueprint(transactions_bp)

# =========================
# ROOT ROUTE
# =========================
@app.route("/")
def index():
    # Redirect to reader home (cloud demo)
    return redirect(url_for("reader.home"))

# =========================
# MAIN ENTRY POINT
# =========================
if __name__ == "__main__":
    # IMPORTANT: 0.0.0.0 allows access from EC2 public IP
    app.run(host="0.0.0.0", port=5000)
