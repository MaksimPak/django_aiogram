import re

from aiogram import types
from aiogram.dispatcher.filters import Filter

from bot import repository as repo
from bot.decorators import create_session

COURSE_PATTERN = re.compile(r'^course(\d+)')
LESSON_PATTERN = re.compile(r'^lesson(\d+)')


class UnknownContact(Filter):
    @create_session
    async def check(self, message: types.Message, session):
        contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)
        if contact:
            await repo.ContactRepository.edit(contact, {
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'blocked_bot': False
            }, session)
        return not contact


class CourseStudent(Filter):
    @create_session
    async def check(self, message: types.Message, session, *args):
        msg_args = message.get_args() if message.get_args() else ''
        match = re.match(COURSE_PATTERN, msg_args)
        contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)

        if not contact.student or not match:
            return False

        return {'deep_link': match}


class LessonStudent(Filter):
    @create_session
    async def check(self, message: types.Message, session, *args):
        msg_args = message.get_args() if message.get_args() else ''
        match = re.match(LESSON_PATTERN, msg_args)
        contact = await repo.ContactRepository.get('tg_id', message.from_user.id, session)

        if not contact.student or not match:
            return False

        lesson = await repo.LessonRepository.get('id', int(match.group(1)), session)
        is_allowed = await repo.StudentCourseRepository.exists(
            contact.student.id,
            lesson.course_id,
            session
        )

        return {'deep_link': match} if is_allowed else False
