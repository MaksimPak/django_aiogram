import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text, ChatTypeFilter
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot, i18n, jinja_env
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
    await message.reply(_('Отменено.'), reply_markup=types.ReplyKeyboardRemove())


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
    kb = await KeyboardGenerator.main_kb()

    if student and not student.tg_id:
        await repo.StudentRepository.edit(student, {'tg_id': message.from_user.id}, session)
        await message.reply(
            _('Спасибо {first_name},'
              'вы были успешно зарегистрированы в боте').format(first_name=message.from_user.first_name),
            reply_markup=kb)
    elif not student:
        await message.reply(_('Неверный инвайт код'))
    elif student and student.tg_id:
        await message.reply(_('Вы уже зарегистрированы. Выберите опцию'), reply_markup=kb)


@dp.message_handler(CommandStart(re.compile(r'promo_\d+')), ChatTypeFilter(types.ChatType.PRIVATE))
@create_session
async def promo_deep_link(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    promotion = await repo.PromotionRepository.get('unique_code', message.get_args().split('_')[1], session)
    student = await repo.StudentRepository.get('tg_id', message.from_user.id, session)
    if not promotion:
        await message.reply(_('Неверный инвайт код'))

    await repo.PromotionRepository.edit(promotion, {'counter': promotion.counter+1}, session)

    text = jinja_env.get_template('promo_text.html').render(promo=promotion)

    await bot.send_video(
        message.from_user.id,
        promotion.video_file_id,
        caption=text,
        parse_mode='html',
    )

    if not student:
        data = [(name.capitalize(), ('lang', member.value))
                for name, member in StudentTable.LanguageType.__members__.items()]
        kb = KeyboardGenerator(data).keyboard

        await message.reply(
            _('Привет, спасибо что перешел по промо! Давай теперь тебя зарегаем. Укажи язык'),
            reply_markup=kb
        )

        async with state.proxy() as data:
            data['promo'] = promotion.id
            data['promo_course'] = promotion.course_id

        await RegistrationState.lang.set()
    else:
        if promotion.course_id:
            studentcourse = await repo.StudentCourseRepository.get_record(student.id, promotion.course_id, session)
            if not studentcourse:
                await repo.StudentCourseRepository.create_record(student.id, promotion.course_id, session)
        await start_reg(message, **kwargs)


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
    student = await repo.StudentRepository.get('tg_id', int(message.from_user.id), session)
    if not student:
        kb = KeyboardGenerator([(_('Через бот'), ('tg_reg',)), (_('Через инвайт'), ('invite_reg',))]).keyboard
        await bot.send_message(message.from_user.id, _('Выберите способ регистрации'), reply_markup=kb)
    else:
        kb = await KeyboardGenerator.main_kb()
        await bot.send_message(message.from_user.id, _('Выбери опцию'),
                               reply_markup=kb)


@dp.callback_query_handler(ChatTypeFilter(types.ChatType.PRIVATE), simple_data.filter(value='invite_reg'))
async def invite_reg(
        cb: types.callback_query
):
    await bot.answer_callback_query(cb.id)
    await bot.send_message(cb.from_user.id, _('Введите инвайт код'))
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
        await message.reply(('Спасибо {first_name},'
                             ' вы были успешно'
                             ' зарегистрированы в боте').format(first_name=message.from_user.first_name))
        await state.finish()
    else:
        await message.reply(_('Неверный инвайт код'))


@dp.callback_query_handler(simple_data.filter(value='tg_reg'))
async def tg_reg(
        cb: types.callback_query
):
    await bot.answer_callback_query(cb.id)
    data = [(name.capitalize(), ('lang', member.value))
            for name, member in StudentTable.LanguageType.__members__.items()]

    kb = KeyboardGenerator(data).keyboard

    await bot.send_message(cb.from_user.id, _('Привет! Выбери язык'), reply_markup=kb)
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
async def set_phone(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        *args,
        **kwargs
):
    async with state.proxy() as data:
        data['phone'] = message.text

    categories = await repo.CategoryRepository.get_categories(session)
    lang = StudentTable.LanguageType(data['lang']).name

    data = [(category.get_title(lang), ('field', category.id)) for category in categories]
    kb = KeyboardGenerator(data).keyboard

    await bot.send_message(message.chat.id, _('В каком направлении вы хотите учиться?'), reply_markup=kb)
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
    field = int(callback_data['value'])

    data = await state.get_data()
    lead_data = {
        'first_name': data['first_name'],
        'city': data['city'],
        'tg_id': cb.from_user.id,
        'language_type': data['lang'],
        'phone': data['phone'],
        'chosen_field_id': field,
        'application_type': StudentTable.ApplicationType.telegram,
        'is_client': False,
        'promo_id': data.get('promo')
    }
    student = await repo.StudentRepository.create(lead_data, session)

    if data.get('promo_course'):
        await repo.StudentCourseRepository.create_record(student.id, data['promo_course'], session)

    reply_kb = await KeyboardGenerator.main_kb()
    await bot.send_message(cb.from_user.id, _('Вы зарегистрированы! В ближайшее время с вами свяжется наш оператор'),
                           reply_markup=reply_kb)
    await state.finish()
