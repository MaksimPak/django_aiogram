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


async def games_continue(
        cb: types.CallbackQuery,
):
    await cb.answer()
    await cb.message.edit_reply_markup(None)
    await cb.message.reply('Отправьте номер')

    await RegistrationState.phone.set()


async def games_custom_answer(
        cb: types.CallbackQuery,
):
    await cb.answer()
    await cb.message.reply('Отправьте игру')


async def games_get_text(
        message: types.Message,
        state: FSMContext
):
    await state.reset_state(False)
    async with state.proxy() as data:
        if data.get('games') and message.text not in data.get('games'):
            data['games'].append(message.text)
        else:
            data['games'] = [message.text]
    await message.reply('Отправьте номер')
    await RegistrationState.phone.set()


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
        cb: types.CallbackQuery,
        game,
        keyboard: InlineKeyboardMarkup
):
    kb = await mark_selected(
        game,
        keyboard.to_python()
    )

    await cb.message.edit_reply_markup(kb)


async def games_get_inline(
        cb: types.CallbackQuery,
        state: FSMContext
):
    await cb.answer()

    game = cb.data.split('|')[-1]
    async with state.proxy() as data:
        if data.get('games') and game not in data.get('games'):
            data['games'].append(game)
        else:
            data['games'] = [game]

    await process_multianswer(cb, game, cb.message.reply_markup)


async def games_fsm_resolver(
        cb: types.CallbackQuery,
        match: str,
        state: FSMContext
):
    if match == 'get_text' or match == 'game':
        await GAMES_HELPER[match](cb, state)
    else:
        await GAMES_HELPER[match](cb)


GAMES_HELPER = {
    'get_text': games_get_text,
    'game': games_get_inline,
    'continue': games_continue,
    'custom_answer': games_custom_answer,
}


async def set_lang(
        cb: types.CallbackQuery,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    async with state.proxy() as data:
        data['lang'] = cb.data.split('|')[-1]

    await bot.send_message(cb.from_user.id, _('Как тебя зовут?'))
    await RegistrationState.first_name.set()


async def set_first_name(
        message: types.Message,
        state: FSMContext
):
    async with state.proxy() as data:
        data['first_name'] = message.text

    await message.reply(_('Отлично, теперь напиши из какого ты города'))
    await RegistrationState.city.set()


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
        data['phone'] = message.text

    data = [('Пропустить', ('skip_loc',)), ('Отправить', ('send_loc',))]

    kb = KeyboardGenerator(data).keyboard
    await message.reply(_('отправить не отправить'), reply_markup=kb)
    await RegistrationState.location.set()


async def send_loc(
        cb: types.CallbackQuery,
):
    await cb.message.reply('Вышлите вашу геопозицию')
    await RegistrationState.location.set()


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


async def dismiss_loc(
        cb: types.CallbackQuery,
        state: FSMContext,
):
    await create_record(cb.from_user.id, state)


async def games_cb_handler(
        cb: types.CallbackQuery,
        state: FSMContext
):
    match = re.match(r'^data\|(\w+)(?:\|[\w ]*)?', cb.data)
    await games_fsm_resolver(cb, match.group(1), state)


async def set_games(
        response: Union[types.CallbackQuery, types.Message],
        state: FSMContext
):
    if type(response) is types.CallbackQuery:
        await games_cb_handler(response, state)
    else:
        await GAMES_HELPER['get_text'](response, state)

LOCATION_HELPER = {
    'send_loc': send_loc,
    'skip_loc': dismiss_loc,
    'accept_loc': set_loc
}


async def location_fsm_resolver(
        cb: types.CallbackQuery,
        state: FSMContext
):
    cb_data = cb.data.split('|')[-1]

    if cb_data == 'skip_loc':
        await LOCATION_HELPER[cb_data](cb, state)
    else:
        await LOCATION_HELPER[cb_data](cb)


async def set_location(
        response: Union[types.CallbackQuery, types.Message],
        state: FSMContext
):
    if type(response) is types.CallbackQuery:
        await location_fsm_resolver(response, state)
    else:
        await LOCATION_HELPER['accept_loc'](response, state)


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
    await state.finish()


QUESTION_MAP = {
    'RegistrationState:invite_link': (...,),
    'RegistrationState:lang': set_lang,
    'RegistrationState:first_name': set_first_name,
    'RegistrationState:city': set_city,
    'RegistrationState:games': set_games,
    'RegistrationState:phone': set_phone,
    'RegistrationState:location': set_location,
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
    data = await state.get_data()
    current_state = await state.get_state()

    answer_handler = QUESTION_MAP[current_state]
    await answer_handler(response, state)
