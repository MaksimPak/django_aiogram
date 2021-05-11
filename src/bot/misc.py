import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from bot import config


os.environ['DJANGO_SETTINGS_MODULE'] = 'app.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"  # Remove?

bot = Bot(token=config.BOT_TOKEN)
storage = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT, db=1)
dp = Dispatcher(bot, storage=storage)

# Configure logging
logging.basicConfig(level=logging.INFO)


def setup():
    from bot import filters
    from bot.utils import executor

    filters.setup(dp)

    logging.info("Configuring handlers...")
    # noinspection PyUnresolvedReferences
    import bot.handlers

    executor.setup()
