from aiogram import types

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import bot, dp, i18n
from bot.db.config import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data

_ = i18n.gettext


@dp.callback_query_handler(short_data.filter(property='to_courses'))
@create_session
async def to_courses(
        cb: types.callback_query,
        session: SessionLocal,
        callback_data: dict
):
    """
    Handles back button to return to course list
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

    client = await repo.StudentRepository.get_course_inload('id', int(client_id), session)

    course_btns = []

    courses = client.courses    # todo rewrite
    for studentcourse in courses:
        watch_count = await repo.StudentLessonRepository.finished_lesson_count(
            studentcourse.courses.id, client.id, session
        )
        lesson_count = len(studentcourse.courses.lessons)
        txt = studentcourse.courses.name + ' ✅' if watch_count == lesson_count else studentcourse.courses.name
        course_btns.append((txt, ('get_course', studentcourse.courses.id)))

    kb = KeyboardGenerator(course_btns)

    msg = _('Ваши курсы') if client.courses else _('Вы не записаны ни на один курс')
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb.keyboard
    )
