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


class Homework(StatesGroup):
    homework_start = State()


class Feedback(StatesGroup):
    feedback = State()


async def send_or_get_file_id(lesson, callback, kb, template):
    if lesson.image_file_id:
        await bot.send_photo(
            callback.from_user.id,
            lesson.image_file_id,
            caption=template,
            parse_mode='html',
            reply_markup=kb
        )
    else:
        with open('../media/' + lesson.image, 'br') as file:
            message = await bot.send_message(callback.from_user.id, 'Идет обработка, пожалуйста, подождите ⌛')
            file_id = (await bot.send_photo(
                callback.from_user.id,
                file.read(),
                caption=template,
                parse_mode='html',
                reply_markup=kb
            )).photo[-1].file_id
            await message.delete()
            return file_id


@dp.callback_query_handler(lambda x: 'courses|' in x.data)
@create_session
async def my_courses(cb: types.CallbackQuery, session: SessionLocal, **kwargs):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')

    client = await repo.StudentRepository.get_course_inload('id', client_id, session)
    free_courses = await repo.CourseRepository.get_many('is_free', True, session)

    btn_list = [InlineKeyboardButton(x.courses.name, callback_data=f'get_course|{x.courses.id}')
                for x in client.courses
                ] + [InlineKeyboardButton(x.name, callback_data=f'get_course|{x.id}') for x in free_courses]

    kb = await make_kb(btn_list)
    kb.add(InlineKeyboardButton('Назад', callback_data=f'back|{client.id}'))

    msg = 'Ваши курсы' if btn_list else 'Вы не записаны ни на один курс'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(lambda x: 'get_course|' in x.data, state='*')
@create_session
async def course_lessons(cb: types.callback_query, state: FSMContext, session: SessionLocal, **kwargs):
    await bot.answer_callback_query(cb.id)
    _, course_id = cb.data.split('|')
    course = await repo.CourseRepository.get_lesson_inload('id', course_id, session)
    client = await repo.StudentRepository.get('tg_id', cb.from_user.id, session)
    lessons = await repo.LessonRepository.load_unsent_from_course(course, 'lessons', session)

    async with state.proxy() as data:
        data['is_finished'] = course.is_finished

    if course.is_free:
        lessons = course.lessons

    kb = await make_kb([InlineKeyboardButton(x.title, callback_data=f'lesson|{x.id}') for x in lessons])
    kb.add(InlineKeyboardButton('Назад', callback_data=f'to_courses|{client.id}'))
    msg = 'Уроки курса' if lessons else 'У курса нет уроков'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(lambda x: 'lesson|' in x.data, state='*')
@create_session
async def get_lesson(cb: types.callback_query, state: FSMContext, session: SessionLocal, **kwargs):
    await bot.answer_callback_query(cb.id)
    _, lesson_id = cb.data.split('|')
    lesson = await repo.LessonRepository.get('id', lesson_id, session)
    client = await repo.StudentRepository.get('tg_id', cb.from_user.id, session)
    lesson_url = await repo.LessonUrlRepository.get_from_lesson_and_student(lesson_id, client.id, session)
    data = await state.get_data()
    kb = None
    if not lesson_url:
        lesson_url = await repo.LessonUrlRepository.create({'student_id': client.id, 'lesson_id': lesson.id}, session)

    student_lesson = await repo.StudentLessonRepository.create(
        {
            'student_id': client.id,
            'lesson_id': lesson_id,
            'date_received': datetime.datetime.now()
        }, session)
    if not data['is_finished']:
        kb = await make_kb([
            InlineKeyboardButton('Отметить как просмотренное', callback_data=f'watched|{student_lesson.id}')])

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


@dp.callback_query_handler(lambda x: 'watched|' in x.data, state='*')
@create_session
async def check_homework(cb: types.callback_query, state: FSMContext, session: SessionLocal, **kwargs):
    _, studentlesson_id = cb.data.split('|')

    record = await repo.StudentLessonRepository.get_lessons_inload('id', studentlesson_id, session)
    await repo.StudentLessonRepository.edit(record, {'date_watched': datetime.datetime.now()}, session)

    async with state.proxy() as data:
        data['hashtag'] = record.lesson.course.hashtag

    if record.lesson.has_homework:
        await bot.answer_callback_query(cb.id)
        template = jinja_env.get_template('lesson_info.html')
        text = template.render(lesson=record.lesson, display_hw=True, display_link=False)
        kb = await make_kb([InlineKeyboardButton(
            'Сдать дз', callback_data=f'submit|{record.lesson.course.chat_id}|{record.id}')])
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


@dp.callback_query_handler(lambda x: 'submit|' in x.data, state='*')
async def request_homework(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, course_tg, student_lesson = cb.data.split('|')

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
async def get_homework(message: types.Message, state: FSMContext, session: SessionLocal, **kwargs):
    data = await state.get_data()

    record = await repo.StudentLessonRepository.get_lesson_student_inload('id', data['student_lesson'], session)
    await repo.StudentLessonRepository.edit(record, {'homework_sent': datetime.datetime.now()}, session)
    template = jinja_env.get_template('new_homework.html')
    await bot.send_message(
        data['course_tg'],
        template.render(student=record.student, hashtag=data['hashtag'])
    )
    await bot.forward_message(
        data['course_tg'],
        message.chat.id,
        message.message_id
    )

    await message.reply('Спасибо')
    await state.finish()


@dp.callback_query_handler(lambda x: 'feedback' in x.data, state='*')
async def get_feedback(cb: types.callback_query, state: FSMContext):
    _, course_id, student_id = cb.data.split('|')
    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['course_id'] = course_id
        data['student_id'] = student_id

    await bot.send_message(
        cb.from_user.id,
        'Отправьте ваше сообщение'
       )
    await Feedback.feedback.set()


@dp.message_handler(state='*')
@create_session
async def get_feedback(message: types.Message, state: FSMContext, session: SessionLocal, **kwargs):
    data = await state.get_data()

    course = await repo.CourseRepository.get('id', data['course_id'], session)
    student = await repo.StudentRepository.get('id', data['student_id'], session)

    template = jinja_env.get_template('feedback.html')

    await bot.send_message(
        course.chat_id,
        template.render(student=student, hashtag=course.hashtag)
    )
    await bot.forward_message(
        course.chat_id,
        message.chat.id,
        message.message_id
    )

    await message.reply('Отправлено')
    await state.finish()

