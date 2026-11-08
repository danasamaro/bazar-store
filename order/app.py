"""
Order microservice.
  POST /purchase/<id> -> checks stock in catalog, decrements it, logs the order
"""
import os
import csv
import threading
import logging
from datetime import datetime
import requests
from flask import Flask, jsonify

CATALOG_URL = os.environ.get("CATALOG_URL", "http://localhost:5001")
ORDERS_FILE = os.environ.get("ORDERS_FILE", "/data/orders.csv")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [ORDER] %(message)s")
log = logging.getLogger("order")

# Makes "check stock + decrement" one atomic step inside this server
purchase_lock = threading.Lock()


def init_orders_file():
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["timestamp", "item_id", "title"])


@app.route("/purchase/<int:item_id>", methods=["POST", "PUT"])
def purchase(item_id):
    with purchase_lock:
        # 1) query the catalog
        try:
            r = requests.get(f"{CATALOG_URL}/info/{item_id}", timeout=5)
        except requests.RequestException as e:
            log.error("catalog unreachable: %s", e)
            return jsonify({"error": "catalog service unavailable"}), 503

        if r.status_code == 404:
            return jsonify({"error": "item not found"}), 404
        book = r.json()

        # 2) verify stock
        if book["quantity"] <= 0:
            log.info("purchase FAILED (out of stock): '%s'", book["title"])
            return jsonify({"success": False, "error": "out of stock"}), 409

        # 3) decrement stock
        try:
            u = requests.put(f"{CATALOG_URL}/update/{item_id}",
                             json={"quantity_delta": -1}, timeout=5)
        except requests.RequestException as e:
            log.error("catalog unreachable: %s", e)
            return jsonify({"error": "catalog service unavailable"}), 503
        if u.status_code != 200:
            return jsonify({"success": False, "error": "could not update stock"}), 409

        # 4) persist the order
        with open(ORDERS_FILE, "a", newline="") as f:
            csv.writer(f).writerow([datetime.now().isoformat(), item_id, book["title"]])

        log.info("bought book '%s'", book["title"])
        return jsonify({"success": True, "message": f"bought book {book['title']}"})


if __name__ == "__main__":
    init_orders_file()
    app.run(host="0.0.0.0", port=5002, threaded=True)