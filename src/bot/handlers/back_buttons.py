from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from bot.misc import bot, dp
from bot.models.dashboard import StudentTable, StudentCourse
from bot.models.db import SessionLocal


@dp.callback_query_handler(lambda x: 'back|' in x.data)
async def to_main(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')

    reply_kb = InlineKeyboardMarkup().add(*[
        InlineKeyboardButton('Курсы', callback_data=f'courses|{client_id}'),
        InlineKeyboardButton('Профиль', callback_data=f'profile|{client_id}'),
        InlineKeyboardButton('Задания', callback_data=f'tasks|{client_id}')
    ])

    await bot.edit_message_text(
        'Выбери опцию',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=reply_kb
    )


@dp.callback_query_handler(lambda x: 'to_courses|' in x.data)
async def to_courses(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')

    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == client_id).options(
                selectinload(StudentTable.courses).selectinload(StudentCourse.courses)
            ))).scalar()

    kb = InlineKeyboardMarkup().add(*[
        InlineKeyboardButton(x.courses.name, callback_data=f'get_course|{x.courses.id}') for x in client.courses
    ])

    kb.add(InlineKeyboardButton('Назад', callback_data=f'back|{client.id}'))

    msg = 'Ваши курсы' if client.courses else 'Вы не записаны ни на один курс'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
