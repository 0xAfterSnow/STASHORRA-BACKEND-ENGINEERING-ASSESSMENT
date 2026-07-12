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
## 2. API Overview

All endpoints are prefixed with `/api/`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register/` | Public | Create a new account (always role=`user`) |
| POST | `/auth/login/` | Public | Obtain JWT access/refresh token pair |
| POST | `/auth/logout/` | Authenticated | Blacklist a refresh token |
| GET | `/auth/me/` | Authenticated | Current user's profile |
| GET | `/auctions/` | Public | List all auction listings (`?status=`, `?owner=`) |
| POST | `/auctions/` | Authenticated | Create an auction listing |
| GET | `/auctions/{id}/` | Public | Retrieve a single auction |
| PUT/PATCH | `/auctions/{id}/` | Owner or Admin | Update an auction (only while `active`) |
| DELETE | `/auctions/{id}/` | Owner or Admin | Delete an auction |
| GET | `/auctions/{id}/bids/` | Public | Full bid history for an auction |
| POST | `/auctions/{id}/bids/` | Authenticated | Place a bid |

Full request/response schemas are in Swagger (`/api/docs/`).

## 3. Database Design Overview

```
User (accounts.User, extends AbstractUser)
 ├─ id, username, email, password, role [user|admin]
 │
 ├──< AuctionListing (owner FK)
 │      id, title, description, starting_price, current_price,
 │      end_time, status [active|completed|cancelled], winner (FK User, nullable)
 │
 └──< Bid (bidder FK)
        id, auction (FK AuctionListing), amount, created_at
```

- **User → AuctionListing** is one-to-many via `owner`: a user can list
  many auctions.
- **AuctionListing → Bid** is one-to-many: every bid placed is preserved
  (bids are never edited or deleted), giving a full, auditable bid
  history per auction.
- **AuctionListing.winner** is a nullable FK to `User`, set only once the
  auction closes. `on_delete=SET_NULL` so historical listings survive a
  user account being removed.
- `current_price` is denormalized onto `AuctionListing` (rather than
  always computed via `MAX(bid.amount)`) so that listing/browsing
  auctions is a single cheap query. It's kept in sync any time a bid is
  accepted or an auction closes.

## 4. Authentication Approach

- JWT via `djangorestframework-simplejwt`. `POST /auth/login/` and
  `POST /auth/register/` both return an `{access, refresh}` pair.
- Protected endpoints expect `Authorization: Bearer <access_token>`.
- **Logout** is implemented via the simplejwt **token blacklist** app:
  `POST /auth/logout/` with a `refresh` token blacklists it, so it can no
  longer be used to mint new access tokens. (Stateless access tokens
  remain valid until they naturally expire — a standard JWT trade-off;
  access-token lifetime is kept short, 60 minutes, to bound this.)
- Passwords are validated with Django's built-in password validators and
  stored using Django's standard hasher (PBKDF2).

## 5. Permission Model

Two roles: `user` (default) and `admin`.

- `IsOwnerOrAdmin` (object-level): safe methods (`GET`/`HEAD`/`OPTIONS`)
  are open to everyone; write methods are only allowed for the object's
  `owner` or a user with `role="admin"` (or `is_superuser`).
- `IsAdminRole`: used anywhere an endpoint should be admin-only (not
  currently required by the spec, but included as a reusable building
  block — e.g. for a future "force-cancel any auction" endpoint).
- Registration **never** accepts a `role` field from the client — every
  new signup is a plain `user`. Promotion to `admin` is an explicit,
  out-of-band action (`promote_to_admin` management command, or via
  `/admin/`), so a user can never self-escalate.
- Auction bidding enforces its own request-level rules directly in the
  view (see below), since these are business rules rather than
  role/ownership checks:
  - A bid must be strictly greater than the auction's current price.
  - The auction owner cannot bid on their own auction.
  - No bids are accepted once an auction is `completed`/`cancelled` or
    its `end_time` has passed.

## 6. Assumptions Made

- "Admin has full access" is interpreted as: any listing/bid,
  create/read/update/delete, regardless of ownership. Admin status is a
  separate `role` field rather than reusing Django's `is_staff`, so that
  marketplace-admin and Django-admin-site-access can be reasoned about
  independently (though a superuser is always treated as a marketplace
  admin too, for convenience).
- An auction can only be edited (`PUT`/`PATCH`) while it's still
  `active`; once bidding has closed, its terms are frozen — this
  protects bidders from a seller changing the listing after bids have
  been placed. Deletion is allowed by the owner/admin at any time.
- Since a real scheduler (Celery/cron) is out of scope for a 4–8 hour
  assessment, auction expiry is enforced **lazily** on every read (list
  or detail), in addition to being exposed as a standalone management
  command for real scheduling. This keeps behavior consistent and
  demoable without extra infrastructure.
- `current_price` starts equal to `starting_price` and is only ever
  updated by an accepted bid or by auction closure — never directly by
  a client request.
- Ties on the highest bid amount are broken by earliest `created_at`
  (first bidder to reach that amount wins), since two identical bid
  amounts can't both "win."
- No image/media uploads, categories, search, or payment/escrow flow —
  out of scope per the brief's emphasis on core auction mechanics.

## 7. Given another week, I would improve...

- **Real-time expiry** via Celery beat (or Django's `django-crontab`)
  instead of lazy, read-triggered closing, plus WebSocket/SSE push
  notifications when you're outbid or when an auction you're watching
  closes.
- **Optimistic concurrency / row locking** (`select_for_update`) around
  bid placement to fully eliminate race conditions under concurrent
  bidding load — currently protected by Django's transactional ORM
  writes but not explicitly locked.
- **Soft delete** for auctions with existing bids, instead of a hard
  `DELETE`, to preserve bid history/audit trail.
- **Rate limiting** on bid placement and auth endpoints (DRF throttling)
  to deter abuse.
- **Automatic auction-close notifications** (email) to the winner and
  seller.
- **Pagination/filtering polish**: price range filters, full-text search
  on title/description, ordering (`?ordering=end_time`).
- **Test suite**: the current project was verified via manual/functional
  API testing during development; a real submission would include
  `pytest-django` coverage for the permission matrix, bid edge cases
  (exact tie, last-second bid), and auction-close logic.
- **Category/tag model** and image uploads for listings.
- Move from SQLite to Postgres with proper indexing (`end_time`,
  `status`) for production-scale querying of "auctions ending soon."