from aiogram import types

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import bot, dp, i18n
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data

_ = i18n.gettext


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

    course_btns = []

    data = await repo.StudentCourseRepository.filter_from_relationship(client, session)
    # todo rewrite
    for record in data:
        watch_count = await repo.StudentLessonRepository.finished_lesson_count(
            record[1].id, client.id, session
        )
        txt = record[1].name + ' ✅' if watch_count == record[0] else record[1].name
        course_btns.append((txt, ('get_course', record[1].id)))

    kb = KeyboardGenerator(course_btns)

    msg = _('Ваши курсы') if client.courses else _('Вы не записаны ни на один курс')
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb.keyboard
    )
