import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_parent

from bot.models.dashboard import StudentTable, CourseTable, StudentCourse, LessonTable, LessonUrlTable, StudentLesson
from bot.models.db import SessionLocal


class BaseRepository:
    table = None

    @classmethod
    async def get(cls, attribute: str, value: Any, session: SessionLocal):
        """
        SELECT from cls.table by specified attribute. Return one object
        """
        async with session:
            instance = (await session.execute(
                select(cls.table).where(getattr(cls.table, attribute) == value)
            )).scalar()

        return instance

    @classmethod
    async def get_many(cls, attribute: str, value: Any, session: SessionLocal):
        """
        SELECT from cls.table by specified attribute. Return many objects
        """
        async with session:
            instances = (await session.execute(
                select(CourseTable).where(getattr(cls.table, attribute) == value)
            )).scalars()

        return instances

    @classmethod
    async def edit(cls, instance, params: dict, session: SessionLocal):
        """
        Edit object with passed params
        """
        async with session:
            session.add(instance)
            for key, value in params.items():
                setattr(instance, key, value)
            await session.commit()

    @classmethod
    async def create(cls, params: dict, session: SessionLocal):
        """
        INSERT record
        """
        async with session:
            instance = cls.table(**params)
            session.add(instance)
            await session.commit()
            return instance


class StudentRepository(BaseRepository):
    table = StudentTable

    @staticmethod
    async def get_course_inload(attribute: str, value: Any, session: SessionLocal):
        """
        Emits a second (or more) SELECT statement to load Courses at once from Student
        and StudentCourse tables
        """
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
        """
        Emits a second (or more) SELECT statement to load Lessons at once from CourseTable
        """
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
        """
        Loads courses along with lessons
        """
        async with session:
            lesson = (await session.execute(
                select(LessonTable).where(getattr(LessonTable, attribute) == value).options(
                    selectinload(LessonTable.course)
                ))).scalar()
        return lesson

    @staticmethod
    async def get_next(attribute: str, value: Any, course_id, session: SessionLocal):
        """
        Return first matching query
        """
        async with session:
            lesson = (await session.execute(
                select(LessonTable).filter(getattr(LessonTable, attribute) > value, LessonTable.course_id == course_id)
                    .order_by(LessonTable.id).options(
                    selectinload(LessonTable.course)
                ))).scalars().first()
        return lesson

    @staticmethod
    async def get_student_lessons(student_id, course_id, session):
        async with session:
            lessons = (await session.execute(
                select(LessonTable).join_from(LessonTable, StudentLesson, LessonTable.id == StudentLesson.lesson_id)
                .filter(StudentLesson.student_id == student_id, LessonTable.course.has(id=course_id)).order_by('id')
            )).scalars()

        return lessons


class LessonUrlRepository(BaseRepository):
    table = LessonUrlTable

    @staticmethod
    async def get_one(lesson_id, student_id, session):
        """
        Select from LessonUrl table by specifying two criterias
        """
        async with session:
            lesson_url = (await session.execute(
                select(LessonUrlTable).where(LessonUrlTable.lesson_id == lesson_id,
                                             LessonUrlTable.student_id == student_id))).scalar()
        return lesson_url

    @staticmethod
    async def get_or_create(lesson_id, student_id, session):
        lesson_url = await LessonUrlRepository.get_one(
            lesson_id, student_id, session)

        if not lesson_url:
            lesson_url = await LessonUrlRepository.create(
                {'student_id': student_id, 'lesson_id': lesson_id}, session)

        return lesson_url


class StudentLessonRepository(BaseRepository):
    table = StudentLesson

    @staticmethod
    async def get_or_create(lesson_id, student_id, session):
        studentlesson = await StudentLessonRepository.get_one(
            lesson_id, student_id, session)

        if not studentlesson:
            await StudentLessonRepository.create(
                {'student_id': student_id, 'lesson_id': lesson_id, 'date_sent': datetime.datetime.now()}, session)

            studentlesson = await StudentLessonRepository.get_one(
                lesson_id, student_id, session)

        return studentlesson

    @staticmethod
    async def get_one(lesson_id, student_id, session):
        """
        Select from LessonUrl table by specifying two criterias
        """
        async with session:
            studentlesson = (await session.execute(
                select(StudentLesson).where(StudentLesson.lesson_id == lesson_id,
                                            StudentLesson.student_id == student_id).options(
                    selectinload(StudentLesson.lesson)).options(
                    selectinload(StudentLesson.student)
                ))).scalar()
        return studentlesson

    @staticmethod
    async def get_lesson_student_inload(attribute, value, session):
        """
        Loads lesson and student from StudentLesson table, course from Lesson table
        """
        async with session:
            record = (await session.execute(
                select(StudentLesson).where(getattr(StudentLesson, attribute) == value).options(
                    selectinload(StudentLesson.lesson).selectinload(LessonTable.course)).options(
                    selectinload(StudentLesson.student)))).scalar()
        return record
