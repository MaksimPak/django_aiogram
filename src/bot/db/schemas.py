import datetime
import enum
from itertools import chain

import sqlalchemy_json
from geoalchemy2 import Geometry
from sqlalchemy import Column, String, Enum, Boolean, ForeignKey, DateTime, Integer, types, SmallInteger, \
    CheckConstraint, select
from sqlalchemy.dialects.postgresql import TEXT, JSONB, ARRAY
from sqlalchemy.orm import relationship, validates, deferred

from bot import config
from bot.db.config import Base


class IntEnum(types.TypeDecorator):
    impl = Integer

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)


class AccessLevel(enum.Enum):
    contact = 1
    lead = 2
    client = 3


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now, nullable=True)


class CompanyTable(BaseModel):
    __tablename__ = 'companies_company'

    title = Column(String(50), unique=True)
    uz_title = Column(String(50), unique=True, nullable=True)
    photo = Column(String(255), nullable=True)
    description = Column(TEXT, nullable=False)
    link = Column(String(255), nullable=True)
    slug = Column(String(50), nullable=False)

    student = relationship('StudentTable', back_populates='company')

    def get_title(self, lang: str):
        return self.title if lang == 'ru' else self.uz_title


class ContactTable(BaseModel):
    __tablename__ = 'contacts_contact'

    first_name = Column(String(255))
    last_name = Column(String(255), nullable=True)
    tg_id = Column(Integer, nullable=True, unique=True)
    data = Column(sqlalchemy_json.mutable_json_type(dbtype=JSONB, nested=True), nullable=True, default=dict)
    is_registered = Column(Boolean, default=False)
    blocked_bot = Column(Boolean, default=False)

    student = relationship('StudentTable', back_populates='contact', uselist=False)
    contact_asset = relationship('ContactAssetTable', back_populates='contact')

    @property
    def access_level(self):
        if not self.student:
            access_level = 1
        elif self.student and self.student.is_client is False:
            access_level = 2
        else:
            access_level = 3

        return access_level

    def get_status(self, modificator: int = 0):
        mapping = {
            1: 'Незарегистрированный',
            2: 'Лид',
            3: 'Клиент'
        }
        try:
            return mapping[self.access_level + modificator]
        except KeyError:
            raise ValueError('The desired status is not considered')

    @property
    def profile_link(self):
        return f'{config.DOMAIN}/admin/contacts/contact/{self.id}/change/'


class StudentTable(BaseModel):
    class LanguageType(enum.Enum):
        ru = '1'
        uz = '2'

    class ApplicationType(enum.Enum):
        admin = '1'
        telegram = '2'
        web = '3'

    __tablename__ = 'users_student'

    first_name = Column(String(50))
    last_name = Column(String(50), nullable=True)
    city = Column(String(50))
    phone = Column(String(20), unique=True)
    company_id = Column(Integer, ForeignKey('companies_company.id', ondelete='RESTRICT'))
    application_type = Column(Enum(ApplicationType, values_callable=lambda x: [e.value for e in x]),
                              default=ApplicationType.admin.value)
    is_client = Column(Boolean, default=False)
    checkout_date = Column(DateTime, nullable=True)
    unique_code = Column(String(255), nullable=True, unique=True)
    invite_link = Column(String(255), nullable=True)
    contact_id = Column(Integer, ForeignKey('contacts_contact.id'))
    location = Column(Geometry('POINT'), nullable=True)
    comment = Column(String(255), nullable=True)
    games = Column(ARRAY(String(50)), nullable=True)

    courses = relationship('StudentCourse', back_populates='students',
                           order_by='[StudentCourse.priority_date_deferred, StudentCourse.created_at]')
    lessons = relationship('StudentLesson', back_populates='student')
    company = relationship('CompanyTable', back_populates='student')
    contact = relationship('ContactTable', back_populates='student')

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}' if self.last_name else self.first_name


class CourseCategoryTable(BaseModel):
    __tablename__ = 'courses_coursecategory'

    name = Column(String(100))


class LessonCategoryTable(BaseModel):
    __tablename__ = 'courses_lessoncategory'

    name = Column(String(100))

    lessons = relationship('LessonTable', back_populates='category')


class CourseTable(BaseModel):
    __tablename__ = 'courses_course'

    class LevelsExtended(enum.Enum):
        controllable = 4

    # Course needs extra level of access which was not considered
    # in base AccessLevel. Since alchemy expects python enums
    # for column, base enum had to be extended.
    # python does not allow inheriting enums, i.e. new enum created
    CourseLevels = enum.Enum('CourseLevels', [(x.name, x.value) for x in chain(AccessLevel, LevelsExtended)])  # noqa

    name = Column(String(50))
    description = Column(TEXT, nullable=False)
    code = Column(String(20), nullable=True)
    company_id = Column(Integer, ForeignKey('companies_company.id', ondelete='RESTRICT'))
    category_id = Column(Integer, ForeignKey('courses_coursecategory.id', ondelete='RESTRICT'))
    data = Column(sqlalchemy_json.mutable_json_type(
        dbtype=JSONB, nested=True), nullable=False, default=lambda: {
        'start_message': '',
        'end_message': '',
        'price': 0
    })
    date_started = Column(DateTime, nullable=True)
    date_finished = Column(DateTime, nullable=True)
    access_level = Column(IntEnum(CourseLevels), nullable=False, default=CourseLevels.client.value)  # noqa

    chat_id = Column(Integer, nullable=False)
    set_priority_date = Column(DateTime, nullable=True)

    students = relationship('StudentCourse', back_populates='courses')
    lessons = relationship('LessonTable', back_populates='course',
                           order_by='[LessonTable.id]')


class LessonTable(BaseModel):
    __tablename__ = 'courses_lesson'

    name = Column(String(50))
    description = Column(TEXT, nullable=True)
    image = Column(String(255), nullable=True)
    video = Column(String(100))
    course_id = Column(Integer, ForeignKey('courses_course.id'))
    category_id = Column(Integer, ForeignKey('courses_lessoncategory.id', ondelete='RESTRICT'))
    homework_desc = Column(TEXT, nullable=True)
    comment = Column(TEXT, nullable=True)

    form_id = Column(Integer, ForeignKey('forms_form.id', ondelete='SET NULL'), nullable=True)
    form_pass_rate = Column(SmallInteger, CheckConstraint('form_pass_rate >= 0'),
                            nullable=True, default=0)

    rate_lesson_msg = Column(TEXT, nullable=True)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    course = relationship('CourseTable', back_populates='lessons')
    category = relationship('LessonCategoryTable', back_populates='lessons', lazy='selectin')
    students = relationship('StudentLesson', back_populates='lesson')
    form = relationship('FormTable', back_populates='lesson')

    @validates('form_pass_rate')
    def validate_pass_rate(self, key, value):
        if value > 100:
            raise ValueError('Value cannot be higher than 100')
        return value


class StudentCourse(BaseModel):
    __tablename__ = 'courses_studentcourse'

    course_id = Column(Integer, ForeignKey('courses_course.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users_student.id'), nullable=False)
    has_paid = Column(Boolean, default=False)
    has_finished = Column(Boolean, default=False)

    courses = relationship('CourseTable', back_populates='students')
    students = relationship('StudentTable', back_populates='courses')

    priority_date_deferred = deferred(select([CourseTable.set_priority_date]).where(
        CourseTable.id == course_id).scalar_subquery())


class StudentLesson(BaseModel):
    __tablename__ = 'courses_studentlesson'

    student_id = Column(Integer, ForeignKey('users_student.id'))
    lesson_id = Column(Integer, ForeignKey('courses_lesson.id'))
    is_rated = Column(Boolean, default=False)

    # todo date_received de facto. rename
    date_sent = Column(DateTime, nullable=True)
    date_watched = Column(DateTime, nullable=True)
    homework_sent = Column(DateTime, nullable=True)

    lesson = relationship('LessonTable', back_populates='students')
    student = relationship('StudentTable', back_populates='lessons')


class FormTable(BaseModel):
    class FormType(enum.Enum):
        private = 'private'
        public = 'public'

    class FormMode(enum.Enum):
        quiz = 'quiz'
        questionnaire = 'questionnaire'

    __tablename__ = 'forms_form'

    name = Column(String(50), nullable=False)
    type = Column(Enum(FormType, values_callable=lambda x: [e.value for e in x]), nullable=False,
                  default=FormType.public.value)
    mode = Column(Enum(FormMode, values_callable=lambda x: [e.value for e in x]), nullable=False)
    unique_code = Column(Integer, nullable=True)
    link = Column(String(50), nullable=True)
    start_message = Column(TEXT, nullable=False)
    end_message = Column(sqlalchemy_json.mutable_json_type(dbtype=JSONB, nested=True), nullable=False, default=dict)
    is_active = Column(Boolean, default=False)
    one_off = Column(Boolean, default=False)
    image = Column(String(255), nullable=True)
    access_level = Column(IntEnum(AccessLevel), nullable=False, default=AccessLevel.client.value)

    questions = relationship('FormQuestionTable', back_populates='form',
                             order_by='[FormQuestionTable.position, FormQuestionTable.id]')
    lesson = relationship('LessonTable', back_populates='form')

    @property
    def form_link(self):
        return f'{config.DOMAIN}/admin/forms/form/{self.id}/change/'


class FormQuestionTable(BaseModel):
    __tablename__ = 'forms_formquestion'

    form_id = Column(Integer, ForeignKey('forms_form.id', ondelete='CASCADE'))
    multi_answer = Column(Boolean, default=False)
    text = Column(String(50))
    image = Column(String(255), nullable=True)
    position = Column(Integer, nullable=False)
    custom_answer = Column(Boolean, default=False)
    custom_answer_text = Column(String(50), nullable=True)
    accept_file = Column(Boolean, default=False)
    chat_id = Column(String(255), nullable=True)

    one_row_btns = Column(Boolean, default=False)

    form = relationship('FormTable', back_populates='questions')
    answers = relationship('FormAnswerTable', back_populates='question', foreign_keys='FormAnswerTable.question_id',
                           order_by='FormAnswerTable.id')
    jump_answers = relationship('FormAnswerTable', back_populates='jump_to_question',
                                foreign_keys='FormAnswerTable.jump_to_id')


class FormAnswerTable(BaseModel):
    __tablename__ = 'forms_formanswer'

    is_correct = Column(Boolean, default=False)
    text = Column(String(50), nullable=False)
    question_id = Column(Integer, ForeignKey('forms_formquestion.id', ondelete='CASCADE'), nullable=False)
    jump_to_id = Column(Integer, ForeignKey('forms_formquestion.id', ondelete='CASCADE'), nullable=True)

    question = relationship('FormQuestionTable', back_populates='answers', foreign_keys=[question_id])
    jump_to_question = relationship('FormQuestionTable', back_populates='jump_answers', foreign_keys=[jump_to_id])


class ContactFormTable(BaseModel):
    __tablename__ = 'forms_contactformanswers'

    contact_id = Column(Integer, ForeignKey('contacts_contact.id', ondelete='SET NULL'), nullable=False)
    form_id = Column(Integer, ForeignKey('forms_form.id', ondelete='SET NULL'), nullable=False)
    score = Column(Integer, nullable=True)
    data = Column(sqlalchemy_json.mutable_json_type(dbtype=JSONB, nested=True), nullable=True, default=dict)


class AssetTable(BaseModel):
    __tablename__ = 'assets_asset'

    title = Column(String(50), nullable=False)
    file = Column(String(255), nullable=False)
    desc = Column(TEXT, nullable=True)
    access_level = Column(IntEnum(AccessLevel), nullable=False, default=AccessLevel.client.value)

    contact_asset = relationship('ContactAssetTable', back_populates='asset')


class ContactAssetTable(BaseModel):
    __tablename__ = 'assets_contactasset'

    contact_id = Column(Integer, ForeignKey('contacts_contact.id', ondelete='CASCADE'), nullable=False)
    asset_id = Column(Integer, ForeignKey('assets_asset.id', ondelete='CASCADE'), nullable=False)

    asset = relationship('AssetTable', back_populates='contact_asset')
    contact = relationship('ContactTable', back_populates='contact_asset')


class Message(BaseModel):
    __tablename__ = 'broadcast_message'

    text = Column(TEXT, nullable=False)
    video = Column(String(100), nullable=True)
    image = Column(String(100), nullable=True)
    link = Column(String(255), nullable=True)
    delivery_start_time = Column(DateTime, nullable=False)
    delivery_end_time = Column(DateTime, nullable=True)
    notes = Column(TEXT, nullable=True)


class MessageHistory(BaseModel):
    __tablename__ = 'broadcast_messagehistory'

    contact_id = Column(Integer, ForeignKey('contacts_contact.id', ondelete='CASCADE'), nullable=False)
    message_id = Column(Integer, ForeignKey('broadcast_message.id', ondelete='CASCADE'), nullable=False)
    delivered = Column(Boolean, default=False)
    response = Column(TEXT, nullable=True)
