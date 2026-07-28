"""Staff handlers: order management, listing, stats and staff control.

Three roles, from most to least powerful:
  * super admin  — the ``ADMIN_CHAT_ID`` from the environment; manages everyone,
                   can never be removed;
  * admin        — receives orders, accepts/rejects, and can add/remove admins
                   and moderators;
  * moderator    — receives orders and accepts/rejects only; cannot manage staff.

The ``IsStaff`` filter guards the whole router; management actions are further
gated by ``can_manage_staff``.
"""

import botcommands
from aiogram import F, Router
from aiogram.filters import BaseFilter, Command, CommandObject
from aiogram.types import CallbackQuery, Message

from callbacks import AdminCB, StaffCB
from config import ADMIN_CHAT_ID
from database import (
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_SUPER,
    STATUS_ACCEPTED,
    STATUS_NEW,
    STATUS_REJECTED,
    add_staff,
    can_manage_staff,
    get_order,
    get_recent_orders,
    get_today_stats,
    get_user_language,
    is_staff,
    list_staff,
    remove_staff,
    update_order_status,
    update_staff_identity,
)
from keyboards import staff_display_name, staff_panel_kb, staff_remove_kb
from locales import DEFAULT_LANG, role_label, status_label, t
from notifications import format_order_full, human_dt

router = Router(name="admin")


class IsStaff(BaseFilter):
    """Allow the update only if it comes from a staff member (any role)."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user is not None and await is_staff(event.from_user.id)


# Restrict the whole router to staff.
router.message.filter(IsStaff())
router.callback_query.filter(IsStaff())


async def _lang(user_id: int) -> str:
    return await get_user_language(user_id) or DEFAULT_LANG


async def _notify_user(bot, user_id: int, key: str) -> bool:
    """Send a localized notice to a user. Returns False if it couldn't be delivered."""
    try:
        await bot.send_message(user_id, t(await _lang(user_id), key))
        return True
    except Exception:
        return False


async def _fetch_identity(bot, user_id: int) -> tuple[str | None, str | None]:
    """Best-effort ``(full_name, username)`` for a user (needs prior interaction)."""
    try:
        chat = await bot.get_chat(user_id)
        return chat.full_name or None, chat.username
    except Exception:
        return None, None


async def _enrich_staff(bot, members: list[dict]) -> list[dict]:
    """Fill in missing usernames from Telegram (self-healing) and persist them.

    A member added by id has no username until they've interacted with the bot;
    once ``get_chat`` succeeds we cache the result so the list shows @username.
    """
    for member in members:
        if member.get("username"):
            continue
        name, username = await _fetch_identity(bot, member["user_id"])
        if username or name:
            member["username"] = username
            member["name"] = member.get("name") or name
            if member["role"] != ROLE_SUPER:  # super admin isn't stored in the table
                await update_staff_identity(member["user_id"], name, username)
    return members


# --------------------------------------------------------------------------- #
# Order listing & statistics (all staff)
# --------------------------------------------------------------------------- #

@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Show the 10 most recent orders with their statuses."""
    lang = await _lang(message.from_user.id)
    orders = await get_recent_orders(limit=10)
    if not orders:
        await message.answer(t(lang, "admin_no_orders"))
        return

    lines = [t(lang, "admin_recent_title") + "\n"]
    for order in orders:
        lines.append(
            f"№{order['id']} · {status_label(lang, order['status'])} · €{order['total']:.2f}\n"
            f"    👤 {order['customer_name']} · 🕒 {human_dt(order['created_at'])}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Show today's order count and revenue."""
    lang = await _lang(message.from_user.id)
    stats = await get_today_stats()
    await message.answer(
        f"{t(lang, 'stats_title')}\n\n"
        f"{t(lang, 'stats_orders')}: <b>{stats['orders_today']}</b>\n"
        f"{t(lang, 'stats_revenue')}: <b>€{stats['revenue_today']:.2f}</b>"
    )


# --------------------------------------------------------------------------- #
# Accept / reject an order (all staff)
# --------------------------------------------------------------------------- #

@router.callback_query(AdminCB.filter(F.action.in_({"accept", "reject"})))
async def handle_decision(callback: CallbackQuery, callback_data: AdminCB) -> None:
    admin_lang = await _lang(callback.from_user.id)
    order = await get_order(callback_data.order_id)
    if order is None:
        await callback.answer(t(admin_lang, "order_not_found"), show_alert=True)
        return

    if order["status"] != STATUS_NEW:  # avoid processing the same order twice
        await callback.answer(
            t(admin_lang, "order_already_handled",
              status=status_label(admin_lang, order["status"])),
            show_alert=True,
        )
        return

    new_status = STATUS_ACCEPTED if callback_data.action == "accept" else STATUS_REJECTED
    await update_order_status(order["id"], new_status)
    order["status"] = new_status

    await callback.message.edit_text(format_order_full(order, admin_lang))

    # Notify the customer in *their* language.
    customer_lang = await _lang(order["user_id"])
    key = "status_accepted" if new_status == STATUS_ACCEPTED else "status_rejected"
    try:
        await callback.bot.send_message(order["user_id"], t(customer_lang, key, id=order["id"]))
    except Exception:
        pass

    await callback.answer(t(admin_lang, "decision_done"))


# --------------------------------------------------------------------------- #
# Staff panel: view (all staff), add (managers), remove via picker (managers)
# --------------------------------------------------------------------------- #

async def _staff_panel_text(bot, lang: str, can_manage: bool) -> str:
    """The staff list, plus an add hint for managers."""
    members = await _enrich_staff(bot, await list_staff())
    lines = [t(lang, "staff_title")]
    for member in members:
        lines.append(f"• {staff_display_name(member)} — <b>{role_label(lang, member['role'])}</b>")
    text = "\n".join(lines)
    if can_manage:
        text += "\n" + t(lang, "staff_add_hint")
    return text


@router.message(Command("staff", "admins"))
async def cmd_staff(message: Message) -> None:
    """Show the staff list with roles (and a remove button for managers)."""
    lang = await _lang(message.from_user.id)
    can_manage = await can_manage_staff(message.from_user.id)
    await message.answer(
        await _staff_panel_text(message.bot, lang, can_manage),
        reply_markup=staff_panel_kb(lang, can_manage),
    )


async def _add_member(message: Message, command: CommandObject, role: str, usage_key: str) -> None:
    """Shared logic for /addadmin and /addmod."""
    lang = await _lang(message.from_user.id)
    if not await can_manage_staff(message.from_user.id):
        await message.answer(t(lang, "no_permission"))
        return

    target = _parse_id(command.args)
    if target is None:
        await message.answer(t(lang, usage_key) if not command.args else t(lang, "invalid_id"))
        return

    name, username = await _fetch_identity(message.bot, target)
    if await add_staff(target, role, name, username):
        try:
            await botcommands.refresh_chat_commands(message.bot, target)
        except Exception:
            pass
        promo_key = "promoted_admin" if role == ROLE_ADMIN else "promoted_moderator"
        delivered = await _notify_user(message.bot, target, promo_key)
        display = staff_display_name({"user_id": target, "name": name, "username": username})
        reply = t(lang, "staff_added", name=display, role=role_label(lang, role))
        if not delivered:
            reply += t(lang, "notify_undeliverable")
        await message.answer(reply)
    else:
        await message.answer(t(lang, "already_admin"))


@router.message(Command("addadmin"))
async def cmd_addadmin(message: Message, command: CommandObject) -> None:
    """Add an administrator by numeric Telegram ID (managers only)."""
    await _add_member(message, command, ROLE_ADMIN, "addadmin_usage")


@router.message(Command("addmod"))
async def cmd_addmod(message: Message, command: CommandObject) -> None:
    """Add a moderator by numeric Telegram ID (managers only)."""
    await _add_member(message, command, ROLE_MODERATOR, "addmod_usage")


@router.callback_query(StaffCB.filter(F.action == "remove_menu"))
async def staff_remove_menu(callback: CallbackQuery) -> None:
    """Show the picker of removable staff (everyone except the super admin)."""
    lang = await _lang(callback.from_user.id)
    if not await can_manage_staff(callback.from_user.id):
        await callback.answer(t(lang, "no_permission"), show_alert=True)
        return

    removable = [m for m in await list_staff() if m["role"] != ROLE_SUPER]
    if not removable:
        await callback.answer(t(lang, "nobody_to_remove"), show_alert=True)
        return

    removable = await _enrich_staff(callback.bot, removable)
    await callback.message.edit_text(
        t(lang, "choose_remove"), reply_markup=staff_remove_kb(removable, lang)
    )
    await callback.answer()


@router.callback_query(StaffCB.filter(F.action == "remove"))
async def staff_remove(callback: CallbackQuery, callback_data: StaffCB) -> None:
    """Remove the picked staff member and notify them."""
    lang = await _lang(callback.from_user.id)
    if not await can_manage_staff(callback.from_user.id):
        await callback.answer(t(lang, "no_permission"), show_alert=True)
        return

    target = callback_data.uid
    if target == ADMIN_CHAT_ID:
        await callback.answer(t(lang, "cannot_remove_super"), show_alert=True)
        return

    # Grab a friendly label before deleting, for the confirmation message.
    member = next((m for m in await list_staff() if m["user_id"] == target), None)
    name = staff_display_name(member) if member else str(target)

    if await remove_staff(target):
        try:
            await botcommands.refresh_chat_commands(callback.bot, target)
        except Exception:
            pass
        await _notify_user(callback.bot, target, "demoted_notice")
        panel = await _staff_panel_text(callback.bot, lang, can_manage=True)
        await callback.message.edit_text(
            f"{t(lang, 'staff_removed', name=name)}\n\n{panel}",
            reply_markup=staff_panel_kb(lang, can_manage=True),
        )
        await callback.answer(t(lang, "decision_done"))
    else:
        await callback.answer(t(lang, "not_an_admin"), show_alert=True)


@router.callback_query(StaffCB.filter(F.action == "back"))
async def staff_back(callback: CallbackQuery) -> None:
    """Return from the removal picker to the staff panel."""
    lang = await _lang(callback.from_user.id)
    can_manage = await can_manage_staff(callback.from_user.id)
    await callback.message.edit_text(
        await _staff_panel_text(callback.bot, lang, can_manage),
        reply_markup=staff_panel_kb(lang, can_manage),
    )
    await callback.answer()


def _parse_id(raw: str | None) -> int | None:
    """Parse a numeric Telegram id from a command argument."""
    if not raw:
        return None
    raw = raw.strip()
    return int(raw) if raw.lstrip("-").isdigit() else None
