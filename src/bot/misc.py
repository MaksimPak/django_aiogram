import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from jinja2 import Environment, PackageLoader, select_autoescape

from bot import config

bot = Bot(token=config.BOT_TOKEN)
storage = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT, db=1)
dp = Dispatcher(bot, storage=storage)
jinja_env = Environment(
    loader=PackageLoader('bot'),
    autoescape=select_autoescape()
)

# Configure logging
logging.basicConfig(level=logging.INFO)


def setup():
    from bot.utils import executor

    logging.info("Configuring handlers...")
    # noinspection PyUnresolvedReferences
    import bot.handlers

    executor.setup()
