from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, CommandStart, Text

from bot.misc import dp, i18n
from bot.views import main

_ = i18n.gettext


def no_deeplink(message):
    return True if not message.get_args() else False


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), state='*', commands='cancel')
@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(
        message: types.Message,
        state: FSMContext
):
    """
    Allow user to cancel any action
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply(_('Отменено.'), reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(CommandStart(), no_deeplink, state='*')
async def initial(
        message: types.Message,
        state: FSMContext
):
    """
    Displays main panel if user exists. Else, offers options for registration
    """
    await state.reset_state()
    await main(message)
