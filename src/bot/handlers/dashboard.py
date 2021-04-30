from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.models.dashboard import StudentTable, CourseTable, StudentCourse


class RegistrationState(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    selected_course = State()


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(CommandStart())
async def greetings(message: types.Message):
    await message.reply('Привет! Для того что-бы продолжить напиши свое имя!')
    await RegistrationState.first_name.set()


@dp.message_handler(state=RegistrationState.first_name)
async def set_first_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['first_name'] = message.text

    await message.reply(f'Хорошо, {message.text}. Теперь укажи фамилию')
    await RegistrationState.last_name.set()


@dp.message_handler(state=RegistrationState.last_name)
async def set_last_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['last_name'] = message.text

    await message.reply('Отлично, теперь пожалуйста отправь свой номер')
    await RegistrationState.phone.set()


@dp.message_handler(state=RegistrationState.phone)
async def set_last_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text

    async with SessionLocal() as session:
        courses = await session.execute(select(CourseTable.id, CourseTable.name))

    kb = InlineKeyboardMarkup()
    btns = [InlineKeyboardButton(name, callback_data=f'course_{idx}') for idx, name in courses]
    for btn in btns:
        kb.insert(btn)

    await bot.send_message(message.chat.id, 'Select a course', reply_markup=kb)
    await RegistrationState.selected_course.set()


@dp.callback_query_handler(lambda x: 'course_' in x.data, state=RegistrationState.selected_course)
async def set_course(cb: types.callback_query, state: FSMContext):
    _, course_id = cb.data.split('_')
    data = await state.get_data()
    async with SessionLocal() as session:
        lead = StudentTable(
            first_name=data['first_name'],
            last_name=data['last_name'],
            tg_id=cb.from_user.id,
            phone=data['phone'],
            application_type=StudentTable.ApplicationType.telegram,
            is_client=False
        )
        session.add(lead)
        await session.commit()
        student_course_record = StudentCourse(
            course_id=course_id,
            student_id=lead.id,
        )
        session.add(student_course_record)
        await session.commit()

    await bot.send_message(cb.from_user.id, 'Done')
