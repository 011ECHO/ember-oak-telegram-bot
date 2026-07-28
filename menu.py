"""Café menu — database-backed, editable from the bot.

Products live in the ``products`` DB table but are cached in memory so the rest
of the code can read them synchronously (``get_product``, ``products_in``). The
cache is (re)loaded at startup and after every edit. On first run the table is
seeded from ``_DEFAULTS`` below.
"""

import json
import logging
import re
from dataclasses import dataclass, field

import database
import images_gen

logger = logging.getLogger(__name__)

# Directory (relative to the project root) with one image per product: <id>.png
IMAGES_DIR = "images"

# Product availability.
STATUS_AVAILABLE = "available"
STATUS_OUT = "out_of_stock"   # visible to customers, cannot be ordered
STATUS_HIDDEN = "hidden"      # not shown to customers at all


@dataclass
class Product:
    """A single menu position."""

    id: str
    name: str
    price: float          # in EUR
    category: str
    emoji: str
    accent: str           # hex accent colour for the generated product image
    description: dict = field(default_factory=dict)  # lang -> text
    status: str = STATUS_AVAILABLE
    position: int = 0

    @property
    def image_path(self) -> str:
        return f"{IMAGES_DIR}/{self.id}.png"

    @property
    def is_available(self) -> bool:
        return self.status == STATUS_AVAILABLE


# Category key -> human-readable title (with emoji) shown in the UI.
CATEGORIES: dict[str, str] = {
    "coffee": "☕ Coffee",
    "pastry": "🥐 Pastry",
    "breakfast": "🍳 Breakfast",
}

# Default accent colour for products added to a category via the editor.
CATEGORY_ACCENT: dict[str, str] = {
    "coffee": "#8B5E3C",
    "pastry": "#C8892B",
    "breakfast": "#6B8E23",
}

# Seed data (used only when the products table is empty).
_DEFAULTS: list[dict] = [
    {"id": "espresso", "name": "Espresso", "price": 2.5, "category": "coffee", "emoji": "☕", "accent": "#4B2E2A",
     "desc": {"ru": "Насыщенный крепкий эспрессо.", "en": "Rich, bold single shot.", "es": "Espresso intenso y con cuerpo."}},
    {"id": "cappuccino", "name": "Cappuccino", "price": 3.5, "category": "coffee", "emoji": "☕", "accent": "#8B5E3C",
     "desc": {"ru": "Эспрессо с воздушной молочной пеной.", "en": "Espresso with airy milk foam.", "es": "Espresso con espuma de leche."}},
    {"id": "latte", "name": "Latte", "price": 3.8, "category": "coffee", "emoji": "☕", "accent": "#B07D52",
     "desc": {"ru": "Мягкий эспрессо с молоком.", "en": "Smooth espresso with steamed milk.", "es": "Espresso suave con leche vaporizada."}},
    {"id": "flat_white", "name": "Flat White", "price": 3.5, "category": "coffee", "emoji": "☕", "accent": "#9C7A5B",
     "desc": {"ru": "Бархатный эспрессо с микропеной.", "en": "Velvety espresso with microfoam.", "es": "Espresso aterciopelado con microespuma."}},
    {"id": "croissant", "name": "Croissant", "price": 2.8, "category": "pastry", "emoji": "🥐", "accent": "#C8892B",
     "desc": {"ru": "Слоёный масляный круассан.", "en": "Buttery, flaky French classic.", "es": "Croissant hojaldrado y mantecoso."}},
    {"id": "cinnamon_roll", "name": "Cinnamon Roll", "price": 3.2, "category": "pastry", "emoji": "🍩", "accent": "#A0522D",
     "desc": {"ru": "Тёплая булочка с корицей и глазурью.", "en": "Warm swirl with cinnamon glaze.", "es": "Rollo tibio con canela y glaseado."}},
    {"id": "muffin", "name": "Muffin", "price": 2.5, "category": "pastry", "emoji": "🧁", "accent": "#6A5ACD",
     "desc": {"ru": "Мягкий черничный маффин.", "en": "Soft blueberry muffin.", "es": "Muffin esponjoso de arándanos."}},
    {"id": "avocado_toast", "name": "Avocado Toast", "price": 6.5, "category": "breakfast", "emoji": "🥑", "accent": "#6B8E23",
     "desc": {"ru": "Тост на закваске с авокадо.", "en": "Sourdough with smashed avocado.", "es": "Tostada de masa madre con aguacate."}},
    {"id": "granola_bowl", "name": "Granola Bowl", "price": 5.5, "category": "breakfast", "emoji": "🥣", "accent": "#B8860B",
     "desc": {"ru": "Гранола, йогурт и свежие фрукты.", "en": "Granola, yogurt & fresh fruit.", "es": "Granola, yogur y fruta fresca."}},
]

# In-memory cache, populated by load_products().
_cache: dict[str, Product] = {}
_order: list[str] = []


# --- loading & seeding ------------------------------------------------------

async def load_products() -> None:
    """(Re)load the product cache from the database, seeding defaults if empty."""
    rows = await database.get_all_products()
    if not rows:
        await database.seed_products([
            {
                "id": d["id"], "name": d["name"], "price": d["price"], "category": d["category"],
                "emoji": d["emoji"], "accent": d["accent"],
                "description": json.dumps(d["desc"], ensure_ascii=False),
                "status": STATUS_AVAILABLE, "position": i,
            }
            for i, d in enumerate(_DEFAULTS)
        ])
        rows = await database.get_all_products()

    global _cache, _order
    _cache, _order = {}, []
    for row in rows:
        _cache[row["id"]] = Product(
            id=row["id"], name=row["name"], price=row["price"], category=row["category"],
            emoji=row["emoji"], accent=row["accent"],
            description=json.loads(row["description"] or "{}"),
            status=row["status"], position=row["position"],
        )
        _order.append(row["id"])


# --- synchronous reads (used everywhere) ------------------------------------

def get_product(product_id: str) -> Product | None:
    """Look up a product by id (returns ``None`` if it no longer exists)."""
    return _cache.get(product_id)


def products_in(category: str, for_customer: bool = False) -> list[Product]:
    """Products of a category. Customers don't see hidden items."""
    items = [_cache[i] for i in _order if _cache[i].category == category]
    if for_customer:
        items = [p for p in items if p.status != STATUS_HIDDEN]
    return items


def all_products() -> list[Product]:
    return [_cache[i] for i in _order]


def product_description(product_id: str, lang: str) -> str:
    """Localized description (falls back to English, then any, then empty)."""
    product = _cache.get(product_id)
    if not product or not product.description:
        return ""
    d = product.description
    return d.get(lang) or d.get("en") or next(iter(d.values()), "")


# --- async mutations (used by the in-bot editor) ----------------------------

async def add_product(name: str, price: float, category: str, emoji: str,
                      description_text: str) -> Product:
    """Create a new product, generate its image, and refresh the cache."""
    product_id = _unique_id(name)
    accent = CATEGORY_ACCENT.get(category, "#8B5E3C")
    desc = {lang: description_text for lang in ("ru", "en", "es")} if description_text else {}
    position = await database.get_max_product_position() + 1
    await database.insert_product({
        "id": product_id, "name": name, "price": round(price, 2), "category": category,
        "emoji": emoji, "accent": accent, "description": json.dumps(desc, ensure_ascii=False),
        "status": STATUS_AVAILABLE, "position": position,
    })
    _regenerate_image(product_id, name, price, emoji, accent)
    await load_products()
    return _cache[product_id]


async def set_price(product_id: str, price: float) -> None:
    await database.set_product_price(product_id, price)
    product = _cache.get(product_id)
    if product:  # keep the card image's price badge in sync
        _regenerate_image(product_id, product.name, price, product.emoji, product.accent)
    await load_products()


async def set_status(product_id: str, status: str) -> None:
    await database.set_product_status(product_id, status)
    await load_products()


async def remove_product(product_id: str) -> None:
    await database.delete_product(product_id)
    await load_products()


# --- helpers ----------------------------------------------------------------

def _regenerate_image(product_id: str, name: str, price: float, emoji: str, accent: str) -> None:
    try:
        images_gen.generate_card(product_id, name, price, emoji, accent, IMAGES_DIR)
    except Exception as error:  # best-effort — a missing image degrades gracefully
        logger.warning("Could not generate image for %s: %s", product_id, error)


def _unique_id(name: str) -> str:
    """Slugify a name into a stable, unique product id."""
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "item"
    product_id, n = base, 2
    while product_id in _cache:
        product_id = f"{base}_{n}"
        n += 1
    return product_id
