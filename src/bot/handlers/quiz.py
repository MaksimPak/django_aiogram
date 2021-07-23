import re
from typing import Optional, Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp, CommandStart, ChatTypeFilter
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, i18n, bot
from bot.models.dashboard import FormTable, FormAnswerTable
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator, FormButtons, MessageSender
from bot.utils.callback_settings import short_data, simple_data

# todo: need to localize
_ = i18n.gettext


class QuestionnaireMode(StatesGroup):
    accept_text = State()


@create_session
async def start_question_sending(
        form_id: int,
        chat_id: int,
        message_id: int,
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
        await bot.edit_message_reply_markup(chat_id, message_id)
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
        form = await repo.FormRepository.get('id', data['form_id'], session)
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
            form.end_message,
        )
        await state.finish()


async def process_multianswer(
        cb: types.CallbackQuery,
        answer: FormAnswerTable,
        state: FSMContext,
        keyboard: InlineKeyboardMarkup
):
    async with state.proxy() as data:
        if 'answers' not in data:
            data['answers'] = [answer.is_correct]
        else:
            data['answers'].append(answer.is_correct)
    kb = await FormButtons(answer.question.form_id).mark_selected(
        answer.id,
        answer.question_id,
        keyboard.to_python()
    )

    await cb.message.edit_reply_markup(kb)


@dp.callback_query_handler(simple_data.filter(value='forms'))
@dp.message_handler(Text(equals='🤔 Опросники'), state='*')
@create_session
async def display_forms(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext,
        session: SessionLocal,
        **kwargs: dict

):
    await state.reset_state()
    if type(response) == types.CallbackQuery:
        await response.answer()

    forms = await repo.FormRepository.get_public(session)
    form_data = [(form.name, ('form', form.id)) for form in forms]
    markup = KeyboardGenerator(form_data).keyboard
    message_id = response.message_id if type(response) == types.Message else None

    await bot.send_message(
        response.from_user.id,
        'Выберите опросник',
        reply_to_message_id=message_id,
        allow_sending_without_reply=True,
        reply_markup=markup
    )


@dp.message_handler(CommandStart(re.compile(r'^quiz(\d+)')), ChatTypeFilter(types.ChatType.PRIVATE))
@dp.message_handler(Regexp(re.compile(r'^/quiz(\d+)')))
@dp.callback_query_handler(short_data.filter(property='form'))
@create_session
async def form_initial(
        response: Union[types.CallbackQuery, types.Message],
        session: SessionLocal,
        callback_data: dict = None,
        regexp: re.Match = None,
        deep_link: re.Match = None,
        **kwargs
):
    if type(response) == types.CallbackQuery:
        await response.answer()
        form_id = callback_data['value']
    else:
        form_id = regexp.group(1) if regexp else deep_link.group(1)

    search_field = 'id' if type(response) == types.CallbackQuery else 'unique_code'
    client = await repo.StudentRepository.get('tg_id', int(response.from_user.id), session)
    form = await repo.FormRepository.get(search_field, int(form_id), session)
    is_record = await repo.StudentFormRepository.exists(client.id, int(form_id), session)
    message_id = response.message.message_id if type(response) == types.CallbackQuery else response.message_id

    if not client:
        return await bot.send_message(
            response.from_user.id,
            'Вы не зарегистрированы. Отправьте /start чтобы зарегистрироваться',
            reply_to_message_id=message_id
        )
    elif not form:
        return await bot.send_message(
            response.from_user.id,
            'Ошибка системы. Получите опросники снова',
            reply_to_message_id=message_id
        )
    elif form.one_off and is_record:
        return await bot.send_message(
            response.from_user.id,
            'Данный опросник нельзя пройти дважды',
            reply_to_message_id=message_id
        )
    data = [('Начать', ('start_form', form.id)), ('Назад', ('forms',))]
    kb = KeyboardGenerator(data, row_width=1).keyboard

    await bot.send_message(
        response.from_user.id,
        form.start_message,
        reply_to_message_id=message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(short_data.filter(property='start_form'))
@create_session
async def start_form(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict = None,
        **kwargs
):
    """
    Start the form for student
    """
    await cb.answer()
    message_id = cb.message.message_id
    form_id = int(callback_data['value'])

    async with state.proxy() as data:
        data['form_id'] = form_id

    await start_question_sending(form_id, cb.from_user.id, message_id, state)


@dp.callback_query_handler(short_data.filter(property='answer'))
@create_session
async def get_inline_answer(
        cb: types.CallbackQuery,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict = None,
        **kwargs: dict
):
    await cb.answer()
    answer = await repo.FormAnswerRepository.load_all_relationships(int(callback_data['value']), session)
    multi_answer = answer.question.multi_answer
    if multi_answer:
        await process_multianswer(cb, answer, state, cb.message.reply_markup)
    else:
        async with state.proxy() as data:
            if answer.is_correct:
                data['score'] += 1

        await start_question_sending(
            answer.question.form.id,
            cb.from_user.id,
            cb.message.message_id,
            state,
            answer=answer
        )


@dp.callback_query_handler(short_data.filter(property='proceed'))
@create_session
async def proceed(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict = None,
        **kwargs
):
    await cb.answer()
    await cb.message.edit_reply_markup(None)
    async with state.proxy() as data:
        if all(data['answers']):
            data['score'] += 1
        data['current_question_id'] = callback_data['value']

    await next_question(cb.from_user.id, state)


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
