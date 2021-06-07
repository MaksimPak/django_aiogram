from aiogram import types

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import bot, dp
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data


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

    client = await repo.StudentRepository.get_course_inload('id', int(client_id), session)

    course_btns = [(studentcourse.courses.name, ('get_course', studentcourse.courses.id))
                   for studentcourse in client.courses]

    kb = KeyboardGenerator(course_btns)

    msg = 'Ваши курсы' if client.courses else 'Вы не записаны ни на один курс'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb.keyboard
    )
