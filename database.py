"""SQLite persistence layer (async, via aiosqlite).

A single ``orders`` table is enough for this demo. Order line items are stored
as a JSON blob so we keep the schema simple while still recording exactly what
was ordered.
"""

import json
from datetime import datetime

import aiosqlite

from config import ADMIN_CHAT_ID, DB_PATH

# --- Order status constants -------------------------------------------------

STATUS_NEW = "new"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"


async def init_db() -> None:
    """Create the database schema if it does not exist yet."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                username       TEXT,                        -- Telegram @username (may be NULL)
                customer_name  TEXT    NOT NULL,
                phone          TEXT    NOT NULL,
                items          TEXT    NOT NULL,           -- JSON array of line items
                total          REAL    NOT NULL,
                status         TEXT    NOT NULL DEFAULT 'new',
                paid           INTEGER NOT NULL DEFAULT 0,  -- 1 if paid online
                payment_method TEXT,                        -- 'online' | 'cash' | NULL
                charge_id      TEXT,                         -- provider payment charge id
                comment        TEXT,                         -- optional customer note
                created_at     TEXT    NOT NULL
            )
            """
        )
        # Per-user preferences (currently just the chosen interface language).
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id  INTEGER PRIMARY KEY,
                language TEXT NOT NULL
            )
            """
        )
        # Staff added at runtime, each with a role. The ADMIN_CHAT_ID from the
        # environment is the super admin and is NOT stored here.
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id  INTEGER PRIMARY KEY,
                role     TEXT    NOT NULL DEFAULT 'admin',
                name     TEXT,
                username TEXT,
                added_at TEXT    NOT NULL
            )
            """
        )
        # Editable menu — seeded from code defaults on first run (see menu.py).
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id          TEXT    PRIMARY KEY,
                name        TEXT    NOT NULL,
                price       REAL    NOT NULL,
                category    TEXT    NOT NULL,
                emoji       TEXT    NOT NULL,
                accent      TEXT    NOT NULL,
                description TEXT,                          -- JSON {lang: text}
                status      TEXT    NOT NULL DEFAULT 'available',
                position    INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        await _migrate(db)
        await db.commit()


async def _migrate(db: aiosqlite.Connection) -> None:
    """Apply small, additive schema migrations for older databases."""
    async def columns_of(table: str) -> set[str]:
        cursor = await db.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in await cursor.fetchall()}

    order_cols = await columns_of("orders")
    if "username" not in order_cols:
        await db.execute("ALTER TABLE orders ADD COLUMN username TEXT")
    if "paid" not in order_cols:
        await db.execute("ALTER TABLE orders ADD COLUMN paid INTEGER NOT NULL DEFAULT 0")
    if "payment_method" not in order_cols:
        await db.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT")
    if "charge_id" not in order_cols:
        await db.execute("ALTER TABLE orders ADD COLUMN charge_id TEXT")
    if "comment" not in order_cols:
        await db.execute("ALTER TABLE orders ADD COLUMN comment TEXT")

    # The "admins" table gained role/name/username columns over time.
    admin_cols = await columns_of("admins")
    if "role" not in admin_cols:
        await db.execute("ALTER TABLE admins ADD COLUMN role TEXT NOT NULL DEFAULT 'admin'")
    if "name" not in admin_cols:
        await db.execute("ALTER TABLE admins ADD COLUMN name TEXT")
    if "username" not in admin_cols:
        await db.execute("ALTER TABLE admins ADD COLUMN username TEXT")


async def create_order(
    user_id: int,
    username: str | None,
    customer_name: str,
    phone: str,
    items: list[dict],
    total: float,
    paid: bool = False,
    payment_method: str | None = None,
    charge_id: str | None = None,
    comment: str | None = None,
) -> int:
    """Insert a new order and return its generated id.

    ``items`` is a list of ``{"id", "name", "price", "qty"}`` dictionaries.
    ``username`` is the customer's Telegram @username (without @), or ``None``.
    ``payment_method`` is ``'online'`` (with ``paid=True``), ``'cash'`` or ``None``.
    ``comment`` is an optional free-text note from the customer.
    """
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO orders
                (user_id, username, customer_name, phone, items, total, status,
                 paid, payment_method, charge_id, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                customer_name,
                phone,
                json.dumps(items, ensure_ascii=False),
                round(total, 2),
                STATUS_NEW,
                1 if paid else 0,
                payment_method,
                charge_id,
                comment,
                created_at,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_order(order_id: int) -> dict | None:
    """Return a single order as a dict (with ``items`` already decoded)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        return _row_to_order(row) if row else None


async def update_order_status(order_id: int, status: str) -> None:
    """Change the status of an order (new / accepted / rejected)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await db.commit()


async def get_recent_orders(limit: int = 10) -> list[dict]:
    """Return the most recent orders, newest first."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [_row_to_order(row) for row in rows]


async def get_today_stats() -> dict:
    """Return today's order count and today's revenue from accepted orders."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT
                COUNT(*) AS orders_today,
                COALESCE(SUM(CASE WHEN status = ? THEN total ELSE 0 END), 0)
                    AS revenue_today
            FROM orders
            WHERE date(created_at) = date('now', 'localtime')
            """,
            (STATUS_ACCEPTED,),
        )
        orders_today, revenue_today = await cursor.fetchone()
        return {
            "orders_today": orders_today,
            "revenue_today": revenue_today,
        }


def _row_to_order(row: aiosqlite.Row) -> dict:
    """Convert a raw DB row into a plain dict, decoding the JSON items."""
    order = dict(row)
    order["items"] = json.loads(order["items"])
    return order


# --- User language preferences ---------------------------------------------

async def get_user_language(user_id: int) -> str | None:
    """Return the user's stored language code, or ``None`` if not chosen yet."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_user_language(user_id: int, language: str) -> None:
    """Store (or update) the user's preferred language."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, language) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
            """,
            (user_id, language),
        )
        await db.commit()


# --- Staff & roles ----------------------------------------------------------

# Role constants, ordered from most to least powerful.
ROLE_SUPER = "super_admin"   # the env ADMIN_CHAT_ID; manages everyone, undeletable
ROLE_ADMIN = "admin"         # can manage admins & moderators
ROLE_MODERATOR = "moderator" # can only accept/reject orders

# Roles that are allowed to add/remove other staff.
_MANAGER_ROLES = {ROLE_SUPER, ROLE_ADMIN}


async def get_role(user_id: int) -> str | None:
    """Return the user's role, or ``None`` if they are not staff."""
    if user_id == ADMIN_CHAT_ID:
        return ROLE_SUPER
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role FROM admins WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def is_staff(user_id: int) -> bool:
    """True for the super admin and any added admin/moderator."""
    return await get_role(user_id) is not None


async def can_manage_staff(user_id: int) -> bool:
    """True if the user may add or remove other staff."""
    return (await get_role(user_id)) in _MANAGER_ROLES


async def add_staff(user_id: int, role: str, name: str | None, username: str | None) -> bool:
    """Add a staff member with a role. Returns ``False`` if already staff."""
    if user_id == ADMIN_CHAT_ID or await is_staff(user_id):
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO admins (user_id, role, name, username, added_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, role, name, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        await db.commit()
    return True


async def update_staff_identity(user_id: int, name: str | None, username: str | None) -> None:
    """Fill in a staff member's display name / username once we learn them."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE admins SET name = COALESCE(?, name), username = COALESCE(?, username) "
            "WHERE user_id = ?",
            (name, username, user_id),
        )
        await db.commit()


async def remove_staff(user_id: int) -> bool:
    """Remove a runtime-added staff member. Returns ``False`` if not found."""
    if user_id == ADMIN_CHAT_ID:  # the super admin can never be removed
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()
        return cursor.rowcount > 0


async def list_staff() -> list[dict]:
    """All staff as dicts ``{user_id, role, name, username}`` — super admin first."""
    staff = [{"user_id": ADMIN_CHAT_ID, "role": ROLE_SUPER, "name": None, "username": None}]
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, role, name, username FROM admins ORDER BY role, added_at"
        )
        for row in await cursor.fetchall():
            if row["user_id"] != ADMIN_CHAT_ID:
                staff.append(dict(row))
    return staff


async def list_staff_ids() -> list[int]:
    """All staff ids (super admin first) — used to broadcast notifications."""
    return [member["user_id"] for member in await list_staff()]


# --- Editable menu (products) ----------------------------------------------

async def get_all_products() -> list[dict]:
    """Return every product ordered by display position."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM products ORDER BY position, id")
        return [dict(row) for row in await cursor.fetchall()]


async def seed_products(products: list[dict]) -> None:
    """Insert default products (used once, when the table is empty)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """
            INSERT INTO products (id, name, price, category, emoji, accent, description, status, position)
            VALUES (:id, :name, :price, :category, :emoji, :accent, :description, :status, :position)
            """,
            products,
        )
        await db.commit()


async def insert_product(product: dict) -> None:
    """Insert a single product created via the in-bot editor."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO products (id, name, price, category, emoji, accent, description, status, position)
            VALUES (:id, :name, :price, :category, :emoji, :accent, :description, :status, :position)
            """,
            product,
        )
        await db.commit()


async def set_product_price(product_id: str, price: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE products SET price = ? WHERE id = ?", (round(price, 2), product_id))
        await db.commit()


async def set_product_status(product_id: str, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE products SET status = ? WHERE id = ?", (status, product_id))
        await db.commit()


async def delete_product(product_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


async def get_max_product_position() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COALESCE(MAX(position), 0) FROM products")
        (value,) = await cursor.fetchone()
        return value
