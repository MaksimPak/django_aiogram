import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, ContentType

from bot import config
from bot import repository as repo
from bot.decorators import create_session
from bot.helpers import make_kb
from bot.misc import dp, bot
from bot.misc import jinja_env
from bot.models.db import SessionLocal
from bot.utils.callback_settings import short_data, two_valued_data, three_valued_data


class Homework(StatesGroup):
    homework_start = State()


class Feedback(StatesGroup):
    feedback = State()
    feedback_student = State()


async def send_or_get_file_id(lesson, callback, kb, text):
    """
    Returns a file_id if photo does not have one recorded in db. Else, sends the photo by file id
    """
    if lesson.image_file_id:
        await bot.send_photo(
            callback.from_user.id,
            lesson.image_file_id,
            caption=text,
            parse_mode='html',
            reply_markup=kb
        )
    else:
        with open('../media/' + lesson.image, 'br') as file:
            message = await bot.send_message(callback.from_user.id, 'Идет обработка, пожалуйста, подождите ⌛')
            file_id = (await bot.send_photo(
                callback.from_user.id,
                file.read(),
                caption=text,
                parse_mode='html',
                reply_markup=kb
            )).photo[-1].file_id
            await message.delete()
            return file_id


@dp.callback_query_handler(short_data.filter(property='course'))
@create_session
async def my_courses(
        cb: types.CallbackQuery,
        callback_data: dict,
        session: SessionLocal,
        **kwargs
):
    """
    Displays free and enrolled courses of the student
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']
    client = await repo.StudentRepository.get_course_inload('id', int(client_id), session)
    free_courses = await repo.CourseRepository.get_many('is_free', True, session)

    btn_list = [InlineKeyboardButton(
        x.courses.name,
        callback_data=short_data.new(property='get_course', value=x.courses.id)) for x in client.courses]

    btn_list += [InlineKeyboardButton(
        x.name,
        callback_data=short_data.new(property='get_course', value=x.id)) for x in free_courses]

    kb = await make_kb(btn_list)
    kb.add(InlineKeyboardButton('Назад', callback_data=short_data.new(property='back', value=client.id)))

    msg = 'Ваши курсы' if btn_list else 'Вы не записаны ни на один курс'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(short_data.filter(property='get_course'))
@create_session
async def course_lessons(
        cb: types.callback_query,
        state: FSMContext,
        session: SessionLocal,
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
    lessons = await repo.LessonRepository.load_unsent_from_course(course, 'lessons', session)

    if course.is_free:
        lessons = course.lessons

    kb = await make_kb([
        InlineKeyboardButton(x.title, callback_data=short_data.new(property='lesson', value=x.id)) for x in lessons])

    kb.add(InlineKeyboardButton('Назад', callback_data=short_data.new(property='to_courses', value=client.id)))

    msg = 'Уроки курса' if lessons else 'У курса нет уроков'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(short_data.filter(property='lesson'))
@create_session
async def get_lesson(
        cb: types.callback_query,
        state: FSMContext,
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
    lesson_url = await repo.LessonUrlRepository.get_from_lesson_and_student(int(lesson_id), int(client.id), session)
    kb = None

    if not lesson_url:
        lesson_url = await repo.LessonUrlRepository.create({'student_id': client.id, 'lesson_id': lesson.id}, session)

    student_lesson = await repo.StudentLessonRepository.create(
        {
            'student_id': client.id,
            'lesson_id': lesson_id,
            'date_received': datetime.datetime.now()
        }, session)

    if not lesson.course.is_finished:
        kb = await make_kb([
            InlineKeyboardButton(
                'Отметить как просмотренное',
                callback_data=short_data.new(property='watched', value=student_lesson.id)
            )])

    template = jinja_env.get_template('lesson_info.html')
    url = f'{config.DOMAIN}/dashboard/watch/{lesson_url.hash}'
    text = template.render(lesson=lesson, url=url, display_hw=False, display_link=True)
    await bot.delete_message(cb.from_user.id, cb.message.message_id)

    if lesson.image:
        file_id = await send_or_get_file_id(lesson, cb, kb, text)
        file_id and await repo.LessonRepository.edit(lesson, {'image_file_id': file_id}, session)

    else:
        await bot.send_message(
            cb.from_user.id,
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

    record = await repo.StudentLessonRepository.get_lessons_inload('id', int(studentlesson_id), session)

    await repo.StudentLessonRepository.edit(record, {'date_watched': datetime.datetime.now()}, session)

    async with state.proxy() as data:
        data['hashtag'] = record.lesson.course.hashtag

    if record.lesson.has_homework:
        await bot.answer_callback_query(cb.id)
        template = jinja_env.get_template('lesson_info.html')
        text = template.render(lesson=record.lesson, display_hw=True, display_link=False)

        kb = await make_kb([InlineKeyboardButton('Сдать дз', callback_data=two_valued_data.new(
            property='submit',
            first_value=record.lesson.course.chat_id,
            second_value=record.id
        ))])

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


