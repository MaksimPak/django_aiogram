from typing import Union
from loguru import logger

from aiogram import types


async def throttled(*args, **kwargs):
    response: Union[types.Message, types.CallbackQuery] = args[0]
    if type(response) == types.CallbackQuery:
        await response.answer()

    message = response if type(response) == types.Message else response.message
    logger.info(f'User: {message.from_user.id} caused throttling.\nMessage:{message.text}')
    await message.answer('Too many requests')
