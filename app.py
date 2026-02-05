# app.py (MySQL / RDS version)

from flask import Flask, redirect, url_for, jsonify
from datetime import timedelta
import os
import pymysql

from reader import reader_bp
from librarian import librarian_bp
from transaction import transactions_bp
import sys
sys.stdout.reconfigure(encoding="utf-8")
app = Flask(__name__)

# =========================
# BASIC CONFIG
# =========================
app.secret_key = "mmu_library_secret"

app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# =========================
# REGISTER BLUEPRINTS
# =========================
app.register_blueprint(reader_bp)
app.register_blueprint(librarian_bp)
app.register_blueprint(transactions_bp)

# =========================
# MYSQL CONNECTION (RDS)
# =========================

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# =========================
# TEST DB CONNECTION
# =========================
@app.route("/test_db")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION();")
        row = cursor.fetchone()
        conn.close()

        return jsonify(
            status="success",
            version=row["VERSION()"]
        )

    except Exception:
        # JANGAN return str(e)
        return jsonify(
            status="error",
            message="Database connection failed"
        ), 500


# =========================
# ROOT
# =========================
@app.route("/")
def index():
    return redirect(url_for("reader.home"))

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
