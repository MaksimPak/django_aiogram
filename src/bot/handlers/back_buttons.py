from aiogram import types
from aiogram.types import InlineKeyboardButton

from bot import repository as repo
from bot.decorators import create_session
from bot.helpers import make_kb
from bot.misc import bot, dp
from bot.models.db import SessionLocal
from bot.utils.callback_settings import short_data


@dp.callback_query_handler(short_data.filter(property='back'))
async def to_main(
        cb: types.callback_query,
        callback_data: dict
):
    """
    Handles back button to return to main panel
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

    reply_kb = await make_kb([
        InlineKeyboardButton('Курсы', callback_data=short_data.new(property='course', value=client_id)),
        InlineKeyboardButton('Профиль', callback_data=short_data.new(property='student', value=client_id)),
        InlineKeyboardButton('Задания', callback_data=short_data.new(property='tasks', value=client_id)),
    ])

    await bot.edit_message_text(
        'Выберите опцию',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=reply_kb
    )


@dp.callback_query_handler(short_data.filter(property='to_courses'))
@create_session
async def to_courses(
        cb: types.callback_query,
        session: SessionLocal,
        callback_data: dict,
        **kwargs
):
    """
    Handles back button to return to course list
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

    client = await repo.StudentRepository.get_course_inload('id', client_id, session)

    kb = await make_kb([
        InlineKeyboardButton(x.courses.name, callback_data=short_data.new(property='get_course', value=x.courses.id))
        for x in client.courses
    ])

    kb.add(InlineKeyboardButton('Назад', callback_data=short_data.new(property='back', value=client.id)))

    msg = 'Ваши курсы' if client.courses else 'Вы не записаны ни на один курс'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
