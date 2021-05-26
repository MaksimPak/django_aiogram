from aiogram.types import InlineKeyboardMarkup


async def make_kb(btns, *args, **kwargs):
    kb = InlineKeyboardMarkup(*args, **kwargs)
    kb.add(*btns)

    return kb
