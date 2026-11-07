"""
Catalog microservice.
Stores books in SQLite and exposes REST endpoints:
  GET /search/<topic>   -> list of {id, title}
  GET /info/<id>        -> {title, quantity, price}
  PUT /update/<id>      -> update price and/or change quantity
"""
import os
import sqlite3
import logging
from flask import Flask, jsonify, request

DB_PATH = os.environ.get("DB_PATH", "/data/catalog.db")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [CATALOG] %(message)s")
log = logging.getLogger("catalog")

INITIAL_BOOKS = [
    (1, "How to get a good grade in DOS in 40 minutes a day", "distributed systems", 10, 50.0),
    (2, "RPCs for Noobs", "distributed systems", 5, 50.0),
    (3, "Xen and the Art of Surviving Undergraduate School", "undergraduate school", 8, 40.0),
    (4, "Cooking for the Impatient Undergrad", "undergraduate school", 7, 30.0),
]


def get_conn():
    # A new connection per request -> safe with Flask's threads
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        topic TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL)""")
    if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        conn.executemany("INSERT INTO books VALUES (?,?,?,?,?)", INITIAL_BOOKS)
        log.info("Database seeded with initial books")
    conn.commit()
    conn.close()


@app.route("/search/<topic>", methods=["GET"])
def search(topic):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title FROM books WHERE LOWER(topic) = LOWER(?)", (topic,)
    ).fetchall()
    conn.close()
    result = [{"id": r["id"], "title": r["title"]} for r in rows]
    log.info("search topic='%s' -> %d result(s)", topic, len(result))
    return jsonify(result)


@app.route("/info/<int:item_id>", methods=["GET"])
def info(item_id):
    conn = get_conn()
    r = conn.execute("SELECT * FROM books WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if r is None:
        log.info("info id=%d -> not found", item_id)
        return jsonify({"error": "item not found"}), 404
    log.info("info id=%d -> '%s' qty=%d", item_id, r["title"], r["quantity"])
    return jsonify({"title": r["title"], "quantity": r["quantity"], "price": r["price"]})


@app.route("/update/<int:item_id>", methods=["PUT"])
def update(item_id):
    """Body (JSON), both fields optional:
       {"price": 60}            -> set new price
       {"quantity_delta": -1}   -> add/subtract from stock (never below 0)
    """
    data = request.get_json(silent=True) or {}
    conn = get_conn()
    try:
        if conn.execute("SELECT 1 FROM books WHERE id=?", (item_id,)).fetchone() is None:
            return jsonify({"error": "item not found"}), 404

        if "price" in data:
            conn.execute("UPDATE books SET price=? WHERE id=?", (data["price"], item_id))

        if "quantity_delta" in data:
            delta = int(data["quantity_delta"])
            # atomic: the WHERE clause prevents negative stock even with concurrent requests
            cur = conn.execute(
                "UPDATE books SET quantity = quantity + ? WHERE id=? AND quantity + ? >= 0",
                (delta, item_id, delta))
            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({"error": "insufficient stock"}), 409

        conn.commit()
        r = conn.execute("SELECT * FROM books WHERE id=?", (item_id,)).fetchone()
        log.info("update id=%d body=%s -> qty=%d price=%.2f",
                 item_id, data, r["quantity"], r["price"])
        return jsonify({"title": r["title"], "quantity": r["quantity"], "price": r["price"]})
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, threaded=True)