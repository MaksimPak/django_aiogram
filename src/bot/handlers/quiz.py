from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, bot
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.utils.callback_settings import short_data


class QuizState(StatesGroup):
    first = State()
    second = State()
    third = State()
    fourth = State()
    fifth = State()
    sixth = State()
    seventh = State()
    eighth = State()
    nineth = State()
    tenth = State()


@dp.message_handler(Text(equals='🤔 Викторина'))
async def start_quiz(
        message: types.Message,
        state: FSMContext,
):
    data = [
        ('Spacewar', ('quiz', 1)),
        ('Super Mario Bros', ('quiz', 2)),
        ('Pong', ('quiz', 3)),
        ('Space Invaders', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await message.reply('Назовите самую первую игру', reply_markup=kb)
    await QuizState.first.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.first)
@create_session
async def answer_first(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])
    student = await repo.StudentRepository.get('tg_id', cb.from_user.id, session)
    quiz_answer = await repo.QuizAnswerRepository.create({'student_id': student.id}, session)

    async with state.proxy() as data:
        data['quiz_id'] = quiz_answer.id
        data['score'] = 1 if answer == 3 else 0
        data['answers'] = str(answer) + '|'

    data = [
        ('Half-Life', ('quiz', 1)),
        ('Unreal Tournament', ('quiz', 2)),
        ('Doom', ('quiz', 3)),
        ('Wolfenstein', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Какая игра изображена на картинке?',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await QuizState.second.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.second)
async def answer_second(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 3:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('CrossFire', ('quiz', 1)),
        ('Mass Effect 3', ('quiz', 2)),
        ('Battlefield', ('quiz', 3)),
        ('Lineage II', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Какая игра изображена на картинке?',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await QuizState.third.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.third)
async def answer_third(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 2:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('Tekken 3', ('quiz', 1)),
        ('Gran Turismo', ('quiz', 2)),
        ('Crash Bandicoot', ('quiz', 3)),
        ('Resident Evil 2', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Самая продаваемая игра на PlayStation 1',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await QuizState.fourth.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.fourth)
async def answer_fourth(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 2:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('Roblox', ('quiz', 1)),
        ('BlockCraft', ('quiz', 2)),
        ('Minecraft', ('quiz', 3)),
        ('Fortnite', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Из какой игры этот скриншот?',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )

    await QuizState.fifth.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.fifth)
async def answer_fifth(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 3:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('GTA: V', ('quiz', 1)),
        ('Red Dead Redemtion 2 ', ('quiz', 2)),
        ('Cyberpunk 2077', ('quiz', 3)),
        ('Unreal Tournament', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Самая дорогая игра в разработке?',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )

    await QuizState.sixth.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.sixth)
async def answer_sixth(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 2:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('FLATOUT', ('quiz', 1)),
        ('FORZA HORIZON', ('quiz', 2)),
        ('NEED FOR SPEED', ('quiz', 3)),
        ('GTA: V', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Какая игра изображена на картинке?',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await QuizState.seventh.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.seventh)
async def answer_seventh(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 4:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('Doom Engine', ('quiz', 1)),
        ('Unity', ('quiz', 2)),
        ('Unreal Engine', ('quiz', 3)),
        ('Source', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Назовите самый первый игровой движок',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await QuizState.eighth.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.eighth)
async def answer_eighth(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 1:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('Robocraft Royale', ('quiz', 1)),
        ('Fortnite', ('quiz', 2)),
        ('PUBG', ('quiz', 3)),
        ('Radical Heights', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Какая игра изображена на картинке?',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await QuizState.nineth.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.nineth)
async def answer_nineth(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 2:
            data['score'] += 1
        data['answers'] += str(answer) + '|'

    data = [
        ('PSP', ('quiz', 1)),
        ('Wii', ('quiz', 2)),
        ('Xbox 360', ('quiz', 3)),
        ('Playstation 2', ('quiz', 4))
    ]

    kb = KeyboardGenerator(data).keyboard

    await bot.edit_message_text(
        'Самая продаваемая игровая приставка в мире?',
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )
    await QuizState.tenth.set()


@dp.callback_query_handler(short_data.filter(property='quiz'), state=QuizState.tenth)
@create_session
async def answer_tenth(
        cb: types.callback_query,
        callback_data: dict,
        state: FSMContext,
        session: SessionLocal,
        **kwargs
):
    await bot.answer_callback_query(cb.id)
    answer = int(callback_data['value'])

    async with state.proxy() as data:
        if answer == 4:
            data['score'] += 1
        data['answers'] += str(answer)

    await bot.edit_message_text(
        'Спасибо за участие',
        cb.from_user.id,
        cb.message.message_id
    )

    quiz = await repo.QuizAnswerRepository.get('id', data['quiz_id'], session)
    await repo.QuizAnswerRepository.edit(
        quiz,
        {'score': data['score'], 'answers': data['answers']},
        session
    )
    await state.finish()
