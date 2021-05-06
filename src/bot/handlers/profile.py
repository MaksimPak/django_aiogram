from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select

from bot.misc import dp, bot
from bot.models.dashboard import StudentTable, CategoryType
from bot.models.db import SessionLocal


class ProfileChange(StatesGroup):
    first_name = State()
    last_name = State()
    lang = State()
    phone = State()
    field = State()


async def default_renderer(client, key):
    return getattr(client, key)


async def enum_renderer(client, key):

    return (await default_renderer(client, key)).name


PROFILE_FIELDS = (
    ('Имя', 'first_name', default_renderer),
    ('Фамилия', 'last_name', default_renderer),
    ('Язык', 'language_type', enum_renderer),
    ('Телефон', 'phone', default_renderer),
    ('Отрасль', 'chosen_field', enum_renderer)
)


async def profile_kb(client_id):
    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == client_id))).scalar()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(*[InlineKeyboardButton(title, callback_data=f'{key}|{client.id}') for title, key, _ in PROFILE_FIELDS])
        message = ''
        for title, key, renderer in PROFILE_FIELDS:
            message += '✅' if getattr(client, key) else '✍️'
            message += ' ' + title + ':' + ' ' + await renderer(client, key) + '\n'

        return tuple((message, kb))


@dp.callback_query_handler(lambda x: 'profile|' in x.data)
async def my_profile(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')

    info, kb = await profile_kb(client_id)

    await bot.send_message(cb.from_user.id, info, reply_markup=kb)


@dp.callback_query_handler(lambda x: 'first_name|' in x.data)
async def change_first_name(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')
    async with state.proxy() as data:
        data['client_id'] = client_id
        data['message_id'] = cb.message.message_id

    await bot.edit_message_text(
        'Укажите новое имя',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=None
    )
    await ProfileChange.first_name.set()


@dp.message_handler(state=ProfileChange.first_name)
async def set_name(message: types.Message, state: FSMContext):
    data = await state.get_data()

    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == data['client_id']))).scalar()
        client.first_name = message.text
        await session.commit()

    info, kb = await profile_kb(data['client_id'])

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(lambda x: 'last_name|' in x.data)
async def change_last_name(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')
    async with state.proxy() as data:
        data['client_id'] = client_id
        data['message_id'] = cb.message.message_id

    await bot.edit_message_text(
        'Укажите фамилию',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=None
    )
    await ProfileChange.last_name.set()


@dp.message_handler(state=ProfileChange.last_name)
async def set_last_name(message: types.Message, state: FSMContext):
    data = await state.get_data()

    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == data['client_id']))).scalar()
        client.last_name = message.text
        await session.commit()

    info, kb = await profile_kb( data['client_id'])

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(lambda x: 'language_type|' in x.data)
async def change_lang(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')
    async with state.proxy() as data:
        data['client_id'] = client_id
        data['message_id'] = cb.message.message_id

    kb = InlineKeyboardMarkup()

    kb.add(*[InlineKeyboardButton(name.capitalize(), callback_data=f'lang|{member.value}')
             for name, member in StudentTable.LanguageType.__members__.items()])

    await bot.edit_message_text(
        'Выберите язык',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await ProfileChange.lang.set()


@dp.callback_query_handler(lambda x: 'lang|' in x.data, state=ProfileChange.lang)
async def set_lang(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, lang = cb.data.split('|')
    data = await state.get_data()
    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == data['client_id']))).scalar()
        client.language_type = lang
        await session.commit()

    info, kb = await profile_kb(data['client_id'])
    await bot.edit_message_text(
        info,
        cb.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(lambda x: 'phone|' in x.data)
async def change_phone(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')
    async with state.proxy() as data:
        data['client_id'] = client_id
        data['message_id'] = cb.message.message_id

    await bot.edit_message_text(
        'Укажите телефон',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=None
    )
    await ProfileChange.phone.set()


@dp.message_handler(state=ProfileChange.phone)
async def set_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()

    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == data['client_id']))).scalar()
        client.phone = message.text
        await session.commit()

    info, kb = await profile_kb(data['client_id'])

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(lambda x: 'chosen_field|' in x.data)
async def change_field(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')
    async with state.proxy() as data:
        data['client_id'] = client_id
        data['message_id'] = cb.message.message_id

    kb = InlineKeyboardMarkup()

    kb.add(*[InlineKeyboardButton(name.capitalize(), callback_data=f'field|{member.value}')
             for name, member in CategoryType.__members__.items()])

    await bot.edit_message_text(
        'Выберите направление',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await ProfileChange.field.set()


@dp.callback_query_handler(lambda x: 'field|' in x.data, state=ProfileChange.field)
async def set_field(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, field = cb.data.split('|')
    data = await state.get_data()
    async with SessionLocal() as session:
        client = (await session.execute(
            select(StudentTable).where(StudentTable.id == data['client_id']))).scalar()
        client.chosen_field = field
        await session.commit()

    info, kb = await profile_kb(data['client_id'])
    await bot.edit_message_text(
        info,
        cb.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()
