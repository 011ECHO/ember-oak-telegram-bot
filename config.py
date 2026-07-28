"""Application configuration.

All secrets are read from environment variables (loaded from a local .env file
via python-dotenv). Nothing sensitive is ever hard-coded in the source.
"""

import os

from dotenv import load_dotenv

# Load variables from a .env file located next to this module (if present).
load_dotenv()

# --- Required settings ------------------------------------------------------

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# Numeric Telegram ID of the administrator who receives and manages orders.
try:
    ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0"))
except ValueError:
    ADMIN_CHAT_ID = 0

# --- Optional settings ------------------------------------------------------

# Path to the SQLite database file.
DB_PATH: str = os.getenv("DB_PATH", "ember_oak.db")

# Café display name, reused across user-facing messages.
CAFE_NAME: str = "Ember & Oak"

# Telegram Payments provider token (from @BotFather -> Payments). Optional:
# when empty, online payment is disabled and the bot only takes orders.
PAYMENT_PROVIDER_TOKEN: str = os.getenv("PAYMENT_PROVIDER_TOKEN", "").strip()

# ISO-4217 currency for invoices (menu prices are in EUR).
PAYMENT_CURRENCY: str = os.getenv("PAYMENT_CURRENCY", "EUR")


def payments_enabled() -> bool:
    """True if a payment provider token is configured."""
    return bool(PAYMENT_PROVIDER_TOKEN)


def validate() -> None:
    """Fail fast with a clear message if mandatory settings are missing."""
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set. Create a .env file (see .env.example) "
            "and put your @BotFather token there."
        )
    if not ADMIN_CHAT_ID:
        raise RuntimeError(
            "ADMIN_CHAT_ID is not set. Add your numeric Telegram ID to the "
            ".env file (see .env.example). You can get it from @userinfobot."
        )
