from typing import Union

from aiogram import types


async def throttled(*args, **kwargs):
    response: Union[types.Message, types.CallbackQuery] = args[0]

    message = response if type(response) == types.Message else response.message

    await message.answer('Too many requests')
