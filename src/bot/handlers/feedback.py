from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot import config
from bot import repository as repo
from bot.db.config import SessionLocal
from bot.decorators import create_session
from bot.misc import dp, bot, i18n
from bot.misc import jinja_env
from bot.utils.callback_settings import two_valued_data

_ = i18n.gettext


class Feedback(StatesGroup):
    feedback = State()
    feedback_student = State()


@dp.callback_query_handler(two_valued_data.filter(property='feedback_student'))
async def get_student_feedback(
        cb: types.callback_query,
        state: FSMContext,
        callback_data: dict
):
    """
    Sets the state for feedback processing handler and requests student feedback
    """
    contact_id = callback_data['first_value']
    history_id = callback_data['second_value']

    await bot.answer_callback_query(cb.id)

    async with state.proxy() as data:
        data['contact_id'] = int(contact_id)
        data['history_id'] = int(history_id)
        data['msg'] = cb.message.text

    await cb.message.edit_reply_markup(reply_markup=None)

    await bot.send_message(
        cb.from_user.id,
        _('Отправьте Ваше сообщение')
    )

    await Feedback.feedback_student.set()


@dp.message_handler(state=Feedback.feedback_student)
@create_session
async def forward_student_feedback(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    """
    Processes feedback from student and forwards it to course chat id
    """
    data = await state.get_data()
    history_msg = await repo.MessageHistoryRepository.get('id', data['history_id'], session)
    contact = await repo.ContactRepository.load_student_data('id', data['contact_id'], session)
    template = jinja_env.get_template('feedback.html')
    await repo.MessageHistoryRepository.edit(history_msg, {'response': message.text}, session)
    await bot.send_message(
        config.CHAT_ID,
        template.render(contact=contact, course=None, lesson=None, msg=data.get('msg')),
        parse_mode='html'
    )
    await bot.forward_message(
        config.CHAT_ID,
        message.chat.id,
        message.message_id
    )

    await message.reply(_('Отправлено'))
    await state.finish()
