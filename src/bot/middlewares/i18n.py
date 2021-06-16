from typing import Any, Tuple

from aiogram import types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.contrib.middlewares.i18n import I18nMiddleware as BaseI18nMiddleware

from bot import repository as repo, config
from bot.decorators import create_session

user_redis = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT, db=3, prefix='user')


async def get_student_lang(tg_id, session=None):
    redis = await user_redis.redis()
    data = await redis.get(f'user_{tg_id}', encoding='utf8')
    if not data:
        user = await repo.StudentRepository.get('tg_id', int(tg_id), session)
        await redis.set(f'user_{tg_id}', user.language_type.name, expire=15*60)
        data = user.language_type.name
    return data


class I18nMiddleware(BaseI18nMiddleware):

    @create_session
    async def get_user_locale(self, action: str, args: Tuple[Any], session) -> str:
        """
        Middleware function to return locale to handlers
        """

        message: types.Message = args[0]
        lang = await get_student_lang(message.from_user.id, session)
        *_, data = args
        data['locale'] = self.default
        if lang:
            data['locale'] = lang
            return data['locale']
        return data['locale']
