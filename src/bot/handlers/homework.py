from typing import Union

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.utils.callback_settings import short_data


@dp.message_handler(commands=['homework'], commands_prefix='/')
@dp.callback_query_handler(short_data.filter(property='tasks'))
@create_session
async def my_tasks(
        payload: Union[types.CallbackQuery, types.Message],
        session: SessionLocal,
        callback_data: dict = None,
        **kwargs
):
    """
    Starting handler to process homework process
    """
    isinstance(payload, types.CallbackQuery) and await bot.answer_callback_query(payload.id)
    client_tg = payload.from_user.id
    message_id = payload.message.message_id if isinstance(payload, types.CallbackQuery) else payload.message_id
    client = await repo.StudentRepository.get('tg_id', int(client_tg), session)

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('Назад', callback_data=short_data.new(property='back', value=client.id)))

    if isinstance(payload, types.CallbackQuery):
        await bot.edit_message_text(
            'Раздел в разработке',
            client_tg,
            message_id,
            reply_markup=kb
        )
    else:
        await payload.reply('Раздел в разработке', reply_markup=kb)
