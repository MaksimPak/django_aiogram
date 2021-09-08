import datetime
from typing import Any

from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload, with_parent

from bot.models.dashboard import (
    StudentTable, CourseTable, StudentCourse,
    LessonTable, LessonUrlTable, StudentLesson,
    PromotionTable, ContactTable,
    FormTable, FormQuestionTable, FormAnswerTable, ContactFormTable, LearningCentreTable
)
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
    async def load_student(contact_id: int, session: SessionLocal):
        """
        load contact with student relationship
        """
        async with session:
            contact = (await session.execute(
                select(ContactTable).where(
                    ContactTable.id == contact_id).options(selectinload(ContactTable.student))
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
                                             LessonUrlTable.student_id == student_id)
                .options(selectinload(LessonUrlTable.lesson)))).scalar()
        return lesson_url

    @staticmethod
    async def get_or_create(lesson_id, student_id, session):
        lesson_url = await LessonUrlRepository.get_one(
            lesson_id, student_id, session)

        if not lesson_url:
            await LessonUrlRepository.create(
                {'student_id': student_id, 'lesson_id': lesson_id}, session
            )
            lesson_url = await LessonUrlRepository.get_one(lesson_id, student_id, session)

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
    async def finished_lesson_count(course_id, student_id, session):
        async with session:
            count = (await session.execute(select(func.count()).select_from(StudentLesson).where(
                StudentLesson.student_id == student_id,
            ).join_from(StudentLesson, LessonTable, StudentLesson.lesson_id == LessonTable.id).filter(
                StudentLesson.date_sent != None,
                StudentLesson.date_watched != None,
                LessonTable.course_id == course_id,
                or_(and_(LessonTable.has_homework == True, StudentLesson.homework_sent != None),
                    LessonTable.has_homework == None)
            ))).scalar()

        return count

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


class LearningCentreRepository(BaseRepository):
    table = LearningCentreTable

    @staticmethod
    async def get_lcs(session):
        async with session:
            lcs = (await session.execute(
                select(LearningCentreTable)
            )).scalars()
        return lcs


class PromotionRepository(BaseRepository):
    table = PromotionTable


class StudentCourseRepository(BaseRepository):
    table = StudentCourse

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
    async def next_question(question_id, form_id, session):
        async with session:
            next_question = (
                await session.execute(
                    select(FormQuestionTable).where(
                        FormQuestionTable.form_id == form_id,
                        FormQuestionTable.id > question_id
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
