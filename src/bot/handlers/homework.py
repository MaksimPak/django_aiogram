from aiogram import types
from aiogram.dispatcher.filters import Text

from bot.decorators import create_session
from bot.misc import dp
from bot.models.db import SessionLocal


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
    await message.reply('Раздел в разработке')
