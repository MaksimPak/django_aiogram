import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from bot import config
from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.models.dashboard import StudentTable, StudentCourse, StudentLesson, CourseTable, LessonTable, LessonUrlTable
from bot.misc import jinja_env


class Homework(StatesGroup):
    homework_start = State()


@dp.callback_query_handler(lambda x: 'courses|' in x.data)
async def my_courses(cb: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')

    async with state.proxy() as data:
        data['client_id'] = client_id

    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == client_id).options(
                selectinload(StudentTable.courses).selectinload(StudentCourse.courses)
            ))).scalar()

    kb = InlineKeyboardMarkup()
    btn_list = [
        InlineKeyboardButton(x.courses.name, callback_data=f'get_course|{x.courses.id}') for x in client.courses
    ]
    kb.add(*btn_list)
    kb.add(InlineKeyboardButton('Назад', callback_data=f'back|{client.id}'))

    msg = 'Ваши курсы' if client.courses else 'Вы не записаны ни на один курс'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(lambda x: 'get_course|' in x.data, state='*')
async def course_lessons(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, course_id = cb.data.split('|')
    data = await state.get_data()
    async with SessionLocal() as session:
        course = (await session.execute(
                select(CourseTable).where(CourseTable.id == course_id).options(
                    selectinload(CourseTable.lessons)
                ))).scalar()
    kb = InlineKeyboardMarkup().add(
        *[InlineKeyboardButton(x.title, callback_data=f'lesson|{x.id}') for x in course.lessons[:course.last_lesson_index]]
    )

    kb.add(InlineKeyboardButton('Назад', callback_data=f'to_courses|{data["client_id"]}'))

    msg = 'Уроки курса' if course.lessons[:course.last_lesson_index] else 'У курса не уроков'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(lambda x: 'lesson|' in x.data, state='*')
async def get_lesson(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    _, lesson_id = cb.data.split('|')
    async with SessionLocal() as session:
        lesson = (await session.execute(
            select(LessonTable).where(LessonTable.id == lesson_id)
        )).scalar()

        client = (await session.execute(select(StudentTable).where(StudentTable.tg_id == cb.from_user.id))).scalar()
        lesson_url = (await session.execute(
            select(LessonUrlTable).where(LessonUrlTable.lesson_id == lesson.id,
                                         LessonUrlTable.student_id == client.id))).scalar()
        if not lesson_url:
            lesson_url = LessonUrlTable(
                student_id=client.id,
                lesson_id=lesson.id
            )
            session.add(lesson_url)
        await session.commit()
    kb = InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton('Отметить как просмотренное', callback_data=f'watched|{client.id}|{lesson.id}'))
    kb.add(InlineKeyboardButton('Назад', callback_data=f'to_lessons|{lesson.course_id}|{client.id}'))

    template = jinja_env.get_template('lesson_info.html')

    await bot.edit_message_text(
        template.render(lesson=lesson),
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )

    await bot.send_message(
        cb.from_user.id,
        f'{config.DOMAIN}/dashboard/watch/{lesson_url.hash}',
    )


@dp.callback_query_handler(lambda x: 'watched|' in x.data, state='*')
async def send_link(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, student_id, lesson_id = cb.data.split('|')
    async with SessionLocal() as session:
        student_lesson = StudentLesson(
            student_id=student_id,
            lesson_id=lesson_id
        )
        session.add(student_lesson)
        await session.commit()
        await session.refresh(student_lesson)

        record = (await session.execute(select(StudentLesson).where(
            StudentLesson.id == student_lesson.id
        ).options(selectinload(StudentLesson.lesson).selectinload(LessonTable.lesson_course)))).scalar()
        if record.lesson.has_homework:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(
                'Сдать дз', callback_data=f'submit|{record.lesson.lesson_course.chat_id}|{record.id}')
            )
            await bot.edit_message_text(
                cb.message.text,
                cb.from_user.id,
                cb.message.message_id,
                reply_markup=kb
            )
        else:
            await bot.delete_message(cb.message.chat.id, cb.message.message_id)


@dp.callback_query_handler(lambda x: 'submit|' in x.data, state='*')
async def send_homework(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, course_tg, student_lesson = cb.data.split('|')

    async with state.proxy() as data:
        data['course_tg'] = course_tg
        data['student_lesson'] = student_lesson
    await bot.delete_message(cb.message.chat.id, cb.message.message_id)
    await bot.send_message(
        cb.from_user.id,
        'Отправьте вашу работу'
       )

    await Homework.homework_start.set()


@dp.message_handler(state=Homework.homework_start, content_types=ContentType.ANY)
async def get_homework(message: types.Message, state: FSMContext):
    data = await state.get_data()

    async with SessionLocal() as session:
        record = (await session.execute(select(StudentLesson).where(
            StudentLesson.id == data['student_lesson']
        ).options(selectinload(StudentLesson.lesson).selectinload(LessonTable.lesson_course)))).scalar()
        record.homework_sent = datetime.datetime.now()
        await session.commit()

    await bot.forward_message(
        data['course_tg'],
        message.chat.id,
        message.message_id
    )

    await message.reply('Спасибо')
    await state.finish()

