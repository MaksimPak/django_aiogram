import re

from aiogram import types
from aiogram.dispatcher.filters import CommandStart, ChatTypeFilter

from bot import repository as repo
from bot.db.config import SessionLocal
from bot.decorators import create_session
from bot.misc import dp, i18n
from bot.serializers import KeyboardGenerator

_ = i18n.gettext


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