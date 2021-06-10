from aiogram import Bot, types
from aiogram.utils.exceptions import ChatNotFound

from bot import config


# todo redefine bot methods

class MegaskillBot(Bot):
    async def send_message(self, *args, **kwargs) -> types.Message:
        try:
            result = await super(MegaskillBot, self).send_message(*args, **kwargs)
        except ChatNotFound:
            result = await super(MegaskillBot, self).send_message(*args, chat_id=config.CHAT_ID, **kwargs)

        return result
