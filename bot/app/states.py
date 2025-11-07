from aiogram.dispatcher.filters.state import State, StatesGroup

class AddCardStates(StatesGroup):
    label = State()
    card_number = State()
    holder = State()
    exp = State()
    cvv = State()
    notes = State()

class AddSubStates(StatesGroup):
    service_name = State()
    cost = State()
    currency = State()
    billing_cycle = State()
    next_billing_date = State()
    start_date = State()
    notes = State()