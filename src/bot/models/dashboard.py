import datetime
import enum
import uuid

from sqlalchemy import Column, String, Enum, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.mssql import TINYINT
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT, CHAR
from sqlalchemy.orm import relationship

from bot.models.db import Base


class CategoryType(enum.Enum):
    game_dev = '1'
    web = '2'


class StudentTable(Base):
    class LanguageType(enum.Enum):
        russian = '1'
        uzbek = '2'

    class ApplicationType(enum.Enum):
        admin = '1'
        telegram = '2'
        web = '3'

    __tablename__ = 'dashboard_student'

    id = Column(BIGINT, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    tg_id = Column(BIGINT, nullable=True, unique=True)
    language_type = Column(Enum(LanguageType, values_callable=lambda x: [e.value for e in x]), default=LanguageType.russian.value)
    phone = Column(String(20), unique=True)
    chosen_field = Column(Enum(CategoryType, values_callable=lambda x: [e.value for e in x]))
    application_type = Column(Enum(ApplicationType, values_callable=lambda x: [e.value for e in x]), default=ApplicationType.admin.value)
    is_client = Column(Boolean, default=False)
    checkout_date = Column(DateTime, nullable=True)
    unique_code = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)

    courses = relationship('StudentCourse', back_populates='students')
    lessons = relationship('StudentLesson', back_populates='student')


class CourseTable(Base):
    class DifficultyType(enum.Enum):
        beginner = '1'
        intermediate = '2'
        advanced = '3'

    __tablename__ = 'dashboard_course'

    id = Column(BIGINT, primary_key=True)
    name = Column(String(50))
    info = Column(LONGTEXT, nullable=True)
    hashtag = Column(String(20), nullable=True)
    category = Column(Enum(CategoryType, values_callable=lambda x: [e.value for e in x]))
    add_message = Column(String(200), nullable=True)
    difficulty = Column(Enum(DifficultyType, values_callable=lambda x: [e.value for e in x]))
    price = Column(BIGINT)
    is_free = Column(TINYINT, default=0)
    week_size = Column(Integer)
    is_started = Column(Boolean, default=False)
    is_finished = Column(Boolean, default=False)
    chat_id = Column(BIGINT, nullable=True)

    date_started = Column(DateTime, nullable=True)
    date_finished = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)

    students = relationship('StudentCourse', back_populates='courses')
    lessons = relationship('LessonTable', back_populates='course')


class LessonTable(Base):
    __tablename__ = 'dashboard_lesson'

    id = Column(BIGINT, primary_key=True)
    title = Column(String(50))
    info = Column(LONGTEXT, nullable=True)
    video = Column(String(100))
    image = Column(String(255), nullable=True)
    image_file_id = Column(String(255), nullable=True)
    course_id = Column(BIGINT, ForeignKey('dashboard_course.id'))
    has_homework = Column(Boolean, default=False)
    homework_desc = Column(LONGTEXT, nullable=True)
    date_sent = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)

    course = relationship('CourseTable', back_populates='lessons')
    students = relationship('StudentLesson', back_populates='lesson')


class LessonUrlTable(Base):
    __tablename__ = 'dashboard_lessonurl'

    student_id = Column(BIGINT, ForeignKey('dashboard_student.id'), primary_key=True)
    hash = Column(CHAR(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(BIGINT, ForeignKey('dashboard_lesson.id'), nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)


class StudentCourse(Base):
    __tablename__ = 'dashboard_studentcourse'

    id = Column(BIGINT, primary_key=True)
    course_id = Column(BIGINT, ForeignKey('dashboard_course.id'), nullable=False)
    student_id = Column(BIGINT, ForeignKey('dashboard_student.id'), nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)

    courses = relationship('CourseTable', back_populates='students')
    students = relationship('StudentTable', back_populates='courses')


class StudentLesson(Base):
    __tablename__ = 'dashboard_studentlesson'

    id = Column(BIGINT, primary_key=True)
    student_id = Column(BIGINT, ForeignKey('dashboard_student.id'))
    lesson_id = Column(BIGINT, ForeignKey('dashboard_lesson.id'))
    date_received = Column(DateTime, nullable=True)
    date_watched = Column(DateTime, nullable=True)
    homework_sent = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)

    lesson = relationship('LessonTable', back_populates='students')
    student = relationship('StudentTable', back_populates='lessons')
