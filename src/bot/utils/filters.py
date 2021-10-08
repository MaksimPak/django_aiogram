from aiogram.dispatcher.filters import Filter
from aiogram import types

from bot import repository as repo
from bot.decorators import create_session


class UnknownContact(Filter):

    @create_session
    async def check(self, message: types.Message, session):
        contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
        return not contact
