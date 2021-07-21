import hashlib
from dataclasses import dataclass
from typing import Iterable, Union

from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton,
    ReplyKeyboardMarkup, InputFile
)

from bot import config
from bot.misc import bot
from bot.models.dashboard import FormTable, FormQuestionTable, FormAnswerTable
from bot.utils.callback_settings import (
    simple_data,
    short_data,
    two_valued_data,
    three_valued_data
)
from bot.utils.redis_connections import DATABASES

question_redis = RedisStorage2(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=DATABASES['QUESTION_DATA']
)


class MessageSender:
    def __init__(self, chat_id: int, text: str = None, photo: str = None,
                 video: str = None, duration: int = None, width: int = None,
                 height: int = None, thumbnail: Union[int, str] = None,
                 markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None):
        self.chat_id = chat_id
        self.text = text
        self.photo = photo
        self.video = video
        self.duration = duration
        self.width = width
        self.height = height
        self.thumbnail = thumbnail
        self.markup = markup

    def set_media(self, attr, value):
        setattr(self, attr, value)

    async def _send(self):
        if self.photo:
            resp = await bot.send_photo(
                self.chat_id,
                self.photo,
                self.text,
                'html',
                reply_markup=self.markup
            )
        elif self.video:
            resp = await bot.send_video(
                self.chat_id,
                self.video,
                self.duration,
                self.width,
                self.height,
                self.thumbnail,
                self.text,
                'html',
                reply_markup=self.markup

            )
        else:
            resp = await bot.send_message(
                self.chat_id,
                self.text,
                reply_markup=self.markup
            )

        return resp

    async def _cache_media(self):
        redis = await question_redis.redis()
        media_attr = 'photo' if self.photo else 'video'
        hashed_filepath = hashlib.md5(getattr(self, media_attr).encode()).hexdigest()
        media_object = await redis.get(hashed_filepath, encoding='utf8')
        wait_message = None

        if not media_object:
            wait_message = await bot.send_message(self.chat_id, 'Пожалуйста, подождите ⏳')
            media_object = InputFile(f'media/{getattr(self, media_attr)}')

        self.set_media(media_attr, media_object)

        resp = await self._send()

        if wait_message:
            await wait_message.delete()
            await redis.set(hashed_filepath, getattr(resp, media_attr)[-1].file_id)

    async def send(self):
        if self.photo or self.video:
            resp = await self._cache_media()
        else:
            resp = await self._send()
        return resp


class KeyboardGenerator:
    def __init__(self, data: Iterable = None, keyboard=None, **kwargs):
        if keyboard:
            self.keyboard = keyboard
        else:
            self.keyboard = InlineKeyboardMarkup(**kwargs)
        if data:
            self.add(data)

    def add(self, buttons: Iterable):
        self.keyboard.add(
            *self.prepare_buttons(buttons)
        )
        return self

    @staticmethod
    def prepare_buttons(buttons):
        btns = []
        buttons = [buttons] if not isinstance(buttons, list) else buttons
        for title, props in buttons:

            callback = None
            props_len = len(props)
            if props_len == 1:
                callback = simple_data.new(value=props[0])
            elif props_len == 2:
                callback = short_data.new(
                    property=props[0], value=props[1]
                )
            elif props_len == 3:
                callback = two_valued_data.new(
                    property=props[0], first_value=props[1], second_value=props[2]
                )
            elif props_len == 4:
                callback = three_valued_data.new(
                    property=props[0],
                    first_value=props[1],
                    second_value=props[2],
                    third_value=props[3],
                )
            btns.append(
                InlineKeyboardButton(str(title), callback_data=callback)
            )
        return btns

    @staticmethod
    async def main_kb():
        btns = [
            KeyboardButton('📝 Курсы'),
            KeyboardButton('🧑‍🎓 Профиль'),
            KeyboardButton('📚 Домашка'),
            KeyboardButton('🤔 Опросники'),
        ]
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*btns)

        return kb

    @staticmethod
    async def main_kb_inline(client_id):
        kb = InlineKeyboardMarkup().add(*[
            InlineKeyboardButton('Курсы', callback_data=short_data.new(property='course', value=client_id)),
            InlineKeyboardButton('Профиль', callback_data=short_data.new(property='student', value=client_id)),
            InlineKeyboardButton('Задания', callback_data=short_data.new(property='tasks', value=client_id)),
        ])
        return kb


@dataclass
class FormButtons(KeyboardGenerator):
    form: FormTable
    question: FormQuestionTable = None
    answer: FormAnswerTable = None

    async def mark_selected(
            self,
            answer_id: int,
            question_id: int,
            keyboard: dict
    ):
        for key in keyboard['inline_keyboard'][0]:
            if int(key['callback_data'][-1]) == answer_id and key['text'][0] != '✅':
                key['text'] = '✅ ' + key['text']
            elif int(key['callback_data'][-1]) == answer_id and key['text'][0] == '✅':
                key['text'] = key['text'][1:]
        self.keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard['inline_keyboard'])
        if self.keyboard.inline_keyboard[-1][-1].text != 'Следующий вопрос':
            self.add(('Следующий вопрос', ('proceed', question_id)))

        return self.keyboard

    async def question_buttons(self):
        kb = None
        if self.form.mode.value == 'quiz':
            data = [(answer.text, ('answer', answer.id)) for answer in self.question.answers]
            kb = KeyboardGenerator(data).keyboard
        return kb
