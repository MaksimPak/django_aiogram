from typing import Iterable

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from bot.utils.callback_settings import simple_data, short_data, two_valued_data, three_valued_data


class KeyboardGenerator:
    def __init__(self, data: Iterable = None, **kwargs):
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
