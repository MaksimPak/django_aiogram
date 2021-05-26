import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, ContentType

from bot import config
from bot import repository as repo
from bot.decorators import create_session
from bot.helpers import make_kb
from bot.misc import dp, bot
from bot.misc import jinja_env
from bot.models.db import SessionLocal


class Homework(StatesGroup):
    homework_start = State()


async def post_photo(*args, **kwargs):  # todo use named args / naming lesson post photo
    if kwargs['lesson'].image_file_id:
        await bot.send_photo(
            kwargs['cb'].from_user.id,
            kwargs['lesson'].image_file_id,
            caption=kwargs['template'].render(lesson=kwargs['lesson'],
                                              url=f'{config.DOMAIN}/dashboard/watch/{kwargs["lesson_url"].hash}'),
            parse_mode='html',
            reply_markup=kwargs['kb']
        )
    else:
        with open('../media/' + kwargs['lesson'].image, 'br') as file:
            file_id = (await bot.send_photo(
                kwargs['cb'].from_user.id,
                file.read(),
                caption=kwargs['template'].render(lesson=kwargs['lesson'],
                                                  url=f'{config.DOMAIN}/dashboard/watch/{kwargs["lesson_url"].hash}'),
                parse_mode='html',
                reply_markup=kwargs['kb']
            )).photo[-1].file_id
            kwargs['lesson'].image_file_id = file_id


@dp.callback_query_handler(lambda x: 'courses|' in x.data)
@create_session
async def my_courses(cb: types.CallbackQuery, session: SessionLocal, **kwargs):
    await bot.answer_callback_query(cb.id)
    _, client_id = cb.data.split('|')

    client = await repo.StudentRepository.get_course_inload('id', client_id, session)
    free_courses = await repo.CourseRepository.get_many('is_free', True, session)

    btn_list = [InlineKeyboardButton(x.courses.name, callback_data=f'get_course|{x.courses.id}')
                for x in client.courses
                ] + [InlineKeyboardButton(x.name, callback_data=f'get_course|{x.id}') for x in free_courses]

    kb = await make_kb(btn_list)
    kb.add(InlineKeyboardButton('Назад', callback_data=f'back|{client.id}'))

    msg = 'Ваши курсы' if btn_list else 'Вы не записаны ни на один курс'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(lambda x: 'get_course|' in x.data, state='*')
@create_session
async def course_lessons(cb: types.callback_query, session: SessionLocal, **kwargs):
    await bot.answer_callback_query(cb.id)
    _, course_id = cb.data.split('|')
    course = await repo.CourseRepository.get_lesson_inload('id', course_id, session)
    client = await repo.StudentRepository.get('tg_id', cb.from_user.id, session)
    lessons = await repo.LessonRepository.load_unsent_from_course(course, 'lessons', session)

    if course.is_free:
        lessons = course.lessons

    kb = await make_kb([InlineKeyboardButton(x.title, callback_data=f'lesson|{x.id}') for x in lessons])
    kb.add(InlineKeyboardButton('Назад', callback_data=f'to_courses|{client.id}'))
    msg = 'Уроки курса' if lessons else 'У курса нет уроков'
    await bot.edit_message_text(
        msg,
        cb.from_user.id,
        cb.message.message_id,
        reply_markup=kb
    )


@dp.callback_query_handler(lambda x: 'lesson|' in x.data, state='*')
@create_session
async def get_lesson(cb: types.callback_query, session: SessionLocal, **kwargs):
    await bot.answer_callback_query(cb.id)
    _, lesson_id = cb.data.split('|')
    lesson = await repo.LessonRepository.get('id', lesson_id, session)
    client = await repo.StudentRepository.get('tg_id', cb.from_user.id, session)
    lesson_url = await repo.LessonUrlRepository.get_from_lesson_and_student(lesson_id, client.id, session)

    if not lesson_url:
        lesson_url = await repo.LessonUrlRepository.create({'student_id': client.id, 'lesson_id': lesson.id}, session)

    student_lesson = await repo.StudentLessonRepository.create(
        {
            'student_id': client.id,
            'lesson_id': lesson_id,
            'date_received': datetime.datetime.now()
        }, session)

    kb = await make_kb([InlineKeyboardButton('Отметить как просмотренное', callback_data=f'watched|{student_lesson.id}')])
    template = jinja_env.get_template('lesson_info.html')

    await bot.delete_message(cb.from_user.id, cb.message.message_id)

    if lesson.image:
        await post_photo(
            lesson=lesson,
            cb=cb,
            lesson_url=lesson_url,
            kb=kb,
            template=template
        )
    else:
        await bot.send_message(
            cb.from_user.id,
            template.render(lesson=lesson, url=f'{config.DOMAIN}/dashboard/watch/{lesson_url.hash}'),
            parse_mode='html',
            reply_markup=kb
        )


@dp.callback_query_handler(lambda x: 'watched|' in x.data, state='*')
@create_session
async def check_homework(cb: types.callback_query, session: SessionLocal, **kwargs):
    await bot.answer_callback_query(cb.id)
    _, studentlesson_id = cb.data.split('|')

    record = await repo.StudentLessonRepository.get_lessons_inload('id', studentlesson_id, session)
    await repo.StudentLessonRepository.edit(record, {'date_watched': datetime.datetime.now()}, session)

    if record.lesson.has_homework:
        kb = await make_kb([InlineKeyboardButton(
            'Сдать дз', callback_data=f'submit|{record.lesson.lesson_course.chat_id}|{record.id}')])
        if cb.message.photo:
            await bot.edit_message_caption(
                cb.from_user.id,
                cb.message.message_id,
                caption=cb.message.caption,
                reply_markup=kb
            )
        else:
            await bot.edit_message_text(
                cb.message.text,
                cb.from_user.id,
                cb.message.message_id,
                reply_markup=kb
            )
    else:
        await bot.delete_message(cb.message.chat.id, cb.message.message_id)


@dp.callback_query_handler(lambda x: 'submit|' in x.data, state='*')
async def request_homework(cb: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(cb.id)
    _, course_tg, student_lesson = cb.data.split('|')

    async with state.proxy() as data:
        data['course_tg'] = course_tg
        data['student_lesson'] = student_lesson
    await bot.delete_message(cb.message.chat.id, cb.message.message_id)
    await bot.send_message(
        cb.from_user.id,
        'Отправьте вашу работу'
       )

    await Homework.homework_start.set()


@dp.message_handler(state=Homework.homework_start, content_types=ContentType.ANY)
@create_session
async def get_homework(message: types.Message, state: FSMContext, session: SessionLocal, **kwargs):
    data = await state.get_data()

    record = await repo.StudentLessonRepository.get_lesson_student_inload('id', data['student_lesson'], session)
    await repo.StudentLessonRepository.edit(record, {'homework_sent': datetime.datetime.now()}, session)

    template = jinja_env.get_template('new_homework.html')
    await bot.send_message(
        data['course_tg'],
        template.render(student=record.student)
    )

    await bot.forward_message(
        data['course_tg'],
        message.chat.id,
        message.message_id
    )

    await message.reply('Спасибо')
    await state.finish()

