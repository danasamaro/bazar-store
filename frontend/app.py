"""
Front-end microservice: single entry point for clients.
  GET  /search/<topic>  -> forwarded to catalog
  GET  /info/<id>       -> forwarded to catalog
  POST /purchase/<id>   -> forwarded to order server
"""
import os
import logging
import requests
from flask import Flask, jsonify

CATALOG_URL = os.environ.get("CATALOG_URL", "http://localhost:5001")
ORDER_URL = os.environ.get("ORDER_URL", "http://localhost:5002")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [FRONTEND] %(message)s")
log = logging.getLogger("frontend")


def forward(method, url, **kwargs):
    try:
        r = requests.request(method, url, timeout=10, **kwargs)
        return jsonify(r.json()), r.status_code
    except requests.RequestException as e:
        log.error("backend error: %s", e)
        return jsonify({"error": "backend service unavailable"}), 503


@app.route("/search/<topic>", methods=["GET"])
def search(topic):
    log.info("search request: topic='%s'", topic)
    return forward("GET", f"{CATALOG_URL}/search/{topic}")


@app.route("/info/<int:item_id>", methods=["GET"])
def info(item_id):
    log.info("info request: item=%d", item_id)
    return forward("GET", f"{CATALOG_URL}/info/{item_id}")


@app.route("/purchase/<int:item_id>", methods=["POST", "PUT"])
def purchase(item_id):
    log.info("purchase request: item=%d", item_id)
    return forward("POST", f"{ORDER_URL}/purchase/{item_id}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)