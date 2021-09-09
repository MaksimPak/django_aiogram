import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union, List, Tuple, Any

from aiogram import types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton,
    ReplyKeyboardMarkup, InputFile
)

from bot import config
from bot.config import DATABASES
from bot.misc import bot
from bot.models.dashboard import FormTable, FormQuestionTable, FormAnswerTable
from bot.utils.callback_settings import (
    simple_data,
    short_data,
    two_valued_data,
    three_valued_data
)

question_redis = RedisStorage2(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=DATABASES['CUSTOM_DATA']
)
ROOT_DIR = Path(__file__).parent.parent


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
                reply_markup=self.markup
            )
        elif self.video:
            resp = await bot.send_video(
                self.chat_id,
                self.video,
                self.duration,
                self.width,
                self.height,
                InputFile(ROOT_DIR / 'media' / self.thumbnail),
                self.text,
                reply_markup=self.markup

            )
        else:
            resp = await bot.send_message(
                self.chat_id,
                self.text,
                reply_markup=self.markup
            )

        return resp

    @staticmethod
    async def _get_file_id(response: types.Message, media_attr: str):
        if media_attr == 'video':
            return response.video.file_id
        else:
            return response.photo[-1].file_id

    async def _cache_media(self):
        redis = await question_redis.redis()
        media_attr = 'photo' if self.photo else 'video'
        path = ROOT_DIR / 'media' / getattr(self, media_attr)
        hashed_filepath = hashlib.md5(str(path).encode()).hexdigest()
        media_object = await redis.get(hashed_filepath, encoding='utf8')
        wait_message = None

        if not media_object:
            wait_message = await bot.send_message(self.chat_id, 'Пожалуйста, подождите ⏳')
            media_object = InputFile(path)

        self.set_media(media_attr, media_object)

        resp = await self._send()

        if wait_message:
            await wait_message.delete()
            key = await self._get_file_id(resp, media_attr)
            await redis.set(hashed_filepath, key)

    async def send(self):
        if self.photo or self.video:
            resp = await self._cache_media()
        else:
            resp = await self._send()
        return resp


class KeyboardGenerator:
    def __init__(self, data: List[Tuple[Any, Tuple[Union[str, int], ...]]] = None,
                 keyboard=None, **kwargs):
        if keyboard:
            self.keyboard = keyboard
        else:
            self.keyboard = InlineKeyboardMarkup(**kwargs)
        if data:
            self.add(data)

    def add(self, buttons: Union[Tuple[Any, Tuple[Union[str, int], ...]], Iterable]):
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
    async def main_kb(contact=None):
        btns = [
            KeyboardButton('📝 Курсы'),
            KeyboardButton('🧑‍🎓 Профиль'),
            KeyboardButton('📚 Домашка'),
            KeyboardButton('🤔 Опросники'),
            KeyboardButton('🏫 Центры'),
        ]

        if contact:
            btns = [
                KeyboardButton('🧑‍🎓 Профиль'),
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
            position: int,
            keyboard: dict
    ):
        # todo REFACTOR
        for row in keyboard['inline_keyboard']:
            for key in row:
                cb_answer_id = key['callback_data'].split('|')[-1]
                if cb_answer_id.isdigit():
                    if int(cb_answer_id) == answer_id and key['text'][0] != '✅':
                        key['text'] = '✅ ' + key['text']
                    elif int(cb_answer_id) == answer_id and key['text'][0] == '✅':
                        key['text'] = key['text'][1:]
        self.keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard['inline_keyboard'])
        if self.keyboard.inline_keyboard[-1][-1].text != 'Следующий вопрос ➡️':
            self.add(('Следующий вопрос ➡️', ('proceed', question_id, position)))

        return self.keyboard

    async def question_buttons(self):
        data = [(answer.text, ('answer', answer.id)) for answer in self.question.answers]
        row_width = 1 if self.question.one_row_btns else 3
        kb = KeyboardGenerator(data, row_width=row_width)
        if self.question.custom_answer:
            text = self.question.custom_answer_text if self.question.custom_answer_text else 'Другое'
            kb.add((text, ('custom_answer',)))
        return kb.keyboard
