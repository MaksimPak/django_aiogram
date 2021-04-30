from aiogram import types
from aiogram.dispatcher.filters import CommandStart

from bot.misc import dp
from bot.models.db import SessionLocal
from bot.models.dashboard import StudentTable


@dp.message_handler(CommandStart())
async def prepare_text_ad(message: types.Message):
    """
    Get message from user
    """
    async with SessionLocal() as session:
        async with session.begin():
            stream = StudentTable(name='Test')
            session.add(stream)
        await session.commit()

    await message.reply('I"m alive!')


