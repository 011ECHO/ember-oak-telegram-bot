"""Application entry point.

Wires together configuration, the database and the handler routers, then starts
long polling.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import botcommands
import config
import menu
from database import init_db
from handlers import admin, menu_admin, user


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    # Make sure BOT_TOKEN / ADMIN_CHAT_ID are present before doing anything else.
    config.validate()

    # Prepare the database schema and load the (seeded/edited) menu.
    await init_db()
    await menu.load_products()

    # HTML is used throughout the bot's messages.
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()

    # Staff routers first (their filters guard staff-only actions); the user
    # router below handles everything else.
    dispatcher.include_router(admin.router)
    dispatcher.include_router(menu_admin.router)
    dispatcher.include_router(user.router)

    # Set up the native "Menu" command button (localized), plus the extra
    # command menu for administrators.
    await botcommands.setup_default_commands(bot)
    await botcommands.setup_staff_commands(bot)

    # Ignore updates accumulated while the bot was offline.
    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("Ember & Oak bot started.")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Ember & Oak bot stopped.")
