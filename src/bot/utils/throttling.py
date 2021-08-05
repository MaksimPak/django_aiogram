from typing import Union
from loguru import logger

from aiogram import types


async def throttled(*args, **kwargs):
    response: Union[types.Message, types.CallbackQuery] = args[0]
    message = response if type(response) == types.Message else response.message
    err = 'Too many requests'
    answer_kwargs = (err, True) if type(response) is types.CallbackQuery else (err,)

    await response.answer(*answer_kwargs)

    logger.info(f'User: {message.from_user.id} caused throttling.\nMessage:{message.text}')
