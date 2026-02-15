import os
import time
import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("POSTGRES_DB", "inventory_db")
DB_USER = os.environ.get("POSTGRES_USER", "admin")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "admin_password")


def get_db_connection():
    """Return a new database connection with retry logic."""
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
            )
            return conn
        except psycopg2.OperationalError:
            if attempt == retries:
                raise
            print(f"DB not ready (attempt {attempt}/{retries}), retrying in 2 s …")
            time.sleep(2)


# ── Routes ───────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/add", methods=["POST"])
def add_item():
    data = request.get_json()
    item_name = data.get("item")
    quantity = data.get("quantity")

    if not item_name or quantity is None:
        return jsonify({"status": "error", "message": "Missing item or quantity"}), 400

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Quantity must be an integer"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO inventory (item_name, quantity) VALUES (%s, %s)",
        (item_name, quantity),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/api/remove", methods=["POST"])
def remove_item():
    data = request.get_json()
    item_id = data.get("id")

    if not item_id:
        return jsonify({"status": "error", "message": "Missing item ID"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Decrement quantity by 1
    cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id = %s", (item_id,))
    # Delete the row if quantity reached 0
    cur.execute("DELETE FROM inventory WHERE id = %s AND quantity <= 0", (item_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})


@app.route("/api/delete", methods=["POST"])
def delete_item():
    data = request.get_json()
    item_id = data.get("id")

    if not item_id:
        return jsonify({"status": "error", "message": "Missing item ID"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success"})


@app.route("/api/report", methods=["GET"])
def report():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, item_name, quantity FROM inventory ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    items = [{"id": r[0], "item_name": r[1], "quantity": r[2]} for r in rows]
    return jsonify(items)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
