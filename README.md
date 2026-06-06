# 📦 Real-Time Order Updates — Django + Signals + WebSockets

A backend service that pushes live order changes to all connected browser clients in real-time.  
Built with **Django**, **Django Channels**, **Django Signals**, **Redis**, and **PostgreSQL**.

---

## 🚀 Live Demo (Railway)

**API Base URL:** `https://web-production-397a5.up.railway.app`  
**WebSocket URL:** `wss://web-production-397a5.up.railway.app/ws/orders/`

---

## 🧪 How to Test (No Setup Required)

The app is already deployed and running. You only need the browser client file.

### Step 1 — Download & open the client

Download [`client/index.html`](./client/index.html) from this repo and open it in your browser by double-clicking it.

> The HTML file already points to the Railway deployment — no configuration needed.

### Step 2 — Open it in 2 tabs

Press `Ctrl+T`, open a new tab, and drag the same `index.html` file into it.  
Both tabs should show **✅ Connected** in the top-right corner.

### Step 3 — Create an order in Tab 1

Fill in the form at the bottom:
- **Customer Name** → e.g. `Alice`
- **Product Name** → e.g. `Laptop`
- Click **➕ Create**

👉 Watch **Tab 2** — the order appears instantly **without refreshing**. That's real-time WebSocket in action!

### Step 4 — Update status

Enter Order ID `1`, select `Shipped` → click **✏️ Update**  
→ Both tabs update the status badge **instantly** ✅

### Step 5 — Delete

Enter Order ID `1` → click **🗑️ Delete**  
→ The row disappears in **both tabs simultaneously** ✅

---

## 🌐 Test with curl

```bash
BASE=https://web-production-397a5.up.railway.app

# List all orders
curl $BASE/api/orders/

# Create an order
curl -X POST $BASE/api/orders/ \
     -H "Content-Type: application/json" \
     -d '{"customer_name": "Alice", "product_name": "Laptop"}'

# Update status
curl -X PATCH $BASE/api/orders/1/ \
     -H "Content-Type: application/json" \
     -d '{"status": "shipped"}'

# Delete an order
curl -X DELETE $BASE/api/orders/1/
```

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
│   ├── settings.py       # Django settings (DB, Channels, ASGI, CORS)
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
├── Procfile              # Railway start command
├── runtime.txt           # Python version pin for Railway
├── docker-compose.yml    # PostgreSQL + Redis (local dev)
├── requirements.txt
└── .env.example
```

---

## REST API Reference

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/orders/` | List all orders |
| `POST` | `/api/orders/` | Create order → triggers real-time update |
| `GET` | `/api/orders/<id>/` | Get single order |
| `PATCH` | `/api/orders/<id>/` | Update status → triggers real-time update |
| `DELETE` | `/api/orders/<id>/` | Delete order → triggers real-time update |

### WebSocket Message Format

**On connect** — full snapshot of all current orders:
```json
{
  "type": "SNAPSHOT",
  "orders": [ { "id": 1, "customer_name": "Alice", "product_name": "Laptop", "status": "pending", "updated_at": "..." } ]
}
```

**On any change** — real-time event pushed to all connected clients:
```json
{
  "type": "ORDER_CHANGE",
  "change_type": "INSERT",
  "order": { "id": 1, "customer_name": "Alice", "product_name": "Laptop", "status": "pending", "updated_at": "..." }
}
```

`change_type` is one of: `INSERT`, `UPDATE`, `DELETE`.

---

## Run Locally

### Prerequisites

- Python 3.12+
- Docker Desktop (for PostgreSQL + Redis)

### 1. Clone and install

```bash
git clone https://github.com/VENUGOPAL-ADUSUMALLI/ws-realtime.git
cd ws-realtime

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### 3. Start PostgreSQL and Redis

```bash
docker-compose up -d
```

### 4. Run migrations and start server

```bash
python manage.py migrate
daphne config.asgi:application
```

Server runs at: `http://localhost:8000`

### 5. Open the client

Open `client/index.html` in your browser.  
Update these two lines in the file to point to `localhost`:

```js
const API    = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws/orders/';
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web server | Django 5.2 + Daphne (ASGI) |
| Real-time | Django Channels 4.1 + Django Signals |
| Message broker | Redis (via channels-redis) |
| Database | PostgreSQL |
| CORS | django-cors-headers |
| Static files | WhiteNoise |
| Deployment | Railway |

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Real-time mechanism | Django Signals | Native Django, no extra infra |
| WebSocket server | Django Channels + Daphne | Official Django WebSocket solution |
| Channel fan-out | Redis Channel Layer | Decouples signal from consumers, scales horizontally |
| Initial state | Snapshot on WS connect | Client always starts with full current data |
| Auto-reconnect | Client retries every 3s | Resilient to server restarts |
| CORS | django-cors-headers | Allows cross-origin browser clients |
