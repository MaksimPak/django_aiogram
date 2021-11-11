import datetime
from contextlib import suppress
from typing import Any

from sqlalchemy import select, func, or_, and_
from sqlalchemy import exc
from sqlalchemy.orm import selectinload, with_parent, subqueryload, contains_eager

from bot.db.schemas import (
    StudentTable, CourseTable, StudentCourse,
    LessonTable, StudentLesson,
    ContactTable, FormTable, FormQuestionTable, FormAnswerTable,
    ContactFormTable, CompanyTable, AssetTable, ContactAssetTable,
    MessageHistory
)
from bot.db.config import SessionLocal


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
                select(cls.table).where(getattr(cls.table, attribute) == value)
            )).scalars()

        return instances

    @classmethod
    async def is_exist(cls, attribute: str, value: Any, session: SessionLocal):
        async with session:
            instance = (await session.execute(
                select(getattr(cls.table, attribute)).where(
                    getattr(cls.table, attribute) == value))).scalar()

            return bool(instance)

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

    @classmethod
    async def delete(cls, instance, session):
        async with session:
            await session.delete(instance)
            await session.commit()


class ContactRepository(BaseRepository):
    table = ContactTable

    @classmethod
    async def get(cls, attribute: str, value: Any, session: SessionLocal):
        async with session:
            instance = (await session.execute(
                select(cls.table).where(getattr(cls.table, attribute) == value)
                .options(selectinload(ContactTable.student))
            )).scalar()

        return instance


    @staticmethod
    async def get_or_create(
            tg_id: int,
            first_name: str,
            last_name: str,
            session: SessionLocal,
    ):
        contact = await ContactRepository.get(
            'tg_id', tg_id, session)

        if not contact:
            contact = await ContactRepository.create({
                'first_name': first_name,
                'last_name': last_name,
                'tg_id': tg_id
            }, session)

        async with session:
            contact = (await session.execute(
                select(ContactTable).where(
                    ContactTable.id == contact.id).options(selectinload(ContactTable.student))
            )).scalar()

        return contact

    @staticmethod
    async def load_student_data(attr: Any, value, session: SessionLocal):
        """
        load contact with student relationship
        """
        async with session:
            contact = (await session.execute(
                select(ContactTable).where(
                    getattr(ContactTable, attr) == value).options(
                    selectinload(ContactTable.student).options(
                        selectinload(StudentTable.company),
                        selectinload(StudentTable.courses)
                        .selectinload(StudentCourse.courses)
                        .selectinload(CourseTable.lessons)))
            )).scalar()

        return contact


class StudentRepository(BaseRepository):
    table = StudentTable

    @staticmethod
    async def load_with_lc(attribute: str, value: any, session: SessionLocal):
        async with session:
            student = (await session.execute(
                select(StudentTable).where(getattr(StudentTable, attribute) == value).options(
                    selectinload(StudentTable.learning_centre)
                )
            )).scalar()
        return student

    @staticmethod
    async def load_with_contact(attr: Any, value, session):
        async with session:
            student = (await session.execute(
                    select(StudentTable).where(getattr(StudentTable, attr) == value).options(
                        selectinload(StudentTable.contact)
                    )
                )).scalar()
        return student

    @staticmethod
    async def get_course_inload(attribute: str, value: Any, session: SessionLocal):
        """
        Emits a second (or more) SELECT statement to load Courses at once from Student
        and StudentCourse tables
        """
        async with session:
            student = (await session.execute(
                select(StudentTable).where(getattr(StudentTable, attribute) == value).options(
                    selectinload(StudentTable.courses).selectinload(StudentCourse.courses)
                    .selectinload(CourseTable.lessons)
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
    async def get_course_lessons(course_id, session):
        async with session:
            lessons = (await session.execute(
                select(LessonTable).filter(LessonTable.course_id == course_id)
            )).scalars()

        return lessons

    @staticmethod
    async def get_student_lessons(student_id, course_id, session):
        async with session:
            lessons = (await session.execute(
                select(LessonTable).join_from(LessonTable, StudentLesson, LessonTable.id == StudentLesson.lesson_id)
                .filter(StudentLesson.student_id == student_id, LessonTable.course.has(id=course_id)).order_by('id')
            )).scalars()

        return lessons


class StudentLessonRepository(BaseRepository):
    table = StudentLesson

    @staticmethod
    async def student_lessons(student_id, course_id, session):
        async with session:
            lessons = (await session.execute(
                select(StudentLesson).join(StudentLesson.lesson)
                .options(contains_eager(StudentLesson.lesson))
                .filter(
                    StudentLesson.lesson.has(course_id=course_id),
                    StudentLesson.student_id == student_id)
                .order_by(LessonTable.id)
            )).all()

        return lessons

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
    async def finished_lesson_count(course_id, student_id, session):
        async with session:
            count = (await session.execute(select(func.count()).select_from(StudentLesson).where(
                StudentLesson.student_id == student_id,
            ).join_from(StudentLesson, LessonTable, StudentLesson.lesson_id == LessonTable.id).filter(
                StudentLesson.date_sent != None,
                StudentLesson.date_watched != None,
                LessonTable.course_id == course_id,
                or_(and_(LessonTable.homework_desc != None, StudentLesson.homework_sent != None),
                    LessonTable.homework_desc == None)
            ))).scalar()

        return count

    @staticmethod
    async def lesson_data(attribute, value, session):
        """
        Loads lesson and student from StudentLesson table, course from Lesson table
        """
        async with session:
            record = (await session.execute(
                select(StudentLesson).where(getattr(StudentLesson, attribute) == value).options(
                    selectinload(StudentLesson.lesson)
                    .options(selectinload(LessonTable.course), selectinload(LessonTable.form))
                    ).options(
                    selectinload(StudentLesson.student)))).scalar()
        return record


class LearningCentreRepository(BaseRepository):
    table = CompanyTable

    @staticmethod
    async def get_lcs(session):
        async with session:
            lcs = (await session.execute(
                select(CompanyTable)
            )).scalars()
        return lcs


class StudentCourseRepository(BaseRepository):
    table = StudentCourse

    @staticmethod
    async def exists(student_id, course_id, session):
        async with session:
            record = (await session.execute(
                select(StudentCourse.id).where(
                    StudentCourse.course_id == course_id,
                    StudentCourse.student_id == student_id
                )
            )).scalar()

        return bool(record)

    @staticmethod
    async def bunch_create(student_id, courses, session):
        async with session:
            session.add_all(
                [
                    StudentCourse(student_id=student_id, course_id=course) for course in courses
                ]
            )
            await session.commit()

    @staticmethod
    async def create_record(student_id, course_id, session):
        async with session:
            instance = StudentCourse(student_id=student_id, course_id=course_id)
            session.add(instance)
            await session.commit()
        return instance

    @staticmethod
    async def get_record(student_id, course_id, session):
        async with session:
            record = (await session.execute(
                select(StudentCourse).where(
                    StudentCourse.student_id == student_id,
                    StudentCourse.course_id == course_id,
                ).options(selectinload(StudentCourse.students))
                .options(selectinload(StudentCourse.courses)))).scalar()
        return record

    @staticmethod
    async def filter_from_relationship(relationship, session: SessionLocal):
        # todo rewrite
        async with session:
            stmt = select(func.count(LessonTable.id), CourseTable, StudentCourse) \
                .join_from(StudentCourse, CourseTable, StudentCourse.course_id == CourseTable.id) \
                .join_from(StudentCourse, LessonTable, LessonTable.course_id == StudentCourse.course_id).where(
                with_parent(relationship, StudentTable.courses),
                CourseTable.is_started == True).group_by(LessonTable.course_id, CourseTable.id, StudentCourse.id)
            filtered = (await session.execute(stmt)).all()

        return filtered


class FormRepository(BaseRepository):
    table = FormTable

    @staticmethod
    async def get_public(session: SessionLocal):
        async with session:
            forms = (
                await session.execute(
                    select(FormTable).where(FormTable.type == 'public'))).scalars()
        return forms

    @staticmethod
    async def get_questions(form_id, session):
        async with session:
            form = (
                await session.execute(
                    select(FormTable).where(FormTable.id == form_id)
                    .options(selectinload(FormTable.questions).selectinload(FormQuestionTable.answers)))
            ).scalar()
        return form


class FormQuestionRepository(BaseRepository):
    table = FormQuestionTable

    @staticmethod
    async def next_question(position, form_id, session):
        async with session:
            next_question = (
                await session.execute(
                    select(FormQuestionTable).where(
                        FormQuestionTable.form_id == form_id,
                        FormQuestionTable.position > position
                    ).options(selectinload(FormQuestionTable.answers))
                    .options(selectinload(FormQuestionTable.form))
                    .order_by(FormQuestionTable.position, FormQuestionTable.id)
                )
            ).scalar()

        return next_question

    @classmethod
    async def get(cls, attribute: str, value: Any, session: SessionLocal):
        async with session:
            question = (await session.execute(
                select(cls.table).where(getattr(cls.table, attribute) == value)
                .options(selectinload(cls.table.answers))
                .options(selectinload(cls.table.form))
            )).scalar()

        return question


class FormAnswerRepository(BaseRepository):
    table = FormAnswerTable

    @staticmethod
    async def load_all_relationships(answer_id, session):
        async with session:
            answer = (
                await session.execute(
                    select(FormAnswerTable).where(FormAnswerTable.id == answer_id)
                    .options(
                        selectinload(FormAnswerTable.question)
                        .selectinload(FormQuestionTable.form)
                        .selectinload(FormTable.questions)
                    )
                )
            ).scalar()
        return answer


class ContactFormRepository(BaseRepository):
    table = ContactFormTable

    @staticmethod
    async def exists(contact_id, form_id, session):
        async with session:
            is_record = (await session.execute(
                select(ContactFormTable.id).where(
                    ContactFormTable.contact_id == contact_id,
                    ContactFormTable.form_id == form_id
                )
            )).first()
        return is_record

    @staticmethod
    async def get_one(contact_id, form_id, session):
        async with session:
            record = (await session.execute(
                select(ContactFormTable).where(
                    ContactFormTable.contact_id == contact_id,
                    ContactFormTable.form_id == form_id
                )
            )).scalar()
        return record

    @staticmethod
    async def create_or_edit(contact_id, form_id, data, session):
        student_form = await ContactFormRepository.get_one(
            contact_id, form_id, session)

        payload = {
            'contact_id': contact_id,
            'form_id': form_id,
            'score': data['score'],
            'data': data['answers'],
        }
        if not student_form:
            student_form = await ContactFormRepository.create(payload, session)
        else:
            student_form = await ContactFormRepository.edit(student_form, payload, session)

        return student_form


class AssetRepository(BaseRepository):
    table = AssetTable


class ContactAssetRepository(BaseRepository):
    table = ContactAssetTable

    @staticmethod
    async def unique_create(contact_id, asset_id, session):
        with suppress(exc.IntegrityError):
            contact_asset = await ContactAssetRepository.create({
                'contact_id': contact_id,
                'asset_id': asset_id
            }, session)

            return contact_asset

    @staticmethod
    async def contact_assets(contact_id, session):
        async with session:
            assets = (await session.execute(
                select(ContactAssetTable).where(ContactAssetTable.contact_id == contact_id)
                .options(selectinload(ContactAssetTable.asset))
            )).scalars()

        return assets


class MessageHistoryRepository(BaseRepository):
    table = MessageHistory
