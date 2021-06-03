from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


async def make_kb(btns, *args, **kwargs):
    kb = InlineKeyboardMarkup(*args, **kwargs)
    kb.add(*btns)

    return kb


async def main_kb():
    btns = [
        KeyboardButton('📝 Курсы'),
        KeyboardButton('🧑‍🎓 Профиль'),
        KeyboardButton('📚 Домашка'),
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*btns)

    return kb
