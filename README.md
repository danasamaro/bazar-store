# Bazar.com - A Multi-tier Online Book Store

Lab 1 - Distributed and Operating Systems, Fall 2026
Author: Your Name

Bazar.com is a tiny online book store built as three Flask microservices
that communicate over HTTP REST and run in three Docker containers.

## Architecture

```
Client -> Frontend (:5000) -> Catalog (:5001)
                           -> Order   (:5002) -> Catalog (:5001)
```

| Service  | Port | Role | Storage |
|----------|------|------|---------|
| frontend | 5000 | Single entry point; forwards requests | none |
| catalog  | 5001 | Books: topic, stock, price. Query and update | SQLite |
| order    | 5002 | Purchases: checks stock, decrements it, logs the order | CSV file |

## Requirements

- Docker Desktop (with Docker Compose)
- Python 3 (only for the test client)
- git

## How to run

```bash
git clone https://github.com/danasamaro/bazar-store.git
cd bazar-store
docker compose up --build
```

Services: frontend http://localhost:5000, catalog http://localhost:5001,
order http://localhost:5002. Data is persisted in the `data/` folder.

To stop: `docker compose down`. To reset the data: stop, then delete the `data/` folder.

## REST API (through the frontend, port 5000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/<topic>` | List books of a topic (`id`, `title`) |
| GET | `/info/<id>` | Book details (`title`, `quantity`, `price`) |
| POST / PUT | `/purchase/<id>` | Buy one copy of a book |

Catalog only (port 5001):

| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT | `/update/<id>` | JSON body: `{"price": 55}` and/or `{"quantity_delta": 10}` |

Topics: `distributed systems`, `undergraduate school`.

### Examples

```bash
curl http://localhost:5000/search/distributed%20systems
curl http://localhost:5000/info/2
curl -X POST http://localhost:5000/purchase/2
curl -X PUT http://localhost:5001/update/2 -H "Content-Type: application/json" -d '{"quantity_delta": 10, "price": 55}'
```

## Running the test client

With the containers running:

```bash
python client_tests.py
```

It sends search, info and purchase requests (including not-found and
out-of-stock cases), prints the results and writes them with the server logs
to `docs/output.txt`.

## Project structure

```
catalog/   catalog service (app.py, Dockerfile, requirements.txt)
order/     order service
frontend/  frontend service
docs/      design document and sample output
docker-compose.yml
client_tests.py
```

## Documentation

- Design document: `docs/design.md`
- Sample output: `docs/output.txt`