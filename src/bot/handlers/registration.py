import re
from functools import partial
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, ChatTypeFilter
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from geoalchemy2 import WKTElement

from bot import repository as repo
from bot.db.config import SessionLocal
from bot.db.schemas import StudentTable
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import simple_data
from bot.utils.throttling import throttled

_ = i18n.gettext


class RegistrationState(StatesGroup):
    first_name = State()
    city = State()
    games = State()
    phone = State()
    location = State()


PHONE_PATTERN = re.compile(r'\+998[0-9]{9}')

GAMES_LIST = ['PUBG', 'MineCraft', 'GTA', 'FIFA', 'CS:GO', 'ClashRoyale',
              'Fortnite', 'Apex Legends', 'Valorant', 'Battlefield', 'Call Of Duty',
              'Assassin\'s Creed', 'Need For Speed']


async def save_answer(
    response: Union[types.Message, types.CallbackQuery],
    state: FSMContext
):
    """
    Default answer saver
    """
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
    """
    Game specific answer saver.
    """
    if hasattr(response, 'text'):
        game = response.text
    else:
        game = response.data.split('|')[-1]

    current_state = await state.get_state()
    async with state.proxy() as data:
        if data.get(current_state) and game not in data.get(current_state):
            # User already selected some games, append new
            data[current_state].append(game)
        elif data.get(current_state) and game in data.get(current_state):
            # User selected same game. Remove from list
            data.get(current_state).remove(game)
        else:
            # No list created. Put selected game to list
            data[current_state] = [game]


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
    """
    Prepends emoji symbol for selected button
    """
    # todo should be used as class serializer method
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
async def create_lead(
        user_id: int,
        state: FSMContext,
        session: SessionLocal
):
    """
    Gathers collected data and inserts record into database
    """
    prefix = 'RegistrationState:'
    contact = await repo.ContactRepository.get('tg_id', user_id, session)
    data = await state.get_data()
    location = None
    if data.get('location'):
        location = WKTElement(F'POINT({data["location"]["longitude"]} {data["location"]["latitude"]})')
    lead_data = {
        'first_name': data[f'{prefix}first_name'],
        'city':  data[f'{prefix}city'],
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
    await bot.send_message(user_id, _('Вы зарегистрированы! В ближайшее время'
                                      ' с вами свяжется наш оператор'),
                           reply_markup=reply_kb)


async def ask_first_name(
        user_response: types.CallbackQuery,
        state: FSMContext
):
    await bot.send_message(user_response.from_user.id, _('Как тебя зовут?'))


async def ask_city(user_response: types.Message, state: FSMContext):
    await bot.send_message(user_response.from_user.id,
                           _('Отлично, теперь напиши из какого ты города'))


async def ask_games(
        user_response: types.Message,
        state: FSMContext
):
    data = [(game, ('game', game))
            for game in GAMES_LIST]
    kb = KeyboardGenerator(data, row_width=3).keyboard
    msg = await bot.send_message(user_response.from_user.id,
                           _('Выберите игры или впишите ответ вручную'),
                           reply_markup=kb)

    await state.update_data({'msg_id': msg.message_id})


async def ask_phone(
        msg: types.Message,
        state: FSMContext
):
    await bot.send_message(msg.from_user.id, _('Отправьте номер'))


async def ask_location(msg: types.Message, state: FSMContext):
    data = [('Пропустить', ('skip_loc',)), ('Отправить', ('send_loc',))]
    kb = KeyboardGenerator(data).keyboard
    msg = await bot.send_message(msg.from_user.id,
                                 _('Отправьте локацию'),
                                 reply_markup=kb)

    await state.update_data({'msg_id': msg.message_id})


async def game_handler(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext
):
    """
    Resolves further instructions for game question.
    """
    async def next_question():
        """
        Proceed to the next question if user sent game by text, or selected games and clicked continue
        """
        user_data = await state.get_data()
        await bot.edit_message_reply_markup(response.from_user.id, user_data['msg_id'])
        await RegistrationState.next()
        await ask_phone(response, state)

    if isinstance(response, types.Message):
        # User decided to send game by text manually
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
    """
    Resolves further instructions for location question
    """
    async def accept_loc():
        """
        If user agreed to send location, ask him to send it
        """
        data = await state.get_data()
        await bot.edit_message_reply_markup(response.from_user.id, data['msg_id'])
        await response.message.reply(_('Вышлите вашу геопозицию'))

    async def proceed():
        """
        Finishes the state and creates record
        """
        await create_lead(response.from_user.id, state)
        await state.finish()

    location_mapper = {
        'send_loc': accept_loc,
        'skip_loc': proceed
    }

    if isinstance(response, types.Message) and response.location:
        # User sent message with location.
        await proceed()

    if isinstance(response, types.CallbackQuery):
        cb_value = response.data.split('|')[-1]
        await location_mapper[cb_value]()
        await state.update_data({'msg_id': response.message.message_id})


async def next_state(state: FSMContext):
    """
    Switches to the next state if current state data is not MT
    """
    data = await state.get_data()
    state = await state.get_state()
    if data.get(state):
        await RegistrationState.next()


async def is_text(user_response):
    if not isinstance(user_response, types.Message) or not user_response.text:
        raise ValueError('Не могу найти текстовое сообщение')


async def type_checker(user_response, required_type):
    is_correct = isinstance(user_response, required_type)
    if type(user_response) == types.Message and not is_correct:
        raise ValueError('Нужно кликнуть на кнопку')
    elif type(user_response) == types.CallbackQuery and not is_correct:
        raise ValueError('Нужно отправить текстовое сообщение')


@create_session
async def phone_checker(user_response, session):
    is_correct_format = re.match(PHONE_PATTERN, user_response.text)

    if not is_correct_format:
        raise ValueError('Неправильный формат телефона. Пример: +998000000000')

    is_phone_exists = await repo.StudentRepository.is_exist('phone', user_response.text, session)
    if is_phone_exists:
        raise ValueError('Данный номер уже используется')


QUESTION_MAP = {
    # State: Answer saver, Next Question Sender, State Resolution, Validators
    'first_name': (save_answer, ask_city, next_state,
                   [partial(type_checker, required_type=types.Message), is_text]),
    'city': (save_answer, ask_games, next_state,
             [partial(type_checker, required_type=types.Message), is_text]),
    'games': (save_games, game_handler, None, []),
    'phone': (save_answer, ask_location, next_state, [phone_checker, is_text]),
    'location': (save_location, location_handler, None, []),
}


@dp.message_handler(CommandStart(re.compile(r'\d+')), ChatTypeFilter(types.ChatType.PRIVATE), state='*')
@create_session
async def register_deep_link(
        message: types.Message,
        session: SessionLocal
):
    """
    Saves user tg_id into db if start was passed w/ deep link
    """
    contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
    student = await repo.StudentRepository.load_with_contact('unique_code', message.get_args(), session)
    kb = await KeyboardGenerator.main_kb()

    if student and not student.contact:
        await repo.StudentRepository.edit(student, {'contact': contact}, session)
        await message.reply(
            _('Спасибо {first_name},'
              'вы были успешно зарегистрированы в боте').format(first_name=message.from_user.first_name),
            reply_markup=kb)
    elif not student:
        await message.reply(_('Неверный инвайт код'))
    elif student and student.contact:
        await message.reply(_('Вы уже зарегистрированы. Выберите опцию'), reply_markup=kb)


@dp.message_handler(commands=['register'], state='*')
@dp.callback_query_handler(simple_data.filter(value='tg_reg'))
@create_session
async def entry_point(
        message: types.Message,
        session: SessionLocal
):
    """
    Entry handler to initiate registration process.
    """
    contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
    if contact.student:
        return await bot.send_message(
            message.from_user.id,
            'Вы уже зарегистрированы'
        )

    await bot.send_message(
        message.from_user.id,
        _('Регистрация в боте MegaSkill.\n'
          'Как тебя зовут?'),
    )
    await RegistrationState.first_name.set()


@dp.throttled(throttled, rate=.7)
@dp.message_handler(state=RegistrationState.states,
                    content_types=[types.ContentType.TEXT, types.ContentType.LOCATION])
@dp.callback_query_handler(state=RegistrationState.states)
async def process_handler(
    user_response: Union[types.CallbackQuery, types.Message],
    state: FSMContext
):
    """
    Intermediate handler that calls needed functions to create registration flow
    """
    if isinstance(user_response, types.CallbackQuery):
        await bot.answer_callback_query(user_response.id)

    current_state = (await state.get_state()).split(':')[-1]
    set_answer, next_question, set_state, validators = QUESTION_MAP[current_state]

    for validator in validators:
        try:
            await validator(user_response)
        except ValueError as e:
            return await bot.send_message(user_response.from_user.id, e)

    await set_answer(user_response, state)
    await next_question(user_response, state)
    if set_state:
        await set_state(state)
