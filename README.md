# 📦 Real-Time Order Updates — Django + Signals + WebSockets

A backend service that pushes live order changes to all connected browser clients in real-time.  
Built with **Django**, **Django Channels**, **Django Signals**, and **PostgreSQL**.

---

## How It Works

```
REST API → Order.save() → Django Signal → Redis → WebSocket → Browser
```

1. A client calls `POST /api/orders/` (or PATCH/DELETE).
2. Django view calls `Order.save()` / `Order.delete()`.
3. Django fires a `post_save` / `post_delete` signal automatically.
4. Our signal handler in `signals.py` calls `channel_layer.group_send()`.
5. Redis delivers the message to all connected WebSocket consumers.
6. Each `OrderConsumer` forwards the JSON event to its browser client instantly.

---

## Project Structure

```
pooling_backend/
├── config/
│   ├── settings.py       # Django settings (DB, Channels, ASGI)
│   ├── urls.py           # Root URL config
│   └── asgi.py           # ASGI entry point (HTTP + WebSocket routing)
├── orders/
│   ├── models.py         # Order model (DB table)
│   ├── serializers.py    # Order → dict converter
│   ├── signals.py  ⭐    # post_save/post_delete → WebSocket broadcast
│   ├── consumers.py      # WebSocket consumer (Django Channels)
│   ├── views.py          # REST API views (GET, POST, PATCH, DELETE)
│   ├── urls.py           # orders/ URL patterns
│   └── apps.py           # Connects signals on Django startup
├── client/
│   └── index.html        # Browser demo (no build step needed)
├── docker-compose.yml    # PostgreSQL + Redis
├── requirements.txt
└── .env
```

---

## Prerequisites

- Python 3.12+
- Docker Desktop (for PostgreSQL + Redis)

---

## Setup & Run

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd pooling_backend

pip install -r requirements.txt
```

### 2. Start PostgreSQL and Redis

```bash
docker-compose up -d
```

### 3. Copy and configure environment variables

```bash
copy .env.example .env
# Edit .env if needed (default values work with docker-compose)
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Start the Django server (ASGI mode for WebSocket support)

```bash
daphne config.asgi:application
```

Server runs at: `http://localhost:8000`

---

## Test It

### Open the browser client

Open `client/index.html` directly in your browser (no web server needed).  
Open it in **2 or more tabs** to see live sync.

### Test with curl

```bash
# Create an order
curl -X POST http://localhost:8000/api/orders/ \
     -H "Content-Type: application/json" \
     -d '{"customer_name": "Alice", "product_name": "Laptop"}'

# Update status
curl -X PATCH http://localhost:8000/api/orders/1/ \
     -H "Content-Type: application/json" \
     -d '{"status": "shipped"}'

# Delete an order
curl -X DELETE http://localhost:8000/api/orders/1/

# List all orders
curl http://localhost:8000/api/orders/
```

Every operation instantly appears in all open browser tabs. ✅

---

## REST API Reference

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/orders/` | List all orders |
| `POST` | `/api/orders/` | Create order → triggers real-time update |
| `GET` | `/api/orders/<id>/` | Get single order |
| `PATCH` | `/api/orders/<id>/` | Update status → triggers real-time update |
| `DELETE` | `/api/orders/<id>/` | Delete order → triggers real-time update |

### WebSocket

| URL | Description |
|-----|-------------|
| `ws://localhost:8000/ws/orders/` | Subscribe to live order events |

### WebSocket Message Format

**On connect** — full snapshot:
```json
{
  "type": "SNAPSHOT",
  "orders": [ { "id": 1, "customer_name": "Alice", ... } ]
}
```

**On change** — event:
```json
{
  "type": "ORDER_CHANGE",
  "change_type": "INSERT",
  "order": { "id": 1, "customer_name": "Alice", "product_name": "Laptop", "status": "pending", "updated_at": "..." }
}
```

`change_type` is one of: `INSERT`, `UPDATE`, `DELETE`.

---

## Why Django Signals?

Django's `post_save` and `post_delete` signals fire automatically after every ORM write.  
This means:
- **No polling** — clients receive updates instantly
- **No SQL triggers** — pure Django, no extra DB setup
- **No daemon threads** — signals run in the same request/response cycle
- **Easy to test** — call `post_save.send(Order, instance=..., created=True)` in tests

The signal handler uses `async_to_sync(channel_layer.group_send)` to bridge the synchronous signal context into the async Redis channel layer.

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Real-time mechanism | Django Signals | Native Django, no extra infra |
| WebSocket server | Django Channels + Daphne | Official Django WebSocket solution |
| Channel fan-out | Redis Channel Layer | Decouples signal from consumers, scales horizontally |
| Initial state | Snapshot on WS connect | Client always starts with full current data |
| Auto-reconnect | Client retries every 3s | Resilient to server restarts |
