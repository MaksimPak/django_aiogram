import os

import requests


class Telegram:
    @staticmethod
    def send_single_message(data):
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
        return requests.post(url, data=data).json()

    @staticmethod
    def send_messages(people, message, kb=None):
        for person in people:
            data = {
                'chat_id': person.tg_id,
                'text': message,
            }
            if kb:
                data['reply_markup'] = kb
            Telegram.send_single_message(data=data)
