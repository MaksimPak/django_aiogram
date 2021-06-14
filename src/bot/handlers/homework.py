from aiogram import types
from aiogram.dispatcher.filters import Text

from bot.decorators import create_session
from bot.misc import dp, i18n
from bot.models.db import SessionLocal

_ = i18n.gettext


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
    await message.reply(_('Раздел в разработке'))
