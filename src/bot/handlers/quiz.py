import os
import re
from typing import Optional, Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp, CommandStart, ChatTypeFilter
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, ContentType

from bot import repository as repo, config
from bot.decorators import create_session
from bot.misc import dp, i18n, bot
from bot.models.dashboard import FormAnswerTable, FormQuestionTable
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator, FormButtons, MessageSender
from bot.utils.callback_settings import short_data, simple_data, two_valued_data
from bot.utils.throttling import throttled

# todo: need to localize
_ = i18n.gettext


class QuestionnaireMode(StatesGroup):
    accept_text = State()
    accept_file = State()


async def _normalize_end_msg(msg: str):
    return msg.replace('<br>', '\n')


async def store_answer(
        question: FormQuestionTable,
        answer: str,
        state: FSMContext,
):
    data = await state.get_data()
    previous_answers = data.get('answers') if data.get('answers') else {}
    key = str(question.id)

    if question.multi_answer:
        if previous_answers.get(key) and answer in previous_answers.get(key):
            previous_answers[key].remove(answer)
        else:
            previous_answers.setdefault(key, [])
            previous_answers[key].append(answer)
    else:
        previous_answers[key] = answer

    await state.update_data({'answers': previous_answers})


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

    async with state.proxy() as data:
        data['form_id'] = int(form_id)

    if not answer:
        await state.update_data({
            'question_len': 1,
            'current_question_id': form.questions[0].id,
            'position': form.questions[0].position,
            'answers': {},
            'score': 0,
        })

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
    if data.get('jump_to_question'):
        async with state.proxy() as data:
            jump_to_id = data.pop('jump_to_question')
        question = await repo.FormQuestionRepository.get('id', jump_to_id, session)
    else:
        question = await repo.FormQuestionRepository.next_question(
            data['current_question_id'],
            data['position'],
            data['form_id'],
            session
        )

    contact = await repo.ContactRepository.get('tg_id', chat_id, session)
    data = await state.get_data()
    form = await repo.FormRepository.get('id', data['form_id'], session)
    await repo.ContactFormRepository.create_or_edit(contact.id, data['form_id'], data, session)

    if question:
        count = data['question_len'] + 1
        await state.update_data({
            'question_len': count,
            'current_question_id': question.id,
            'position': question.position,
        })
        kb = await FormButtons(question.form, question).question_buttons()

        await MessageSender(
            chat_id,
            question.text,
            question.image,
            markup=kb
        ).send()
    else:
        percent_score = round((data['score'] / data['question_len']) * 100)
        end_message = _('Спасибо за участие')
        for key in form.end_message.keys():
            num1, num2 = map(int, key.split('-'))
            if percent_score in range(num1, num2+1):
                end_message = await _normalize_end_msg(form.end_message[key])
        kb = await KeyboardGenerator.main_kb(contact)
        await bot.send_message(
            chat_id,
            end_message,
            reply_markup=kb,
        )
        await state.finish()


async def process_multianswer(
        cb: types.CallbackQuery,
        answer: FormAnswerTable,
        state: FSMContext,
        keyboard: InlineKeyboardMarkup
):
    async with state.proxy() as data:
        if 'is_correct' not in data:
            data['is_correct'] = [answer.is_correct]
        else:
            data['is_correct'].append(answer.is_correct)
    kb = await FormButtons(answer.question.form_id).mark_selected(
        answer.id,
        answer.question_id,
        answer.question.position,
        keyboard.to_python()
    )

    await cb.message.edit_reply_markup(kb)


@dp.callback_query_handler(simple_data.filter(value='forms'))
@dp.message_handler(Text(equals='🤔 Опросники'), state='*')
@create_session
async def display_forms(
        response: Union[types.Message, types.CallbackQuery],
        state: FSMContext,
        session: SessionLocal
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
        _('Выберите опросник'),
        reply_to_message_id=message_id,
        allow_sending_without_reply=True,
        reply_markup=markup
    )


@dp.message_handler(CommandStart(re.compile(r'^quiz(\d+)')), ChatTypeFilter(types.ChatType.PRIVATE))
@dp.message_handler(Regexp(re.compile(r'^/quiz(\d+)')))
@dp.callback_query_handler(short_data.filter(property='form'))
@dp.throttled(throttled, rate=.7)
@create_session
async def form_initial(
        response: Union[types.CallbackQuery, types.Message],
        session: SessionLocal,
        callback_data: dict = None,
        regexp: re.Match = None,
        deep_link: re.Match = None
):
    if type(response) == types.CallbackQuery:
        await response.answer()
        form_id = callback_data['value']
    else:
        form_id = regexp.group(1) if regexp else deep_link.group(1)

    message_id = response.message.message_id if type(response) == types.CallbackQuery else response.message_id
    search_field = 'id' if type(response) == types.CallbackQuery else 'unique_code'
    contact = await repo.ContactRepository.get_or_create(
        response.from_user.id,
        response.from_user.first_name,
        response.from_user.last_name,
        session
    )

    form = await repo.FormRepository.get(search_field, int(form_id), session)

    if not form:
        return await bot.send_message(
            response.from_user.id,
            _('Ошибка системы. Получите опросники снова'),
            reply_to_message_id=message_id
        )
    elif not form.is_active:
        return await bot.send_message(
            response.from_user.id,
            _('Форма не активна. Свяжитесь с администрацией'),
            reply_to_message_id=message_id
        )
    if contact.access_level >= form.access_level.value:
        is_record = await repo.ContactFormRepository.exists(contact.id, form.id, session)

        if form.one_off and is_record:
            return await bot.send_message(
                response.from_user.id,
                _('Данный опросник нельзя пройти дважды'),
                reply_to_message_id=message_id
            )

        data = [(_('Начать'), ('start_form', form.id)), ('Назад', ('forms',))]
        kb = KeyboardGenerator(data, row_width=1).keyboard

        await MessageSender(
            response.from_user.id,
            form.start_message,
            form.image,
            markup=kb
        ).send()
    else:
        delta = form.access_level.value - contact.access_level
        if delta == 2:
            kb = KeyboardGenerator([(_('Регистрация'), ('tg_reg',))]).keyboard
            return await bot.send_message(contact.tg_id, _('Пожалуйста, пройдите регистрацию'), reply_markup=kb)
        else:
            await bot.send_message(contact.tg_id, _('Недостаточно доступа'))


@dp.callback_query_handler(short_data.filter(property='start_form'))
@dp.throttled(throttled, rate=.7)
async def start_form(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict = None
):
    """
    Start the form for student
    """
    await cb.answer()
    message_id = cb.message.message_id
    form_id = int(callback_data['value'])

    async with state.proxy() as data:
        data['form_id'] = int(form_id)

    await start_question_sending(form_id, cb.from_user.id, message_id, state)


@dp.callback_query_handler(short_data.filter(property='answer'))
@dp.throttled(throttled, rate=.7)
@create_session
async def get_inline_answer(
        cb: types.CallbackQuery,
        session: SessionLocal,
        state: FSMContext,
        callback_data: dict = None
):
    await cb.answer()
    answer = await repo.FormAnswerRepository.load_all_relationships(int(callback_data['value']), session)
    await store_answer(answer.question, answer.text, state)

    if answer.jump_to_id:
        await state.update_data({'jump_to_question': answer.jump_to_id})

    if answer.question.multi_answer:
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


@dp.callback_query_handler(two_valued_data.filter(property='proceed'))
@dp.throttled(throttled, rate=.7)
async def proceed(
        cb: types.CallbackQuery,
        state: FSMContext,
        callback_data: dict = None
):
    await cb.answer()
    await cb.message.edit_reply_markup(None)
    async with state.proxy() as data:
        if all(data['is_correct']):
            data['score'] += 1
        data['current_question_id'] = int(callback_data['first_value'])
        data['position'] = int(callback_data['second_value'])

    await next_question(cb.from_user.id, state)


@dp.callback_query_handler(simple_data.filter(value='custom_answer'))
@dp.throttled(throttled, rate=.7)
async def custom_answer(
        cb: types.CallbackQuery,
):
    await cb.answer()
    await cb.message.edit_reply_markup(None)
    await bot.send_message(
        cb.from_user.id,
        _('Напишите свой ответ'),
    )
    await QuestionnaireMode.accept_text.set()


@dp.callback_query_handler(simple_data.filter(value='file_answer'))
@dp.throttled(throttled, rate=.7)
async def file_answer(
        cb: types.CallbackQuery,
):
    await cb.answer()
    await cb.message.edit_reply_markup(None)
    await bot.send_message(
        cb.from_user.id,
        _('Вышлите файл'),
    )
    await QuestionnaireMode.accept_file.set()


@dp.message_handler(state=QuestionnaireMode.accept_text)
@dp.throttled(throttled, rate=.7)
@create_session
async def get_text_answer(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    await state.reset_state(False)
    data = await state.get_data()
    question = await repo.FormQuestionRepository.get(
        'id',
        data['current_question_id'],
        session
    )
    await store_answer(question, message.text, state)

    await next_question(message.from_user.id, state)


@dp.message_handler(state=QuestionnaireMode.accept_file, content_types=[ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT])
@dp.throttled(throttled, rate=.7)
@create_session
async def get_file_answer(
        message: types.Message,
        state: FSMContext,
        session: SessionLocal
):
    await state.reset_state(False)
    data = await state.get_data()
    question = await repo.FormQuestionRepository.get(
        'id',
        data['current_question_id'],
        session
    )
    if message.content_type is not ContentType.PHOTO:
        filename = getattr(message, message.content_type).file_name
    else:
        filename = 'pic'

    await store_answer(question, filename, state)
    chat_id = question.chat_id if question.chat_id else config.CHAT_ID
    await bot.forward_message(chat_id, message.from_user.id, message.message_id)

    await next_question(message.from_user.id, state)
