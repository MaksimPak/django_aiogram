import re
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, i18n
from bot.models.db import SessionLocal
from bot.serializers import MessageSender, KeyboardGenerator
from bot.utils.callback_settings import short_data

_ = i18n.gettext


@dp.message_handler(Text(equals='🏫 Центры'), state='*')
@create_session
async def list_all(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    await state.reset_state()
    lcs = await repo.LearningCentreRepository.get_lcs(session)
    lcs_data = [(lc.title, ('lc', lc.slug)) for lc in lcs]
    markup = KeyboardGenerator(lcs_data).keyboard

    await message.reply(
        _('Выберите центр'),
        reply_markup=markup
    )


@dp.message_handler(Regexp(re.compile(r'^/lc_([a-z0-9]+(?:-+[a-z0-9]+)*$)')), state='*')
@dp.callback_query_handler(short_data.filter(property='lc'))
@create_session
async def display_lc(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext,
        session: SessionLocal,
        callback_data: dict = None,
        regexp: re.Match = None,
):
    """
    Starting handler to process homework process
    """
    await state.reset_state()

    if isinstance(response, types.CallbackQuery):
        await response.answer()
        slug = callback_data['value']
    else:
        slug = regexp.group(1)

    lc = await repo.LearningCentreRepository.get('slug', slug, session)
    if not lc:
        return await response.reply(_('Такого центра не существует'))
    msg = f'{lc.title}\n{lc.description}'
    kb = InlineKeyboardMarkup()
    if lc.link:
        kb.add(InlineKeyboardButton(_('Геолокация'), url=lc.link))

    await MessageSender(
        response.from_user.id,
        msg,
        lc.photo,
        markup=kb
    ).send()
