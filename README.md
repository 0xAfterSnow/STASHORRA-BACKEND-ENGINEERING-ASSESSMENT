# Stashorra — Auction Marketplace API

A backend assessment project: a simple auction marketplace API built with
**Django** and **Django REST Framework**, using class-based `APIView`s
throughout (no generic/viewset shortcuts), JWT authentication, and
role-based permissions.

## Tech Stack

- Python 3.11+, Django 6, Django REST Framework
- `djangorestframework-simplejwt` — JWT auth + refresh-token blacklist (logout)
- `drf-spectacular` — OpenAPI schema + Swagger UI
- SQLite (default, zero-config for this assessment — swap `DATABASES` for
  Postgres in a real deployment)

## 1. Setup Instructions

```bash
# 1. Clone and enter the project
git clone https://github.com/0xAfterSnow/STASHORRA-BACKEND-ENGINEERING-ASSESSMENT stashorra
cd stashorra

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional — sane defaults are provided)
cp .env.example .env

# 5. Run migrations
python manage.py migrate

# 6. (Optional) create a Django superuser for /admin/
python manage.py createsuperuser

# 7. Run the dev server
python manage.py runserver
```

The API is now available at `http://localhost:8000/api/`.

**Swagger UI:** `http://localhost:8000/api/docs/`
**ReDoc:** `http://localhost:8000/api/redoc/`
**Raw OpenAPI schema:** `http://localhost:8000/api/schema/`
**Django admin:** `http://localhost:8000/admin/`

### Closing expired auctions

Auction expiry is enforced **lazily**: any read of an auction (list or
detail) first closes auctions whose `end_time` has passed, assigning the
highest bidder as the winner. This keeps the demo fully functional with
zero extra infrastructure.

For a more realistic setup, a management command is also provided so it
can be wired into cron / Celery beat:

```bash
python manage.py close_expired_auctions
```