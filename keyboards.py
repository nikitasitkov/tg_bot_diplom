from telebot import types


class Cmd:
    NEXT = "Дальше ⏭"
    ADD = "Добавить слово ➕"
    DELETE = "Удалить слово 🔙"


def quiz_keyboard(options: list[str]) -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add(*[types.KeyboardButton(x) for x in options])
    kb.add(types.KeyboardButton(Cmd.NEXT), types.KeyboardButton(Cmd.ADD))
    kb.add(types.KeyboardButton(Cmd.DELETE))
    return kb


def main_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add(types.KeyboardButton(Cmd.NEXT), types.KeyboardButton(Cmd.ADD))
    kb.add(types.KeyboardButton(Cmd.DELETE))
    return kb


def remove_keyboard() -> types.ReplyKeyboardRemove:
    return types.ReplyKeyboardRemove()