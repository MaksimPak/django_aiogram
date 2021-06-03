from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton

from bot import repository as repo
from bot.decorators import create_session
from bot.helpers import make_kb
from bot.misc import dp, bot
from bot.models.dashboard import StudentTable, CategoryType
from bot.models.db import SessionLocal
from bot.utils.callback_settings import short_data


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


@create_session
async def profile_kb(
        client_tg: int,
        session: SessionLocal
):
    """
    Renders Student information in message and adds keyboard for edit
    """
    client = await repo.StudentRepository.get('tg_id', int(client_tg), session)

    kb = await make_kb([InlineKeyboardButton(title, callback_data=short_data.new(property=key, value=client.id))
                        for title, key, _ in PROFILE_FIELDS], row_width=2)
    message = ''
    for title, key, renderer in PROFILE_FIELDS:
        message += '✅' if getattr(client, key) else '✍️'
        message += ' ' + title + ':' + ' ' + await renderer(client, key) + '\n'

    kb.add(InlineKeyboardButton('Назад', callback_data=short_data.new(property='back', value=client.id)))
    return message, kb


@dp.message_handler(commands=['profile'], commands_prefix='/')
@dp.callback_query_handler(short_data.filter(property='student'))
async def my_profile(
        payload: Union[types.CallbackQuery, types.Message],
        callback_data: dict = None
):
    """
    Starting point for profile view/edit
    """
    isinstance(payload, types.CallbackQuery) and await bot.answer_callback_query(payload.id)
    client_tg = payload.from_user.id
    message_id = payload.message.message_id if isinstance(payload, types.CallbackQuery) else payload.message_id

    # client_id = callback_data['value']

    info, kb = await profile_kb(client_tg)

    if isinstance(payload, types.CallbackQuery):
        await bot.edit_message_text(
            info,
            client_tg,
            message_id,
            reply_markup=kb
        )
    else:
        await payload.reply(info, reply_markup=kb)


@dp.callback_query_handler(short_data.filter(property='first_name'))
async def change_first_name(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Asks student for new first_name
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

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
@create_session
async def set_name(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    """
    Saves new first_name into db
    """
    data = await state.get_data()

    client = await repo.StudentRepository.get('id', int(data['client_id']), session)
    await repo.StudentRepository.edit(client, {'first_name': message.text}, session)

    info, kb = await profile_kb(data['client_id'])

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(short_data.filter(property='last_name'))
async def change_last_name(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Asks student for new last_name
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

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
@create_session
async def set_last_name(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    """
    Saves last_name into db
    """
    data = await state.get_data()
    client = await repo.StudentRepository.get('id', int(data['client_id']), session)
    await repo.StudentRepository.edit(client, {'last_name': message.text}, session)

    info, kb = await profile_kb(data['client_id'])

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(short_data.filter(property='language_type'))
async def change_lang(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Asks student for new lang
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

    async with state.proxy() as data:
        data['client_id'] = client_id
        data['message_id'] = cb.message.message_id

    kb = await make_kb([InlineKeyboardButton(name.capitalize(), callback_data=short_data.new(property='lang',
                                                                                             value=member.value))
                        for name, member in StudentTable.LanguageType.__members__.items()])
    await bot.edit_message_text(
        'Выберите язык',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await ProfileChange.lang.set()


@dp.callback_query_handler(short_data.filter(property='lang'), state=ProfileChange.lang)
@create_session
async def set_lang(
        cb: types.callback_query,
        state: FSMContext,
        session: SessionLocal,
        callback_data: dict,
        **kwargs
):
    """
    Saves new lang into db
    """
    await bot.answer_callback_query(cb.id)
    lang = callback_data['value']

    data = await state.get_data()

    client = await repo.StudentRepository.get('id', int(data['client_id']), session)
    await repo.StudentRepository.edit(client, {'language_type': lang}, session)

    info, kb = await profile_kb(data['client_id'])
    await bot.edit_message_text(
        info,
        cb.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(short_data.filter(property='phone'))
async def change_phone(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Asks student for new phone
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

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
@create_session
async def set_phone(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    """
    Saves phone into db
    """
    data = await state.get_data()

    client = await repo.StudentRepository.get('id', int(data['client_id']), session)
    await repo.StudentRepository.edit(client, {'phone': message.text}, session)

    info, kb = await profile_kb(data['client_id'])

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(short_data.filter(property='chosen_field'))
async def change_field(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Asks student for new field
    """
    await bot.answer_callback_query(cb.id)
    client_id = callback_data['value']

    async with state.proxy() as data:
        data['client_id'] = client_id
        data['message_id'] = cb.message.message_id

    kb = await make_kb([InlineKeyboardButton(name.capitalize(), callback_data=short_data.new(
        property='field', value=member.value))
                        for name, member in CategoryType.__members__.items()])

    await bot.edit_message_text(
        'Выберите направление',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await ProfileChange.field.set()


@dp.callback_query_handler(short_data.filter(property='field'), state=ProfileChange.field)
@create_session
async def set_field(
        cb: types.callback_query,
        state: FSMContext,
        session: SessionLocal,
        callback_data: dict,
        **kwargs
):
    """
    Saves field into db
    """
    await bot.answer_callback_query(cb.id)
    field = callback_data['value']

    data = await state.get_data()

    client = await repo.StudentRepository.get('id', int(data['client_id']), session)
    await repo.StudentRepository.edit(client, {'chosen_field': field}, session)

    info, kb = await profile_kb(data['client_id'])
    await bot.edit_message_text(
        info,
        cb.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()
