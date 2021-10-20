from typing import Any, Tuple

from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware as BaseI18nMiddleware

from bot import repository as repo
from bot.db.schemas import StudentTable
from bot.decorators import create_session


class I18nMiddleware(BaseI18nMiddleware):
    @create_session
    async def get_user_locale(self, action: str, args: Tuple[Any], session) -> str:
        """
        Middleware function to return locale to handlers
        """
        message: types.Message = args[0]
        contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
        lang = self.default
        if contact:
            lang = StudentTable.LanguageType(contact.data.get('lang', StudentTable.LanguageType.ru)).name
        *_, data = args
        data['locale'] = lang
        return data['locale']
