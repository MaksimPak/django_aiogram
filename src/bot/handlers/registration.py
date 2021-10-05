import re
from collections import deque
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from geoalchemy2 import WKTElement

from bot import repository as repo
from bot.db.config import SessionLocal
from bot.db.schemas import StudentTable
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.serializers import KeyboardGenerator
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


async def save_games(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext
):
    game = None
    if isinstance(response, types.CallbackQuery) and re.match(r'^data\|game\|[\w ]+', response.data):
        game = response.data.split('|')[-1]
    elif isinstance(response, types.Message):
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
async def save_phone(
        response: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    is_phone_exists = await repo.StudentRepository.is_exist('phone', response.text, session)
    if is_phone_exists:
        return await response.reply('Данный номер уже используется')
    await save_answer(response, state)


async def save_location(response, state: FSMContext):
    if isinstance(response, types.Message) and response.location:
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
        user_id: int,
        state: FSMContext,
        session: SessionLocal
):
    prefix = 'RegistrationState:'
    contact = await repo.ContactRepository.get('tg_id', user_id, session)
    data = await state.get_data()
    location = None
    if data.get('location'):
        location = WKTElement(F'POINT({data["location"]["longitude"]} {data["location"]["latitude"]})')
    lead_data = {
        'first_name': data[f'{prefix}first_name'],
        'city':  data[f'{prefix}city'],
        'language_type': data[f'{prefix}lang'],
        'phone': data[f'{prefix}phone'],
        'application_type': StudentTable.ApplicationType.telegram,
        'is_client': False,
        'contact_id': contact.id,
        'games': data[f'{prefix}games'],
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


async def ask_first_name(
        cb: types.CallbackQuery,
        state: FSMContext
):
    msg = await cb.message.edit_text(_('Как тебя зовут?'))
    await state.update_data({'msg_id': msg.message_id})


async def ask_city(msg: types.Message, state: FSMContext):

    async with state.proxy() as data:
        msg = await bot.edit_message_text(_('Отлично, теперь напиши из какого ты города'),
                                          msg.from_user.id, data['msg_id'])
        data['msg_id'] = msg.message_id


async def ask_games(
        response: types.Message,
        state: FSMContext
):
    games_list = ['PUBG', 'MineCraft', 'GTA', 'FIFA', 'CS:GO', 'ClashRoyale',
                  'Fortnite', 'Apex Legends', 'Valorant', 'Battlefield', 'Call Of Duty',
                  'Assassin\'s Creed', 'Need For Speed']

    data = [(game, ('game', game))
            for game in games_list]
    kb = KeyboardGenerator(data, row_width=3).keyboard
    async with state.proxy() as data:
        msg = await bot.edit_message_text(_('Выберите игры или впишите ответ вручную'),
                                          response.from_user.id,
                                          data['msg_id'],
                                          reply_markup=kb)
        data['msg_id'] = msg.message_id


async def ask_phone(
        response: types.CallbackQuery,
        state: FSMContext
):
    async with state.proxy() as data:
        msg = await bot.edit_message_text(_('Отправьте номер'),
                                          response.from_user.id,
                                          data['msg_id'],)
        data['msg_id'] = msg.message_id


async def ask_location(response: types.Message, state: FSMContext):
    data = [('Пропустить', ('skip_loc',)), ('Отправить', ('send_loc',))]  # naming

    kb = KeyboardGenerator(data).keyboard

    async with state.proxy() as data:
        msg = await bot.edit_message_text(_('отправить не отправить'),
                                          response.from_user.id,
                                          data['msg_id'],
                                          reply_markup=kb)
        data['msg_id'] = msg.message_id


async def game_handler(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext
):
    async def next_question():
        user_data = await state.get_data()
        await bot.edit_message_reply_markup(response.from_user.id, user_data['msg_id'])
        await RegistrationState.next()
        await ask_phone(response, state)

    if isinstance(response, types.Message):
        return await next_question()

    cb_value = response.data.split('|')[-1]

    if cb_value == 'continue':
        await next_question()
    else:
        kb = await mark_selected(
                cb_value,
                response.message.reply_markup.to_python()
            )
        await response.message.edit_reply_markup(kb)


async def location_handler(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext
):
    async def accept_loc():
        async with state.proxy() as data:
            msg = await bot.edit_message_text(_('Вышлите вашу геопозицию'),
                                              response.from_user.id,
                                              data['msg_id'],
                                              )
            data['msg_id'] = msg.message_id

    async def proceed():
        data = await state.get_data()
        await create_record(response.from_user.id, state)
        await bot.delete_message(response.from_user.id, data['msg_id'])
        await state.finish()

    location_mapper = {
        'send_loc': accept_loc,
        'skip_loc': proceed
    }

    if isinstance(response, types.Message) and response.location:
        await proceed()

    if isinstance(response, types.CallbackQuery):
        cb_value = response.data.split('|')[-1]
        await location_mapper[cb_value]()
        await state.update_data({'msg_id': response.message.message_id})


async def next_state(state: FSMContext):
    data = await state.get_data()
    state = await state.get_state()
    if data.get(state):
        await RegistrationState.next()


async def get_message_id(msg):
    if isinstance(msg, types.Message):
        return msg.message_id
    elif isinstance(msg, types.CallbackQuery):
        return msg.message.message_id


async def delete_msg(msg):
    if isinstance(msg, types.Message):
        await msg.delete()
    elif isinstance(msg, types.CallbackQuery):
        await msg.message.delete()


QUESTION_MAP = {
    'invite_link': (...,),
    'lang': (save_answer, ask_first_name, next_state, [types.CallbackQuery]),
    'first_name': (save_answer, ask_city, next_state, [types.Message]),
    'city': (save_answer, ask_games, next_state, [types.Message]),
    'games': (save_games, game_handler, None, [types.CallbackQuery, types.Message]),
    'phone': (save_phone, ask_location, next_state, [types.Message]),
    'location': (save_location, location_handler, None, [types.CallbackQuery, types.Message]),
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
    user_response: Union[types.CallbackQuery, types.Message],
    state: FSMContext
):
    if isinstance(user_response, types.CallbackQuery):
        await bot.answer_callback_query(user_response.id)

    current_state = (await state.get_state()).split(':')[-1]
    set_answer, next_question, set_state, available_types = QUESTION_MAP[current_state]

    # Pycharm triggers error when accessing elements through [],
    # assuming incorrect comparison with typing module
    # https://youtrack.jetbrains.com/issue/PY-36317
    if type(user_response) in available_types:
        await set_answer(user_response, state)
        await next_question(user_response, state)
        if set_state:
            await set_state(state)

    if isinstance(user_response, types.Message):
        await delete_msg(user_response)
