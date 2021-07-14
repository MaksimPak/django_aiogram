from aiogram import types
from aiogram.dispatcher.filters import Text

from bot.decorators import create_session
from bot.misc import dp
from bot.models.db import SessionLocal
from bot.repository import FormRepository
from bot.serializers import KeyboardGenerator


@dp.message_handler(Text(equals='🤔 Опросники'))
@create_session
async def start_quiz(
        message: types.Message,
        session: SessionLocal,
        **kwargs

):
    forms = await FormRepository.get_all(session)
    form_data = [(form.name, ('form', form.id)) for form in forms]
    markup = KeyboardGenerator(form_data).keyboard

    await message.reply('Выберите опросник', reply_markup=markup)
