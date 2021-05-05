from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.models.dashboard import StudentTable, CourseTable, StudentCourse, CategoryType


class RegistrationState(StatesGroup):
    lang = State()
    first_name = State()
    last_name = State()
    phone = State()
    selected_field = State()


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
    kb = InlineKeyboardMarkup()
    btns = [InlineKeyboardButton(name.capitalize(), callback_data=f'lang|{member.value}')
            for name, member in StudentTable.LanguageType.__members__.items()]

    for btn in btns:
        kb.insert(btn)
    await bot.send_message(message.from_user.id, 'Привет! Выбери язык', reply_markup=kb)
    await RegistrationState.lang.set()


@dp.callback_query_handler(lambda x: 'lang|' in x.data, state=RegistrationState.lang)
async def set_lang(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, lang = cb.data.split('|')
    async with state.proxy() as data:
        data['lang'] = lang

    await bot.send_message(cb.from_user.id, 'Как тебя зовут?')
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
async def set_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text

    kb = InlineKeyboardMarkup()
    btns = [InlineKeyboardButton(name.capitalize(), callback_data=f'field|{member.value}')
            for name, member in CategoryType.__members__.items()]
    for btn in btns:
        kb.insert(btn)

    await bot.send_message(message.chat.id, 'В каком направлении вы хотите учиться?', reply_markup=kb)
    await RegistrationState.selected_field.set()


@dp.callback_query_handler(lambda x: 'field|' in x.data, state=RegistrationState.selected_field)
async def set_course(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)

    _, field = cb.data.split('|')
    data = await state.get_data()
    async with SessionLocal() as session:
        lead = StudentTable(
            first_name=data['first_name'],
            last_name=data['last_name'],
            tg_id=cb.from_user.id,
            language_type=data['lang'],
            phone=data['phone'],
            chosen_field=field,
            application_type=StudentTable.ApplicationType.telegram,
            is_client=False
        )
        session.add(lead)
        await session.commit()

    await bot.send_message(cb.from_user.id, 'Вы зарегистрированы! В ближайшее время с вами свяжется наш оператор')
    await state.finish()
