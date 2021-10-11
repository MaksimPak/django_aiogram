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
    contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
    if contact.blocked_bot:
        await repo.ContactRepository.edit(contact, {'blocked_bot': False}, session)

    if not contact.student:
        kb = await KeyboardGenerator.main_kb(contact)
        await bot.send_message(
            message.from_user.id,
            _('Добро пожаловать в бот Megaskill! Пожалуйста, выберите опцию'),
            reply_markup=kb
        )
    else:
        kb = await KeyboardGenerator.main_kb()
        await bot.send_message(
            message.from_user.id,
            _('Выбери опцию'),
            reply_markup=kb
        )
