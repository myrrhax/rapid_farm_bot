from aiogram.dispatcher.filters.state import StatesGroup, State

class DialogState(StatesGroup):
    enter_name = State()