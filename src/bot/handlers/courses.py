from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.models.dashboard import StudentTable, StudentCourse, CourseTable, LessonCourse, LessonTable, LessonUrlTable


@dp.message_handler(state='*', commands='courses', is_client=True)
async def my_courses(message: types.Message):
    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.tg_id == message.from_user.id).options(
                selectinload(StudentTable.courses).selectinload(StudentCourse.courses)
            ))).scalar()
        kb = InlineKeyboardMarkup()
        btn_list = [
            InlineKeyboardButton(x.courses.name, callback_data=f'get_course|{x.courses.id}') for x in client.courses
        ]
        for x in btn_list:
            kb.insert(x)

        await bot.send_message(message.from_user.id, 'Your courses', reply_markup=kb)


@dp.callback_query_handler(lambda x: 'get_course|' in x.data, state='*')
async def course_lessons(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    _, course_id = cb.data.split('|')

    async with SessionLocal() as session:
        course = (await session.execute(
                select(CourseTable).where(CourseTable.id == course_id).options(
                    selectinload(CourseTable.lessons).selectinload(LessonCourse.lessons)
                ))).scalar()
        kb = InlineKeyboardMarkup()
        btn_list = [
            InlineKeyboardButton(x.lessons.title, callback_data=f'lesson|{x.lessons.id}') for x in course.lessons
        ]

        for x in btn_list:
            kb.insert(x)

        await bot.send_message(cb.from_user.id, 'Lessons for the course', reply_markup=kb)


@dp.callback_query_handler(lambda x: 'lesson|' in x.data, state='*')
async def get_lesson(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    _, lesson_id = cb.data.split('|')
    async with SessionLocal() as session:
        lesson = (await session.execute(
            select(LessonTable).where(LessonTable.id == lesson_id)
        )).scalar()

        client = (await session.execute(select(StudentTable).where(StudentTable.tg_id == cb.from_user.id))).scalar()
        lesson_url = (await session.execute(select(LessonUrlTable).where(LessonUrlTable.lesson_id == lesson.id,
                                                                         LessonUrlTable.student_id == client.id))).scalar()
        if not lesson_url:
            lesson_url = LessonUrlTable(
                student_id=client.id,
                lesson_id=lesson.id
            )
            session.add(lesson_url)
        await session.commit()
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton('Watch video', url=f'http://127.0.0.1:8000/dashboard/watch/{lesson_url.hash}'))
        await bot.send_message(
            cb.from_user.id,
            f'{lesson.title}\n\n'
            f'{lesson.info}',
            reply_markup=kb
        )
