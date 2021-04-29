from aiogram import types
from aiogram.dispatcher.filters import CommandStart

from bot.misc import dp


@dp.message_handler(CommandStart())
async def prepare_text_ad(message: types.Message):
    """
    Get message from user
    """
    await message.reply('I"m alive!')


