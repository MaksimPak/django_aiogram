from contextlib import suppress

from aiogram import types
from sqlalchemy.exc import IntegrityError

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import bot, i18n
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator

_ = i18n.gettext


@create_session
async def start_reg(
        message: types.Message,
        session: SessionLocal = None
):
    student = await repo.StudentRepository.get('tg_id', int(message.from_user.id), session)
    if not student:
        with suppress(IntegrityError):
            await repo.ContactRepository.create({
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'tg_id': message.from_user.id
            }, session)
        kb = KeyboardGenerator([(_('Через бот'), ('tg_reg',)), (_('Через инвайт'), ('invite_reg',))]).keyboard
        await bot.send_message(message.from_user.id, _('Выберите способ регистрации'), reply_markup=kb)
    else:
        kb = await KeyboardGenerator.main_kb()
        if student.blocked_bot:
            await repo.StudentRepository.edit(student, {'blocked_bot': False}, session)
        await bot.send_message(
            message.from_user.id,
            _('Выбери опцию'),
            reply_markup=kb
        )
