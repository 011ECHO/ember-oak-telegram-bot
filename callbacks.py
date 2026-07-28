"""Typed callback-data factories.

aiogram's ``CallbackData`` gives us structured, self-documenting button payloads
instead of hand-parsed strings. Each class serialises to a compact string that
travels inside the inline button and is parsed back automatically by filters.
"""

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="m"):
    """Navigation between the main menu, category list and category items."""

    action: str        # "main" | "categories" | "category"
    value: str = ""    # category key when action == "category"


class CartCB(CallbackData, prefix="c"):
    """Cart operations."""

    action: str        # "view" | "add" | "inc" | "dec" | "del" | "clear" | "checkout" | "noop"
    pid: str = ""      # product id the action applies to


class ProductCB(CallbackData, prefix="p"):
    """Product detail card (opened from the category list)."""

    action: str        # "open" | "add" | "inc" | "dec" | "close"
    pid: str = ""      # product id the action applies to


class OrderCB(CallbackData, prefix="o"):
    """Final confirmation of an order (used when payments are disabled)."""

    action: str        # "confirm" | "cancel"


class PayCB(CallbackData, prefix="pay"):
    """Payment method choice on the order summary."""

    method: str        # "online" | "cash"


class AdminCB(CallbackData, prefix="a"):
    """Admin decision on an incoming order."""

    action: str        # "accept" | "reject"
    order_id: int


class LangCB(CallbackData, prefix="lang"):
    """Language selection."""

    code: str          # "ru" | "en" | "es"


class MenuAdminCB(CallbackData, prefix="ma"):
    """In-bot menu editor navigation and actions."""

    action: str        # "cats" | "cat" | "prod" | "price" | "status" | "del" | "delok" | "add"
    pid: str = ""      # product id or category key, depending on action
    extra: str = ""    # e.g. the new status for action == "status"


class StaffCB(CallbackData, prefix="staff"):
    """Staff-management panel (add hint / remove via selection)."""

    action: str        # "remove_menu" | "remove" | "back"
    uid: int = 0       # target user id for the "remove" action
