from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot.decorators import create_session
from bot.misc import dp, i18n
from bot.models.db import SessionLocal
from bot import repository as repo
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data

# todo: need to localize
_ = i18n.gettext


@dp.message_handler(Text(equals='🤔 Опросники'))
@create_session
async def start_quiz(
        message: types.Message,
        session: SessionLocal,
        **kwargs

):
    forms = await repo.FormRepository.get_public(session)
    form_data = [(form.name, ('form', form.id)) for form in forms]
    markup = KeyboardGenerator(form_data).keyboard

    await message.reply('Выберите опросник', reply_markup=markup)


@dp.callback_query_handler(short_data.filter(property='form'))
@create_session
async def start_form(
        cb: types.callback_query,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict,
        **kwargs
):
    """
    Start the form for student
    """
    await cb.answer()
    form_id = callback_data['value']
    client = await repo.StudentRepository.get('tg_id', int(cb.from_user.id), session)
    form = await repo.FormRepository.get_with_first_question(int(form_id), session)
    if not client:
        await cb.message.reply(_('Вы не зарегистрированы. Отправьте /start чтобы зарегистрироваться'))
        return
    elif not form:
        await cb.message.reply(_('Ошибка системы. Получите опросники снова'))
    await cb.message.reply('ALIVE')
