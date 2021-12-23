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

class DislikeText(StatesGroup):
    freeze = State()

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
    if studentlesson.lesson.form:
        form_data = ('Пройти', ('form', studentlesson.lesson.form.id, studentlesson.lesson.id))
        markup = KeyboardGenerator(form_data).keyboard
        return await MessageSender(user_id, 'Пройдите форму для продолжения', markup=markup).send()

    next_lesson = await repo.LessonRepository.get_next(
        'id', studentlesson.lesson.id, studentlesson.lesson.course.id, session)

    if not next_lesson:
        return

    new_studentlesson = await repo.StudentLessonRepository.get_or_create(
        next_lesson.id, studentlesson.student.id, session)
    kb = KeyboardGenerator([(_('Отметить как просмотренное'), ('watched', new_studentlesson.id))]).keyboard

    text = await get_lesson_text(new_studentlesson, display_hw=False, display_link=True)
    await MessageSender(user_id, text, new_studentlesson.lesson.image, markup=kb).send()


@dp.message_handler(Text(equals='📝 Курсы'), state='*')
@dp.callback_query_handler(simple_data.filter(value='to_courses'))
@create_session
async def get_categories(
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

    groups = await repo.CourseCategoryRepository.get_all(session)
    groups_btns = [(x.name, ('group_course', x.id)) for x in groups]
    markup = KeyboardGenerator(groups_btns).keyboard
    msg = _('Выберите группу') if markup else _('Ошибка. Нет созданных групп')

    await MessageSender(response.from_user.id, msg, markup=markup).send()


@dp.callback_query_handler(short_data.filter(property='group_course'))
@create_session
async def group_courses(
        cb: types.CallbackQuery,
        callback_data: dict,
        session: SessionLocal
):
    """
    Displays free and enrolled courses of the student
    """
    await cb.message.delete()
    await cb.answer()
    category_id = int(callback_data['value'])
    contact = await repo.ContactRepository.load_student_data('tg_id', cb.from_user.id, session)

    course_btns = []

    courses = await repo.StudentCourseRepository.get_courses(contact.student.id, category_id, session)
    for studentcourse, course in courses:
        watch_count = await repo.StudentLessonRepository.finished_lesson_count(
            course.id, contact.student.id, session
        )
        lesson_count = await repo.LessonRepository.course_lesson_count(course.id, session)
        txt = course.name + ' ✅' if watch_count == lesson_count else course.name
        course_btns.append((txt, ('get_course', course.id)))

    markup = KeyboardGenerator(course_btns).keyboard

    msg = _('Ваши курсы') if course_btns else _('Вы не записаны ни на один курс')

    await MessageSender(cb.from_user.id, msg, markup=markup).send()


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
    contact = await repo.ContactRepository.load_student_data('tg_id', response.from_user.id, session)

    await repo.StudentCourseRepository.create_or_none(contact.student.id, course_id, session)

    received_lessons = await repo.StudentLessonRepository.student_lessons(
        contact.student.id, course_id, session)

    lessons = [x.lesson for x, in received_lessons] if received_lessons else [course.lessons[0]]

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


@create_session
async def proceed_normal(
        response: Union[types.CallbackQuery, types.Message],
        record,
        session
):
    chat_id = response.from_user.id
    message = response.message if isinstance(response, types.CallbackQuery) else response

    if isinstance(response, types.CallbackQuery):
        await response.answer()
        await message.edit_reply_markup(reply_markup=None)

    if not record.lesson.homework_desc:
        user_id = chat_id
        await send_next_lesson(record, user_id, session)
    else:
        text = await get_lesson_text(record, display_hw=True, display_link=False)
        kb = KeyboardGenerator([(_('Отправить работу'), ('submit', record.lesson.course.chat_id, record.id))]).keyboard
        is_media = bool(message.photo)

        await MessageSender.edit(
            chat_id,
            message.message_id,
            text,
            kb,
            is_media
        )


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

    await state.update_data({'hashtag': record.lesson.course.code, 'studentlesson': record.id})
    await repo.StudentLessonRepository.edit(record, {'date_watched': datetime.datetime.now()}, session)

    if record.lesson.rate_lesson_msg and not record.is_rated:
        await send_rate_msg(cb, record)
    elif record.lesson.comment:
        await send_lesson_comment(cb, record)
    else:
        await proceed_normal(cb, record)


async def send_rate_msg(cb, record):
    await cb.message.edit_reply_markup(None)
    markup = KeyboardGenerator([('👍', ('rate_lesson', 'like')),
                                ('👎', ('rate_lesson', 'dislike'))]).keyboard
    return await MessageSender(
        cb.from_user.id,
        record.lesson.rate_lesson_msg,
        markup=markup
    ).send()


async def send_lesson_comment(response: Union[types.CallbackQuery, types.Message], record):
    message = response.message if isinstance(response, types.CallbackQuery) else response

    if isinstance(response, types.CallbackQuery):
        await message.edit_reply_markup(reply_markup=None)

    markup = KeyboardGenerator((_('Перейти дальше'), ('proceed', record.id))).keyboard
    await MessageSender(response.from_user.id, record.lesson.comment, markup=markup).send()


async def process_dislike(cb, record):
    markup = KeyboardGenerator([('Ответить 📝', ('dislike_msg',)),
                                ('Пропустить ➡️', ('proceed', record.id))]).keyboard
    await cb.message.edit_reply_markup(reply_markup=None)

    await MessageSender(
        cb.from_user.id,
        _('Пожалуйста, напишите, что вам не понравилось'),
        markup=markup
    ).send()


@dp.callback_query_handler(simple_data.filter(value='dislike_msg'))
async def dislike_reason(
        cb: types.CallbackQuery,
):
    await cb.answer()
    await MessageSender(
        cb.from_user.id,
        _('Пожалуйста, напишите, что вам не понравилось в уроке')
        ).send()
    await DislikeText.freeze.set()


@dp.message_handler(state=DislikeText.freeze)
@create_session
async def dislike_notify(
        msg: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    await msg.answer(_('Спасибо за отзыв!'))

    data = await state.get_data()
    course = await repo.CourseRepository.get('id', data['course_id'], session)
    contact = await repo.ContactRepository.load_student_data('tg_id', msg.from_user.id, session)
    record = await repo.StudentLessonRepository.lesson_data('id', data['studentlesson'], session)
    template = jinja_env.get_template('inform_dislike.html')

    txt = template.render(contact=contact, course=course, lesson=record.lesson, msg=msg.text)

    await MessageSender(course.chat_id, txt).send()

    if record.lesson.comment:
        await send_lesson_comment(msg, record)
    else:
        await proceed_normal(msg, record)
    await state.reset_state(with_data=False)


@dp.callback_query_handler(short_data.filter(property='rate_lesson'))
@create_session
async def rate_lesson(
        cb: types.CallbackQuery,
        callback_data: dict,
        state: FSMContext,
        session: SessionLocal
):
    await cb.answer()
    rate = callback_data['value']
    data = await state.get_data()

    try:
        record = await repo.StudentLessonRepository.lesson_data('id', data['studentlesson'], session)
    except KeyError:
        return await cb.message.delete()
    await repo.StudentLessonRepository.edit(record, {'is_rated': True}, session)

    if rate == 'like':
        await repo.LessonRepository.edit(record.lesson, {'likes': record.lesson.likes + 1}, session)

        if record.lesson.comment:
            await send_lesson_comment(cb, record)
        else:
            await proceed_normal(cb, record)

    else:
        await repo.LessonRepository.edit(record.lesson, {'dislikes': record.lesson.dislikes + 1}, session)
        await process_dislike(cb, record)


@dp.callback_query_handler(short_data.filter(property='proceed'))
@create_session
async def mark_understood(
        cb: types.CallbackQuery,
        callback_data: dict,
        session: SessionLocal
):
    await cb.answer()
    studentlesson_id = callback_data['value']
    record = await repo.StudentLessonRepository.lesson_data('id', int(studentlesson_id), session)
    await proceed_normal(cb, record)


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
