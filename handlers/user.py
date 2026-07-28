"""Customer-facing handlers: language, menu browsing, cart and checkout.

Everything a normal user does lives on this router: /start, /language, /menu,
navigating the menu, editing the cart and walking through the FSM-driven
checkout. Every reply is localized with the user's chosen language.
"""

import html
import os
import re

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LabeledPrice, Message, PreCheckoutQuery

import cart as cart_service
import botcommands
import config
from callbacks import CartCB, LangCB, MenuCB, OrderCB, PayCB, ProductCB
from database import (
    create_order,
    get_order,
    get_user_language,
    set_user_language,
)
from keyboards import (
    categories_kb,
    catalog_footer_kb,
    cart_kb,
    checkout_actions_kb,
    language_kb,
    main_menu_kb,
    nav_reply_kb,
    phone_request_kb,
    product_card_kb,
    skip_comment_kb,
)
from locales import NAV_LABELS, DEFAULT_LANG, match_nav_action, normalize_lang, t
from menu import (
    CATEGORIES,
    STATUS_AVAILABLE,
    get_product,
    product_description,
    products_in,
)
from notifications import format_order_items, notify_admins_new_order, notify_staff_feedback
from states import Checkout, Feedback

router = Router(name="user")

# Rough phone sanity check: digits, spaces, +, -, () and a reasonable length.
_PHONE_RE = re.compile(r"^[+]?[\d\s()\-]{7,20}$")


async def resolve_lang(user_id: int) -> str:
    """Return the user's chosen language, or the default if none is stored."""
    return await get_user_language(user_id) or DEFAULT_LANG


# --------------------------------------------------------------------------- #
# Language selection
# --------------------------------------------------------------------------- #

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Greet the customer — or ask for a language on the very first contact."""
    await state.set_state(None)  # a fresh /start must not leave the user mid-checkout
    lang = await get_user_language(message.from_user.id)
    if lang is None:
        # First time we see this user: ask which language to use. Guess the
        # prompt language from their Telegram client settings.
        guess = normalize_lang(message.from_user.language_code)
        await message.answer(t(guess, "choose_language"), reply_markup=language_kb())
        return
    # The greeting also installs the persistent bottom navigation bar.
    await message.answer(t(lang, "greeting"), reply_markup=nav_reply_kb(lang))


@router.message(Command("language"))
async def cmd_language(message: Message) -> None:
    """Let the user change the interface language at any time."""
    lang = await resolve_lang(message.from_user.id)
    await message.answer(t(lang, "choose_language"), reply_markup=language_kb())


@router.callback_query(LangCB.filter())
async def set_language(callback: CallbackQuery, callback_data: LangCB, state: FSMContext) -> None:
    lang = callback_data.code
    await set_user_language(callback.from_user.id, lang)
    # Refresh this user's native command menu so it matches the new language.
    await botcommands.refresh_chat_commands(callback.bot, callback.from_user.id)

    await callback.message.edit_text(t(lang, "language_set"))
    # Re-send the greeting so the persistent bar picks up the new language.
    await callback.message.answer(t(lang, "greeting"), reply_markup=nav_reply_kb(lang))
    await callback.answer()


# --------------------------------------------------------------------------- #
# Persistent navigation bar (reply keyboard)
# --------------------------------------------------------------------------- #

@router.message(F.text.in_(set(NAV_LABELS)))
async def nav_buttons(message: Message, state: FSMContext) -> None:
    """Handle taps on the persistent bottom bar (Menu / Cart / Language).

    Registered before the checkout text handlers so a tap always navigates,
    even mid-checkout (which it then leaves, keeping the cart intact).
    """
    action = match_nav_action(message.text)
    lang = await resolve_lang(message.from_user.id)
    await state.set_state(None)

    if action == "menu":
        await message.answer(t(lang, "choose_category"), reply_markup=categories_kb(lang))
    elif action == "cart":
        cart = await cart_service.get_cart(state)
        await message.answer(
            cart_service.format_cart(cart, lang), reply_markup=cart_kb(cart, lang)
        )
    elif action == "language":
        await message.answer(t(lang, "choose_language"), reply_markup=language_kb())
    elif action == "feedback":
        await _start_feedback(message, state, lang)


# --------------------------------------------------------------------------- #
# Contact & feedback
# --------------------------------------------------------------------------- #

async def _start_feedback(message: Message, state: FSMContext, lang: str) -> None:
    """Show café contacts and start collecting a feedback message."""
    await state.set_state(Feedback.message)
    await message.answer(
        f"{t(lang, 'feedback_intro')}\n\n{t(lang, 'contact_info')}\n\n{t(lang, 'feedback_ask')}"
    )


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, state: FSMContext) -> None:
    lang = await resolve_lang(message.from_user.id)
    await _start_feedback(message, state, lang)


@router.message(Feedback.message, F.text)
async def receive_feedback(message: Message, state: FSMContext) -> None:
    """Deliver the customer's message to the staff and thank them."""
    lang = await resolve_lang(message.from_user.id)
    await notify_staff_feedback(message.bot, message.from_user, message.text.strip())
    await state.set_state(None)
    await message.answer(t(lang, "feedback_sent"), reply_markup=nav_reply_kb(lang))


# --------------------------------------------------------------------------- #
# Menu navigation
# --------------------------------------------------------------------------- #

@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Open the category list directly (also reachable from the Menu button)."""
    lang = await resolve_lang(message.from_user.id)
    await message.answer(
        f"{t(lang, 'choose_category')}", reply_markup=categories_kb(lang)
    )


@router.callback_query(MenuCB.filter(F.action == "main"))
async def show_main_menu(callback: CallbackQuery) -> None:
    lang = await resolve_lang(callback.from_user.id)
    await callback.message.edit_text(
        t(lang, "main_menu_title"), reply_markup=main_menu_kb(lang)
    )
    await callback.answer()


@router.callback_query(MenuCB.filter(F.action == "categories"))
async def show_categories(callback: CallbackQuery) -> None:
    lang = await resolve_lang(callback.from_user.id)
    await callback.message.edit_text(
        t(lang, "choose_category"), reply_markup=categories_kb(lang)
    )
    await callback.answer()


@router.callback_query(MenuCB.filter(F.action == "category"))
async def show_category(callback: CallbackQuery, callback_data: MenuCB, state: FSMContext) -> None:
    """Show every product of the category as a photo card, then a nav footer."""
    lang = await resolve_lang(callback.from_user.id)
    category = callback_data.value
    title = CATEGORIES.get(category, "Menu")
    cart = await cart_service.get_cart(state)

    # Turn the triggering message into the section header, then post the cards.
    await callback.message.edit_text(f"{title}\n\n{t(lang, 'category_hint')}")
    for product in products_in(category, for_customer=True):
        await _send_card(callback.message, product, cart.get(product.id, 0), lang)
    await callback.message.answer(t(lang, "catalog_more"), reply_markup=catalog_footer_kb(lang))
    await callback.answer()


# --------------------------------------------------------------------------- #
# Cart operations
# --------------------------------------------------------------------------- #

# Cache Telegram file_ids so re-opening a product doesn't re-upload the image.
_photo_cache: dict[str, str] = {}


def _product_caption(product, lang: str) -> str:
    return (
        f"<b>{product.name}</b>\n"
        f"{product_description(product.id, lang)}\n\n"
        f"💶 <b>€{product.price:.2f}</b>"
    )


async def _send_card(message: Message, product, qty: int, lang: str) -> None:
    """Post one product card (photo + caption + add controls) below ``message``."""
    caption = _product_caption(product, lang)
    keyboard = product_card_kb(product, qty, lang)
    if product.id in _photo_cache or os.path.exists(product.image_path):
        photo = _photo_cache.get(product.id) or FSInputFile(product.image_path)
        sent = await message.answer_photo(photo=photo, caption=caption, reply_markup=keyboard)
        if product.id not in _photo_cache and sent.photo:
            _photo_cache[product.id] = sent.photo[-1].file_id
    else:  # no image on disk — show a text card instead
        await message.answer(caption, reply_markup=keyboard)


@router.callback_query(ProductCB.filter(F.action.in_({"add", "inc", "dec"})))
async def product_quantity(callback: CallbackQuery, callback_data: ProductCB, state: FSMContext) -> None:
    """Adjust quantity from a product card and refresh its buttons in place."""
    lang = await resolve_lang(callback.from_user.id)
    product = get_product(callback_data.pid)
    if product is None:
        await callback.answer(t(lang, "item_unavailable"), show_alert=True)
        return

    # Block adding an item that is no longer available.
    if callback_data.action in ("add", "inc") and product.status != STATUS_AVAILABLE:
        await callback.answer(t(lang, "out_of_stock_note"), show_alert=True)
        return

    if callback_data.action == "dec":
        await cart_service.change_qty(state, product.id, -1)
    else:  # "add" or "inc" -> +1
        await cart_service.add_item(state, product.id)

    cart = await cart_service.get_cart(state)
    qty = cart.get(product.id, 0)
    await callback.message.edit_reply_markup(reply_markup=product_card_kb(product, qty, lang))
    await callback.answer(
        t(lang, "added_to_cart", name=product.name) if callback_data.action == "add" else None
    )


async def _render_cart(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Re-draw the cart message from the current state."""
    cart = await cart_service.get_cart(state)
    await callback.message.edit_text(
        cart_service.format_cart(cart, lang), reply_markup=cart_kb(cart, lang)
    )


@router.callback_query(CartCB.filter(F.action == "view"))
async def view_cart(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await resolve_lang(callback.from_user.id)
    await _render_cart(callback, state, lang)
    await callback.answer()


@router.callback_query(CartCB.filter(F.action == "inc"))
async def cart_increment(callback: CallbackQuery, callback_data: CartCB, state: FSMContext) -> None:
    lang = await resolve_lang(callback.from_user.id)
    await cart_service.change_qty(state, callback_data.pid, +1)
    await _render_cart(callback, state, lang)
    await callback.answer()


@router.callback_query(CartCB.filter(F.action == "dec"))
async def cart_decrement(callback: CallbackQuery, callback_data: CartCB, state: FSMContext) -> None:
    lang = await resolve_lang(callback.from_user.id)
    await cart_service.change_qty(state, callback_data.pid, -1)
    await _render_cart(callback, state, lang)
    await callback.answer()


@router.callback_query(CartCB.filter(F.action == "del"))
async def cart_delete(callback: CallbackQuery, callback_data: CartCB, state: FSMContext) -> None:
    lang = await resolve_lang(callback.from_user.id)
    await cart_service.remove_item(state, callback_data.pid)
    await _render_cart(callback, state, lang)
    await callback.answer(t(lang, "item_removed"))


@router.callback_query(CartCB.filter(F.action == "clear"))
async def cart_clear(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await resolve_lang(callback.from_user.id)
    await cart_service.clear_cart(state)
    await _render_cart(callback, state, lang)
    await callback.answer(t(lang, "cart_cleared"))


@router.callback_query(CartCB.filter(F.action == "noop"))
async def cart_noop(callback: CallbackQuery) -> None:
    # The read-only "item summary" button — just acknowledge the tap.
    await callback.answer()


# --------------------------------------------------------------------------- #
# Checkout (FSM)
# --------------------------------------------------------------------------- #

@router.callback_query(CartCB.filter(F.action == "checkout"))
async def start_checkout(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await resolve_lang(callback.from_user.id)
    cart = await cart_service.get_cart(state)
    if not cart:
        await callback.answer(t(lang, "cart_empty_alert"), show_alert=True)
        return

    # If Telegram already gives us a name, skip the "name" step.
    profile_name = (callback.from_user.full_name or "").strip()
    if profile_name:
        await state.update_data(customer_name=profile_name)
        await state.set_state(Checkout.phone)
        await callback.message.answer(
            t(lang, "ask_phone_named", name=profile_name),
            reply_markup=phone_request_kb(lang),
        )
    else:
        await state.set_state(Checkout.name)
        await callback.message.answer(t(lang, "ask_name"))
    await callback.answer()


@router.message(Checkout.name, F.text)
async def checkout_name(message: Message, state: FSMContext) -> None:
    lang = await resolve_lang(message.from_user.id)
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(t(lang, "name_too_short"))
        return
    await state.update_data(customer_name=name)
    await state.set_state(Checkout.phone)
    await message.answer(t(lang, "ask_phone"), reply_markup=phone_request_kb(lang))


@router.message(Checkout.phone, F.contact)
async def checkout_phone_contact(message: Message, state: FSMContext) -> None:
    """Phone received via the native 'share contact' button."""
    await _save_phone_and_ask_comment(message, state, message.contact.phone_number)


@router.message(Checkout.phone, F.text)
async def checkout_phone_text(message: Message, state: FSMContext) -> None:
    """Phone typed in manually."""
    lang = await resolve_lang(message.from_user.id)
    phone = message.text.strip()
    if not _PHONE_RE.match(phone):
        await message.answer(t(lang, "invalid_phone"))
        return
    await _save_phone_and_ask_comment(message, state, phone)


async def _save_phone_and_ask_comment(message: Message, state: FSMContext, phone: str) -> None:
    """Store the phone number and ask for an optional order comment."""
    lang = await resolve_lang(message.from_user.id)
    await state.update_data(phone=phone)
    await state.set_state(Checkout.comment)
    # Swap the "share contact" keyboard back for the persistent navigation bar,
    # then ask for the (optional) comment with a Skip button.
    await message.answer(t(lang, "checkout_almost_done"), reply_markup=nav_reply_kb(lang))
    await message.answer(t(lang, "ask_comment"), reply_markup=skip_comment_kb(lang))


@router.message(Checkout.comment, F.text)
async def checkout_comment(message: Message, state: FSMContext) -> None:
    """Store the typed comment and show the order summary."""
    lang = await resolve_lang(message.from_user.id)
    await state.update_data(comment=message.text.strip())
    await _show_summary(message, state, lang)


@router.callback_query(Checkout.comment, OrderCB.filter(F.action == "skip_comment"))
async def checkout_skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
    """Skip the comment and show the order summary."""
    lang = await resolve_lang(callback.from_user.id)
    await state.update_data(comment="")
    await _show_summary(callback.message, state, lang)
    await callback.answer()


async def _show_summary(message: Message, state: FSMContext, lang: str) -> None:
    """Render the order summary and wait for confirmation / payment."""
    data = await state.get_data()
    cart = data.get("cart", {})
    comment = (data.get("comment") or "").strip()
    comment_line = (
        f"\n💬 <b>{t(lang, 'label_comment')}:</b> {html.escape(comment)}" if comment else ""
    )
    summary = (
        f"{t(lang, 'summary_title')}\n\n"
        f"{cart_service.format_cart(cart, lang)}\n\n"
        f"👤 <b>{t(lang, 'summary_name')}:</b> {data['customer_name']}\n"
        f"📞 <b>{t(lang, 'summary_phone')}:</b> {data['phone']}{comment_line}\n\n"
        f"{t(lang, 'summary_confirm_q')}"
    )
    await state.set_state(Checkout.confirm)
    await message.answer(
        summary, reply_markup=checkout_actions_kb(lang, config.payments_enabled())
    )


async def _finalize_order(bot, user, state: FSMContext, *, paid: bool,
                          method: str | None, charge_id: str | None = None):
    """Freeze the cart into an order, notify admins and clear the FSM.

    Returns ``(order_id, items, total)`` or ``None`` if the cart was empty.
    """
    data = await state.get_data()
    cart = data.get("cart", {})
    if not cart:
        return None

    items = [
        {"id": product.id, "name": product.name, "price": product.price, "qty": qty}
        for product, qty, _ in cart_service.cart_lines(cart)
    ]
    total = cart_service.cart_total(cart)

    order_id = await create_order(
        user_id=user.id,
        username=user.username,
        customer_name=data["customer_name"],
        phone=data["phone"],
        items=items,
        total=total,
        paid=paid,
        payment_method=method,
        charge_id=charge_id,
        comment=(data.get("comment") or "").strip() or None,
    )
    order = await get_order(order_id)
    await notify_admins_new_order(bot, order)
    await state.clear()
    return order_id, items, total


async def _place_via_callback(callback: CallbackQuery, state: FSMContext, lang: str,
                              *, paid: bool, method: str | None) -> None:
    """Create an order from a summary button (cash / confirm) and reply."""
    result = await _finalize_order(callback.bot, callback.from_user, state, paid=paid, method=method)
    if result is None:  # safety net — cart emptied somewhere along the way
        await callback.answer(t(lang, "cart_empty_alert"), show_alert=True)
        await state.clear()
        return
    order_id, items, total = result
    # "paid" orders confirm the payment; others stay "being processed".
    key = "order_paid" if paid else "order_placed"
    await callback.message.edit_text(
        t(lang, key, id=order_id, items=format_order_items(items), total=total)
    )
    await callback.answer(t(lang, "order_placed_toast"))
    await callback.message.answer(t(lang, "order_again"), reply_markup=nav_reply_kb(lang))


@router.callback_query(Checkout.confirm, OrderCB.filter(F.action == "confirm"))
async def checkout_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Place the order when online payment is not configured."""
    lang = await resolve_lang(callback.from_user.id)
    await _place_via_callback(callback, state, lang, paid=False, method=None)


@router.callback_query(Checkout.confirm, PayCB.filter(F.method == "cash"))
async def pay_on_pickup(callback: CallbackQuery, state: FSMContext) -> None:
    """Place the order to be paid in cash on pickup."""
    lang = await resolve_lang(callback.from_user.id)
    await _place_via_callback(callback, state, lang, paid=False, method="cash")


@router.callback_query(Checkout.confirm, PayCB.filter(F.method == "online"))
async def pay_online(callback: CallbackQuery, state: FSMContext) -> None:
    """Send a Telegram Payments invoice; the order is created after payment."""
    lang = await resolve_lang(callback.from_user.id)
    cart = await cart_service.get_cart(state)
    if not cart:
        await callback.answer(t(lang, "cart_empty_alert"), show_alert=True)
        return

    # One invoice line per cart position; amounts are in minor units (cents).
    prices = [
        LabeledPrice(label=f"{product.name} × {qty}", amount=int(round(subtotal * 100)))
        for product, qty, subtotal in cart_service.cart_lines(cart)
    ]
    await callback.message.answer_invoice(
        title=t(lang, "invoice_title"),
        description=t(lang, "invoice_description"),
        payload=f"order:{callback.from_user.id}",
        provider_token=config.PAYMENT_PROVIDER_TOKEN,
        currency=config.PAYMENT_CURRENCY,
        prices=prices,
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    """Approve the payment (last chance to reject; we always accept here)."""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def got_payment(message: Message, state: FSMContext) -> None:
    """Payment confirmed by Telegram — create the order as paid."""
    lang = await resolve_lang(message.from_user.id)
    charge_id = message.successful_payment.provider_payment_charge_id
    result = await _finalize_order(
        message.bot, message.from_user, state, paid=True, method="online", charge_id=charge_id
    )
    if result is None:
        return
    order_id, items, total = result
    await message.answer(
        t(lang, "order_paid", id=order_id, items=format_order_items(items), total=total)
    )
    await message.answer(t(lang, "order_again"), reply_markup=nav_reply_kb(lang))


@router.callback_query(Checkout.confirm, OrderCB.filter(F.action == "cancel"))
async def checkout_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await resolve_lang(callback.from_user.id)
    # Leave the FSM but keep the cart so nothing the user picked is lost.
    await state.set_state(None)
    cart = await cart_service.get_cart(state)
    await callback.message.edit_text(
        t(lang, "order_cancelled"), reply_markup=cart_kb(cart, lang)
    )
    await callback.answer()
