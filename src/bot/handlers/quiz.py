from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot.misc import dp
from bot.serializers import KeyboardGenerator


@dp.message_handler(Text(equals='🤔 Викторина'))
async def start_quiz(
        message: types.Message,
        state: FSMContext,
):
    data = [
        ('Spacewar', ('quiz', 1)),
        ('Super Mario Bros', ('quiz', 2)),
        ('Pong', ('quiz', 3)),
        ('Space Invaders', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data, row_width=1).keyboard

    await message.reply('1. Назовите самую первую видео-игру', reply_markup=kb)
