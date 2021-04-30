import enum

from sqlalchemy import Column, String, Enum, Boolean, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT, CHAR
from sqlalchemy.orm import relationship

from bot.models.db import Base


class StudentTable(Base):
    class ApplicationType(enum.Enum):
        web = '1'
        telegram = '2'

    __tablename__ = 'dashboard_student'

    id = Column(BIGINT, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    tg_id = Column(BIGINT, nullable=True)
    phone = Column(String(20))
    application_type = Column(Enum(ApplicationType, values_callable=lambda x: [e.value for e in x]), default=ApplicationType.web.value)
    is_client = Column(Boolean)

    courses = relationship('StudentCourse', back_populates='students')
    lessons = relationship('StudentLesson', back_populates='students')


class StreamTable(Base):
    __tablename__ = 'dashboard_stream'

    id = Column(BIGINT, primary_key=True)
    name = Column(String(50))


class CourseTable(Base):
    class CategoryType(enum.Enum):
        game_dev = '1'
        web = '2'

    class DifficultyType(enum.Enum):
        beginner = '1'
        intermediate = '2'
        advanced = '3'

    __tablename__ = 'dashboard_course'

    id = Column(BIGINT, primary_key=True)
    name = Column(String(50))
    info = Column(LONGTEXT, nullable=True)
    category = Column(Enum(CategoryType, values_callable=lambda x: [e.value for e in x]))
    difficulty = Column(Enum(DifficultyType), values_callable=lambda x: [e.value for e in x])
    price = Column(BIGINT)

    students = relationship('StudentCourse', back_populates='courses')


class LessonTable(Base):
    __tablename__ = 'dashboard_lesson'

    id = Column(BIGINT, primary_key=True)
    title = Column(String(50))
    info = Column(LONGTEXT, nullable=True)

    students = relationship('StudentLesson', back_populates='lessons')


class LessonUrlTable(Base):
    __tablename__ = 'dashboard_lessonurl'

    student_id = Column(BIGINT, ForeignKey('dashboard_student.id'), primary_key=True)
    hash = Column(CHAR(32), nullable=False)
    lesson_id = Column(BIGINT, ForeignKey('dashbpoard_lesson.id'), nullable=False)


class StudentCourse(Base):
    __tablename__ = 'dashboard_studentcourse'

    id = Column(BIGINT, primary_key=True)
    course_id = Column(BIGINT, ForeignKey('dashboard_course.id'), nullable=False)
    stream_id = Column(BIGINT, ForeignKey('dashboard_stream.id'))
    student_id = Column(BIGINT, ForeignKey('dashboard_student.id'), nullable=False)

    students = relationship('StudentTable', back_populates='courses')
    courses = relationship('CourseTable', back_populates='students')


class StudentLesson(Base):
    __tablename__ = 'dashboard_studentlesson'

    id = Column(BIGINT, primary_key=True)
    has_homework = Column(Boolean, default=False)
    lesson_id = Column(BIGINT, ForeignKey('dashboard_lesson.id'), nullable=False)
    student_id = Column(BIGINT, ForeignKey('dashboard_student.id'), nullable=False)

    students = relationship('StudentTable', back_populates='lessons')
    lessons = relationship('LessonTable', back_populates='students')
