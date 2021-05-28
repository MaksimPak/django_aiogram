from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_parent

from bot.models.dashboard import StudentTable, CourseTable, StudentCourse, LessonTable, LessonUrlTable, StudentLesson
from bot.models.db import SessionLocal


class BaseRepository:
    table = None

    @classmethod
    async def get(cls, attribute: str, value: Any, session: SessionLocal):
        async with session:
            instance = (await session.execute(
                select(cls.table).where(getattr(cls.table, attribute) == value)
            )).scalar()

        return instance

    @classmethod
    async def get_many(cls, attribute: str, value: Any, session: SessionLocal):
        async with session:
            instances = (await session.execute(
                select(CourseTable).where(getattr(cls.table, attribute) == value)
            )).scalars()

        return instances

    @classmethod
    async def edit(cls, instance, params: dict, session: SessionLocal):
        async with session:
            session.add(instance)
            for key, value in params.items():
                setattr(instance, key, value)
            await session.commit()

    @classmethod
    async def create(cls, params: dict, session: SessionLocal):
        async with session:
            instance = cls.table(**params)
            session.add(instance)
            await session.commit()
            return instance


class StudentRepository(BaseRepository):
    table = StudentTable

    @staticmethod
    async def get_course_inload(attribute: str, value: Any, session: SessionLocal):
        # todo create deferred properties dynamically
        async with session:
            student = (await session.execute(
                select(StudentTable).where(getattr(StudentTable, attribute) == value).options(
                    selectinload(StudentTable.courses).selectinload(StudentCourse.courses)
                ))).scalar()

        return student


class CourseRepository(BaseRepository):
    table = CourseTable

    @staticmethod
    async def get_lesson_inload(attribute: str, value: Any, session: SessionLocal):
        async with session:
            course = (await session.execute(
                select(CourseTable).where(
                    getattr(CourseTable, attribute) == value
                ).options(
                    selectinload(CourseTable.lessons)
                ))).scalar()

        return course


class LessonRepository(BaseRepository):
    table = LessonTable

    @staticmethod
    async def get_course_inload(attribute: str, value: Any, session: SessionLocal):
        async with session:
            lesson = (await session.execute(
                select(LessonTable).where(getattr(LessonTable, attribute) == value).options(
                    selectinload(LessonTable.course)
                ))).scalar()
        return lesson

    @staticmethod
    async def load_unsent_from_course(course, attribute, session):
        async with session:
            lessons = (await session.execute(select(LessonTable).where(
                with_parent(course, getattr(CourseTable, attribute))
            ).filter(LessonTable.date_sent != None))).scalars().all()

        return lessons


class LessonUrlRepository(BaseRepository):
    table = LessonUrlTable

    @staticmethod
    async def get_from_lesson_and_student(lesson_id, student_id, session):
        async with session:
            lesson_url = (await session.execute(
                select(LessonUrlTable).where(LessonUrlTable.lesson_id == lesson_id,
                                             LessonUrlTable.student_id == student_id))).scalar()
        return lesson_url


class StudentLessonRepository(BaseRepository):
    table = StudentLesson

    @staticmethod
    async def get_lessons_inload(attribute, value, session):
        async with session:
            record = (await session.execute(select(StudentLesson).where(
                getattr(StudentLesson, attribute) == value
            ).options(selectinload(StudentLesson.lesson).selectinload(LessonTable.course)))).scalar()
        return record

    @staticmethod
    async def get_lesson_student_inload(attribute, value, session):
        async with session:
            record = (await session.execute(
                select(StudentLesson).where(getattr(StudentLesson, attribute) == value).options(
                    selectinload(StudentLesson.lesson).selectinload(LessonTable.course)).options(
                    selectinload(StudentLesson.student)))).scalar()
        return record
