from telebot.handler_backends import StatesGroup, State


class BotStates(StatesGroup):
    quiz = State()
    add_ru = State()
    add_en = State()