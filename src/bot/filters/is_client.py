from dataclasses import dataclass

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from bot.models.dashboard import StudentTable
from bot.models.db import SessionLocal
from sqlalchemy.future import select


@dataclass
class IsClientFilter(BoundFilter):
    key = 'is_client'

    is_client: bool

    async def check(self, message: types.Message):
        async with SessionLocal() as session:
            students = await session.execute(select(StudentTable))
            clients_tg = [
                x.tg_id for x in students.scalars() if x.is_client is True
            ]
            return self.is_client and message.from_user.id in clients_tg
