"""Native Telegram command menu (the "Menu" button next to the input field).

The command list shown to a user depends on their role:
  * everyone           -> start, menu, language
  * moderators & above -> + admin, stats, staff
  * admins & super      -> + addadmin, addmod (staff removal is done via the panel)
"""

from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)

from database import (
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_SUPER,
    get_role,
    get_user_language,
    list_staff_ids,
)
from locales import DEFAULT_LANG, LANGUAGES, t

# (command, translation-key) pairs.
_USER_COMMANDS = [
    ("start", "cmd_start"),
    ("menu", "cmd_menu"),
    ("feedback", "cmd_feedback"),
    ("language", "cmd_language"),
]
_STAFF_COMMANDS = [  # available to moderators and above
    ("admin", "cmd_admin"),
    ("stats", "cmd_stats"),
    ("staff", "cmd_staff"),
]
_MANAGE_COMMANDS = [  # available to admins and the super admin
    ("editmenu", "cmd_editmenu"),
    ("addadmin", "cmd_addadmin"),
    ("addmod", "cmd_addmod"),
]


def _build(lang: str, role: str | None) -> list[BotCommand]:
    pairs = list(_USER_COMMANDS)
    if role in (ROLE_SUPER, ROLE_ADMIN, ROLE_MODERATOR):
        pairs += _STAFF_COMMANDS
    if role in (ROLE_SUPER, ROLE_ADMIN):
        pairs += _MANAGE_COMMANDS
    return [BotCommand(command=cmd, description=t(lang, key)) for cmd, key in pairs]


async def setup_default_commands(bot: Bot) -> None:
    """Set the customer command list for everyone, localized per language."""
    # A language-agnostic fallback first...
    await bot.set_my_commands(_build(DEFAULT_LANG, role=None), scope=BotCommandScopeDefault())
    # ...then a localized list for each supported language.
    for lang in LANGUAGES:
        await bot.set_my_commands(
            _build(lang, role=None),
            scope=BotCommandScopeDefault(),
            language_code=lang,
        )


async def refresh_chat_commands(bot: Bot, user_id: int) -> None:
    """Set per-chat commands for one user according to their current role."""
    lang = await get_user_language(user_id) or DEFAULT_LANG
    role = await get_role(user_id)
    await bot.set_my_commands(
        _build(lang, role=role), scope=BotCommandScopeChat(chat_id=user_id)
    )


async def setup_staff_commands(bot: Bot) -> None:
    """On startup, give every known staff member their command menu."""
    for staff_id in await list_staff_ids():
        try:
            await refresh_chat_commands(bot, staff_id)
        except Exception:
            # Staff member may not have started the bot yet; ignore.
            pass
