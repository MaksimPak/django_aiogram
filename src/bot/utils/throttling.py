from typing import Union
from loguru import logger

from aiogram import types


async def throttled(*args, **kwargs):
    response: Union[types.Message, types.CallbackQuery] = args[0]
    message = response if type(response) == types.Message else response.message

    if type(response) == types.CallbackQuery:
        await response.answer(text='Повторите попытку еще раз', show_alert=True)
    else:
        await message.answer('Повторите попытку еще раз')
    logger.info(f'User: {message.from_user.id} caused throttling.\nMessage:{message.text}')
