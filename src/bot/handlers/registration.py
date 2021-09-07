from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.models.dashboard import StudentTable
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data, simple_data

_ = i18n.gettext


class RegistrationState(StatesGroup):
    invite_link = State()
    lang = State()
    first_name = State()
    city = State()
    phone = State()


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), state=RegistrationState.invite_link)
@create_session
async def check_invite_code(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    student = await repo.StudentRepository.get('unique_code', message.text, session)
    if student:
        await repo.StudentRepository.edit(student, {'tg_id': message.from_user.id}, session)
        await message.reply(('Спасибо {first_name},'
                             ' вы были успешно'
                             ' зарегистрированы в боте').format(first_name=message.from_user.first_name))
        await state.finish()
    else:
        await message.reply(_('Неверный инвайт код'))


@dp.message_handler(commands=['register'])
@dp.callback_query_handler(simple_data.filter(value='tg_reg'))
@create_session
async def tg_reg(
        response: Union[types.CallbackQuery, types.Message],
        session: SessionLocal
):
    if type(response) == types.CallbackQuery:
        await response.answer()
    client = await repo.StudentRepository.get('tg_id', response.from_user.id, session)
    if client:
        return await bot.send_message(
            response.from_user.id,
            'Вы уже зарегистрированы'
        )
    data = [(name.capitalize(), ('lang', member.value))
            for name, member in StudentTable.LanguageType.__members__.items()]

    kb = KeyboardGenerator(data).keyboard

    await bot.send_message(
        response.from_user.id,
        _('Регистрация в боте MegaSkill.\n'
          'Выберите язык:'),
        reply_markup=kb
    )
    await RegistrationState.lang.set()


@dp.callback_query_handler(short_data.filter(property='lang'), state=RegistrationState.lang)
async def set_lang(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict
):
    await bot.answer_callback_query(cb.id)
    lang = callback_data['value']

    async with state.proxy() as data:
        data['lang'] = lang

    await bot.send_message(cb.from_user.id, _('Как тебя зовут?'))
    await RegistrationState.first_name.set()


@dp.message_handler(state=RegistrationState.first_name)
async def set_first_name(
        message: types.Message,
        state: FSMContext
):
    async with state.proxy() as data:
        data['first_name'] = message.text

    await message.reply(_('Отлично, теперь напиши из какого ты города'))
    await RegistrationState.city.set()


@dp.message_handler(state=RegistrationState.city)
async def set_first_name(
        message: types.Message,
        state: FSMContext
):
    async with state.proxy() as data:
        data['city'] = message.text

    await message.reply(_('Хорошо, теперь пожалуйста отправь свой номер'))
    await RegistrationState.phone.set()


@dp.message_handler(state=RegistrationState.phone)
@create_session
async def create_record(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    is_phone_exists = await repo.StudentRepository.is_exist('phone', message.text, session)
    if is_phone_exists:
        return await message.reply('Данный номер уже используется')
    async with state.proxy() as data:
        data['phone'] = message.text

    contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
    data = await state.get_data()
    lead_data = {
        'first_name': data['first_name'],
        'city': data['city'],
        'tg_id': message.from_user.id,
        'language_type': data['lang'],
        'phone': data['phone'],
        'application_type': StudentTable.ApplicationType.telegram,
        'is_client': False,
        'contact_id': contact.id,
    }
    if contact:
        lead_data['promo_id'] = contact.data.get('promo')

    student = await repo.StudentRepository.create(lead_data, session)
    await repo.ContactRepository.edit(contact, {
        'is_registered': True
    }, session)

    if contact.data.get('courses'):
        await repo.StudentCourseRepository.bunch_create(student.id, contact.data['courses'], session)

    reply_kb = await KeyboardGenerator.main_kb()
    await bot.send_message(message.from_user.id, _('Вы зарегистрированы! В ближайшее время с вами свяжется наш оператор'),
                           reply_markup=reply_kb)
    await state.finish()
