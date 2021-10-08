from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, CommandStart, Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.handler import SkipHandler

from bot.db.schemas import StudentTable
from bot.decorators import create_session
from bot.misc import dp, i18n
from bot import repository as repo
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import simple_data, short_data
from bot.utils.filters import UnknownContact
from bot.views import main

_ = i18n.gettext


class TestState(StatesGroup):
    lang = State()


def no_deeplink(message):
    return True if not message.get_args() else False


@dp.message_handler(UnknownContact(), ChatTypeFilter(types.ChatType.PRIVATE), state='*')
async def lang(msg: types.Message, state: FSMContext):
    update = types.Update.get_current()
    data = [(name.capitalize(), ('lang', member.value))
            for name, member in StudentTable.LanguageType.__members__.items()]
    kb = KeyboardGenerator(data).keyboard
    await msg.reply(' язык', reply_markup=kb)
    await state.update_data({'processed_update': update.to_python()})
    await TestState.lang.set()


@dp.callback_query_handler(short_data.filter(property='lang'), state=TestState.lang)
@create_session
async def save_lang(cb: types.CallbackQuery, state: FSMContext, callback_data: dict, session):
    await cb.answer()
    data = await state.get_data()
    chosen_lang = callback_data['value']
    await repo.ContactRepository.create(
        {
            'first_name': cb.from_user.first_name,
            'last_name': cb.from_user.last_name,
            'tg_id': cb.from_user.id,
            'data': {'lang': chosen_lang}
        }, session)
    await state.finish()
    update = types.Update.to_object(data['processed_update'])
    res = await dp.process_update(update)


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
