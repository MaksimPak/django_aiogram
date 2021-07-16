from typing import Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot.decorators import create_session
from bot.misc import dp, i18n, bot
from bot.models.db import SessionLocal
from bot import repository as repo
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data, two_valued_data

# todo: need to localize
_ = i18n.gettext


@dp.message_handler(Text(equals='🤔 Опросники'))
@create_session
async def start_quiz(
        message: types.Message,
        session: SessionLocal,
        **kwargs

):
    forms = await repo.FormRepository.get_public(session)
    form_data = [(form.name, ('form', form.id)) for form in forms]
    markup = KeyboardGenerator(form_data).keyboard

    await message.reply('Выберите опросник', reply_markup=markup)


@dp.callback_query_handler(short_data.filter(property='form'))
@create_session
async def start_form(
        cb: types.callback_query,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict,
        **kwargs
):
    """
    Start the form for student
    """
    await cb.answer()
    form_id = callback_data['value']
    client = await repo.StudentRepository.get('tg_id', int(cb.from_user.id), session)
    form = await repo.FormRepository.get('id', int(form_id), session)
    if not client:
        await cb.message.reply(_('Вы не зарегистрированы. Отправьте /start чтобы зарегистрироваться'))
        return
    elif not form:
        await cb.message.reply(_('Ошибка системы. Получите опросники снова'))
    await send_question(form_id, cb.from_user.id, state)


@create_session
async def send_question(
        form_id: int,
        chat_id: int,
        state: FSMContext,
        session: SessionLocal,
        answer: Optional = None,
):
    form = await repo.FormRepository.get_questions(int(form_id), session)
    if not answer:
        async with state.proxy() as data:
            data['score'] = 0

        data = [(answer.text, ('answer', answer.id)) for answer in form.questions[0].answers]

        kb = KeyboardGenerator(data)
        await bot.send_message(
            chat_id,
            form.questions[0].text,
            reply_markup=kb.keyboard
        )
    else:
        await send_next_question(answer, chat_id, state)


@create_session
async def send_next_question(answer, chat_id, state, session=None):
    next_question = await repo.FornQuestionRepository.next_question(
            answer.question.id,
            answer.question.form_id,
            session
        )
    if next_question:
        data = [(answer.text, ('answer', answer.id)) for answer in next_question.answers]

        kb = KeyboardGenerator(data)

        await bot.send_message(
            chat_id,
            next_question.text,
            reply_markup=kb.keyboard
        )
    else:
        await bot.send_message(
            chat_id,
            'Спасибо за то что прошли опросник',
        )
        await state.finish()


@dp.callback_query_handler(short_data.filter(property='answer'))
@create_session
async def get_answer(
        cb: types.callback_query,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict = None,
        **kwargs
):
    await cb.answer()
    answer = await repo.FormAnswerRepository.load_all_relationships(int(callback_data['value']), session)
    async with state.proxy() as data:
        if answer.is_correct:
            data['score'] += 1

    await send_question(answer.question.form.id, cb.from_user.id, state, answer=answer)
