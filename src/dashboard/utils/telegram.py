import hashlib
import os
from io import BufferedReader
from typing import Dict, List, Any
from django.conf import settings
import redis
import requests

redis = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    db=settings.REDIS_CUSTOM_DATA
)


class Telegram:
    @staticmethod
    def send_single_message(data):
        url = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendMessage'
        return requests.post(url, data=data).json()

    @staticmethod
    def send_to_people(people, message, kb=None):
        for person in people:
            data = {
                'chat_id': person.tg_id,
                'text': message,
                'parse_mode': 'html',
            }
            if kb:
                data['reply_markup'] = kb
            Telegram.send_single_message(data=data)

    @staticmethod
    def video_to_person(data, thumb, video=None):
        url = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendVideo'
        files = {'video': video, 'thumb': thumb}
        return requests.post(url, files=files, data=data).json()


class TelegramSender:
    def __init__(self, chat_id: int, text: str = None, photo: str = None,
                 video: str = None, duration: int = None, width: int = None,
                 height: int = None, thumbnail: str = None,
                 markup: Dict[str, List[List[Dict[str, Any]]]] = None):
        self.chat_id = chat_id
        self.text = text
        self.photo = photo
        self.video = video
        self.duration = duration
        self.width = width
        self.height = height
        self.thumbnail = thumbnail
        self.markup = markup
        self.base_url = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/'
        self.data = {
            'chat_id': self.chat_id,
            'parse_mode': 'html',
        }
        if markup:
            self.data['reply_markup'] = markup

    def send_video(self):
        if self.photo:
            raise TypeError('Cannot send video and image together')
        url = self.base_url + 'sendVideo'
        self.data['caption'] = self.text
        self.data['duration'] = self.duration
        self.data['width'] = self.width
        self.data['height'] = self.height

        files = {'thumb': open(self.thumbnail, 'rb')}
        if type(self.video) is not BufferedReader:
            self.data['video'] = self.video
        else:
            files['video'] = self.video
        return requests.post(url, files=files, data=self.data).json()

    def send_image(self):
        if self.video:
            raise TypeError('Cannot send video and image together')
        url = self.base_url + 'sendPhoto'
        self.data['caption'] = self.text
        files = {}
        if type(self.photo) is not BufferedReader:
            self.data['photo'] = self.photo
        else:
            files['photo'] = self.photo

        return requests.post(url, files=files, data=self.data).json()

    def send_message(self):
        url = self.base_url + 'sendMessage'
        self.data['text'] = self.text
        return requests.post(url, data=self.data).json()

    def _send(self):
        if self.photo:
            resp = self.send_image()
        elif self.video:
            resp = self.send_video()
        else:
            resp = self.send_message()
        return resp

    def set_media(self, attr, value):
        setattr(self, attr, value)

    @staticmethod
    def _get_file_id(response, media_attr: str):
        if media_attr == 'video':
            return response['result'][media_attr]['file_id']
        else:
            return response['result'][media_attr][-1]['file_id']

    def _cache_media(self):
        media_attr = 'photo' if self.photo else 'video'
        hashed_filepath = hashlib.md5(getattr(self, media_attr).encode()).hexdigest()
        media_object = redis.get(hashed_filepath)
        wait = False

        if not media_object:
            wait = True
            media_object = open(f'{getattr(self, media_attr)}', 'rb')

        self.set_media(media_attr, media_object)

        resp = self._send()

        if wait:
            file_id = self._get_file_id(resp, media_attr)
            redis.set(hashed_filepath, file_id)

        return resp

    def send(self):
        if self.photo or self.video:
            resp = self._cache_media()
        else:
            resp = self._send()
        return resp
