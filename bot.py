import re

from telebot import TeleBot, custom_filters
from telebot.storage import StateMemoryStorage

from config import TG_BOT_TOKEN, DATABASE_URL
from db import DB
from keyboards import Cmd, quiz_keyboard, main_keyboard, remove_keyboard
from states import BotStates


WELCOME_TEXT = (
    "Привет 👋 Давай попрактикуемся в английском языке. "
    "Тренировки можешь проходить в удобном для себя темпе.\n\n"
    "У тебя есть возможность использовать тренажёр, как конструктор, "
    "и собирать свою собственную базу для обучения. Для этого воспользуйся инструментами:\n\n"
    "добавить слово ➕,\n"
    "удалить слово 🔙.\n\n"
    "Ну что, начнём ⬇️"
)

state_storage = StateMemoryStorage()
bot = TeleBot(TG_BOT_TOKEN, state_storage=state_storage)
db = DB(DATABASE_URL)


def _get_user_id(message) -> int:
    return db.upsert_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )


def _send_card(message):
    user_id = _get_user_id(message)

    card = db.get_random_card(user_id)
    options = db.build_options(user_id, card, n=4)

    bot.set_state(message.from_user.id, BotStates.quiz, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["card_word_id"] = card.word_id
        data["card_en"] = card.en
        data["card_ru"] = card.ru
        data["options"] = options

    bot.send_message(
        message.chat.id,
        f"Выбери перевод слова:\n🇷🇺 {card.ru}",
        reply_markup=quiz_keyboard(options),
    )


@bot.message_handler(commands=["start"])
def start(message):
    _get_user_id(message)
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=main_keyboard())
    _send_card(message)


@bot.message_handler(func=lambda m: m.text == Cmd.NEXT)
def next_card(message):
    _send_card(message)


@bot.message_handler(func=lambda m: m.text == Cmd.ADD)
def add_word_start(message):
    bot.set_state(message.from_user.id, BotStates.add_ru, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Введи слово/фразу на русском (например: Кошка):",
        reply_markup=remove_keyboard(),
    )


@bot.message_handler(state=BotStates.add_ru, content_types=["text"])
def add_word_ru(message):
    ru = message.text.strip()
    if len(ru) < 1:
        bot.send_message(message.chat.id, "Русское слово пустое. Попробуй снова:")
        return

    bot.set_state(message.from_user.id, BotStates.add_en, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["new_ru"] = ru

    bot.send_message(message.chat.id, "Теперь введи перевод на английском (например: Cat):")


@bot.message_handler(state=BotStates.add_en, content_types=["text"])
def add_word_en(message):
    en = message.text.strip()

    # простая валидация: хотя бы одна латинская буква
    if not re.search(r"[A-Za-z]", en):
        bot.send_message(message.chat.id, "Похоже, это не английское слово. Введи ещё раз (латиницей):")
        return

    user_id = _get_user_id(message)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        ru = data.get("new_ru")

    db.add_user_word(user_id, en=en, ru=ru)

    # доп. требование: показать сколько слов изучает пользователь
    cnt = db.user_word_count(user_id)

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(
        message.chat.id,
        f"✅ Добавлено: {en} — {ru}\n"
        f"Теперь у тебя {cnt} слов(а) для изучения.",
        reply_markup=main_keyboard(),
    )
    _send_card(message)


@bot.message_handler(func=lambda m: m.text == Cmd.DELETE)
def delete_current_word(message):
    user_id = _get_user_id(message)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word_id = data.get("card_word_id")
        en = data.get("card_en")
        ru = data.get("card_ru")

    if not word_id:
        bot.send_message(message.chat.id, "Пока нечего удалять. Нажми «Дальше ⏭»")
        return

    status = db.delete_word_for_user(user_id, int(word_id))
    cnt = db.user_word_count(user_id)

    bot.send_message(
        message.chat.id,
        f"🗑 {status}\n"
        f"Удалено/скрыто: {en} — {ru}\n"
        f"Теперь у тебя {cnt} слов(а) для изучения.",
        reply_markup=main_keyboard(),
    )
    _send_card(message)


@bot.message_handler(state=BotStates.quiz, content_types=["text"])
def check_answer(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        correct_en = data.get("card_en")
        ru = data.get("card_ru")
        options = data.get("options", [])

    if not correct_en:
        bot.send_message(message.chat.id, "Нажми /start чтобы начать.")
        return

    if message.text == correct_en:
        bot.send_message(message.chat.id, f"Отлично! ❤️\n{correct_en} -> {ru}", reply_markup=main_keyboard())
        return

    # неправильно: предлагаем попробовать снова (клавиатуру оставляем)
    bot.send_message(
        message.chat.id,
        f"Допущена ошибка!\nПопробуй ещё раз вспомнить слово: 🇷🇺 {ru}",
        reply_markup=quiz_keyboard(options),
    )


# fallback: если человек пишет что-то вне состояния
@bot.message_handler(content_types=["text"])
def fallback(message):
    bot.send_message(message.chat.id, "Нажми /start чтобы начать или «Дальше ⏭» чтобы продолжить.", reply_markup=main_keyboard())


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)