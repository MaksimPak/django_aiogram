from aiogram import types

from bot.misc import dp, bot


@dp.callback_query_handler(lambda x: 'tasks|' in x.data)
async def my_tasks(cb: types.callback_query):
    await bot.answer_callback_query(cb.id)
    await bot.send_message(cb.from_user.id, 'Раздел в разработке')
