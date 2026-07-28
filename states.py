"""Finite-state machine (FSM) states.

aiogram keeps per-user state and a small data dictionary between updates, which
lets us walk the customer through multi-step flows one message at a time.
"""

from aiogram.fsm.state import State, StatesGroup


class Checkout(StatesGroup):
    """Steps a customer goes through while placing an order."""

    name = State()     # waiting for the customer's name
    phone = State()    # waiting for the phone number (contact or text)
    comment = State()  # waiting for an optional order comment
    confirm = State()  # showing the summary, waiting for confirmation / payment


class Feedback(StatesGroup):
    """Customer is writing a message to the café team."""

    message = State()


class MenuAdd(StatesGroup):
    """Manager is adding a new product through the in-bot menu editor."""

    name = State()
    price = State()
    emoji = State()
    description = State()


class MenuEditPrice(StatesGroup):
    """Manager is changing a product's price."""

    value = State()
