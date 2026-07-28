"""Localization (i18n) for Russian, English and Spanish.

Every user-facing string lives here, keyed first by message name and then by
language code. Product and category names are intentionally kept in English
(they are proper menu items), only the interface chrome is translated.
"""

# Supported languages: code -> button label.
LANGUAGES: dict[str, str] = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "es": "🇪🇸 Español",
}

DEFAULT_LANG = "en"


def normalize_lang(code: str | None) -> str:
    """Map a raw Telegram ``language_code`` to one we support."""
    if code:
        short = code.split("-")[0].lower()
        if short in LANGUAGES:
            return short
    return DEFAULT_LANG


# message key -> {lang: text}. Use {placeholders} for runtime values.
TEXTS: dict[str, dict[str, str]] = {
    # --- language selection ---
    "choose_language": {
        "ru": "🌍 Выберите язык:",
        "en": "🌍 Choose your language:",
        "es": "🌍 Elige tu idioma:",
    },
    "language_set": {
        "ru": "Язык переключён на русский ✅",
        "en": "Language set to English ✅",
        "es": "Idioma cambiado a español ✅",
    },
    # --- greeting / main menu ---
    "greeting": {
        "ru": "👋 Добро пожаловать в <b>Ember & Oak</b>!\n\n"
              "Соберите заказ из нашего меню и оформите его за пару минут.\n"
              "Нажмите «Меню», чтобы начать. ☕",
        "en": "👋 Welcome to <b>Ember & Oak</b>!\n\n"
              "Build your order from our menu and place it in a couple of minutes.\n"
              "Tap “Menu” to start. ☕",
        "es": "👋 ¡Bienvenido a <b>Ember & Oak</b>!\n\n"
              "Arma tu pedido con nuestro menú y complétalo en un par de minutos.\n"
              "Pulsa «Menú» para empezar. ☕",
    },
    "main_menu_title": {
        "ru": "🏠 <b>Ember & Oak</b> — главное меню",
        "en": "🏠 <b>Ember & Oak</b> — main menu",
        "es": "🏠 <b>Ember & Oak</b> — menú principal",
    },
    "order_again": {
        "ru": "Хотите заказать что-нибудь ещё? ☕",
        "en": "Would you like to order something else? ☕",
        "es": "¿Quieres pedir algo más? ☕",
    },
    # --- buttons ---
    "btn_menu": {"ru": "🍽 Меню", "en": "🍽 Menu", "es": "🍽 Menú"},
    "btn_cart": {"ru": "🛒 Корзина", "en": "🛒 Cart", "es": "🛒 Carrito"},
    # Persistent reply-keyboard buttons (the bar above the input field).
    "rk_language": {"ru": "🌐 Язык", "en": "🌐 Language", "es": "🌐 Idioma"},
    "nav_placeholder": {
        "ru": "Выберите действие…",
        "en": "Choose an action…",
        "es": "Elige una acción…",
    },
    "btn_back": {"ru": "⬅️ Назад", "en": "⬅️ Back", "es": "⬅️ Atrás"},
    "btn_categories": {"ru": "⬅️ Категории", "en": "⬅️ Categories", "es": "⬅️ Categorías"},
    "btn_to_menu": {"ru": "⬅️ В меню", "en": "⬅️ To menu", "es": "⬅️ Al menú"},
    "btn_checkout": {"ru": "✅ Оформить заказ", "en": "✅ Checkout", "es": "✅ Confirmar pedido"},
    "btn_clear": {"ru": "🗑 Очистить корзину", "en": "🗑 Clear cart", "es": "🗑 Vaciar carrito"},
    "btn_confirm": {"ru": "✅ Подтвердить заказ", "en": "✅ Confirm order", "es": "✅ Confirmar pedido"},
    "btn_cancel": {"ru": "✖️ Отменить", "en": "✖️ Cancel", "es": "✖️ Cancelar"},
    "btn_add_to_cart": {
        "ru": "➕ В корзину",
        "en": "➕ Add to cart",
        "es": "➕ Al carrito",
    },
    "btn_feedback": {
        "ru": "💬 Связь",
        "en": "💬 Contact",
        "es": "💬 Contacto",
    },
    "btn_skip": {
        "ru": "⏭ Пропустить",
        "en": "⏭ Skip",
        "es": "⏭ Omitir",
    },
    "btn_share_contact": {
        "ru": "📱 Поделиться контактом",
        "en": "📱 Share contact",
        "es": "📱 Compartir contacto",
    },
    # --- menu navigation ---
    "choose_category": {
        "ru": "🍽 <b>Выберите категорию:</b>",
        "en": "🍽 <b>Choose a category:</b>",
        "es": "🍽 <b>Elige una categoría:</b>",
    },
    "category_hint": {
        "ru": "Выберите позицию, чтобы добавить её в корзину:",
        "en": "Tap an item to add it to your cart:",
        "es": "Pulsa un producto para añadirlo al carrito:",
    },
    "added_to_cart": {
        "ru": "✅ {name} добавлен в корзину",
        "en": "✅ {name} added to cart",
        "es": "✅ {name} añadido al carrito",
    },
    "catalog_more": {
        "ru": "⬇️ Другие категории или перейти в корзину:",
        "en": "⬇️ Other categories or go to cart:",
        "es": "⬇️ Otras categorías o ir al carrito:",
    },
    "item_unavailable": {
        "ru": "Позиция недоступна",
        "en": "Item unavailable",
        "es": "Producto no disponible",
    },
    # --- cart ---
    "cart_empty": {
        "ru": "🛒 <b>Ваша корзина пуста.</b>\n\nЗагляните в меню, чтобы что-нибудь выбрать.",
        "en": "🛒 <b>Your cart is empty.</b>\n\nOpen the menu to pick something.",
        "es": "🛒 <b>Tu carrito está vacío.</b>\n\nAbre el menú para elegir algo.",
    },
    "cart_title": {
        "ru": "🛒 <b>Ваша корзина</b>",
        "en": "🛒 <b>Your cart</b>",
        "es": "🛒 <b>Tu carrito</b>",
    },
    "cart_total": {"ru": "Итого", "en": "Total", "es": "Total"},
    "cart_cleared": {"ru": "Корзина очищена", "en": "Cart cleared", "es": "Carrito vaciado"},
    "item_removed": {"ru": "Позиция удалена", "en": "Item removed", "es": "Producto eliminado"},
    "cart_empty_alert": {
        "ru": "Корзина пуста — сначала добавьте позиции",
        "en": "Cart is empty — add items first",
        "es": "El carrito está vacío — añade productos primero",
    },
    # --- checkout ---
    "ask_name": {
        "ru": "Как вас зовут? ✍️",
        "en": "What's your name? ✍️",
        "es": "¿Cómo te llamas? ✍️",
    },
    "name_too_short": {
        "ru": "Пожалуйста, введите корректное имя.",
        "en": "Please enter a valid name.",
        "es": "Por favor, introduce un nombre válido.",
    },
    "ask_phone_named": {
        "ru": "Отлично, {name}! 📞\nПоделитесь номером телефона кнопкой ниже или введите его вручную.",
        "en": "Great, {name}! 📞\nShare your phone number with the button below or type it in.",
        "es": "¡Genial, {name}! 📞\nComparte tu número con el botón de abajo o escríbelo.",
    },
    "ask_phone": {
        "ru": "Спасибо! 📞 Теперь поделитесь номером телефона кнопкой ниже или введите его вручную.",
        "en": "Thanks! 📞 Now share your phone number with the button below or type it in.",
        "es": "¡Gracias! 📞 Ahora comparte tu número con el botón de abajo o escríbelo.",
    },
    "phone_placeholder": {
        "ru": "Отправьте контакт или введите номер",
        "en": "Share contact or type the number",
        "es": "Comparte contacto o escribe el número",
    },
    "invalid_phone": {
        "ru": "Хм, это не похоже на номер телефона. Попробуйте ещё раз или нажмите «Поделиться контактом».",
        "en": "Hmm, that doesn't look like a phone number. Try again or tap “Share contact”.",
        "es": "Mmm, eso no parece un número. Inténtalo de nuevo o pulsa «Compartir contacto».",
    },
    "building_order": {
        "ru": "Собираю ваш заказ… 🧾",
        "en": "Building your order… 🧾",
        "es": "Preparando tu pedido… 🧾",
    },
    "summary_title": {
        "ru": "🧾 <b>Проверьте заказ</b>",
        "en": "🧾 <b>Check your order</b>",
        "es": "🧾 <b>Revisa tu pedido</b>",
    },
    "summary_name": {"ru": "Имя", "en": "Name", "es": "Nombre"},
    "summary_phone": {"ru": "Телефон", "en": "Phone", "es": "Teléfono"},
    "summary_confirm_q": {
        "ru": "Всё верно?",
        "en": "Is everything correct?",
        "es": "¿Está todo correcto?",
    },
    # --- order result (processing, NOT accepted yet) ---
    "order_placed": {
        "ru": "🧾 <b>Заказ №{id} оформлен!</b>\n\n{items}\n\n<b>Сумма: €{total:.2f}</b>\n\n"
              "⏳ Заказ передан на обработку — ожидайте подтверждения от кофейни.",
        "en": "🧾 <b>Order #{id} placed!</b>\n\n{items}\n\n<b>Total: €{total:.2f}</b>\n\n"
              "⏳ Your order is being processed — please wait for the café to confirm it.",
        "es": "🧾 <b>¡Pedido #{id} realizado!</b>\n\n{items}\n\n<b>Total: €{total:.2f}</b>\n\n"
              "⏳ Tu pedido está en proceso — espera la confirmación de la cafetería.",
    },
    "order_placed_toast": {
        "ru": "Заказ оформлен!",
        "en": "Order placed!",
        "es": "¡Pedido realizado!",
    },
    "order_paid": {
        "ru": "✅ <b>Оплата получена. Заказ №{id} оформлен!</b>\n\n{items}\n\n"
              "<b>Оплачено: €{total:.2f}</b>\n\n"
              "⏳ Заказ передан на обработку — ожидайте подтверждения от кофейни.",
        "en": "✅ <b>Payment received. Order #{id} placed!</b>\n\n{items}\n\n"
              "<b>Paid: €{total:.2f}</b>\n\n"
              "⏳ Your order is being processed — please wait for the café to confirm it.",
        "es": "✅ <b>Pago recibido. ¡Pedido #{id} realizado!</b>\n\n{items}\n\n"
              "<b>Pagado: €{total:.2f}</b>\n\n"
              "⏳ Tu pedido está en proceso — espera la confirmación de la cafetería.",
    },
    # --- payment ---
    "btn_pay_online": {
        "ru": "💳 Оплатить онлайн",
        "en": "💳 Pay online",
        "es": "💳 Pagar online",
    },
    "btn_pay_cash": {
        "ru": "💵 Оплата при получении",
        "en": "💵 Pay on pickup",
        "es": "💵 Pagar al recoger",
    },
    "invoice_title": {
        "ru": "Ember & Oak — заказ",
        "en": "Ember & Oak — order",
        "es": "Ember & Oak — pedido",
    },
    "invoice_description": {
        "ru": "Оплата вашего заказа в кофейне Ember & Oak.",
        "en": "Payment for your Ember & Oak order.",
        "es": "Pago de tu pedido en Ember & Oak.",
    },
    "pay_label_online": {
        "ru": "💳 Оплачено онлайн",
        "en": "💳 Paid online",
        "es": "💳 Pagado online",
    },
    "pay_label_cash": {
        "ru": "💵 Оплата при получении",
        "en": "💵 Pay on pickup",
        "es": "💵 Pagar al recoger",
    },
    "order_cancelled": {
        "ru": "Оформление отменено. Ваша корзина сохранена.",
        "en": "Checkout cancelled. Your cart is saved.",
        "es": "Pedido cancelado. Tu carrito se ha guardado.",
    },
    # --- order comment ---
    "ask_comment": {
        "ru": "💬 Добавьте комментарий к заказу (пожелания, аллергии и т.п.) "
              "или нажмите «Пропустить».",
        "en": "💬 Add a note to your order (preferences, allergies, etc.) "
              "or tap “Skip”.",
        "es": "💬 Añade una nota a tu pedido (preferencias, alergias, etc.) "
              "o pulsa «Omitir».",
    },
    "checkout_almost_done": {
        "ru": "Отлично, почти готово! 🧾",
        "en": "Great, almost done! 🧾",
        "es": "¡Genial, casi listo! 🧾",
    },
    "label_comment": {"ru": "Комментарий", "en": "Note", "es": "Nota"},
    # --- contact & feedback ---
    "contact_info": {
        "ru": "📍 Barcelona, Carrer de l'Exemple 12\n📞 +34 600 000 000\n🕐 Пн–Вс, 8:00–20:00",
        "en": "📍 Barcelona, Carrer de l'Exemple 12\n📞 +34 600 000 000\n🕐 Mon–Sun, 8:00–20:00",
        "es": "📍 Barcelona, Carrer de l'Exemple 12\n📞 +34 600 000 000\n🕐 Lun–Dom, 8:00–20:00",
    },
    "feedback_intro": {
        "ru": "📞 <b>Связь с Ember & Oak</b>",
        "en": "📞 <b>Contact Ember & Oak</b>",
        "es": "📞 <b>Contacto con Ember & Oak</b>",
    },
    "feedback_ask": {
        "ru": "Напишите сообщение ниже — мы передадим его команде. "
              "Чтобы выйти, нажмите «Меню».",
        "en": "Write your message below — we'll pass it to the team. "
              "Tap “Menu” to exit.",
        "es": "Escribe tu mensaje abajo — se lo pasaremos al equipo. "
              "Pulsa «Menú» para salir.",
    },
    "feedback_sent": {
        "ru": "✅ Спасибо! Ваше сообщение отправлено команде.",
        "en": "✅ Thank you! Your message has been sent to the team.",
        "es": "✅ ¡Gracias! Tu mensaje se ha enviado al equipo.",
    },
    "feedback_admin_header": {
        "ru": "💬 <b>Новое сообщение от клиента</b>",
        "en": "💬 <b>New message from a customer</b>",
        "es": "💬 <b>Nuevo mensaje de un cliente</b>",
    },
    # --- status updates sent to the customer ---
    "status_accepted": {
        "ru": "✅ Ваш заказ №{id} принят!\nМы уже готовим его и свяжемся с вами по времени готовности. ☕",
        "en": "✅ Your order #{id} has been accepted!\nWe're preparing it and will contact you about the pickup time. ☕",
        "es": "✅ ¡Tu pedido #{id} ha sido aceptado!\nLo estamos preparando y te contactaremos sobre la hora de recogida. ☕",
    },
    "status_rejected": {
        "ru": "❌ К сожалению, ваш заказ №{id} отклонён.\nСвяжитесь с нами, если остались вопросы.",
        "en": "❌ Unfortunately, your order #{id} was rejected.\nContact us if you have any questions.",
        "es": "❌ Lamentablemente, tu pedido #{id} fue rechazado.\nContáctanos si tienes dudas.",
    },
    # --- order status labels ---
    "status_new": {"ru": "🆕 Обрабатывается", "en": "🆕 Processing", "es": "🆕 En proceso"},
    "status_accepted_label": {"ru": "✅ Принят", "en": "✅ Accepted", "es": "✅ Aceptado"},
    "status_rejected_label": {"ru": "❌ Отклонён", "en": "❌ Rejected", "es": "❌ Rechazado"},
    # --- admin: order card ---
    "admin_new_order": {
        "ru": "🔔 <b>Новый заказ!</b>",
        "en": "🔔 <b>New order!</b>",
        "es": "🔔 <b>¡Nuevo pedido!</b>",
    },
    "admin_order": {"ru": "Заказ", "en": "Order", "es": "Pedido"},
    "admin_status": {"ru": "Статус", "en": "Status", "es": "Estado"},
    "admin_sum": {"ru": "Сумма", "en": "Total", "es": "Total"},
    "admin_write_dm": {
        "ru": "✍️ Написать клиенту в ЛС",
        "en": "✍️ Message the customer",
        "es": "✍️ Escribir al cliente",
    },
    "btn_accept": {"ru": "✅ Принять", "en": "✅ Accept", "es": "✅ Aceptar"},
    "btn_reject": {"ru": "❌ Отклонить", "en": "❌ Reject", "es": "❌ Rechazar"},
    # --- admin: commands ---
    "admin_recent_title": {
        "ru": "📋 <b>Последние заказы</b>",
        "en": "📋 <b>Recent orders</b>",
        "es": "📋 <b>Pedidos recientes</b>",
    },
    "admin_no_orders": {
        "ru": "Заказов пока нет.",
        "en": "No orders yet.",
        "es": "Aún no hay pedidos.",
    },
    "stats_title": {
        "ru": "📊 <b>Статистика за сегодня</b>",
        "en": "📊 <b>Today's statistics</b>",
        "es": "📊 <b>Estadísticas de hoy</b>",
    },
    "stats_orders": {"ru": "Заказов", "en": "Orders", "es": "Pedidos"},
    "stats_revenue": {
        "ru": "Выручка (принятые заказы)",
        "en": "Revenue (accepted orders)",
        "es": "Ingresos (pedidos aceptados)",
    },
    "decision_done": {"ru": "Готово", "en": "Done", "es": "Hecho"},
    "order_not_found": {
        "ru": "Заказ не найден",
        "en": "Order not found",
        "es": "Pedido no encontrado",
    },
    "order_already_handled": {
        "ru": "Заказ уже обработан ({status})",
        "en": "Order already handled ({status})",
        "es": "El pedido ya fue gestionado ({status})",
    },
    # --- staff management ---
    "addadmin_usage": {
        "ru": "Использование: <code>/addadmin &lt;числовой Telegram ID&gt;</code>\n"
              "ID можно узнать у @userinfobot.",
        "en": "Usage: <code>/addadmin &lt;numeric Telegram ID&gt;</code>\n"
              "Get the ID from @userinfobot.",
        "es": "Uso: <code>/addadmin &lt;ID numérico de Telegram&gt;</code>\n"
              "Consigue el ID en @userinfobot.",
    },
    "invalid_id": {
        "ru": "Некорректный ID. Нужно число, например 123456789.",
        "en": "Invalid ID. Provide a number, e.g. 123456789.",
        "es": "ID no válido. Introduce un número, p. ej. 123456789.",
    },
    "admin_added": {
        "ru": "✅ Администратор <code>{id}</code> добавлен.",
        "en": "✅ Administrator <code>{id}</code> added.",
        "es": "✅ Administrador <code>{id}</code> añadido.",
    },
    "already_admin": {
        "ru": "Этот пользователь уже администратор.",
        "en": "This user is already an administrator.",
        "es": "Este usuario ya es administrador.",
    },
    "admin_removed": {
        "ru": "🗑 Администратор <code>{id}</code> удалён.",
        "en": "🗑 Administrator <code>{id}</code> removed.",
        "es": "🗑 Administrador <code>{id}</code> eliminado.",
    },
    "not_an_admin": {
        "ru": "Этот пользователь не является администратором.",
        "en": "This user is not an administrator.",
        "es": "Este usuario no es administrador.",
    },
    "cannot_remove_super": {
        "ru": "Главного администратора нельзя удалить.",
        "en": "The main administrator can't be removed.",
        "es": "No se puede eliminar al administrador principal.",
    },
    # --- roles ---
    "role_super_admin": {"ru": "супер-админ", "en": "super admin", "es": "súper administrador"},
    "role_admin": {"ru": "администратор", "en": "administrator", "es": "administrador"},
    "role_moderator": {"ru": "модератор", "en": "moderator", "es": "moderador"},
    # --- staff panel ---
    "staff_title": {
        "ru": "👥 <b>Персонал:</b>",
        "en": "👥 <b>Staff:</b>",
        "es": "👥 <b>Personal:</b>",
    },
    "staff_add_hint": {
        "ru": "\n➕ Добавить: <code>/addadmin &lt;ID&gt;</code> — админ, "
              "<code>/addmod &lt;ID&gt;</code> — модератор.",
        "en": "\n➕ To add: <code>/addadmin &lt;ID&gt;</code> — admin, "
              "<code>/addmod &lt;ID&gt;</code> — moderator.",
        "es": "\n➕ Para añadir: <code>/addadmin &lt;ID&gt;</code> — admin, "
              "<code>/addmod &lt;ID&gt;</code> — moderador.",
    },
    "btn_remove_member": {
        "ru": "➖ Удалить сотрудника",
        "en": "➖ Remove a member",
        "es": "➖ Eliminar a un miembro",
    },
    "btn_back": {"ru": "⬅️ Назад", "en": "⬅️ Back", "es": "⬅️ Atrás"},
    "choose_remove": {
        "ru": "Выберите, кого удалить:",
        "en": "Select who to remove:",
        "es": "Selecciona a quién eliminar:",
    },
    "nobody_to_remove": {
        "ru": "Некого удалять — есть только супер-админ.",
        "en": "No one to remove — only the super admin exists.",
        "es": "No hay a quién eliminar — solo existe el súper administrador.",
    },
    "no_permission": {
        "ru": "⛔ У вас нет прав для этого действия. Управлять персоналом могут только админы.",
        "en": "⛔ You don't have permission for this. Only admins can manage staff.",
        "es": "⛔ No tienes permiso para esto. Solo los admins pueden gestionar el personal.",
    },
    "addmod_usage": {
        "ru": "Использование: <code>/addmod &lt;числовой Telegram ID&gt;</code>\n"
              "ID можно узнать у @userinfobot.",
        "en": "Usage: <code>/addmod &lt;numeric Telegram ID&gt;</code>\n"
              "Get the ID from @userinfobot.",
        "es": "Uso: <code>/addmod &lt;ID numérico de Telegram&gt;</code>\n"
              "Consigue el ID en @userinfobot.",
    },
    "staff_added": {
        "ru": "✅ {name} добавлен(а) — роль: <b>{role}</b>.",
        "en": "✅ {name} added — role: <b>{role}</b>.",
        "es": "✅ {name} añadido(a) — rol: <b>{role}</b>.",
    },
    "staff_removed": {
        "ru": "🗑 {name} удалён(а) из персонала.",
        "en": "🗑 {name} removed from staff.",
        "es": "🗑 {name} eliminado(a) del personal.",
    },
    # Notices sent to the person being promoted / demoted.
    "promoted_admin": {
        "ru": "🎉 Вас назначили <b>администратором</b> <b>Ember & Oak</b>!\n"
              "Вам будут приходить новые заказы; вы можете их принимать/отклонять "
              "и управлять персоналом.\n"
              "Команды администратора — в меню слева внизу.",
        "en": "🎉 You've been made an <b>administrator</b> of <b>Ember & Oak</b>!\n"
              "You'll receive new orders, can accept/reject them and manage staff.\n"
              "The admin commands are in the menu at the bottom-left.",
        "es": "🎉 ¡Te han nombrado <b>administrador</b> de <b>Ember & Oak</b>!\n"
              "Recibirás nuevos pedidos, podrás aceptarlos/rechazarlos y gestionar el personal.\n"
              "Los comandos de administrador están en el menú de abajo a la izquierda.",
    },
    "promoted_moderator": {
        "ru": "🎉 Вас назначили <b>модератором</b> <b>Ember & Oak</b>!\n"
              "Вам будут приходить новые заказы, и вы сможете их принимать или отклонять.\n"
              "Команды — в меню слева внизу.",
        "en": "🎉 You've been made a <b>moderator</b> of <b>Ember & Oak</b>!\n"
              "You'll receive new orders and can accept or reject them.\n"
              "The commands are in the menu at the bottom-left.",
        "es": "🎉 ¡Te han nombrado <b>moderador</b> de <b>Ember & Oak</b>!\n"
              "Recibirás nuevos pedidos y podrás aceptarlos o rechazarlos.\n"
              "Los comandos están en el menú de abajo a la izquierda.",
    },
    "demoted_notice": {
        "ru": "ℹ️ Вы больше не входите в персонал <b>Ember & Oak</b>.\n"
              "Уведомления о заказах приходить не будут.",
        "en": "ℹ️ You are no longer part of the <b>Ember & Oak</b> staff.\n"
              "You will no longer receive order notifications.",
        "es": "ℹ️ Ya no formas parte del personal de <b>Ember & Oak</b>.\n"
              "Dejarás de recibir notificaciones de pedidos.",
    },
    # Appended for the acting admin when the target never started the bot.
    "notify_undeliverable": {
        "ru": "\n⚠️ Не удалось отправить ему уведомление — он ещё не запускал бота.",
        "en": "\n⚠️ Couldn't send them a notification — they haven't started the bot yet.",
        "es": "\n⚠️ No se pudo enviarle la notificación — aún no ha iniciado el bot.",
    },
    # --- product status ---
    "prod_status_available": {"ru": "✅ В наличии", "en": "✅ Available", "es": "✅ Disponible"},
    "prod_status_out_of_stock": {"ru": "⛔ Нет в наличии", "en": "⛔ Out of stock", "es": "⛔ Agotado"},
    "prod_status_hidden": {"ru": "🙈 Скрыт", "en": "🙈 Hidden", "es": "🙈 Oculto"},
    "out_of_stock_note": {
        "ru": "⛔ Нет в наличии",
        "en": "⛔ Out of stock",
        "es": "⛔ Agotado",
    },
    # --- menu editor ---
    "editmenu_title": {
        "ru": "🛠 <b>Редактор меню</b>\nВыберите категорию:",
        "en": "🛠 <b>Menu editor</b>\nChoose a category:",
        "es": "🛠 <b>Editor de menú</b>\nElige una categoría:",
    },
    "editmenu_pick_product": {
        "ru": "Выберите товар для редактирования или добавьте новый:",
        "en": "Pick a product to edit, or add a new one:",
        "es": "Elige un producto para editar o añade uno nuevo:",
    },
    "btn_add_product": {"ru": "➕ Добавить товар", "en": "➕ Add product", "es": "➕ Añadir producto"},
    "btn_change_price": {"ru": "💶 Изменить цену", "en": "💶 Change price", "es": "💶 Cambiar precio"},
    "btn_set_available": {"ru": "✅ В наличии", "en": "✅ Mark available", "es": "✅ Disponible"},
    "btn_set_out": {"ru": "⛔ Нет в наличии", "en": "⛔ Out of stock", "es": "⛔ Agotado"},
    "btn_set_hidden": {"ru": "🙈 Скрыть", "en": "🙈 Hide", "es": "🙈 Ocultar"},
    "btn_delete": {"ru": "🗑 Удалить", "en": "🗑 Delete", "es": "🗑 Eliminar"},
    "btn_delete_confirm": {"ru": "🗑 Точно удалить", "en": "🗑 Confirm delete", "es": "🗑 Confirmar"},
    "editmenu_prod_card": {
        "ru": "{emoji} <b>{name}</b>\n{desc}\n\n💶 Цена: <b>€{price:.2f}</b>\nСтатус: {status}",
        "en": "{emoji} <b>{name}</b>\n{desc}\n\n💶 Price: <b>€{price:.2f}</b>\nStatus: {status}",
        "es": "{emoji} <b>{name}</b>\n{desc}\n\n💶 Precio: <b>€{price:.2f}</b>\nEstado: {status}",
    },
    "add_ask_name": {
        "ru": "Введите <b>название</b> товара (например, Iced Latte):",
        "en": "Enter the product <b>name</b> (e.g. Iced Latte):",
        "es": "Escribe el <b>nombre</b> del producto (p. ej. Iced Latte):",
    },
    "add_ask_price": {
        "ru": "Введите <b>цену</b> в евро (например, 4.20):",
        "en": "Enter the <b>price</b> in EUR (e.g. 4.20):",
        "es": "Escribe el <b>precio</b> en EUR (p. ej. 4.20):",
    },
    "add_ask_emoji": {
        "ru": "Отправьте <b>эмодзи</b> для карточки (например, 🧋):",
        "en": "Send an <b>emoji</b> for the card (e.g. 🧋):",
        "es": "Envía un <b>emoji</b> para la tarjeta (p. ej. 🧋):",
    },
    "add_ask_description": {
        "ru": "Введите <b>описание</b> (или нажмите «Пропустить»):",
        "en": "Enter a <b>description</b> (or tap “Skip”):",
        "es": "Escribe una <b>descripción</b> (o pulsa «Omitir»):",
    },
    "add_invalid_price": {
        "ru": "Некорректная цена. Введите число, например 4.20.",
        "en": "Invalid price. Enter a number, e.g. 4.20.",
        "es": "Precio no válido. Escribe un número, p. ej. 4.20.",
    },
    "product_added": {
        "ru": "✅ Товар «{name}» добавлен за €{price:.2f}.",
        "en": "✅ Product “{name}” added for €{price:.2f}.",
        "es": "✅ Producto «{name}» añadido por €{price:.2f}.",
    },
    "price_updated": {
        "ru": "✅ Цена «{name}» обновлена: €{price:.2f}.",
        "en": "✅ Price of “{name}” updated: €{price:.2f}.",
        "es": "✅ Precio de «{name}» actualizado: €{price:.2f}.",
    },
    "status_updated": {
        "ru": "✅ Статус обновлён: {status}.",
        "en": "✅ Status updated: {status}.",
        "es": "✅ Estado actualizado: {status}.",
    },
    "product_deleted": {
        "ru": "🗑 Товар удалён.",
        "en": "🗑 Product deleted.",
        "es": "🗑 Producto eliminado.",
    },
    "product_gone": {
        "ru": "Товар не найден (возможно, уже удалён).",
        "en": "Product not found (maybe already deleted).",
        "es": "Producto no encontrado (quizá ya eliminado).",
    },
    # --- bot command descriptions (native menu button) ---
    "cmd_start": {"ru": "Запустить бота", "en": "Start the bot", "es": "Iniciar el bot"},
    "cmd_menu": {"ru": "Открыть меню", "en": "Open the menu", "es": "Abrir el menú"},
    "cmd_feedback": {"ru": "Связаться / отзыв", "en": "Contact / feedback", "es": "Contacto / opinión"},
    "cmd_language": {"ru": "Сменить язык", "en": "Change language", "es": "Cambiar idioma"},
    "cmd_admin": {"ru": "Последние заказы", "en": "Recent orders", "es": "Pedidos recientes"},
    "cmd_stats": {"ru": "Статистика за сегодня", "en": "Today's stats", "es": "Estadísticas de hoy"},
    "cmd_staff": {"ru": "Персонал и роли", "en": "Staff & roles", "es": "Personal y roles"},
    "cmd_editmenu": {"ru": "Редактор меню", "en": "Menu editor", "es": "Editor de menú"},
    "cmd_addadmin": {"ru": "Добавить администратора", "en": "Add an administrator", "es": "Añadir administrador"},
    "cmd_addmod": {"ru": "Добавить модератора", "en": "Add a moderator", "es": "Añadir moderador"},
}

# Role key -> translation key for its human-readable label.
_ROLE_LABEL_KEYS = {
    "super_admin": "role_super_admin",
    "admin": "role_admin",
    "moderator": "role_moderator",
}

# Status key -> translation key for its label.
_STATUS_LABEL_KEYS = {
    "new": "status_new",
    "accepted": "status_accepted_label",
    "rejected": "status_rejected_label",
}


def t(lang: str, key: str, **kwargs) -> str:
    """Translate ``key`` into ``lang`` (falling back to the default language)."""
    variants = TEXTS[key]
    template = variants.get(lang) or variants.get(DEFAULT_LANG) or next(iter(variants.values()))
    return template.format(**kwargs) if kwargs else template


def status_label(lang: str, status: str) -> str:
    """Localized label for an order status."""
    key = _STATUS_LABEL_KEYS.get(status)
    return t(lang, key) if key else status


def role_label(lang: str, role: str) -> str:
    """Localized label for a staff role."""
    key = _ROLE_LABEL_KEYS.get(role)
    return t(lang, key) if key else role


_PROD_STATUS_KEYS = {
    "available": "prod_status_available",
    "out_of_stock": "prod_status_out_of_stock",
    "hidden": "prod_status_hidden",
}


def prod_status_label(lang: str, status: str) -> str:
    """Localized label for a product's availability status."""
    key = _PROD_STATUS_KEYS.get(status)
    return t(lang, key) if key else status


# Reply-keyboard label (in any language) -> navigation action.
NAV_LABELS: dict[str, str] = {
    label: action
    for action, key in (
        ("menu", "btn_menu"),
        ("cart", "btn_cart"),
        ("feedback", "btn_feedback"),
        ("language", "rk_language"),
    )
    for label in TEXTS[key].values()
}


def match_nav_action(text: str | None) -> str | None:
    """Return the nav action for a tapped reply-keyboard button, if any."""
    return NAV_LABELS.get(text) if text else None
