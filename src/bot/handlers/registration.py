from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from geoalchemy2 import WKTElement

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.db.schemas import StudentTable
from bot.db.config import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data, simple_data
from bot.utils.throttling import throttled

_ = i18n.gettext


class RegistrationState(StatesGroup):
    invite_link = State()
    lang = State()
    first_name = State()
    city = State()
    games = State()
    phone = State()
    location = State()


@dp.message_handler(state=RegistrationState.location, content_types=ContentType.LOCATION)
async def set_loc(
        message: types.Message,
        state: FSMContext,
):
    async with state.proxy() as data:
        data['location'] = {
            'longitude': message.location.longitude,
            'latitude': message.location.latitude
        }

    await create_record(message.from_user.id, state)


@dp.message_handler(state=RegistrationState.phone)
@create_session
async def set_phone(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    is_phone_exists = await repo.StudentRepository.is_exist('phone', message.text, session)
    if is_phone_exists:
        return await message.reply('Данный номер уже используется')

    async with state.proxy() as data:
        print(data)
        data['phone'] = message.text

    data = [('Пропустить', ('skip_loc',)), ('Отправить', ('send_loc',))]

    kb = KeyboardGenerator(data).keyboard
    await message.reply(_('отправить не отправить'), reply_markup=kb)


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


@dp.message_handler(state=RegistrationState.city)
async def set_city(
        message: types.Message,
        state: FSMContext
):
    async with state.proxy() as data:
        data['city'] = message.text

    games_list = ['PUBG', 'MineCraft', 'GTA', 'FIFA', 'CS:GO', 'ClashRoyale',
                  'Fortnite', 'Apex Legends', 'Valorant', 'Battlefield', 'Call Of Duty',
                  'Assassin\'s Creed', 'Need For Speed']

    data = [(game, ('game', game))
            for game in games_list]
    kb = KeyboardGenerator(data, row_width=3).add(('Svoi otvet', ('custom_answer',))).keyboard
    await message.reply(_('Хорошо, выбирай игры'), reply_markup=kb)
    await RegistrationState.games.set()


@dp.message_handler(commands=['register'])
@dp.callback_query_handler(simple_data.filter(value='tg_reg'))
@create_session
async def tg_reg(
        response: Union[types.CallbackQuery, types.Message],
        session: SessionLocal
):
    if type(response) == types.CallbackQuery:
        await response.answer()
    contact = await repo.ContactRepository.get('tg_id', response.from_user.id, session)
    if contact.student:
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


async def mark_selected(
        game: str,
        keyboard: dict
):
    # todo REFACTOR
    for row in keyboard['inline_keyboard']:
        for key in row:
            game_name = key['callback_data'].split('|')[-1]
            if key['text'][0] != '✅' and game == game_name:
                key['text'] = '✅ ' + key['text']
            elif key['text'][0] == '✅' and game == game_name:
                key['text'] = key['text'][1:]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard['inline_keyboard'])
    if keyboard.inline_keyboard[-1][-1].text != 'Следующий вопрос ➡️':
        keyboard.add(InlineKeyboardButton(text='Следующий вопрос ➡️', callback_data='data|continue'))

    return keyboard


async def process_multianswer(
        cb,
        game,
        keyboard: InlineKeyboardMarkup
):
    kb = await mark_selected(
        game,
        keyboard.to_python()
    )

    await cb.message.edit_reply_markup(kb)


@dp.callback_query_handler(short_data.filter(property='game'), state=RegistrationState.games)
@dp.throttled(throttled, rate=.7)
async def get_inline_answer(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict = None
):
    await cb.answer()
    game = callback_data['value']
    async with state.proxy() as data:
        if data.get('games') and game not in data.get('games'):
            data['games'].append(game)
        else:
            data['games'] = [game]

    await process_multianswer(cb, game, cb.message.reply_markup)


@dp.callback_query_handler(simple_data.filter(value='custom_answer'), state=RegistrationState.games)
@dp.throttled(throttled, rate=.7)
async def get_inline_answer(
        cb: types.CallbackQuery,
):

    await cb.answer()
    await cb.message.reply('отправьте игру')


@dp.message_handler(state=RegistrationState.games)
async def get_text_answer(
        message: types.Message,
        state: FSMContext
):
    await state.reset_state(False)
    async with state.proxy() as data:
        if data.get('games') and message.text not in data.get('games'):
            data['games'].append(message.text)
        else:
            data['games'] = [message.text]

    await message.reply('отправьте номер')

    await RegistrationState.phone.set()


@dp.callback_query_handler(simple_data.filter(value='continue'), state=RegistrationState.games)
@dp.throttled(throttled, rate=.7)
async def next_question(
        cb: types.CallbackQuery
):
    await cb.answer()
    await cb.message.edit_reply_markup(None)

    await cb.message.reply('отправьте номер')

    await RegistrationState.phone.set()




@dp.callback_query_handler(simple_data.filter(value='send_loc'), state='*')
async def accept_loc(
        cb: types.CallbackQuery,
):
    await cb.message.reply('go send it')
    await RegistrationState.location.set()


@dp.callback_query_handler(simple_data.filter(value='skip_loc'), state='*')
async def dismiss_loc(
        cb: types.CallbackQuery,
        state: FSMContext,
):
    await create_record(cb.from_user.id, state)



@create_session
async def create_record(
        user_id,
        state: FSMContext,
        session: SessionLocal
):
    contact = await repo.ContactRepository.get('tg_id', user_id, session)
    data = await state.get_data()
    location = None
    if data.get('location'):
        location = WKTElement(F'POINT({data["location"]["longitude"]} {data["location"]["latitude"]})')
    lead_data = {
        'first_name': data['first_name'],
        'city': data['city'],
        'tg_id': user_id,
        'language_type': data['lang'],
        'phone': data['phone'],
        'application_type': StudentTable.ApplicationType.telegram,
        'is_client': False,
        'contact_id': contact.id,
        'games': data['games'],
        'location': location,
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
    await bot.send_message(user_id, _('Вы зарегистрированы! В ближайшее время с вами свяжется наш оператор'),
                           reply_markup=reply_kb)
    await state.finish()
