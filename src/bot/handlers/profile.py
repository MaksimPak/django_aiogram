import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot import repository as repo
from bot.db.config import SessionLocal
from bot.db.schemas import StudentTable
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data

_ = i18n.gettext

PHONE_PATTERN = re.compile(r'\+998[0-9]{9}')


@create_session
async def phone_checker(user_response, session):
    is_correct_format = re.match(PHONE_PATTERN, user_response.text)

    if not is_correct_format:
        raise ValueError(_('Неправильный формат телефона. Пример: +998000000000'))

    is_phone_exists = await repo.StudentRepository.is_exist('phone', user_response.text, session)
    if is_phone_exists:
        raise ValueError(_('Данный номер уже используется'))


class ProfileChange(StatesGroup):
    first_name = State()
    last_name = State()
    lang = State()
    phone = State()
    city = State()


async def default_renderer(client, key):
    return str(getattr(client, key)) if getattr(client, key) else ''


async def enum_renderer(client, key):
    return StudentTable.LanguageType(client.contact.data.get(key, StudentTable.LanguageType.ru)).name


async def model_renderer(client, key, model_key):
    instance = getattr(client, key)
    if instance:
        return getattr(getattr(client, key), model_key)


async def lc_renderer(client, key):
    lc = await model_renderer(client, key, 'title')
    return lc if lc else _('Не указано')

PROFILE_FIELDS = (
    (_('Имя'), 'first_name', default_renderer),
    (_('Фамилия'), 'last_name', default_renderer),
    (_('Язык'), 'lang', enum_renderer),
    (_('Телефон'), 'phone', default_renderer),
    (_('Город'), 'city', default_renderer),
)


async def profile_kb(
        client: StudentTable,
):
    """
    Renders Student information in message and adds keyboard for edit
    """

    data = [(title, (key, client.id)) for title, key, _tmp in PROFILE_FIELDS]

    kb = KeyboardGenerator(data, row_width=2).keyboard
    ro_fields = [(_('Учебный центр'), 'learning_centre', lc_renderer)]
    message = ''
    fields = (*PROFILE_FIELDS, *ro_fields)
    for title, key, renderer in fields:
        message += title + ':' + ' ' + await renderer(client, key) + '\n'

    return message, kb


@dp.message_handler(Text(equals='🧑‍🎓 Профиль'), state='*')
@create_session
async def my_profile(
        message: types.Message,
        session: SessionLocal,
        state: FSMContext
):
    """
    Starting point for profile view/edit
    """
    await state.reset_state()
    contact = await repo.ContactRepository.load_student_data('tg_id', message.from_user.id, session)
    kb = KeyboardGenerator([(_('Регистрация'), ('tg_reg',))]).keyboard
    if not contact.student:
        return await message.reply(
            _('<i>Ваш статус: Незарегистрированный пользователь.\n</i>' 
              '<i>Зарегистрируйтесь и получите больше возможностей.</i>'),
            parse_mode='html',
            reply_markup=kb
            )

    async with session:
        session.add(contact)
        await session.refresh(contact)
        info, kb = await profile_kb(contact.student)

    await message.reply(info, reply_markup=kb)


@dp.callback_query_handler(short_data.filter(property='first_name'))
async def change_first_name(
        cb: types.callback_query,
        state: FSMContext,
):
    """
    Asks student for new first_name
    """
    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['message_id'] = cb.message.message_id

    await bot.edit_message_text(
        _('Укажите имя'),
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
        session: SessionLocal
):
    """
    Saves new first_name into db
    """
    data = await state.get_data()

    contact = await repo.ContactRepository.load_student_data('tg_id', message.from_user.id, session)
    await repo.StudentRepository.edit(contact.student, {'first_name': message.text}, session)

    async with session:
        session.add(contact)
        await session.refresh(contact)
        info, kb = await profile_kb(contact.student)

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
        state: FSMContext
):
    """
    Asks student for new last_name
    """
    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['message_id'] = cb.message.message_id

    await bot.edit_message_text(
        _('Укажите фамилию'),
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
        session: SessionLocal
):
    """
    Saves last_name into db
    """
    data = await state.get_data()
    contact = await repo.ContactRepository.load_student_data('tg_id', message.from_user.id, session)
    await repo.StudentRepository.edit(contact.student, {'last_name': message.text}, session)

    async with session:
        session.add(contact)
        await session.refresh(contact)
        info, kb = await profile_kb(contact.student)

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(short_data.filter(property='lang'))
async def change_lang(
        cb: types.callback_query,
        state: FSMContext
):
    """
    Asks student for new lang
    """
    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['message_id'] = cb.message.message_id

    data = [(name.capitalize(), ('lang', member.value))
            for name, member in StudentTable.LanguageType.__members__.items()]
    kb = KeyboardGenerator(data).keyboard
    await bot.edit_message_text(
        _('Выберите язык'),
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
        callback_data: dict
):
    """
    Saves new lang into db
    """
    await bot.answer_callback_query(cb.id)
    lang = callback_data['value']

    data = await state.get_data()

    contact = await repo.ContactRepository.load_student_data('tg_id', cb.from_user.id, session)
    contact.data['lang'] = lang

    async with session:
        session.add(contact)
        await session.commit()
        info, kb = await profile_kb(contact.student)

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
        state: FSMContext
):
    """
    Asks student for new phone
    """
    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['message_id'] = cb.message.message_id

    await bot.edit_message_text(
        _('Укажите телефон'),
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
        session: SessionLocal
):
    """
    Saves phone into db
    """
    data = await state.get_data()
    contact = await repo.ContactRepository.load_student_data('tg_id', message.from_user.id, session)
    try:
        await phone_checker(message)
    except ValueError as e:
        return await bot.send_message(message.from_user.id, e)

    await repo.StudentRepository.edit(contact.student, {'phone': message.text}, session)

    async with session:
        session.add(contact)
        await session.refresh(contact)
        info, kb = await profile_kb(contact.student)

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()


@dp.callback_query_handler(short_data.filter(property='city'))
async def change_city(
        cb: types.callback_query,
        state: FSMContext
):
    """
    Asks student for new first_name
    """
    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['message_id'] = cb.message.message_id

    await bot.edit_message_text(
        _('Укажите город проживания'),
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=None
    )
    await ProfileChange.city.set()


@dp.message_handler(state=ProfileChange.city)
@create_session
async def set_city(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    """
    Saves phone into db
    """
    data = await state.get_data()

    contact = await repo.ContactRepository.load_student_data('tg_id', message.from_user.id, session)

    await repo.StudentRepository.edit(contact.student, {'city': message.text}, session)

    async with session:
        session.add(contact)
        await session.refresh(contact)
        info, kb = await profile_kb(contact.student)

    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.edit_message_text(
        info,
        message.from_user.id,
        data['message_id'],
        reply_markup=kb
    )
    await state.finish()
