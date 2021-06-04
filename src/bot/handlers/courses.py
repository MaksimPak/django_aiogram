import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ContentType

from bot import config
from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot
from bot.misc import jinja_env
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data, two_valued_data, three_valued_data


class Homework(StatesGroup):
    homework_start = State()


class Feedback(StatesGroup):
    feedback = State()
    feedback_student = State()


async def send_photo(lesson, user_id, kb, text):
    """
    Returns a file_id if photo does not have one recorded in db. Else, sends the photo by file id
    """
    wait_message = None
    file_obj = lesson.image_file_id
    if not file_obj:

        with open('media/' + lesson.image, 'br') as file:
            file_obj = file.read()
            wait_message = await bot.send_message(user_id, 'Идет обработка, пожалуйста, подождите ⌛')

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


async def get_lesson_text(studentlesson, session, *args, **kwargs):
    lesson_url = await repo.LessonUrlRepository.get_or_create(
        studentlesson.lesson.id, studentlesson.student.id, session)
    template = jinja_env.get_template('lesson_info.html')
    text = template.render(lesson=studentlesson.lesson, hash=lesson_url.hash, **kwargs)

    return text


async def send_next_lesson(studentlesson, user_id, session):
    next_lesson = await repo.LessonRepository.get_next(
        'id', studentlesson.lesson.id, studentlesson.lesson.course.id, session)
    if studentlesson.lesson.course.is_finished or not next_lesson:
        return

    new_studentlesson = await repo.StudentLessonRepository.get_or_create(
        next_lesson.id, int(studentlesson.student.id), session)
    kb = KeyboardGenerator(('Отметить как просмотренное', ('watched', new_studentlesson.id))).keyboard

    text = await get_lesson_text(new_studentlesson, session, display_hw=False, display_link=True)

    if studentlesson.lesson.image:
        file_id = await send_photo(studentlesson.lesson, user_id, kb, text)
        if not studentlesson.lesson.image_file_id:
            await repo.LessonRepository.edit(studentlesson.lesson, {'image_file_id': file_id}, session)
    else:
        await bot.send_message(
            user_id,
            text,
            parse_mode='html',
            reply_markup=kb
        )


@dp.message_handler(Text(equals='📝 Курсы'))
@create_session
async def my_courses(
        message: types.Message,
        session: SessionLocal,
        **kwargs
):
    """
    Displays free and enrolled courses of the student
    """
    client = await repo.StudentRepository.get_course_inload('tg_id', int(message.from_user.id), session)
    free_courses = await repo.CourseRepository.get_many('is_free', True, session)

    course_btns = [(studentcourse.courses.name, ('get_course', studentcourse.courses.id))
                   for studentcourse in client.courses]
    course_btns += [(course.name, ('get_course', course.id)) for course in free_courses]

    kb = KeyboardGenerator(course_btns)

    msg = 'Ваши курсы' if course_btns else 'Вы не записаны ни на один курс'

    await message.reply(msg, reply_markup=kb.keyboard)


@dp.callback_query_handler(short_data.filter(property='get_course'))
@create_session
async def course_lessons(
        cb: types.callback_query,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict,
        **kwargs
):
    """
    Displays all lessons of the course
    """
    await bot.answer_callback_query(cb.id)
    course_id = callback_data['value']

    course = await repo.CourseRepository.get_lesson_inload('id', int(course_id), session)
    client = await repo.StudentRepository.get('tg_id', int(cb.from_user.id), session)
    lessons = await repo.LessonRepository.get_student_lessons(client.id, course.id, session)
    async with state.proxy() as data:
        data['course_id'] = course_id

    if course.is_free:
        lessons = course.lessons
    lessons_data = [(lesson.title, ('lesson', lesson.id)) for lesson in lessons]
    markup = KeyboardGenerator(lessons_data).add(('Назад', ('to_courses', client.id))).keyboard

    msg = 'Уроки курса' if lessons else 'У курса нет уроков'
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
        session: SessionLocal,
        **kwargs
):
    """
    Display content of the lesson and create access link for video watch
    """
    await bot.answer_callback_query(cb.id)
    lesson_id = callback_data['value']

    lesson = await repo.LessonRepository.get_course_inload('id', int(lesson_id), session)
    client = await repo.StudentRepository.get('tg_id', int(cb.from_user.id), session)
    kb = None

    student_lesson = await repo.StudentLessonRepository.get_or_create(lesson.id, client.id, session)

    if not lesson.course.is_finished:
        kb = KeyboardGenerator().add(('Отметить как просмотренное', ('watched', student_lesson.id))).keyboard

    text = await get_lesson_text(student_lesson, session, display_hw=False, display_link=True)
    await bot.delete_message(cb.from_user.id, cb.message.message_id)
    user_id = cb.from_user.id

    if lesson.image:
        file_id = await send_photo(lesson, user_id, kb, text)
        if not lesson.image_file_id:
            await repo.LessonRepository.edit(lesson, {'image_file_id': file_id}, session)

    else:
        await bot.send_message(
            user_id,
            text,
            parse_mode='html',
            reply_markup=kb
        )


@dp.callback_query_handler(short_data.filter(property='watched'))
@create_session
async def check_homework(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict,
        session: SessionLocal,
        **kwargs
):
    """
    Checks if lesson has homework. If it does, provides student with submit button
    """
    studentlesson_id = callback_data['value']
    record = await repo.StudentLessonRepository.get_lesson_student_inload('id', int(studentlesson_id), session)

    async with state.proxy() as data:
        data['hashtag'] = record.lesson.course.hashtag

    await repo.StudentLessonRepository.edit(record, {'date_watched': datetime.datetime.now()}, session)

    if record.lesson.course.autosend and not record.lesson.has_homework:
        user_id = cb.from_user.id
        await send_next_lesson(record, user_id, session)
        await cb.message.edit_reply_markup(reply_markup=None)

    if record.lesson.has_homework:
        await bot.answer_callback_query(cb.id)
        text = await get_lesson_text(record, session, display_hw=True, display_link=False)
        kb = KeyboardGenerator(('Сдать дз', ('submit', record.lesson.course.chat_id, record.id))).keyboard

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
        await bot.answer_callback_query(cb.id, 'Отмечено')


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
    await bot.send_message(
        cb.from_user.id,
        'Отправьте вашу работу'
       )

    await Homework.homework_start.set()


@dp.message_handler(state=Homework.homework_start, content_types=ContentType.ANY)
@create_session
async def forward_homework(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    """
    Gets the content of the homework and forwards it to the chat specified for course
    """
    data = await state.get_data()
    student_lesson = await repo.StudentLessonRepository.get_lesson_student_inload(
        'id', int(data['student_lesson']), session)

    record = await repo.StudentLessonRepository.get_lesson_student_inload('id', int(data['student_lesson']), session)

    await repo.StudentLessonRepository.edit(record, {'homework_sent': datetime.datetime.now()}, session)
    template = jinja_env.get_template('new_homework.html')
    await bot.send_message(
        data['course_tg'],
        template.render(student=record.student, hashtag=data['hashtag'], lesson=record.lesson)
    )
    await bot.forward_message(
        data['course_tg'],
        message.chat.id,
        message.message_id
    )

    await message.reply('Спасибо')

    if student_lesson.lesson.course.autosend:
        await send_next_lesson(record, message.from_user.id, session)

    await state.finish()


@dp.callback_query_handler(three_valued_data.filter(property='feedback'))
async def get_course_feedback(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Sets the state for feedback processing handler and requests course feedback
    """

    course_id = callback_data['first_value']
    student_id = callback_data['second_value']
    lesson_id = callback_data['third_value']

    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['course_id'] = course_id
        data['student_id'] = student_id
        data['lesson_id'] = lesson_id

    await bot.send_message(
        cb.from_user.id,
        'Отправьте ваше сообщение'
       )
    await Feedback.feedback.set()


@dp.message_handler(state=Feedback.feedback)
@create_session
async def forward_course_feedback(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    """
    Processes feedback from student and forwards it to course chat id
    """
    data = await state.get_data()
    course = await repo.CourseRepository.get('id', int(data['course_id']), session)
    student = await repo.StudentRepository.get('id', int(data['student_id']), session)
    lesson = await repo.LessonRepository.get('id', int(data['lesson_id']), session)

    template = jinja_env.get_template('feedback.html')

    await bot.send_message(
        course.chat_id,
        template.render(student=student, course=course, lesson=lesson)
    )
    await bot.forward_message(
        course.chat_id,
        message.chat.id,
        message.message_id
    )

    await message.reply('Отправлено')
    await state.finish()


@dp.callback_query_handler(short_data.filter(property='feedback_student'))
async def get_student_feedback(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Sets the state for feedback processing handler and requests student feedback
    """
    student_id = callback_data['value']

    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['student_id'] = student_id

    await bot.send_message(
        cb.from_user.id,
        'Отправьте ваше сообщение'
    )
    await Feedback.feedback_student.set()


@dp.message_handler(state=Feedback.feedback_student)
@create_session
async def forward_student_feedback(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    """
    Processes feedback from student and forwards it to course chat id
    """
    data = await state.get_data()
    student = await repo.StudentRepository.get('id', int(data['student_id']), session)

    await bot.send_message(
        config.CHAT_ID,
        f'Вам пришло сообщение от: {student.first_name} {student.last_name}'
    )
    await bot.forward_message(
        config.CHAT_ID,
        message.chat.id,
        message.message_id
    )

    await message.reply('Отправлено')
    await state.finish()

