from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.misc import dp, bot


@dp.callback_query_handler(lambda x: 'tasks|' in x.data)
async def my_tasks(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('Назад', callback_data=f'back|{client_id}'))

    await bot.edit_message_text(
        'Раздел в разработке',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
