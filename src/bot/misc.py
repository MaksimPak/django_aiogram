import logging
import os

from aiogram import Bot, Dispatcher

from bot import config


os.environ['DJANGO_SETTINGS_MODULE'] = 'app.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"  # Remove?

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# Configure logging
logging.basicConfig(level=logging.INFO)


def setup():
    from bot.utils import executor
    import django

    django.setup()

    logging.info("Configuring handlers...")
    # noinspection PyUnresolvedReferences
    import bot.handlers

    executor.setup()
