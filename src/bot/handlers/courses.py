import datetime
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ContentType
from aiogram.utils.exceptions import ChatNotFound
import base64
from bot import config
from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.misc import jinja_env
from bot.db.config import SessionLocal
from bot.serializers import KeyboardGenerator, MessageSender
from bot.utils.callback_settings import short_data, two_valued_data, three_valued_data, simple_data

_ = i18n.gettext


class Homework(StatesGroup):
    homework_start = State()


async def send_photo(lesson, user_id, kb, text):
    """
    Returns a file_id if photo does not have one recorded in db. Else, sends the photo by file id
    """
    wait_message = None
    file_obj = lesson.image_file_id
    if not file_obj:
        with open('media/' + lesson.image, 'br') as file:
            file_obj = file.read()
            wait_message = await bot.send_message(user_id, _('Идет обработка, пожалуйста, подождите ⌛'))

    message = await bot.send_photo(
        user_id,
        file_obj,
        caption=text,
        parse_mode='html',
        reply_markup=kb
    )

    if wait_message:
        await wait_message.delete()
    return message.photo[-1].file_id


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
        await response.answer(_('Вы не зарегистрированы. Отправьте /register чтобы зарегистрироваться'))
        return

    course_btns = []

    courses = contact.student.courses
    for studentcourse in courses:
        watch_count = await repo.StudentLessonRepository.finished_lesson_count(
            studentcourse.courses.id, contact.student.id, session
        )
        lesson_count = len(studentcourse.courses.lessons)
        txt = studentcourse.courses.name + ' ✅' if watch_count == lesson_count else studentcourse.courses.name
        course_btns.append((txt, ('get_course', studentcourse.courses.id)))

    kb = KeyboardGenerator(course_btns)

    msg = _('Ваши курсы') if course_btns else _('Вы не записаны ни на один курс')

    await bot.send_message(response.from_user.id, msg, reply_markup=kb.keyboard)


@dp.callback_query_handler(short_data.filter(property='get_course'))
@create_session
async def course_lessons(
        cb: types.callback_query,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict
):
    """
    Displays all lessons of the course
    """
    await bot.answer_callback_query(cb.id)
    course_id = callback_data['value']

    course = await repo.CourseRepository.get_lesson_inload('id', int(course_id), session)
    lessons = await repo.LessonRepository.get_course_lessons(course.id, session)
    async with state.proxy() as data:
        data['course_id'] = course_id

    lessons_data = [(lesson.name, ('lesson', lesson.id)) for lesson in lessons] if course.date_started else None
    markup = KeyboardGenerator(lessons_data).add((_('Назад'), ('to_courses',))).keyboard
    msg = course.description if lessons_data else _('Курс ещё не начат')
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=markup
    )


@dp.callback_query_handler(short_data.filter(property='lesson'))
@create_session
async def get_lesson(
        cb: types.callback_query,
        callback_data: dict,
        session: SessionLocal
):
    """
    Display content of the lesson and create access link for video watch
    """
    await bot.answer_callback_query(cb.id)
    lesson_id = callback_data['value']

    lesson = await repo.LessonRepository.get_course_inload('id', int(lesson_id), session)
    contact = await repo.ContactRepository.load_student_data('tg_id', int(cb.from_user.id), session)
    kb = None

    student_lesson = await repo.StudentLessonRepository.get_or_create(lesson.id, contact.student.id, session)

    if not lesson.course.date_finished:
        kb = KeyboardGenerator().add((_('Отметить как просмотренное'), ('watched', student_lesson.id))).keyboard

    text = await get_lesson_text(student_lesson, display_hw=False, display_link=True)
    await bot.delete_message(cb.from_user.id, cb.message.message_id)

    await MessageSender(cb.from_user.id, text, lesson.image, markup=kb).send()


@dp.callback_query_handler(short_data.filter(property='watched'))
@create_session
async def check_homework(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict,
        session: SessionLocal
):
    """
    Checks if lesson has homework. If it does, provides student with submit button
    """
    studentlesson_id = callback_data['value']
    record = await repo.StudentLessonRepository.lesson_data('id', int(studentlesson_id), session)

    async with state.proxy() as data:
        data['hashtag'] = record.lesson.course.code

    await repo.StudentLessonRepository.edit(record, {'date_watched': datetime.datetime.now()}, session)

    if not record.lesson.homework_desc:
        user_id = cb.from_user.id
        await send_next_lesson(record, user_id, session)
        await cb.message.edit_reply_markup(reply_markup=None)

    if record.lesson.homework_desc:
        await bot.answer_callback_query(cb.id)
        text = await get_lesson_text(record, display_hw=True, display_link=False)
        kb = KeyboardGenerator([(_('Отправить работу'), ('submit', record.lesson.course.chat_id, record.id))]).keyboard

        if cb.message.photo:
            await bot.edit_message_caption(
                cb.from_user.id,
                cb.message.message_id,
                caption=text,
                parse_mode='html',
                reply_markup=kb
            )
        else:
            await bot.edit_message_text(
                text,
                cb.from_user.id,
                cb.message.message_id,
                parse_mode='html',
                reply_markup=kb
            )
    else:
        await bot.answer_callback_query(cb.id, _('Отмечено'))


@dp.callback_query_handler(two_valued_data.filter(property='submit'))
async def request_homework(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Requests homework from student and sets the for homework processing handler
    """
    await bot.answer_callback_query(cb.id)
    await cb.message.edit_reply_markup(
        reply_markup=None
    )
    course_tg = callback_data['first_value']
    student_lesson = callback_data['second_value']

    async with state.proxy() as data:
        data['course_tg'] = course_tg
        data['student_lesson'] = student_lesson

    await cb.message.edit_reply_markup(reply_markup=None)

    await bot.send_message(
        cb.from_user.id,
        _('Отправьте Вашу работу')
    )

    await Homework.homework_start.set()

#
# @dp.message_handler(state=Homework.homework_start, content_types=ContentType.ANY)
# @create_session
# async def forward_homework(
#         message: types.Message,
#         state: FSMContext,
#         session: SessionLocal
# ):
#     """
#     Gets the content of the homework and forwards it to the chat specified for course
#     """
#     data = await state.get_data()
#     student_lesson = await repo.StudentLessonRepository.get_lesson_student_inload(
#         'id', int(data['student_lesson']), session)
#
#     record = await repo.StudentLessonRepository.get_lesson_student_inload('id', int(data['student_lesson']), session)
#
#     await repo.StudentLessonRepository.edit(record, {'homework_sent': datetime.datetime.now()}, session)
#     template = jinja_env.get_template('new_homework.html')
#
#     try:
#         await bot.send_message(
#             data['course_tg'],
#             template.render(student=record.student, hashtag=data['hashtag'], lesson=record.lesson),
#             parse_mode='html'
#         )
#         await bot.forward_message(
#             data['course_tg'],
#             message.chat.id,
#             message.message_id
#         )
#     except ChatNotFound:
#         error = _('Неверный Chat id у курса {course_name}. '
#                   'Пожалуйста исправьте').format(course_name=record.lesson.course.name)
#         await bot.send_message(
#             config.CHAT_ID,
#             template.render(student=record.student, hashtag=data['hashtag'], lesson=record.lesson, error=error),
#             parse_mode='html'
#         )
#         await bot.forward_message(
#             config.CHAT_ID,
#             message.chat.id,
#             message.message_id
#         )
#
#     await message.reply(_('Спасибо'))
#
#     if student_lesson.lesson.course.autosend:
#         await send_next_lesson(record, message.from_user.id, session)
#
#     await state.finish()

#
# @dp.callback_query_handler(three_valued_data.filter(property='feedback'))
# async def get_course_feedback(
#         cb: types.CallbackQuery,
#         state: FSMContext,
#         callback_data: dict
# ):
#     """
#     Sets the state for feedback processing handler and requests course feedback
#     """
#
#     course_id = callback_data['first_value']
#     student_id = callback_data['second_value']
#     lesson_id = callback_data['third_value']
#
#     await bot.answer_callback_query(cb.id)
#
#     async with state.proxy() as data:
#         data['course_id'] = int(course_id) if course_id != 'None' else None
#         data['student_id'] = int(student_id) if student_id != 'None' else None
#         data['lesson_id'] = int(lesson_id) if lesson_id != 'None' else None
#         data['msg'] = cb.message.text
#
#     await cb.message.edit_reply_markup(reply_markup=None)
#
#     await bot.send_message(
#         cb.from_user.id,
#         _('Отправьте Ваше сообщение')
#        )
#     await Feedback.feedback.set()
#
#
# @dp.message_handler(state=Feedback.feedback)
# @create_session
# async def forward_course_feedback(
#         message: types.Message,
#         state: FSMContext,
#         session: SessionLocal
# ):
#     """
#     Processes feedback from student and forwards it to course chat id
#     """
#     data = await state.get_data()
#     course = await repo.CourseRepository.get('id', data['course_id'], session)
#     student = await repo.StudentRepository.get('id', data['student_id'], session)
#     lesson = await repo.LessonRepository.get('id', data['lesson_id'], session)
#
#     chat_id = course.chat_id if course else config.CHAT_ID
#
#     template = jinja_env.get_template('feedback.html')
#
#     try:
#         await bot.send_message(
#             chat_id,
#             template.render(student=student, course=course, lesson=lesson, msg=data.get('msg'))
#         )
#         await bot.forward_message(
#             chat_id,
#             message.chat.id,
#             message.message_id
#         )
#     except ChatNotFound:
#         error = _('Неверный Chat id у курса {course_name}. '
#                   'Пожалуйста исправьте').format(course_name=course.name) if course else None
#         await bot.send_message(
#             chat_id,
#             template.render(student=student, course=course,
#                             lesson=lesson, msg=data.get('msg'), error=error),
#             parse_mode='html'
#         )
#         await bot.forward_message(
#             chat_id,
#             message.chat.id,
#             message.message_id
#         )
#
#     await message.reply(_('Отправлено'))
#     await state.finish()
