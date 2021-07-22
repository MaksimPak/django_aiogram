import re
from contextlib import suppress

from aiogram import types
from aiogram.dispatcher.filters import CommandStart, ChatTypeFilter
from aiogram.utils.exceptions import Unauthorized

from bot import repository as repo
from bot.decorators import create_session
from bot.misc import dp, jinja_env, bot, i18n
from bot.models.db import SessionLocal
from bot.serializers import KeyboardGenerator
from bot.views import start_reg

_ = i18n.gettext


@dp.message_handler(CommandStart(re.compile(r'\d+')), ChatTypeFilter(types.ChatType.PRIVATE))
@create_session
async def register_deep_link(
        message: types.Message,
        session: SessionLocal,
        **kwargs
):
    """
    Saves user tg_id into db if start was passed w/ deep link
    """
    student = await repo.StudentRepository.get('unique_code', message.get_args(), session)
    kb = await KeyboardGenerator.main_kb()

    if student and not student.tg_id:
        await repo.StudentRepository.edit(student, {'tg_id': message.from_user.id}, session)
        await message.reply(
            _('Спасибо {first_name},'
              'вы были успешно зарегистрированы в боте').format(first_name=message.from_user.first_name),
            reply_markup=kb)
    elif not student:
        await message.reply(_('Неверный инвайт код'))
    elif student and student.tg_id:
        await message.reply(_('Вы уже зарегистрированы. Выберите опцию'), reply_markup=kb)


@dp.message_handler(CommandStart(re.compile(r'promo_\d+')), ChatTypeFilter(types.ChatType.PRIVATE))
@create_session
async def promo_deep_link(
        message: types.Message,
        session: SessionLocal,
        **kwargs
):
    promotion = await repo.PromotionRepository.get('unique_code', message.get_args().split('_')[1], session)
    student = await repo.StudentRepository.get('tg_id', message.from_user.id, session)
    if not promotion:
        await message.reply(_('Неверный инвайт код'))

    text = jinja_env.get_template('promo_text.html').render(promo=promotion)

    with suppress(Unauthorized):
        await repo.PromotionRepository.edit(promotion, {'counter': promotion.counter + 1}, session)
        await bot.send_video(
            message.from_user.id,
            promotion.video_file_id,
            caption=text,
            parse_mode='html',
        )

        if not student:
            contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
            if not contact:
                await repo.ContactRepository.create({
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'tg_id': message.from_user.id,
                    'data': {
                        'promo': promotion.id,
                        'courses': [promotion.course_id] if promotion.course_id else []
                    }
                }, session)
            else:
                if promotion.course_id and promotion.course_id not in contact.data['courses']:
                    contact.data['courses'].append(promotion.course_id)

                await repo.ContactRepository.edit(contact, {
                    'data': {
                        'promo': promotion.id,
                        'courses': contact.data['courses']
                    }
                }, session)

            await message.reply(
                _('Спасибо за ваш интерес! Пройдите регистрацию нажав '
                  '/start и получите мгновенный доступ к бесплатным курсам Megaskill'),
            )

        else:
            if promotion.course_id:
                studentcourse = await repo.StudentCourseRepository.get_record(student.id, promotion.course_id, session)
                if not studentcourse:
                    await repo.StudentCourseRepository.create_record(student.id, promotion.course_id, session)
            await message.reply(promotion.start_message)
            await start_reg(message, **kwargs)
