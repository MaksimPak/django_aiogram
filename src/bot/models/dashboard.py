import datetime
import enum
import uuid

from sqlalchemy import Column, String, Enum, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import TEXT, VARCHAR
from sqlalchemy.orm import relationship

from bot.models.db import Base


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)


class CategoryType(BaseModel):
    __tablename__ = 'dashboard_categorytype'

    title = Column(String(50), unique=True)
    uz_title = Column(String(50), unique=True, nullable=True)

    student = relationship('StudentTable', back_populates='category')

    def get_title(self, lang: str):
        return self.title if lang == 'ru' else self.uz_title


class StudentTable(BaseModel):
    class LanguageType(enum.Enum):
        ru = '1'
        uz = '2'

    class ApplicationType(enum.Enum):
        admin = '1'
        telegram = '2'
        web = '3'

    __tablename__ = 'dashboard_student'

    first_name = Column(String(50))
    last_name = Column(String(50), nullable=True)
    city = Column(String(50))
    tg_id = Column(Integer, nullable=True, unique=True)
    language_type = Column(Enum(LanguageType, values_callable=lambda x: [e.value for e in x]), default=LanguageType.ru.value)
    phone = Column(String(20), unique=True)
    chosen_field_id = Column(Integer, ForeignKey('dashboard_categorytype.id', ondelete='RESTRICT'))
    application_type = Column(Enum(ApplicationType, values_callable=lambda x: [e.value for e in x]), default=ApplicationType.admin.value)
    is_client = Column(Boolean, default=False)
    checkout_date = Column(DateTime, nullable=True)
    unique_code = Column(String(255), nullable=True, unique=True)
    promo_id = Column(Integer, ForeignKey('dashboard_promotion.id', ondelete='SET NULL'), nullable=True)

    courses = relationship('StudentCourse', back_populates='students')
    lessons = relationship('StudentLesson', back_populates='student')
    category = relationship('CategoryType', back_populates='student')
    promo = relationship('PromotionTable', back_populates='student')

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}' if self.last_name else self.first_name


class CourseTable(BaseModel):
    class DifficultyType(enum.Enum):
        beginner = '1'
        intermediate = '2'
        advanced = '3'

    __tablename__ = 'dashboard_course'

    name = Column(String(50))
    info = Column(TEXT, nullable=True)
    hashtag = Column(String(20), nullable=True)
    category_id = Column(Integer, ForeignKey('dashboard_categorytype.id', ondelete='RESTRICT'))
    start_message = Column(String(200), nullable=True)
    end_message = Column(String(200), nullable=True)
    difficulty = Column(Enum(DifficultyType, values_callable=lambda x: [e.value for e in x]))
    price = Column(Integer)
    is_free = Column(Boolean, default=False)
    week_size = Column(Integer)
    is_started = Column(Boolean, default=False)
    is_finished = Column(Boolean, default=False)
    chat_id = Column(Integer, nullable=True)
    autosend = Column(Boolean, default=False)

    date_started = Column(DateTime, nullable=True)
    date_finished = Column(DateTime, nullable=True)

    students = relationship('StudentCourse', back_populates='courses')
    lessons = relationship('LessonTable', back_populates='course')
    promo = relationship('PromotionTable', back_populates='course')


class PromotionTable(BaseModel):
    __tablename__ = 'dashboard_promotion'

    title = Column(String(50))
    video = Column(String(100))
    thumbnail = Column(String(100), nullable=True)
    description = Column(TEXT)
    course_id = Column(Integer, ForeignKey('dashboard_course.id', ondelete='SET NULL'), nullable=True)
    counter = Column(Integer, default=0)
    registration_button = Column(Boolean, default=False)
    link = Column(String(255), nullable=True)
    video_file_id = Column(String(255), nullable=True)
    unique_code = Column(String(255), nullable=True, unique=True)

    student = relationship('StudentTable', back_populates='promo')
    course = relationship('CourseTable', back_populates='promo')


class LessonTable(BaseModel):
    __tablename__ = 'dashboard_lesson'

    title = Column(String(50))
    info = Column(TEXT, nullable=True)
    video = Column(String(100))
    image = Column(String(255), nullable=True)
    image_file_id = Column(String(255), nullable=True)
    course_id = Column(Integer, ForeignKey('dashboard_course.id'))
    has_homework = Column(Boolean, default=False)
    homework_desc = Column(TEXT, nullable=True)
    date_sent = Column(DateTime, nullable=True)

    course = relationship('CourseTable', back_populates='lessons')
    students = relationship('StudentLesson', back_populates='lesson')


class LessonUrlTable(BaseModel):
    __tablename__ = 'dashboard_lessonurl'

    student_id = Column(Integer, ForeignKey('dashboard_student.id'), primary_key=True)
    hash = Column(VARCHAR(length=36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(Integer, ForeignKey('dashboard_lesson.id'), nullable=False)


class StudentCourse(BaseModel):
    __tablename__ = 'dashboard_studentcourse'

    course_id = Column(Integer, ForeignKey('dashboard_course.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('dashboard_student.id'), nullable=False)

    courses = relationship('CourseTable', back_populates='students')
    students = relationship('StudentTable', back_populates='courses')


class StudentLesson(BaseModel):
    __tablename__ = 'dashboard_studentlesson'

    student_id = Column(Integer, ForeignKey('dashboard_student.id'))
    lesson_id = Column(Integer, ForeignKey('dashboard_lesson.id'))

    date_sent = Column(DateTime, nullable=True)
    date_watched = Column(DateTime, nullable=True)
    homework_sent = Column(DateTime, nullable=True)

    lesson = relationship('LessonTable', back_populates='students')
    student = relationship('StudentTable', back_populates='lessons')


class QuizAnswerTable(BaseModel):
    __tablename__ = 'dashboard_quizanswer'

    student_id = Column(Integer, ForeignKey('dashboard_student.id', ondelete='CASCADE'), nullable=False)
    score = Column(Integer, default=0)
    answers = Column(TEXT, nullable=True)
