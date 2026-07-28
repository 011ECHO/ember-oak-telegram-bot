"""Helpers for composing and sending order notifications."""

import html
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import User

from database import list_staff_ids, get_user_language
from keyboards import admin_order_kb
from locales import DEFAULT_LANG, status_label, t

logger = logging.getLogger(__name__)


def human_dt(created_at: str) -> str:
    """Format a stored ISO datetime as European ``DD.MM.YYYY HH:MM`` for display.

    Storage stays ISO (``YYYY-MM-DD HH:MM:SS``) so SQLite date functions and
    sorting keep working; only the shown value is reformatted.
    """
    try:
        return datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        return created_at


def format_order_items(items: list[dict]) -> str:
    """Render stored order line items as an HTML list (names stay original)."""
    lines = []
    for item in items:
        subtotal = item["price"] * item["qty"]
        lines.append(
            f"• {item['name']} — €{item['price']:.2f} × {item['qty']} = €{subtotal:.2f}"
        )
    return "\n".join(lines)


def format_customer_contact(order: dict, lang: str) -> str:
    """Contact block for the admin: name, @username and a direct-message link.

    The ``tg://user?id=...`` link opens the customer's chat even when they have
    no public @username, so the admin can always message them in one tap.
    """
    lines = [f"👤 {order['customer_name']}"]
    if order.get("username"):
        # A public username — clickable link straight to the chat.
        username = order["username"]
        lines.append(f'🔗 <a href="https://t.me/{username}">@{username}</a>')
    lines.append(f"📞 {order['phone']}")
    lines.append(f'✍️ <a href="tg://user?id={order["user_id"]}">{t(lang, "admin_write_dm")}</a>')
    return "\n".join(lines)


def format_payment_line(order: dict, lang: str) -> str:
    """A localized payment line (empty when payments are not used)."""
    method = order.get("payment_method")
    if order.get("paid") or method == "online":
        return t(lang, "pay_label_online")
    if method == "cash":
        return t(lang, "pay_label_cash")
    return ""


def format_order_full(order: dict, lang: str) -> str:
    """Full order card used in admin messages and listings."""
    payment = format_payment_line(order, lang)
    payment_block = f"\n{payment}" if payment else ""
    comment = (order.get("comment") or "").strip()
    comment_block = (
        f"\n\n💬 <b>{t(lang, 'label_comment')}:</b> {html.escape(comment)}" if comment else ""
    )
    return (
        f"🧾 <b>{t(lang, 'admin_order')} №{order['id']}</b>\n"
        f"{t(lang, 'admin_status')}: {status_label(lang, order['status'])}\n"
        f"🕒 {human_dt(order['created_at'])}\n\n"
        f"{format_order_items(order['items'])}\n\n"
        f"<b>{t(lang, 'admin_sum')}: €{order['total']:.2f}</b>{payment_block}"
        f"{comment_block}\n\n"
        f"{format_customer_contact(order, lang)}"
    )


async def _admin_lang(user_id: int) -> str:
    """Preferred language of an admin (falls back to the default)."""
    return await get_user_language(user_id) or DEFAULT_LANG


async def notify_admins_new_order(bot: Bot, order: dict) -> None:
    """Send a new order to every staff member, each in their own language."""
    for admin_id in await list_staff_ids():
        lang = await _admin_lang(admin_id)
        text = t(lang, "admin_new_order") + "\n\n" + format_order_full(order, lang)
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=admin_order_kb(order["id"], lang),
            )
        except Exception as error:
            # An admin may not have started the bot yet — don't fail the order.
            logger.warning("Could not notify admin %s: %s", admin_id, error)


async def notify_staff_feedback(bot: Bot, from_user: User, text: str) -> None:
    """Deliver a customer's feedback message to every staff member."""
    for staff_id in await list_staff_ids():
        lang = await _admin_lang(staff_id)
        contact = f"👤 {from_user.full_name}"
        if from_user.username:
            contact += f'\n🔗 <a href="https://t.me/{from_user.username}">@{from_user.username}</a>'
        contact += f'\n✍️ <a href="tg://user?id={from_user.id}">{t(lang, "admin_write_dm")}</a>'
        body = (
            f"{t(lang, 'feedback_admin_header')}\n\n{contact}\n\n💬 {html.escape(text)}"
        )
        try:
            await bot.send_message(staff_id, body)
        except Exception as error:
            logger.warning("Could not deliver feedback to %s: %s", staff_id, error)
