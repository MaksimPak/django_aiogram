import re
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


async def save_answer(
    response: Union[types.Message, types.CallbackQuery],
    state: FSMContext
):
    if type(response) is types.CallbackQuery:
        answer = response.data.split('|')[-1]
    else:
        answer = response.text

    key = await state.get_state()
    async with state.proxy() as data:
        data[key] = answer


async def save_games(response: Union[types.Message, types.CallbackQuery], state: FSMContext):
    game = None
    if type(response) is types.CallbackQuery and re.match(r'^data\|game\|[\w ]+', response.data):
        game = response.data.split('|')[-1]
    elif type(response) is types.Message:
        game = response.text

    if game:
        current_state = await state.get_state()
        async with state.proxy() as data:
            if data.get(current_state) and game not in data.get(current_state):
                data[current_state].append(game)
            elif data.get(current_state) and game in data.get(current_state):
                data.get(current_state).remove(game)
            else:
                data[current_state] = [game]


@create_session
async def save_phone(response, state, session):
    is_phone_exists = await repo.StudentRepository.is_exist('phone', response.text, session)
    if is_phone_exists:
        return await response.reply('Данный номер уже используется')
    await save_answer(response, state)


async def save_location(response, state):
    if response.location:
        async with state.proxy() as data:
            data['location'] = {
                'longitude': response.location.longitude,
                'latitude': response.location.latitude
            }


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
        'language_type': data['lang'],
        'phone': data['phone'],
        'application_type': StudentTable.ApplicationType.telegram,
        'is_client': False,
        'contact_id': contact.id,
        'games': data['games'],
        'location': location,
    }

    student = await repo.StudentRepository.create(lead_data, session)
    await repo.ContactRepository.edit(contact, {
        'is_registered': True
    }, session)

    if contact.data.get('courses'):
        await repo.StudentCourseRepository.bunch_create(student.id, contact.data['courses'], session)

    reply_kb = await KeyboardGenerator.main_kb()
    await bot.send_message(user_id, _('Вы зарегистрированы! В ближайшее время с вами свяжется наш оператор'),
                           reply_markup=reply_kb)


async def ask_first_name(response):
    await bot.send_message(response.from_user.id, _('Как тебя зовут?'))


async def ask_city(response):
    await bot.send_message(response.from_user.id, _('Отлично, теперь напиши из какого ты города'))


async def ask_games(response):
    games_list = ['PUBG', 'MineCraft', 'GTA', 'FIFA', 'CS:GO', 'ClashRoyale',
                  'Fortnite', 'Apex Legends', 'Valorant', 'Battlefield', 'Call Of Duty',
                  'Assassin\'s Creed', 'Need For Speed']

    data = [(game, ('game', game))
            for game in games_list]
    kb = KeyboardGenerator(data, row_width=3).add(('Svoi otvet', ('custom_answer',))).keyboard
    await bot.send_message(response.from_user.id, _('Хорошо, выбирай игры'), reply_markup=kb)


async def ask_phone(response):
    await bot.send_message(response.from_user.id, _('Отправьте номер'))


async def ask_location(response):
    data = [('Пропустить', ('skip_loc',)), ('Отправить', ('send_loc',))]  # naming

    kb = KeyboardGenerator(data).keyboard
    await bot.send_message(response.from_user.id, _('отправить не отправить'), reply_markup=kb)


async def game_handler(
        response: Union[types.Message, types.CallbackQuery]
):
    async def custom_answer():
        await response.message.reply('Отправьте игру')

    async def next_question():
        await bot.send_message(response.from_user.id, 'Send phone')

    if type(response) is types.Message:
        await RegistrationState.next()
        return await next_question()

    games_mapper = {
        'custom_answer': custom_answer,
        'continue': next_question
    }

    cb_value = response.data.split('|')[-1]

    if cb_value in games_mapper:
        await games_mapper[cb_value]()
    else:
        kb = await mark_selected(
                cb_value,
                response.message.reply_markup.to_python()
            )
        await response.message.edit_reply_markup(kb)


async def location_handler(response: Union[types.Message, types.CallbackQuery]):
    async def accept_loc():
        await response.message.reply('Вышлите вашу геопозицию')

    async def proceed():
        await create_record()

    location_mapper = {
        'send_loc': accept_loc,
        'skip_loc': proceed
    }

    if type(response) is types.Message:
        return proceed()

    cb_value = response.data.split('|')[-1]
    await location_mapper[cb_value]()


async def next_state(state: FSMContext):
    data = await state.get_data()
    state = await state.get_state()
    if data.get(state):
        await RegistrationState.next()


async def finish_state(state: FSMContext):
    await state.finish()


QUESTION_MAP = {
    'invite_link': (...,),
    'lang': (save_answer, ask_first_name, next_state),
    'first_name': (save_answer, ask_city, next_state),
    'city': (save_answer, ask_games, next_state),
    'games': (save_games, game_handler, None),
    'phone': (save_phone, ask_location, next_state),
    'location': (save_location, location_handler, finish_state),
}


@dp.message_handler(commands=['register'])
@create_session
async def entry_point(
        message: types.Message,
        session: SessionLocal
):
    contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
    if contact.student:
        return await bot.send_message(
            message.from_user.id,
            'Вы уже зарегистрированы'
        )

    data = [(name.capitalize(), ('lang', member.value))
            for name, member in StudentTable.LanguageType.__members__.items()]

    kb = KeyboardGenerator(data).keyboard

    await bot.send_message(
        message.from_user.id,
        _('Регистрация в боте MegaSkill.\n'
          'Выберите язык:'),
        reply_markup=kb
    )
    await RegistrationState.lang.set()


@dp.throttled(throttled, rate=.7)
@dp.message_handler(state=RegistrationState.states,
                    content_types=[types.ContentType.TEXT, types.ContentType.LOCATION])
@dp.callback_query_handler(state=RegistrationState.states)
async def process_handler(
    response: Union[types.CallbackQuery, types.Message],
    state: FSMContext
):
    if type(response) is types.CallbackQuery:
        await bot.answer_callback_query(response.id)

    current_state = (await state.get_state()).split(':')[-1]

    set_answer, next_question, set_state = QUESTION_MAP[current_state]
    await set_answer(response, state)
    await next_question(response)
    if set_state:
        await set_state(state)

    data = await state.get_data()
    print(data)
