import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, i18n
from bot.models.db import SessionLocal
from bot.serializers import MessageSender

_ = i18n.gettext


@dp.message_handler(Regexp(re.compile(r'^/lc_([a-z0-9]+(?:-+[a-z0-9]+)*$)')), state='*')
@create_session
async def display_lc(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        regexp: re.Match = None,
):
    """
    Starting handler to process homework process
    """
    await state.reset_state()
    lc = await repo.LearningCentreRepository.get('slug', regexp.group(1), session)
    msg = f'{lc.title}\n{lc.description}'
    kb = InlineKeyboardMarkup()
    if lc.link:
        kb.add(InlineKeyboardButton('Геолокация', url=lc.link))

    await MessageSender(
        message.from_user.id,
        msg,
        lc.photo,
        markup=kb
    ).send()
