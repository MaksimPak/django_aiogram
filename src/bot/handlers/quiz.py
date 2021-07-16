from typing import Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, i18n, bot
from bot.models.dashboard import FormTable
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator, FormButtons, MessageSender
from bot.utils.callback_settings import short_data

# todo: need to localize
_ = i18n.gettext


class QuestionnaireMode(StatesGroup):
    accept_text = State()


@create_session
async def send_question(
        form_id: int,
        chat_id: int,
        state: FSMContext,
        session: SessionLocal,
        answer: Optional = None,
):
    form = await repo.FormRepository.get_questions(int(form_id), session)
    if form.mode == FormTable.FormMode.questionnaire:
        await QuestionnaireMode.accept_text.set()

    async with state.proxy() as data:
        data['form_id'] = form_id

    if not answer:
        await state.update_data({'current_question_id': form.questions[0].id})
        await state.update_data({'text_answers': {}})
        await state.update_data({'score': 0})

        kb = await FormButtons(form, form.questions[0]).question_buttons()

        await MessageSender(
            chat_id,
            form.questions[0].text,
            form.questions[0].image,
            markup=kb
        ).send()

    else:
        await next_question(chat_id, state)


@create_session
async def next_question(
        chat_id: int,
        state: FSMContext,
        session: SessionLocal = None
):
    data = await state.get_data()
    question = await repo.FormQuestionRepository.next_question(
            int(data['current_question_id']),
            int(data['form_id']),
            session
        )
    if question:
        await state.update_data({'current_question_id': question.id})
        kb = await FormButtons(question.form, question).question_buttons()

        await MessageSender(
            chat_id,
            question.text,
            question.image,
            markup=kb
        ).send()
    else:
        student = await repo.StudentRepository.get('tg_id', chat_id, session)
        data = await state.get_data()
        await repo.StudentFormRepository.create(
            {
                'student_id': student.id,
                'form_id': int(data['form_id']),
                'score':  int(data['score']),
                'data': data['text_answers']
            },
            session
        )
        await bot.send_message(
            chat_id,
            'Спасибо за то что прошли опросник',
        )
        await state.finish()


@dp.message_handler(Text(equals='🤔 Опросники'))
@create_session
async def display_forms(
        message: types.Message,
        session: SessionLocal,
        **kwargs: dict

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
        **kwargs: dict
):
    """
    Start the form for student
    """
    await cb.answer()
    form_id = callback_data['value']
    client = await repo.StudentRepository.get('tg_id', int(cb.from_user.id), session)
    form = await repo.FormRepository.get('id', int(form_id), session)

    async with state.proxy() as data:
        data['form_id'] = form_id

    if not client:
        await cb.message.reply(_('Вы не зарегистрированы. Отправьте /start чтобы зарегистрироваться'))
        return
    elif not form:
        await cb.message.reply(_('Ошибка системы. Получите опросники снова'))
    await send_question(form_id, cb.from_user.id, state)


@dp.callback_query_handler(short_data.filter(property='answer'))
@create_session
async def get_answer(
        cb: types.callback_query,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict = None,
        **kwargs: dict
):
    await cb.answer()
    answer = await repo.FormAnswerRepository.load_all_relationships(int(callback_data['value']), session)
    async with state.proxy() as data:
        if answer.is_correct:
            data['score'] += 1

    await send_question(answer.question.form.id, cb.from_user.id, state, answer=answer)


@dp.message_handler(state=QuestionnaireMode.accept_text)
@create_session
async def get_text_answer(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    data = await state.get_data()
    question = await repo.FormQuestionRepository.get(
        'id',
        int(data['current_question_id']),
        session
    )
    answers = data.get('text_answers') if data.get('text_answers') else {}
    answers[question.text] = message.text
    await state.update_data({'text_answers': answers})

    await next_question(message.from_user.id, state)
