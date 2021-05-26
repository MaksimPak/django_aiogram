from aiogram.types import InlineKeyboardMarkup


async def make_kb(btns):
    kb = InlineKeyboardMarkup()
    kb.add(*btns)

    return kb
