from typing import Union

from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.utils.callback_settings import short_data


@dp.message_handler(Text(equals='📚 Домашка'))
@create_session
async def my_tasks(
        message: types.Message,
        session: SessionLocal,
        **kwargs
):
    """
    Starting handler to process homework process
    """
    client = await repo.StudentRepository.get('tg_id', int(message.from_user.id), session)

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('Назад', callback_data=short_data.new(property='back', value=client.id)))

    await message.reply('Раздел в разработке', reply_markup=kb)
