from typing import Any

from sqlalchemy import select

from bot.models.dashboard import StudentTable, CourseTable, StudentCourse
from bot.models.db import SessionLocal


class StudentRepository:
    @staticmethod
    async def get_student(attribute: str, value: Any, session: SessionLocal):
        async with session:
            student = (await session.execute(
                select(StudentTable).where(getattr(StudentTable, attribute) == value)
            )).scalar()

        return student

    @staticmethod
    async def change_student_params(student: StudentTable, student_params: dict, session: SessionLocal):
        async with session:
            session.add(student)
            for key, value in student_params.items():
                setattr(student, key, value)
            await session.commit()

    @staticmethod
    async def create_student(student_params: dict, session: SessionLocal):
        async with session:
            student = StudentTable(**student_params)
            session.add(student)
            await session.commit()
            return student


class CourseRepository:
    @staticmethod
    async def get_courses(attribute: str, value: Any, session: SessionLocal):
        """
        method not used
        """
        async with session:
            courses = (await session.execute(
                        select(CourseTable).where(getattr(CourseTable, attribute) == value))).scalars()

        return courses


class StudentCourseRepository:
    @staticmethod
    async def create_from_courses(courses, student_id, session: SessionLocal):
        """
        method not used
        """
        async with session:
            records = session.add_all([StudentCourse(course_id=course.id, student_id=student_id) for course in courses])
            await session.commit()
            return records
