from aiogram import types

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import bot, i18n
from bot.db.schemas import ContactTable, StudentTable
from bot.db.config import SessionLocal
from bot.serializers import KeyboardGenerator

_ = i18n.gettext


@create_session
async def main(
        message: types.Message,
        session: SessionLocal = None
):
    student = await repo.StudentRepository.get('tg_id', int(message.from_user.id), session)
    contact = await repo.ContactRepository.get_or_create(
        message.from_user.id,
        message.from_user.first_name,
        message.from_user.last_name,
        session
    )
    if contact.blocked_bot:
        await repo.ContactRepository.edit(contact, {'blocked_bot': False}, session)

    if not student:
        kb = await KeyboardGenerator.main_kb(contact)
        await bot.send_message(
            message.from_user.id,
            _('Добро пожаловать в бот Megaskill! Пожалуйста, выберите опцию'),
            reply_markup=kb
        )
    else:
        kb = await KeyboardGenerator.main_kb()
        if student.blocked_bot:
            await repo.StudentRepository.edit(student, {'blocked_bot': False}, session)
        await bot.send_message(
            message.from_user.id,
            _('Выбери опцию'),
            reply_markup=kb
        )
