"""Keyboard builders (inline + reply).

All keyboards are constructed here so the handlers stay focused on logic and the
button layout lives in one place. Every builder takes a ``lang`` code so button
captions are localized; product and category names stay in their original form.
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from callbacks import AdminCB, CartCB, LangCB, MenuAdminCB, MenuCB, OrderCB, PayCB, ProductCB, StaffCB
from cart import cart_lines
from locales import LANGUAGES, prod_status_label, role_label, t
from menu import (
    CATEGORIES,
    STATUS_HIDDEN,
    STATUS_OUT,
    Product,
    products_in,
)


def language_kb() -> InlineKeyboardMarkup:
    """One button per supported language."""
    builder = InlineKeyboardBuilder()
    for code, label in LANGUAGES.items():
        builder.button(text=label, callback_data=LangCB(code=code))
    builder.adjust(1)
    return builder.as_markup()


def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Root keyboard shown by /start."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_menu"), callback_data=MenuCB(action="categories"))
    builder.button(text=t(lang, "btn_cart"), callback_data=CartCB(action="view"))
    builder.adjust(1)
    return builder.as_markup()


def categories_kb(lang: str) -> InlineKeyboardMarkup:
    """List of product categories."""
    builder = InlineKeyboardBuilder()
    for key, title in CATEGORIES.items():
        builder.button(text=title, callback_data=MenuCB(action="category", value=key))
    builder.button(text=t(lang, "btn_cart"), callback_data=CartCB(action="view"))
    builder.button(text=t(lang, "btn_back"), callback_data=MenuCB(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def catalog_footer_kb(lang: str) -> InlineKeyboardMarkup:
    """Navigation shown after a category's product cards."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_categories"), callback_data=MenuCB(action="categories"))
    builder.button(text=t(lang, "btn_cart"), callback_data=CartCB(action="view"))
    builder.adjust(2)
    return builder.as_markup()


def product_card_kb(product: Product, qty: int, lang: str) -> InlineKeyboardMarkup:
    """Add / quantity controls under a product card in the catalog."""
    builder = InlineKeyboardBuilder()
    if product.status == STATUS_OUT:
        builder.row(
            InlineKeyboardButton(
                text=t(lang, "out_of_stock_note"),
                callback_data=CartCB(action="noop", pid=product.id).pack(),
            )
        )
    elif qty <= 0:
        builder.row(
            InlineKeyboardButton(
                text=t(lang, "btn_add_to_cart"),
                callback_data=ProductCB(action="add", pid=product.id).pack(),
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(text="➖", callback_data=ProductCB(action="dec", pid=product.id).pack()),
            InlineKeyboardButton(text=f"🛒 {qty}", callback_data=CartCB(action="view").pack()),
            InlineKeyboardButton(text="➕", callback_data=ProductCB(action="inc", pid=product.id).pack()),
        )
    return builder.as_markup()


def cart_kb(cart: dict[str, int], lang: str) -> InlineKeyboardMarkup:
    """Cart view with per-item +/-/delete controls and the checkout button."""
    builder = InlineKeyboardBuilder()

    for product, qty, subtotal in cart_lines(cart):
        # Line 1: read-only summary of the position.
        builder.row(
            InlineKeyboardButton(
                text=f"{product.name} · {qty} × €{product.price:.2f} = €{subtotal:.2f}",
                callback_data=CartCB(action="noop", pid=product.id).pack(),
            )
        )
        # Line 2: quantity controls for that position.
        builder.row(
            InlineKeyboardButton(
                text="➖", callback_data=CartCB(action="dec", pid=product.id).pack()
            ),
            InlineKeyboardButton(
                text="❌", callback_data=CartCB(action="del", pid=product.id).pack()
            ),
            InlineKeyboardButton(
                text="➕", callback_data=CartCB(action="inc", pid=product.id).pack()
            ),
        )

    if cart:
        builder.row(
            InlineKeyboardButton(
                text=t(lang, "btn_checkout"),
                callback_data=CartCB(action="checkout").pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=t(lang, "btn_clear"),
                callback_data=CartCB(action="clear").pack(),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=t(lang, "btn_to_menu"), callback_data=MenuCB(action="categories").pack()
        )
    )
    return builder.as_markup()


def checkout_actions_kb(lang: str, payments_enabled: bool) -> InlineKeyboardMarkup:
    """Actions on the order summary.

    With payments configured the customer picks how to pay; otherwise they just
    confirm the order.
    """
    builder = InlineKeyboardBuilder()
    if payments_enabled:
        builder.button(text=t(lang, "btn_pay_online"), callback_data=PayCB(method="online"))
        builder.button(text=t(lang, "btn_pay_cash"), callback_data=PayCB(method="cash"))
    else:
        builder.button(text=t(lang, "btn_confirm"), callback_data=OrderCB(action="confirm"))
    builder.button(text=t(lang, "btn_cancel"), callback_data=OrderCB(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def nav_reply_kb(lang: str) -> ReplyKeyboardMarkup:
    """Persistent bottom bar with the main navigation buttons.

    ``is_persistent`` keeps it available via the grid icon next to the input
    field, the way large bots (e.g. Chat Wars) expose their quick actions.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_menu")), KeyboardButton(text=t(lang, "btn_cart"))],
            [KeyboardButton(text=t(lang, "btn_feedback")), KeyboardButton(text=t(lang, "rk_language"))],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=t(lang, "nav_placeholder"),
    )


def skip_comment_kb(lang: str) -> InlineKeyboardMarkup:
    """A single 'skip' button for the optional order-comment step."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_skip"), callback_data=OrderCB(action="skip_comment"))
    return builder.as_markup()


def phone_request_kb(lang: str) -> ReplyKeyboardMarkup:
    """Reply keyboard with a native 'share contact' button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "btn_share_contact"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=t(lang, "phone_placeholder"),
    )


def admin_order_kb(order_id: int, lang: str) -> InlineKeyboardMarkup:
    """Accept / reject buttons attached to the admin notification."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_accept"), callback_data=AdminCB(action="accept", order_id=order_id))
    builder.button(text=t(lang, "btn_reject"), callback_data=AdminCB(action="reject", order_id=order_id))
    builder.adjust(2)
    return builder.as_markup()


def staff_display_name(member: dict) -> str:
    """A short label for a staff member: @username, else name, else id."""
    if member.get("username"):
        return f"@{member['username']}"
    return member.get("name") or str(member["user_id"])


def staff_panel_kb(lang: str, can_manage: bool) -> InlineKeyboardMarkup | None:
    """Panel under the staff list — only managers get the remove button."""
    if not can_manage:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_remove_member"), callback_data=StaffCB(action="remove_menu"))
    builder.adjust(1)
    return builder.as_markup()


def staff_remove_kb(members: list[dict], lang: str) -> InlineKeyboardMarkup:
    """A picker (inline "dropdown") of removable staff members."""
    builder = InlineKeyboardBuilder()
    for member in members:
        label = f"{staff_display_name(member)} · {role_label(lang, member['role'])}"
        builder.button(text=f"➖ {label}", callback_data=StaffCB(action="remove", uid=member["user_id"]))
    builder.button(text=t(lang, "btn_back"), callback_data=StaffCB(action="back"))
    builder.adjust(1)
    return builder.as_markup()


# --- menu editor keyboards --------------------------------------------------

def editmenu_categories_kb(lang: str) -> InlineKeyboardMarkup:
    """Category picker for the menu editor."""
    builder = InlineKeyboardBuilder()
    for key, title in CATEGORIES.items():
        builder.button(text=title, callback_data=MenuAdminCB(action="cat", pid=key))
    builder.adjust(1)
    return builder.as_markup()


def editmenu_products_kb(category: str, lang: str) -> InlineKeyboardMarkup:
    """Products of a category (all statuses) plus an 'add product' button."""
    builder = InlineKeyboardBuilder()
    for product in products_in(category):  # managers see everything, incl. hidden
        icon = {STATUS_OUT: "⛔", STATUS_HIDDEN: "🙈"}.get(product.status, "✅")
        builder.button(
            text=f"{icon} {product.emoji} {product.name} · €{product.price:.2f}",
            callback_data=MenuAdminCB(action="prod", pid=product.id),
        )
    builder.button(text=t(lang, "btn_add_product"), callback_data=MenuAdminCB(action="add", pid=category))
    builder.button(text=t(lang, "btn_back"), callback_data=MenuAdminCB(action="cats"))
    builder.adjust(1)
    return builder.as_markup()


def product_admin_kb(product: Product, lang: str) -> InlineKeyboardMarkup:
    """Actions for one product: price, status, delete."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_change_price"),
                             callback_data=MenuAdminCB(action="price", pid=product.id).pack())
    )
    # Offer the status changes that aren't the current one.
    status_buttons = []
    if product.status != "available":
        status_buttons.append(("btn_set_available", "available"))
    if product.status != STATUS_OUT:
        status_buttons.append(("btn_set_out", STATUS_OUT))
    if product.status != STATUS_HIDDEN:
        status_buttons.append(("btn_set_hidden", STATUS_HIDDEN))
    builder.row(*[
        InlineKeyboardButton(text=t(lang, key),
                             callback_data=MenuAdminCB(action="status", pid=product.id, extra=value).pack())
        for key, value in status_buttons
    ])
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_delete"),
                             callback_data=MenuAdminCB(action="del", pid=product.id).pack())
    )
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_back"),
                             callback_data=MenuAdminCB(action="cat", pid=product.category).pack())
    )
    return builder.as_markup()


def product_delete_confirm_kb(product: Product, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_delete_confirm"), callback_data=MenuAdminCB(action="delok", pid=product.id))
    builder.button(text=t(lang, "btn_back"), callback_data=MenuAdminCB(action="prod", pid=product.id))
    builder.adjust(1)
    return builder.as_markup()


def add_skip_description_kb(lang: str) -> InlineKeyboardMarkup:
    """Skip button for the optional description step when adding a product."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t(lang, "btn_skip"), callback_data=MenuAdminCB(action="skipdesc"))
    return builder.as_markup()
