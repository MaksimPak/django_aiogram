from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.misc import dp, bot
from bot.utils.callback_settings import short_data


@dp.callback_query_handler(short_data.filter(property='tasks'))
async def my_tasks(cb: types.callback_query, callback_data: dict):
    """
    Starting handler to process homework process
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('Назад', callback_data=short_data.new(property='back', value=client_id)))

    await bot.edit_message_text(
        'Раздел в разработке',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
