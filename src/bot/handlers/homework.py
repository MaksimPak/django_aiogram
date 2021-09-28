from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot.decorators import create_session
from bot.misc import dp, i18n
from bot.db.config import SessionLocal

_ = i18n.gettext


@dp.message_handler(Text(equals='📚 Домашка'), state='*')
@create_session
async def my_tasks(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    """
    Starting handler to process homework process
    """
    await state.reset_state()
    await message.reply(_('Раздел в разработке'))
