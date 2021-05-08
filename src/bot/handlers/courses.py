from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from bot import config
from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.models.dashboard import StudentTable, StudentCourse, CourseTable, LessonTable, LessonUrlTable


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
        *[InlineKeyboardButton(x.title, callback_data=f'lesson|{x.id}') for x in course.lessons]
    )

    kb.add(InlineKeyboardButton('Назад', callback_data=f'to_courses|{data["client_id"]}'))

    msg = 'Уроки курса' if course.lessons else 'У курса не уроков'
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
    kb.add(InlineKeyboardButton('Watch video', url=f'{config.DOMAIN}/dashboard/watch/{lesson_url.hash}'))
    await bot.send_message(
        cb.from_user.id,
        f'{lesson.title}\n\n'
        f'{lesson.info}',
        reply_markup=kb
    )
