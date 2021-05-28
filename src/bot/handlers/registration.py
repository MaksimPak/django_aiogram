import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text, ChatTypeFilter
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton

from bot import repository as repo
from bot.decorators import create_session
from bot.helpers import make_kb
from bot.misc import dp, bot
from bot.models.dashboard import StudentTable, CategoryType
from bot.models.db import SessionLocal
from bot.utils.callback_settings import short_data, simple_data


class RegistrationState(StatesGroup):
    invite_link = State()
    lang = State()
    first_name = State()
    last_name = State()
    phone = State()
    selected_field = State()


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), state='*', commands='cancel')
@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(
        message: types.Message,
        state: FSMContext
):
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


@dp.message_handler(CommandStart(re.compile(r'\d+')), ChatTypeFilter(types.ChatType.PRIVATE))
@create_session
async def register_deep_link(
        message: types.Message,
        session: SessionLocal,
        **kwargs
):
    """
    Saves user tg_id into db if start was passed w/ deep link
    """
    student = await repo.StudentRepository.get('unique_code', message.get_args(), session)

    if student and not student.tg_id:
        await repo.StudentRepository.edit(student, {'tg_id': message.from_user.id}, session)
        await message.reply('Вы были успешно зарегистрированы')
    elif not student:
        await message.reply('Неверный инвайт код')
    elif student and student.tg_id:
        await message.reply('Вы уже зарегистрированы. Отправьте /start чтобы начать взаимодействие')


@dp.message_handler(CommandStart(), ChatTypeFilter(types.ChatType.PRIVATE))
@create_session
async def start_reg(
        message: types.Message,
        session: SessionLocal,
        **kwargs
):
    """
    Displays main panel if user exists. Else, offers options for registration
    """
    student = await repo.StudentRepository.get('tg_id', message.from_user.id, session)
    if not student:
        kb = await make_kb([InlineKeyboardButton('Через бот', callback_data=simple_data.new(value='tg_reg')),
                            InlineKeyboardButton('Через инвайт', callback_data=simple_data.new(value='invite_reg'))])

        await bot.send_message(message.from_user.id, 'Выберите способ регистрации', reply_markup=kb)
    else:
        reply_kb = await make_kb([
            InlineKeyboardButton('Курсы', callback_data=short_data.new(property='course', value=student.id)),
            InlineKeyboardButton('Профиль', callback_data=short_data.new(property='student', value=student.id)),
            InlineKeyboardButton('Задания', callback_data=short_data.new(property='tasks', value=student.id)),
        ])
        await bot.send_message(message.from_user.id, 'Выбери опцию',
                               reply_markup=reply_kb)


@dp.callback_query_handler(ChatTypeFilter(types.ChatType.PRIVATE), simple_data.filter(value='invite_reg'))
async def invite_reg(
        cb: types.callback_query
):
    await bot.answer_callback_query(cb.id)
    await bot.send_message(cb.from_user.id, 'Введите инвайт код')
    await RegistrationState.invite_link.set()


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), state=RegistrationState.invite_link)
@create_session
async def check_invite_code(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    student = await repo.StudentRepository.get('unique_code', message.text, session)
    if student:
        await repo.StudentRepository.edit(student, {'tg_id': message.from_user.id}, session)
        await message.reply('Вы были успешно зарегистрированы')
        await state.finish()
    else:
        await message.reply('Неверный инвайт код')


@dp.callback_query_handler(simple_data.filter(value='tg_reg'))
async def tg_reg(
        cb: types.callback_query
):
    await bot.answer_callback_query(cb.id)

    kb = await make_kb([
        InlineKeyboardButton(name.capitalize(), callback_data=short_data.new(property='lang', value=member.value))
        for name, member in StudentTable.LanguageType.__members__.items()])

    await bot.send_message(cb.from_user.id, 'Привет! Выбери язык', reply_markup=kb)
    await RegistrationState.lang.set()


@dp.callback_query_handler(short_data.filter(property='lang'), state=RegistrationState.lang)
async def set_lang(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    await bot.answer_callback_query(cb.id)
    lang = callback_data['value']

    async with state.proxy() as data:
        data['lang'] = lang

    await bot.send_message(cb.from_user.id, 'Как тебя зовут?')
    await RegistrationState.first_name.set()


@dp.message_handler(state=RegistrationState.first_name)
async def set_first_name(
        message: types.Message,
        state: FSMContext
):
    async with state.proxy() as data:
        data['first_name'] = message.text

    await message.reply(f'Хорошо, {message.text}. Теперь укажи фамилию')
    await RegistrationState.last_name.set()


@dp.message_handler(state=RegistrationState.last_name)
async def set_last_name(
        message: types.Message,
        state: FSMContext
):
    async with state.proxy() as data:
        data['last_name'] = message.text

    await message.reply('Отлично, теперь пожалуйста отправь свой номер')
    await RegistrationState.phone.set()


@dp.message_handler(state=RegistrationState.phone)
async def set_phone(
        message: types.Message,
        state: FSMContext
):
    async with state.proxy() as data:
        data['phone'] = message.text

    kb = await make_kb([
        InlineKeyboardButton(name.capitalize(), callback_data=short_data.new(property='field', value=member.value))
        for name, member in CategoryType.__members__.items()])

    await bot.send_message(message.chat.id, 'В каком направлении вы хотите учиться?', reply_markup=kb)
    await RegistrationState.selected_field.set()


@dp.callback_query_handler(short_data.filter(property='field'), state=RegistrationState.selected_field)
@create_session
async def create_record(
        cb: types.callback_query,
        state: FSMContext,
        session: SessionLocal,
        callback_data: dict,
        **kwargs
):
    await bot.answer_callback_query(cb.id)
    field = callback_data['value']

    data = await state.get_data()
    lead_data = {
        'first_name': data['first_name'],
        'last_name': data['last_name'],
        'tg_id': cb.from_user.id,
        'language_type': data['lang'],
        'phone': data['phone'],
        'chosen_field': field,
        'application_type': StudentTable.ApplicationType.telegram,
        'is_client': False
    }

    lead = await repo.StudentRepository.create(lead_data, session)

    reply_kb = await make_kb([
        InlineKeyboardButton('Курсы', callback_data=short_data.new(property='course', value=lead.id)),
        InlineKeyboardButton('Профиль', callback_data=short_data.new(property='student', value=lead.id)),
        InlineKeyboardButton('Задания', callback_data=short_data.new(property='tasks', value=lead.id)),
    ])

    await bot.send_message(cb.from_user.id, 'Вы зарегистрированы! В ближайшее время с вами свяжется наш оператор',
                           reply_markup=reply_kb)
    await state.finish()



