import base64
import datetime
import re
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ContentType
from aiogram.utils.exceptions import ChatNotFound

from bot import config
from bot import repository as repo
from bot.db.config import SessionLocal
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.misc import jinja_env
from bot.serializers import KeyboardGenerator, MessageSender
from bot.utils.callback_settings import short_data, two_valued_data, simple_data
from bot.utils.filters import CourseStudent, LessonStudent

_ = i18n.gettext


class Homework(StatesGroup):
    homework_start = State()


async def get_lesson_text(studentlesson, **kwargs):
    """
    Create byte object and encode it with base64.
    """
    template = jinja_env.get_template('lesson_info.html')
    idx = studentlesson.lesson.id
    binary_id = studentlesson.lesson.id.to_bytes((idx.bit_length() + 7) // 8, 'big')
    encoded = base64.urlsafe_b64encode(binary_id)
    encoded_str = encoded.decode()
    text = template.render(lesson=studentlesson.lesson, encoded_id=encoded_str, **kwargs)

    return text


async def send_next_lesson(studentlesson, user_id, session):
    next_lesson = await repo.LessonRepository.get_next(
        'id', studentlesson.lesson.id, studentlesson.lesson.course.id, session)
    if not next_lesson:
        return

    new_studentlesson = await repo.StudentLessonRepository.get_or_create(
        next_lesson.id, int(studentlesson.student.id), session)
    kb = KeyboardGenerator([(_('Отметить как просмотренное'), ('watched', new_studentlesson.id))]).keyboard

    text = await get_lesson_text(new_studentlesson, display_hw=False, display_link=True)
    await MessageSender(user_id, text, new_studentlesson.lesson.image, markup=kb).send()


@dp.message_handler(Text(equals='📝 Курсы'), state='*')
@dp.callback_query_handler(simple_data.filter(value='to_courses'))
@create_session
async def my_courses(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext,
        session: SessionLocal
):
    """
    Displays free and enrolled courses of the student
    """
    if isinstance(response, types.CallbackQuery):
        await response.message.delete()
        await response.answer()
    await state.reset_state()
    contact = await repo.ContactRepository.load_student_data('tg_id', response.from_user.id, session)
    if not contact.student:
        return await response.answer(_('Вы не зарегистрированы. Отправьте /register чтобы зарегистрироваться'))

    course_btns = []

    courses = contact.student.courses
    for studentcourse in courses:
        watch_count = await repo.StudentLessonRepository.finished_lesson_count(
            studentcourse.courses.id, contact.student.id, session
        )
        lesson_count = len(studentcourse.courses.lessons)
        txt = studentcourse.courses.name + ' ✅' if watch_count == lesson_count else studentcourse.courses.name
        course_btns.append((txt, ('get_course', studentcourse.courses.id)))

    markup = KeyboardGenerator(course_btns).keyboard

    msg = _('Ваши курсы') if course_btns else _('Вы не записаны ни на один курс')

    await MessageSender(response.from_user.id, msg, markup=markup).send()


@dp.callback_query_handler(short_data.filter(property='get_course'))
@dp.message_handler(CourseStudent(), state='*')
@create_session
async def course_lessons(
        response: Union[types.CallbackQuery, types.Message],
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict = None,
        deep_link: re.Match = None
):
    """
    Displays all lessons of the course
    """
    if type(response) == types.CallbackQuery:
        await response.answer() and await response.message.delete()
        course_id = int(callback_data['value'])
    else:
        course_id = int(deep_link.group(1))

    course = await repo.CourseRepository.get_lesson_inload('id', course_id, session)
    lessons = await repo.LessonRepository.get_course_lessons(course.id, session)
    async with state.proxy() as data:
        data['course_id'] = course_id

    lessons_data = [(lesson.name, ('lesson', lesson.id)) for lesson in lessons] if course.date_started else None
    markup = KeyboardGenerator(lessons_data).add((_('Назад'), ('to_courses',))).keyboard
    msg = course.description if lessons_data else _('Курс ещё не начат')

    await MessageSender(response.from_user.id, msg,  markup=markup).send()


@dp.callback_query_handler(short_data.filter(property='lesson'))
@dp.message_handler(LessonStudent(), state='*')
@create_session
async def get_lesson(
        response: Union[types.CallbackQuery, types.Message],
        session: SessionLocal,
        callback_data: dict = None,
        deep_link: re.Match = None
):
    """
    Display content of the lesson and create access link for video watch
    """
    if type(response) == types.CallbackQuery:
        await response.answer() and await response.message.delete()
        lesson_id = int(callback_data['value'])
    else:
        lesson_id = int(deep_link.group(1))

    lesson = await repo.LessonRepository.get_course_inload(
        'id', int(lesson_id), session)
    contact = await repo.ContactRepository.load_student_data(
        'tg_id', int(response.from_user.id), session)
    kb = None

    student_lesson = await repo.StudentLessonRepository.get_or_create(
        lesson.id, contact.student.id, session)

    if not lesson.course.date_finished:
        kb = KeyboardGenerator().add(
            (_('Отметить как просмотренное'), ('watched', student_lesson.id))).keyboard

    text = await get_lesson_text(student_lesson, display_hw=False, display_link=True)
    await MessageSender(response.from_user.id, text, lesson.image, markup=kb).send()


@dp.callback_query_handler(short_data.filter(property='watched'))
@create_session
async def check_homework(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict,
        session: SessionLocal
):
    """
    Checks if lesson has homework. If it does, provides student with submit button
    """
    await bot.answer_callback_query(cb.id, _('Отмечено'))
    studentlesson_id = callback_data['value']
    record = await repo.StudentLessonRepository.lesson_data('id', int(studentlesson_id), session)

    await state.update_data({'hashtag': record.lesson.course.code})
    await repo.StudentLessonRepository.edit(record, {'date_watched': datetime.datetime.now()}, session)

    if not record.lesson.homework_desc:
        user_id = cb.from_user.id
        await send_next_lesson(record, user_id, session)
        await cb.message.edit_reply_markup(reply_markup=None)
    else:
        await bot.answer_callback_query(cb.id)
        text = await get_lesson_text(record, display_hw=True, display_link=False)
        kb = KeyboardGenerator([(_('Отправить работу'), ('submit', record.lesson.course.chat_id, record.id))]).keyboard
        is_media = bool(cb.message.photo)

        await MessageSender.edit(
            cb.from_user.id,
            cb.message.message_id,
            text,
            kb,
            is_media
        )


@dp.callback_query_handler(two_valued_data.filter(property='submit'))
async def request_homework(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict
):
    """
    Requests homework from student and sets the for homework processing handler
    """
    await cb.answer()
    await cb.message.edit_reply_markup(
        reply_markup=None
    )
    course_tg = callback_data['first_value']
    student_lesson = callback_data['second_value']

    async with state.proxy() as data:
        data['course_tg'] = course_tg
        data['student_lesson'] = student_lesson

    await MessageSender(cb.from_user.id, _('Отправьте Вашу работу')).send()

    await Homework.homework_start.set()


@dp.message_handler(state=Homework.homework_start, content_types=ContentType.ANY)
@create_session
async def forward_homework(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    """
    Gets the content of the homework and forwards it to the chat specified for course
    """
    data = await state.get_data()
    record = await repo.StudentLessonRepository.lesson_data('id', int(data['student_lesson']), session)

    await repo.StudentLessonRepository.edit(record, {'homework_sent': datetime.datetime.now()}, session)
    template = jinja_env.get_template('new_homework.html')

    try:
        txt = template.render(student=record.student, hashtag=data['hashtag'], lesson=record.lesson)
        await MessageSender(data['course_tg'], txt).send()
        await bot.forward_message(
            data['course_tg'],
            message.chat.id,
            message.message_id
        )
    except ChatNotFound:
        error = _('Неверный Chat id у курса {course_name}. '
                  'Пожалуйста исправьте').format(course_name=record.lesson.course.name)
        txt = template.render(student=record.student, hashtag=data['hashtag'], lesson=record.lesson, error=error)
        await MessageSender(config.CHAT_ID, txt).send()
        await bot.forward_message(
            config.CHAT_ID,
            message.chat.id,
            message.message_id
        )
    await message.reply(_('Спасибо'))
    await send_next_lesson(record, message.from_user.id, session)
    await state.finish()
