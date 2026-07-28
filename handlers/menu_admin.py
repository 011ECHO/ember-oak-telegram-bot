"""In-bot menu editor (managers only).

Lets admins and the super admin add products, change prices, mark items out of
stock, hide them, or delete them — all from Telegram, no code changes. Products
are persisted in the database (see menu.py); the cache is refreshed after each
edit so customers see the change immediately.
"""

import html

import menu
from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from callbacks import MenuAdminCB
from database import can_manage_staff, get_user_language
from keyboards import (
    add_skip_description_kb,
    editmenu_categories_kb,
    editmenu_products_kb,
    product_admin_kb,
    product_delete_confirm_kb,
)
from locales import DEFAULT_LANG, prod_status_label, t
from states import MenuAdd, MenuEditPrice

router = Router(name="menu_admin")


class IsManager(BaseFilter):
    """Only the super admin and admins may edit the menu (not moderators)."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user is not None and await can_manage_staff(event.from_user.id)


router.message.filter(IsManager())
router.callback_query.filter(IsManager())


async def _lang(user_id: int) -> str:
    return await get_user_language(user_id) or DEFAULT_LANG


def _card_text(product: menu.Product, lang: str) -> str:
    return t(
        lang, "editmenu_prod_card",
        emoji=product.emoji,
        name=html.escape(product.name),
        desc=html.escape(menu.product_description(product.id, lang)),
        price=product.price,
        status=prod_status_label(lang, product.status),
    )


# --- navigation -------------------------------------------------------------

@router.message(Command("editmenu"))
async def cmd_editmenu(message: Message) -> None:
    lang = await _lang(message.from_user.id)
    await message.answer(t(lang, "editmenu_title"), reply_markup=editmenu_categories_kb(lang))


@router.callback_query(MenuAdminCB.filter(F.action == "cats"))
async def show_categories(callback: CallbackQuery) -> None:
    lang = await _lang(callback.from_user.id)
    await callback.message.edit_text(t(lang, "editmenu_title"), reply_markup=editmenu_categories_kb(lang))
    await callback.answer()


@router.callback_query(MenuAdminCB.filter(F.action == "cat"))
async def show_products(callback: CallbackQuery, callback_data: MenuAdminCB) -> None:
    lang = await _lang(callback.from_user.id)
    await callback.message.edit_text(
        t(lang, "editmenu_pick_product"),
        reply_markup=editmenu_products_kb(callback_data.pid, lang),
    )
    await callback.answer()


@router.callback_query(MenuAdminCB.filter(F.action == "prod"))
async def show_product(callback: CallbackQuery, callback_data: MenuAdminCB) -> None:
    lang = await _lang(callback.from_user.id)
    product = menu.get_product(callback_data.pid)
    if product is None:
        await callback.answer(t(lang, "product_gone"), show_alert=True)
        return
    await callback.message.edit_text(_card_text(product, lang), reply_markup=product_admin_kb(product, lang))
    await callback.answer()


# --- change status ----------------------------------------------------------

@router.callback_query(MenuAdminCB.filter(F.action == "status"))
async def change_status(callback: CallbackQuery, callback_data: MenuAdminCB) -> None:
    lang = await _lang(callback.from_user.id)
    if menu.get_product(callback_data.pid) is None:
        await callback.answer(t(lang, "product_gone"), show_alert=True)
        return
    await menu.set_status(callback_data.pid, callback_data.extra)
    product = menu.get_product(callback_data.pid)
    await callback.message.edit_text(_card_text(product, lang), reply_markup=product_admin_kb(product, lang))
    await callback.answer(t(lang, "status_updated", status=prod_status_label(lang, product.status)))


# --- delete -----------------------------------------------------------------

@router.callback_query(MenuAdminCB.filter(F.action == "del"))
async def delete_prompt(callback: CallbackQuery, callback_data: MenuAdminCB) -> None:
    lang = await _lang(callback.from_user.id)
    product = menu.get_product(callback_data.pid)
    if product is None:
        await callback.answer(t(lang, "product_gone"), show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=product_delete_confirm_kb(product, lang))
    await callback.answer()


@router.callback_query(MenuAdminCB.filter(F.action == "delok"))
async def delete_confirm(callback: CallbackQuery, callback_data: MenuAdminCB) -> None:
    lang = await _lang(callback.from_user.id)
    product = menu.get_product(callback_data.pid)
    category = product.category if product else next(iter(menu.CATEGORIES))
    await menu.remove_product(callback_data.pid)
    await callback.message.edit_text(
        t(lang, "editmenu_pick_product"), reply_markup=editmenu_products_kb(category, lang)
    )
    await callback.answer(t(lang, "product_deleted"))


# --- change price -----------------------------------------------------------

@router.callback_query(MenuAdminCB.filter(F.action == "price"))
async def price_prompt(callback: CallbackQuery, callback_data: MenuAdminCB, state: FSMContext) -> None:
    lang = await _lang(callback.from_user.id)
    if menu.get_product(callback_data.pid) is None:
        await callback.answer(t(lang, "product_gone"), show_alert=True)
        return
    await state.set_state(MenuEditPrice.value)
    await state.update_data(pid=callback_data.pid)
    await callback.message.answer(t(lang, "add_ask_price"))
    await callback.answer()


@router.message(MenuEditPrice.value, F.text)
async def price_received(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    price = _parse_price(message.text)
    if price is None:
        await message.answer(t(lang, "add_invalid_price"))
        return
    data = await state.get_data()
    product = menu.get_product(data["pid"])
    if product is None:
        await state.clear()
        await message.answer(t(lang, "product_gone"))
        return
    await menu.set_price(product.id, price)
    await state.clear()
    updated = menu.get_product(product.id)
    await message.answer(t(lang, "price_updated", name=updated.name, price=updated.price))
    await message.answer(_card_text(updated, lang), reply_markup=product_admin_kb(updated, lang))


# --- add a product (FSM) ----------------------------------------------------

@router.callback_query(MenuAdminCB.filter(F.action == "add"))
async def add_start(callback: CallbackQuery, callback_data: MenuAdminCB, state: FSMContext) -> None:
    lang = await _lang(callback.from_user.id)
    await state.set_state(MenuAdd.name)
    await state.update_data(category=callback_data.pid)
    await callback.message.answer(t(lang, "add_ask_name"))
    await callback.answer()


@router.message(MenuAdd.name, F.text)
async def add_name(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    await state.update_data(name=message.text.strip()[:60])
    await state.set_state(MenuAdd.price)
    await message.answer(t(lang, "add_ask_price"))


@router.message(MenuAdd.price, F.text)
async def add_price(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    price = _parse_price(message.text)
    if price is None:
        await message.answer(t(lang, "add_invalid_price"))
        return
    await state.update_data(price=price)
    await state.set_state(MenuAdd.emoji)
    await message.answer(t(lang, "add_ask_emoji"))


@router.message(MenuAdd.emoji, F.text)
async def add_emoji(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    await state.update_data(emoji=message.text.strip()[:8] or "🍽")
    await state.set_state(MenuAdd.description)
    await message.answer(t(lang, "add_ask_description"), reply_markup=add_skip_description_kb(lang))


@router.message(MenuAdd.description, F.text)
async def add_description(message: Message, state: FSMContext) -> None:
    await _finish_add(message, state, message.text.strip())


@router.callback_query(MenuAdd.description, MenuAdminCB.filter(F.action == "skipdesc"))
async def add_skip_description(callback: CallbackQuery, state: FSMContext) -> None:
    await _finish_add(callback.message, state, "", user_id=callback.from_user.id)
    await callback.answer()


async def _finish_add(message: Message, state: FSMContext, description: str, user_id: int | None = None) -> None:
    lang = await _lang(user_id or message.chat.id)
    data = await state.get_data()
    await state.clear()
    product = await menu.add_product(
        name=data["name"], price=data["price"], category=data["category"],
        emoji=data["emoji"], description_text=description,
    )
    await message.answer(t(lang, "product_added", name=product.name, price=product.price))
    await message.answer(
        t(lang, "editmenu_pick_product"),
        reply_markup=editmenu_products_kb(data["category"], lang),
    )


# --- helpers ----------------------------------------------------------------

def _parse_price(raw: str) -> float | None:
    try:
        value = float(raw.strip().replace(",", ".").replace("€", ""))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None
