"""
Test client for Bazar.com.
Sends different types of requests to the front-end and writes a clean
report (requests, responses, and server logs) to docs/output.txt
"""
import json
import subprocess
import urllib.parse
import urllib.request
import urllib.error

BASE = "http://localhost:5000"
OUT = "docs/output.txt"
lines = []


def log(text=""):
    print(text)
    lines.append(text)


def call(method, path, label):
    url = BASE + path
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            status, body = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode()
    log(f"\n--- {label} ---")
    log(f"{method} {path}  ->  HTTP {status}")
    try:
        log(json.dumps(json.loads(body), indent=2))
    except ValueError:
        log(body)


log("===== CLIENT REQUESTS =====")

topic1 = urllib.parse.quote("distributed systems")
topic2 = urllib.parse.quote("undergraduate school")

call("GET", f"/search/{topic1}", "1. search: distributed systems")
call("GET", f"/search/{topic2}", "2. search: undergraduate school")
call("GET", "/info/2", "3. info: book 2")
call("GET", "/info/99", "4. info: nonexistent book 99 (expect 404)")
call("POST", "/purchase/2", "5. purchase: book 2")
call("GET", "/info/2", "6. info: book 2 after purchase (quantity decreased)")

log("\n===== 7. purchase until out of stock: book 4 =====")
for i in range(1, 10):
    call("POST", "/purchase/4", f"7.{i} purchase book 4 (attempt {i})")

call("POST", "/purchase/99", "8. purchase: nonexistent book 99 (expect 404)")

log("\n===== SERVER LOGS =====")
for svc in ["frontend", "catalog", "order"]:
    out = subprocess.run(
        ["docker", "compose", "logs", "--no-color", "--no-log-prefix", svc],
        capture_output=True, text=True, encoding="utf-8").stdout
    log(f"\n----- {svc.upper()} LOG -----")
    log(out)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nSaved to {OUT}")