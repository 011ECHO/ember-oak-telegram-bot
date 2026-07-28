"""Shopping-cart helpers.

The cart lives inside the per-user FSM data as a simple ``{product_id: qty}``
mapping. aiogram keeps that data around even when no FSM state is active, so the
cart survives while the customer browses the menu and only gets cleared once an
order is placed.
"""

from aiogram.fsm.context import FSMContext

from locales import t
from menu import Product, get_product

# Key under which the cart is stored inside the FSM data dictionary.
_CART_KEY = "cart"


async def get_cart(state: FSMContext) -> dict[str, int]:
    """Return a copy of the current cart ({product_id: quantity})."""
    data = await state.get_data()
    return dict(data.get(_CART_KEY, {}))


async def _save(state: FSMContext, cart: dict[str, int]) -> None:
    await state.update_data({_CART_KEY: cart})


async def add_item(state: FSMContext, product_id: str, qty: int = 1) -> None:
    """Add ``qty`` units of a product to the cart."""
    cart = await get_cart(state)
    cart[product_id] = cart.get(product_id, 0) + qty
    await _save(state, cart)


async def change_qty(state: FSMContext, product_id: str, delta: int) -> dict[str, int]:
    """Increment/decrement a product's quantity, removing it when it hits zero."""
    cart = await get_cart(state)
    if product_id in cart:
        cart[product_id] += delta
        if cart[product_id] <= 0:
            cart.pop(product_id)
        await _save(state, cart)
    return cart


async def remove_item(state: FSMContext, product_id: str) -> None:
    """Remove a product from the cart entirely."""
    cart = await get_cart(state)
    cart.pop(product_id, None)
    await _save(state, cart)


async def clear_cart(state: FSMContext) -> None:
    """Empty the cart."""
    await _save(state, {})


def cart_lines(cart: dict[str, int]) -> list[tuple[Product, int, float]]:
    """Expand a raw cart into ``(product, quantity, subtotal)`` tuples."""
    lines: list[tuple[Product, int, float]] = []
    for product_id, qty in cart.items():
        product = get_product(product_id)
        if product is None:  # product was removed from the menu — skip it
            continue
        lines.append((product, qty, product.price * qty))
    return lines


def cart_total(cart: dict[str, int]) -> float:
    """Total price of everything currently in the cart."""
    return sum(subtotal for _, _, subtotal in cart_lines(cart))


def cart_count(cart: dict[str, int]) -> int:
    """Total number of items (summed quantities) in the cart."""
    return sum(cart.values())


def format_cart(cart: dict[str, int], lang: str) -> str:
    """Render the cart contents as an HTML message body."""
    lines = cart_lines(cart)
    if not lines:
        return t(lang, "cart_empty")

    text = t(lang, "cart_title") + "\n\n"
    for product, qty, subtotal in lines:
        text += f"• {product.name} — €{product.price:.2f} × {qty} = <b>€{subtotal:.2f}</b>\n"
    text += f"\n<b>{t(lang, 'cart_total')}: €{cart_total(cart):.2f}</b>"
    return text
